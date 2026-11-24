"""SQL for looking up and adding customers."""


def search_customers(db, search_text):
    """Customers whose name or phone matches the search, with their order count.

    An empty search lists every customer. The LEFT JOIN keeps customers who
    have never ordered (they show 0 orders).
    """
    like = f"%{search_text}%"
    digits = "".join(ch for ch in search_text if ch.isdigit())
    # Only match phone numbers when the search actually has digits in it,
    # otherwise "%%" would match every phone number.
    phone_like = f"%{digits}%" if digits else None
    return db.execute(
        """
        SELECT customer.customer_id, customer.name, customer.phone,
               customer.alt_name, customer.alt_phone,
               COUNT(customer_order.order_id) AS order_count
        FROM customer
            LEFT JOIN customer_order ON customer_order.customer_id = customer.customer_id
        WHERE ? = ''
           OR customer.name LIKE ?
           OR customer.alt_name LIKE ?
           OR customer.phone LIKE ?
           OR customer.alt_phone LIKE ?
        GROUP BY customer.customer_id
        ORDER BY customer.name
        """,
        (search_text, like, like, phone_like, phone_like),
    ).fetchall()


def get_customer(db, customer_id):
    return db.execute(
        "SELECT * FROM customer WHERE customer_id = ?", (customer_id,)
    ).fetchone()


def list_customers(db):
    return db.execute(
        "SELECT customer_id, name, phone FROM customer ORDER BY name"
    ).fetchall()


def get_order_history(db, customer_id):
    """Every order for a customer with its items, newest season first.

    Joins customer_order, customer_items and product. The LEFT JOINs keep an
    order on the list even if no items have been added to it yet.
    """
    return db.execute(
        """
        SELECT customer_order.order_id, customer_order.pick_up_year,
               customer_order.pick_up_month, customer_order.pick_up_day,
               customer_order.is_ready, customer_order.is_picked_up,
               customer_order.notes AS order_notes,
               customer_items.item_id, customer_items.quantity,
               customer_items.weight_lb, customer_items.is_done,
               product.product_name, product.grade
        FROM customer_order
            LEFT JOIN customer_items ON customer_items.order_id = customer_order.order_id
            LEFT JOIN product ON product.product_id = customer_items.product_id
        WHERE customer_order.customer_id = ?
        ORDER BY customer_order.pick_up_year DESC, customer_order.pick_up_month,
                 customer_order.pick_up_day, customer_items.item_id
        """,
        (customer_id,),
    ).fetchall()


def add_customer(db, name, phone, alt_name, alt_phone, notes):
    """Insert a customer and return the new id.

    Doesn't commit, so the caller can save it together with the customer's
    first order in one transaction.
    """
    cursor = db.execute(
        """
        INSERT INTO customer (name, phone, alt_name, alt_phone, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, phone, alt_name, alt_phone, notes),
    )
    return cursor.lastrowid
