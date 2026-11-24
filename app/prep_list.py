"""SQL for the daily prep list."""
from datetime import date

CATEGORIES = ["rib_roast", "tenderloin", "beef", "pork", "poultry", "charcuterie", "provisions"]


def pickup_dates(db):
    """Every pickup date that has an order, as date objects."""
    rows = db.execute(
        """
        SELECT DISTINCT pick_up_year, pick_up_month, pick_up_day
        FROM customer_order
        ORDER BY pick_up_year, pick_up_month, pick_up_day
        """
    ).fetchall()
    return [date(row[0], row[1], row[2]) for row in rows]


def default_pickup_date(dates):
    """The next pickup date from today, or the last one if they're all past."""
    today = date.today()
    for pickup in dates:
        if pickup >= today:
            return pickup
    return dates[-1] if dates else today


def orders_for_day(db, pickup):
    """The orders picking up on one day, with the customer's name."""
    return db.execute(
        """
        SELECT customer_order.order_id, customer_order.is_ready,
               customer_order.is_picked_up, customer_order.notes,
               customer.name, customer.phone, customer.alt_name, customer.alt_phone
        FROM customer_order
            JOIN customer ON customer.customer_id = customer_order.customer_id
        WHERE customer_order.pick_up_year = ?
          AND customer_order.pick_up_month = ?
          AND customer_order.pick_up_day = ?
        ORDER BY customer.name
        """,
        (pickup.year, pickup.month, pickup.day),
    ).fetchall()


def items_for_day(db, pickup, category, customer_search):
    """The items to prep on one day, from the v_daily_prep_list view.

    The view already joins orders, customers, products and the three detail
    tables, so the filters here are just WHERE conditions. An empty category
    or customer search means "don't filter on it".
    Note: the view's `ready` column is the item's is_done flag.
    """
    return db.execute(
        """
        SELECT *
        FROM v_daily_prep_list
        WHERE year = ? AND month = ? AND day = ?
          AND (? = '' OR category = ?)
          AND (? = '' OR name LIKE ?)
        ORDER BY category, item_name, item_id
        """,
        (pickup.year, pickup.month, pickup.day,
         category, category,
         customer_search, f"%{customer_search}%"),
    ).fetchall()
