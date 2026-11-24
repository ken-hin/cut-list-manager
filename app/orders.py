"""SQL for orders and the items on them."""


class StockError(Exception):
    """Raised when an item would go over a product's stock limit."""


# ---------------------------------------------------------------- products

def list_products(db):
    """Active catalog products for the 'add item' dropdown."""
    return db.execute(
        """
        SELECT product_id, product_name, grade, is_frozen, category, sold_by, price_cents
        FROM product
        WHERE is_active = 1
        ORDER BY category, product_name, grade
        """
    ).fetchall()


def get_product(db, product_id):
    return db.execute(
        "SELECT * FROM product WHERE product_id = ? AND is_active = 1", (product_id,)
    ).fetchone()


# ------------------------------------------------------------------ orders

def get_order(db, order_id):
    """One order with its customer's name and phone numbers."""
    return db.execute(
        """
        SELECT customer_order.*, customer.name, customer.phone, customer.alt_name, customer.alt_phone
        FROM customer_order
	             JOIN customer ON customer.customer_id = customer_order.customer_id
        WHERE customer_order.order_id = ?
        """,
        (order_id,),
    ).fetchone()


def get_order_items(db, order_id):
    """The items on an order with their product and any cutting details."""
    return db.execute(
        """
        SELECT customer_items.*, product.product_name, product.grade,
               product.category, product.sold_by, product.is_frozen,
               rib_roast_detail.num_bones, rib_roast_detail.frenched_bones,
               rib_roast_detail.end_preference, rib_roast_detail.bones_tied_on,
               tenderloin_detail.cut_style, tenderloin_detail.filet_thickness_in,
               tenderloin_detail.grind_trim,
               charcuterie_detail.nut_option, charcuterie_detail.meat_preferences,
               charcuterie_detail.cheese_preferences
        FROM customer_items
            JOIN product ON product.product_id = customer_items.product_id
            LEFT JOIN rib_roast_detail ON rib_roast_detail.item_id = customer_items.item_id
            LEFT JOIN tenderloin_detail ON tenderloin_detail.item_id = customer_items.item_id
            LEFT JOIN charcuterie_detail ON charcuterie_detail.item_id = customer_items.item_id
        WHERE customer_items.order_id = ?
        ORDER BY customer_items.item_id
        """,
        (order_id,),
    ).fetchall()


def add_order(db, customer_id, pickup, notes):
    """Insert an order and return its id. The caller commits."""
    cursor = db.execute(
        """
        INSERT INTO customer_order (customer_id, pick_up_month, pick_up_day, pick_up_year, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (customer_id, pickup.month, pickup.day, pickup.year, notes),
    )
    return cursor.lastrowid


def change_pickup_date(db, order_id, pickup):
    db.execute(
        """
        UPDATE customer_order
        SET pick_up_month = ?, pick_up_day = ?, pick_up_year = ?
        WHERE order_id = ?
        """,
        (pickup.month, pickup.day, pickup.year, order_id),
    )
    db.commit()


def set_order_ready(db, order_id, is_ready):
    db.execute(
        "UPDATE customer_order SET is_ready = ? WHERE order_id = ?", (is_ready, order_id)
    )
    db.commit()


def set_order_picked_up(db, order_id, is_picked_up):
    # An order that's picked up was obviously ready, so set both.
    # Un-marking only clears is_picked_up.
    if is_picked_up:
        db.execute(
            "UPDATE customer_order SET is_ready = 1, is_picked_up = 1 WHERE order_id = ?",
            (order_id,),
        )
    else:
        db.execute(
            "UPDATE customer_order SET is_picked_up = 0 WHERE order_id = ?", (order_id,)
        )
    db.commit()


def delete_order(db, order_id):
    """Cancel an order. ON DELETE CASCADE removes its items and their details."""
    db.execute("DELETE FROM customer_order WHERE order_id = ?", (order_id,))
    db.commit()


# ------------------------------------------------------------------- items

def get_item(db, item_id):
    return db.execute(
        """
        SELECT customer_items.*, product.category, product.stock_limit,
               customer_order.pick_up_year
        FROM customer_items
            JOIN product ON product.product_id = customer_items.product_id
            JOIN customer_order ON customer_order.order_id = customer_items.order_id
        WHERE customer_items.item_id = ?
        """,
        (item_id,),
    ).fetchone()


def stock_used(db, product, year, skip_item_id=None):
    """How much of a product's stock is already ordered for a season.

    Rib roasts are counted in bones (num_bones x quantity), everything else
    in units. skip_item_id leaves out the item being edited.
    """
    if product["category"] == "rib_roast":
        sql = """
            SELECT SUM(rib_roast_detail.num_bones * customer_items.quantity) AS used
            FROM customer_items
                JOIN rib_roast_detail ON rib_roast_detail.item_id = customer_items.item_id
                JOIN customer_order ON customer_order.order_id = customer_items.order_id
            WHERE customer_items.product_id = ?
              AND customer_order.pick_up_year = ?
              AND customer_items.item_id IS NOT ?
        """
    else:
        sql = """
            SELECT SUM(customer_items.quantity) AS used
            FROM customer_items
                JOIN customer_order ON customer_order.order_id = customer_items.order_id
            WHERE customer_items.product_id = ?
              AND customer_order.pick_up_year = ?
              AND customer_items.item_id IS NOT ?
        """
    row = db.execute(sql, (product["product_id"], year, skip_item_id)).fetchone()
    return row["used"] or 0


def check_stock(db, product, year, amount, skip_item_id=None):
    """Raise StockError if adding `amount` would go over the stock limit."""
    if product["stock_limit"] is None:
        return
    left = product["stock_limit"] - stock_used(db, product, year, skip_item_id)
    if amount > left:
        unit = "bones" if product["category"] == "rib_roast" else "left"
        raise StockError(
            f"Not enough {product['product_name']} for {year}: only {left} {unit} in stock."
        )


def add_item(db, order, product, quantity, weight_lb, thickness_in, notes, detail):
    """Add an item, plus its detail row for rib roasts, tenderloins and boards.

    Both inserts run in one transaction: if the detail row fails, the item
    isn't saved either, so there's never a rib roast with no bone count.
    `detail` holds the category-specific fields from the form.
    """
    amount = quantity
    if product["category"] == "rib_roast":
        amount = quantity * detail["num_bones"]
    check_stock(db, product, order["pick_up_year"], amount)

    try:
        cursor = db.execute(
            """
            INSERT INTO customer_items
                (order_id, product_id, quantity, weight_lb, thickness_in, unit_price_cents, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            # The current catalog price is copied onto the item.
            (order["order_id"], product["product_id"], quantity, weight_lb,
             thickness_in, product["price_cents"], notes),
        )
        item_id = cursor.lastrowid

        if product["category"] == "rib_roast":
            db.execute(
                """
                INSERT INTO rib_roast_detail (item_id, num_bones, frenched_bones, end_preference, bones_tied_on)
                VALUES (?, ?, ?, ?, ?)
                """,
                (item_id, detail["num_bones"], detail["frenched_bones"],
                 detail["end_preference"], detail["bones_tied_on"]),
            )
        elif product["category"] == "tenderloin":
            db.execute(
                """
                INSERT INTO tenderloin_detail (item_id, cut_style, filet_thickness_in, grind_trim)
                VALUES (?, ?, ?, ?)
                """,
                (item_id, detail["cut_style"], detail["filet_thickness_in"], detail["grind_trim"]),
            )
        elif product["category"] == "charcuterie":
            db.execute(
                """
                INSERT INTO charcuterie_detail (item_id, nut_option, meat_preferences, cheese_preferences)
                VALUES (?, ?, ?, ?)
                """,
                (item_id, detail["nut_option"], detail["meat_preferences"],
                 detail["cheese_preferences"]),
            )
        db.commit()
    except Exception:
        db.rollback()
        raise


def update_item(db, item, quantity, weight_lb, notes):
    """Change an item's quantity, weight or notes, re-checking stock."""
    product = db.execute(
        "SELECT * FROM product WHERE product_id = ?", (item["product_id"],)
    ).fetchone()
    amount = quantity
    if product["category"] == "rib_roast":
        bones = db.execute(
            "SELECT num_bones FROM rib_roast_detail WHERE item_id = ?", (item["item_id"],)
        ).fetchone()
        amount = quantity * (bones["num_bones"] if bones else 0)
    check_stock(db, product, item["pick_up_year"], amount, skip_item_id=item["item_id"])

    db.execute(
        "UPDATE customer_items SET quantity = ?, weight_lb = ?, notes = ? WHERE item_id = ?",
        (quantity, weight_lb, notes, item["item_id"]),
    )
    db.commit()


def set_item_done(db, item_id, is_done):
    db.execute(
        "UPDATE customer_items SET is_done = ? WHERE item_id = ?", (is_done, item_id)
    )
    db.commit()


def delete_item(db, item_id):
    """Remove one item. ON DELETE CASCADE removes its detail row."""
    db.execute("DELETE FROM customer_items WHERE item_id = ?", (item_id,))
    db.commit()
