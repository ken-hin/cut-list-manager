"""SQL for the reports page. Every report is for one season (pickup year)."""


def seasons(db):
    rows = db.execute(
        "SELECT DISTINCT pick_up_year FROM customer_order ORDER BY pick_up_year DESC"
    ).fetchall()
    return [row["pick_up_year"] for row in rows]


def rib_roasts_by_day(db, year):
    """How many rib roasts and bones go out on each pickup day."""
    return db.execute(
        """
        SELECT customer_order.pick_up_month, customer_order.pick_up_day,
               COUNT(*) AS rib_roasts,
               SUM(rib_roast_detail.num_bones * customer_items.quantity) AS total_bones,
               SUM(customer_items.is_done) AS roasts_cut
        FROM rib_roast_detail
            JOIN customer_items ON customer_items.item_id = rib_roast_detail.item_id
            JOIN customer_order ON customer_order.order_id = customer_items.order_id
        WHERE customer_order.pick_up_year = ?
        GROUP BY customer_order.pick_up_month, customer_order.pick_up_day
        ORDER BY customer_order.pick_up_month, customer_order.pick_up_day
        """,
        (year,),
    ).fetchall()


def orders_with_work_left(db, year):
    """Orders that still have items left to cut."""
    return db.execute(
        """
        SELECT customer_order.order_id, customer.name,
               customer_order.pick_up_month, customer_order.pick_up_day,
               COUNT(*) AS items_on_order,
               SUM(customer_items.is_done) AS items_done
        FROM customer_order
            JOIN customer ON customer.customer_id = customer_order.customer_id
            JOIN customer_items ON customer_items.order_id = customer_order.order_id
        WHERE customer_order.pick_up_year = ?
        GROUP BY customer_order.order_id
        HAVING SUM(customer_items.is_done) < COUNT(*)
        ORDER BY customer_order.pick_up_month, customer_order.pick_up_day, customer.name
        """,
        (year,),
    ).fetchall()


def product_totals(db, year):
    """How much of each product was ordered this season, and its stock limit.

    Rib roasts are listed separately in bones by rib_roast_stock().
    """
    return db.execute(
        """
        SELECT product.product_name, product.grade, product.is_frozen, product.category,
               product.sold_by, product.stock_limit,
               COUNT(*) AS order_lines,
               SUM(customer_items.quantity) AS units_ordered
        FROM product
            JOIN customer_items ON customer_items.product_id = product.product_id
            JOIN customer_order ON customer_order.order_id = customer_items.order_id
        WHERE customer_order.pick_up_year = ?
          AND product.category <> 'rib_roast'
        GROUP BY product.product_id
        ORDER BY units_ordered DESC, product.product_name
        """,
        (year,),
    ).fetchall()


def rib_roast_stock(db, year):
    """Bones ordered for each rib roast product this season, and the bone limit."""
    return db.execute(
        """
        SELECT product.product_name, product.grade, product.stock_limit,
               COUNT(*) AS rib_roasts,
               SUM(rib_roast_detail.num_bones * customer_items.quantity) AS bones_ordered
        FROM product
            JOIN customer_items ON customer_items.product_id = product.product_id
            JOIN rib_roast_detail ON rib_roast_detail.item_id = customer_items.item_id
            JOIN customer_order ON customer_order.order_id = customer_items.order_id
        WHERE customer_order.pick_up_year = ?
        GROUP BY product.product_id
        ORDER BY product.grade DESC
        """,
        (year,),
    ).fetchall()


def returning_customers(db, year):
    """Last season's customers who haven't ordered for this season yet."""
    return db.execute(
        """
        SELECT customer_id, name, phone, alt_name, alt_phone
        FROM customer
        WHERE customer_id IN (SELECT customer_id FROM customer_order WHERE pick_up_year = ?)
          AND customer_id NOT IN (SELECT customer_id FROM customer_order WHERE pick_up_year = ?)
        ORDER BY name
        """,
        (year - 1, year),
    ).fetchall()
