"""Cut List Manager - Jesse's Butcher Shop holiday orders.

A small Flask web app on top of the SQLite database from Deliverables 3 and 4.
Pages:
    /prep        Daily prep list (home page)
    /customers   Customer search and order history
    /orders/new  New order
    /orders/<id> One order: add, edit and remove items, change the date, cancel
    /reports     Season reports

Run it with:  flask --app app run   (see README.md)
"""
import os
import sqlite3
from datetime import date

from flask import Flask, abort, flash, redirect, render_template, request, url_for

import customers
import orders
import prep_list
import reports
import validation
from db import DEFAULT_DB_PATH, DatabaseMissingError, close_db, get_db, init_db
from orders import StockError
from validation import ValidationError

app = Flask(__name__)
app.config["DATABASE"] = os.environ.get("CUTLIST_DB", DEFAULT_DB_PATH)
# Only used to sign the one-time messages shown after a save.
app.config["SECRET_KEY"] = os.environ.get("CUTLIST_SECRET_KEY", "dev-only-change-me")
app.teardown_appcontext(close_db)


@app.cli.command("init-db")
def init_db_command():
    """flask --app app init-db : rebuild the database from the SQL files."""
    init_db(app.config["DATABASE"])
    print(f"Created {app.config['DATABASE']} from schema.sql and insert_data.sql.")


# ------------------------------------------------------- display helpers

GRADE_NAMES = {"P": "Prime", "C": "Choice", "AUS": "Australian Wagyu",
               "JPN": "Japanese A5 Wagyu", "NA": ""}
CATEGORY_NAMES = {"rib_roast": "Rib Roast", "tenderloin": "Tenderloin", "beef": "Beef",
                  "pork": "Pork", "poultry": "Poultry", "charcuterie": "Charcuterie",
                  "provisions": "Provisions"}
CUT_STYLES = {"whole": "Whole", "halved": "Halved", "filets": "Cut into filets",
              "chateau": "Chateau", "chateau_and_filets": "Chateau + filets"}
NUT_OPTIONS = {"included": "Nuts included", "on_side": "Nuts on the side", "none": "No nuts"}
END_PREFERENCES = {"none": "No preference", "chuck": "Chuck end", "loin": "Loin end"}


@app.context_processor
def display_names():
    return dict(GRADE_NAMES=GRADE_NAMES, CATEGORY_NAMES=CATEGORY_NAMES,
                CUT_STYLES=CUT_STYLES, NUT_OPTIONS=NUT_OPTIONS,
                END_PREFERENCES=END_PREFERENCES)


@app.template_filter("money")
def money(cents):
    return f"${cents / 100:,.2f}"


@app.template_filter("phone")
def format_phone(digits):
    """8655550101 -> (865) 555-0101. Phones are stored as 10 digits."""
    if not digits:
        return ""
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"


@app.template_filter("nice_date")
def nice_date(pickup):
    return f"{pickup.strftime('%a, %b')} {pickup.day}, {pickup.year}"


@app.template_filter("short_date")
def short_date(pickup):
    """Wed, Dec 23 - for tables where the season is already shown."""
    return f"{pickup.strftime('%a, %b')} {pickup.day}"


@app.template_filter("counted")
def counted(number, word):
    """3, 'order' -> '3 orders'; 1, 'order' -> '1 order'."""
    return f"{number} {word}{'' if number == 1 else 's'}"


@app.template_global()
def season_day(year, row):
    """Build a date from a season year and a row's pick_up_month/day columns."""
    return date(year, row["pick_up_month"], row["pick_up_day"])


@app.template_global()
def pickup_of(row):
    """Build a date from a row's pick_up_year/month/day columns."""
    return date(row["pick_up_year"], row["pick_up_month"], row["pick_up_day"])


# ------------------------------------------------------- error handling

def friendly_db_error(error):
    """Turn a SQLite constraint error into a message staff can act on."""
    text = str(error)
    if "UNIQUE constraint failed: customer_order" in text:
        return "That customer already has an order on that pickup day. Add the items to that order instead."
    if "UNIQUE" in text:
        return "That record already exists."
    if "FOREIGN KEY" in text:
        return "That record is linked to other data, so it can't be changed that way."
    if "is_picked_up <= is_ready" in text:
        return "An order has to be marked ready before it can be picked up."
    if "CHECK" in text:
        return "One of the values is outside what the shop allows."
    return "That change couldn't be saved."


def try_to_save(action, success_message):
    """Run a database change and show a success or error message.

    Returns True if it worked. Validation and stock problems show their own
    message; database errors show a friendly one instead of the raw error.
    """
    try:
        action()
    except (ValidationError, StockError) as error:
        flash(str(error), "error")
        return False
    except sqlite3.IntegrityError as error:
        get_db().rollback()
        flash(friendly_db_error(error), "error")
        return False
    except sqlite3.Error:
        get_db().rollback()
        app.logger.exception("Database error")
        flash("Something went wrong saving to the database. Nothing was changed.", "error")
        return False
    flash(success_message, "success")
    return True


def back_to(fallback):
    """Redirect to the page the form came from (only local paths)."""
    next_url = request.form.get("next", "")
    if next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    return redirect(fallback)


def form_id(name):
    """Read an id from the form; a missing or non-numeric id is a 400 error."""
    try:
        return int(request.form.get(name, ""))
    except ValueError:
        abort(400)


@app.errorhandler(400)
def bad_request(error):
    return render_template("error.html", message="That request was missing something."), 400


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", message="That page or record doesn't exist."), 404


@app.errorhandler(DatabaseMissingError)
def database_missing(error):
    """The database hasn't been created yet: say how to fix it."""
    app.logger.error(str(error))
    return render_template("error.html", message="The database hasn't been set up yet.",
                           detail=str(error)), 503


@app.errorhandler(500)
def server_error(error):
    return render_template("error.html", message="Something went wrong. Please try again."), 500


# ------------------------------------------------------- prep list (home)

@app.route("/")
def home():
    return redirect(url_for("prep_list_page"))


@app.route("/prep")
def prep_list_page():
    db = get_db()
    dates = prep_list.pickup_dates(db)
    try:
        pickup = validation.pickup_date(request.args["date"])
    except (KeyError, ValidationError):
        pickup = prep_list.default_pickup_date(dates)

    category = request.args.get("category", "")
    if category not in prep_list.CATEGORIES:
        category = ""
    customer_search = request.args.get("customer", "").strip()

    day_orders = prep_list.orders_for_day(db, pickup)
    items = prep_list.items_for_day(db, pickup, category, customer_search)

    # Group the items under their orders for display.
    items_by_order = {}
    for item in items:
        items_by_order.setdefault(item["order_id"], []).append(item)
    filtering = bool(category or customer_search)
    shown_orders = [o for o in day_orders
                    if o["order_id"] in items_by_order or not filtering]

    return render_template(
        "prep_list.html", pickup=pickup, dates=dates, category=category,
        customer_search=customer_search, orders=shown_orders,
        items_by_order=items_by_order, items_left=sum(1 for i in items if not i["ready"]),
        categories=prep_list.CATEGORIES,
    )


@app.post("/items/<int:item_id>/done")
def mark_item_done(item_id):
    db = get_db()
    if orders.get_item(db, item_id) is None:
        abort(404)
    is_done = validation.checkbox(request.form, "done")
    try_to_save(lambda: orders.set_item_done(db, item_id, is_done),
                "Marked as cut." if is_done else "Marked as not cut.")
    return back_to(url_for("prep_list_page"))


@app.post("/orders/<int:order_id>/ready")
def mark_order_ready(order_id):
    db = get_db()
    if orders.get_order(db, order_id) is None:
        abort(404)
    is_ready = validation.checkbox(request.form, "ready")
    try_to_save(lambda: orders.set_order_ready(db, order_id, is_ready),
                "Order marked ready." if is_ready else "Order marked not ready.")
    return back_to(url_for("order_page", order_id=order_id))


@app.post("/orders/<int:order_id>/picked-up")
def mark_order_picked_up(order_id):
    db = get_db()
    if orders.get_order(db, order_id) is None:
        abort(404)
    picked_up = validation.checkbox(request.form, "picked_up")
    try_to_save(lambda: orders.set_order_picked_up(db, order_id, picked_up),
                "Order marked picked up." if picked_up else "Order marked not picked up.")
    return back_to(url_for("order_page", order_id=order_id))


# ------------------------------------------------------- customers

@app.route("/customers")
def customers_page():
    search_text = request.args.get("q", "").strip()
    results = customers.search_customers(get_db(), search_text)
    return render_template("customers.html", search_text=search_text, results=results)


@app.route("/customers/<int:customer_id>")
def customer_page(customer_id):
    db = get_db()
    customer = customers.get_customer(db, customer_id)
    if customer is None:
        abort(404)
    # One row per item; group them under their orders for display.
    history = []
    for row in customers.get_order_history(db, customer_id):
        if not history or history[-1]["order"]["order_id"] != row["order_id"]:
            history.append({"order": row, "items": []})
        if row["item_id"] is not None:
            history[-1]["items"].append(row)
    return render_template("customer.html", customer=customer, history=history)


# ------------------------------------------------------- new order

@app.route("/orders/new", methods=["GET", "POST"])
def new_order_page():
    db = get_db()
    form = request.form

    if request.method == "POST":
        new_order_id = []

        def save():
            pickup = validation.pickup_date(form.get("pickup_date"))
            notes = validation.optional_text(form.get("notes"))
            # The new customer (if any) and the order are one transaction:
            # if the order fails (say, a duplicate pickup day), the customer
            # isn't left behind on their own.
            try:
                if form.get("customer_mode") == "new":
                    customer_id = customers.add_customer(
                        db,
                        validation.required_text(form.get("name"), "Customer name"),
                        validation.optional_phone(form.get("phone"), "Phone"),
                        validation.optional_text(form.get("alt_name")),
                        validation.optional_phone(form.get("alt_phone"), "Second phone"),
                        validation.optional_text(form.get("customer_notes")),
                    )
                else:
                    customer_id = validation.whole_number(form.get("customer_id"), "Customer")
                    if customers.get_customer(db, customer_id) is None:
                        raise ValidationError("Pick a customer from the list.")
                new_order_id.append(orders.add_order(db, customer_id, pickup, notes))
                db.commit()
            except Exception:
                db.rollback()
                raise

        if try_to_save(save, "Order created. Now add the items."):
            return redirect(url_for("order_page", order_id=new_order_id[0]))

    return render_template(
        "new_order.html", form=form, customers=customers.list_customers(db),
        selected_customer=request.args.get("customer_id", form.get("customer_id", "")),
    )


# ------------------------------------------------------- one order

@app.route("/orders/<int:order_id>")
def order_page(order_id):
    db = get_db()
    order = orders.get_order(db, order_id)
    if order is None:
        abort(404)
    return render_template(
        "order.html", order=order, items=orders.get_order_items(db, order_id),
        products=orders.list_products(db),
    )


@app.post("/orders/<int:order_id>/date")
def change_order_date(order_id):
    db = get_db()
    if orders.get_order(db, order_id) is None:
        abort(404)

    def save():
        pickup = validation.pickup_date(request.form.get("pickup_date"))
        orders.change_pickup_date(db, order_id, pickup)

    try_to_save(save, "Pickup date changed.")
    return redirect(url_for("order_page", order_id=order_id))


@app.post("/orders/<int:order_id>/items")
def add_item(order_id):
    db = get_db()
    order = orders.get_order(db, order_id)
    if order is None:
        abort(404)
    form = request.form

    def save():
        product = orders.get_product(db, validation.whole_number(form.get("product_id"), "Product"))
        if product is None:
            raise ValidationError("Pick a product from the list.")
        quantity = validation.whole_number(form.get("quantity"), "Quantity", 1, 99)
        weight = validation.optional_positive_decimal(form.get("weight_lb"), "Weight")
        thickness = validation.optional_positive_decimal(form.get("thickness_in"), "Thickness")
        notes = validation.optional_text(form.get("notes"))

        # Only the details that match the product's category are read.
        detail = {}
        if product["category"] == "rib_roast":
            detail = {
                "num_bones": validation.whole_number(form.get("num_bones"), "Number of bones", 2, 7),
                "frenched_bones": validation.checkbox(form, "frenched_bones"),
                "end_preference": validation.choice(form.get("end_preference"), END_PREFERENCES, "end preference"),
                "bones_tied_on": validation.checkbox(form, "bones_tied_on"),
            }
        elif product["category"] == "tenderloin":
            cut_style = validation.choice(form.get("cut_style"), CUT_STYLES, "cut style")
            filet_thickness = None
            if cut_style in ("filets", "chateau_and_filets"):
                filet_thickness = validation.optional_positive_decimal(
                    form.get("filet_thickness_in"), "Filet thickness")
            detail = {"cut_style": cut_style, "filet_thickness_in": filet_thickness,
                      "grind_trim": validation.checkbox(form, "grind_trim")}
        elif product["category"] == "charcuterie":
            detail = {
                "nut_option": validation.choice(form.get("nut_option"), NUT_OPTIONS, "nut option"),
                "meat_preferences": validation.optional_text(form.get("meat_preferences")),
                "cheese_preferences": validation.optional_text(form.get("cheese_preferences")),
            }

        orders.add_item(db, order, product, quantity, weight, thickness, notes, detail)

    try_to_save(save, "Item added.")
    return redirect(url_for("order_page", order_id=order_id))


@app.post("/items/<int:item_id>/edit")
def edit_item(item_id):
    db = get_db()
    item = orders.get_item(db, item_id)
    if item is None:
        abort(404)

    def save():
        orders.update_item(
            db, item,
            validation.whole_number(request.form.get("quantity"), "Quantity", 1, 99),
            validation.optional_positive_decimal(request.form.get("weight_lb"), "Weight"),
            validation.optional_text(request.form.get("notes")),
        )

    try_to_save(save, "Item updated.")
    return redirect(url_for("order_page", order_id=item["order_id"]))


@app.post("/items/<int:item_id>/delete")
def delete_item(item_id):
    db = get_db()
    item = orders.get_item(db, item_id)
    if item is None:
        abort(404)
    try_to_save(lambda: orders.delete_item(db, item_id), "Item removed.")
    return redirect(url_for("order_page", order_id=item["order_id"]))


@app.post("/orders/<int:order_id>/delete")
def cancel_order(order_id):
    db = get_db()
    order = orders.get_order(db, order_id)
    if order is None:
        abort(404)
    if try_to_save(lambda: orders.delete_order(db, order_id), "Order cancelled."):
        return redirect(url_for("customer_page", customer_id=order["customer_id"]))
    return redirect(url_for("order_page", order_id=order_id))


# ------------------------------------------------------- reports

@app.route("/reports")
def reports_page():
    db = get_db()
    season_list = reports.seasons(db)
    try:
        year = int(request.args.get("year", ""))
    except ValueError:
        year = season_list[0] if season_list else date.today().year
    return render_template(
        "reports.html", year=year, seasons=season_list,
        rib_by_day=reports.rib_roasts_by_day(db, year),
        work_left=reports.orders_with_work_left(db, year),
        product_totals=reports.product_totals(db, year),
        rib_stock=reports.rib_roast_stock(db, year),
        returning=reports.returning_customers(db, year),
    )


if __name__ == "__main__":
    # Debug mode stays off so errors never show a stack trace in the browser.
    app.run(debug=False)
