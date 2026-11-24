# Cut List Manager (Jesse's Butcher Shop)
COSC 465 Final Project
Kenneth Hinman

## Project Overview

- **What it does:** a web app for taking and prepping a butcher shop's holiday
  orders (rib roasts, tenderloins, charcuterie boards, etc.) on top of a SQLite
  database, so staff never have to write SQL.
- **Intended users:** the shop's counter and cutting staff.
- **Major functionality:** customer search and order history, entering and
  editing orders, a daily prep list for the cutting room, and season reports
  (see [The six operations](#the-six-operations)).

## Technology

- **Language:** Python 3.10 or newer (tested on 3.13)
- **Web framework:** Flask 3 (the only package to install, see `app/requirements.txt`)
- **Database:** SQLite 3, through Python's built-in `sqlite3` module (plain SQL, no ORM)
- **Styling:** Tailwind CSS and DaisyUI (pinned versions) plus the IBM Plex
  fonts, loaded from a CDN in `app/templates/base.html`, with the shop's theme
  in `app/static/cutlist.css`. No build step is needed, but the browser needs
  an internet connection for the CDN styles. Without it the app still works,
  just less styled.

## Folder layout

```
cut-list-manager/
├── README.md           this file
├── schema.sql          database tables, indexes and view
├── insert_data.sql     sample data
├── queries.sql         Deliverable 4 queries
├── transaction.sql     Deliverable 4 transaction
├── run_queries.sh      Deliverable 4 script; also creates xmas_orders.db
├── docs/               ER diagram (erd.pdf), design notes, proposal
└── app/
    ├── app.py          Flask app: routes, error handling, display helpers
    ├── db.py           opening/closing the database connection, init-db
    ├── customers.py    SQL for customer search, history and adding customers
    ├── orders.py       SQL for orders and items (adds, edits, deletes, stock check)
    ├── prep_list.py    SQL for the daily prep list (uses the v_daily_prep_list view)
    ├── reports.py      SQL for the reports page
    ├── validation.py   checks for form input
    ├── templates/      HTML pages (Jinja templates; _ui.html holds shared pieces)
    ├── static/         cutlist.css, the app's colors and type
    └── requirements.txt
```

## Database Setup (SQL files)

Requires the `sqlite3` command-line tool (preinstalled on macOS; on Windows or
Linux, install it from https://sqlite.org/download.html or your package
manager). `queries.sql` uses sqlite3 dot-commands (`.mode`, `.print`), so run it
with the `sqlite3` CLI rather than a GUI tool.

From the `cut-list-manager` folder, run the files in this order:

1. `schema.sql`: creates the tables, indexes and view
2. `insert_data.sql`: loads the sample data
3. `queries.sql`: runs the required queries
4. `transaction.sql`: runs the transaction example (ends in `ROLLBACK`, so data is unchanged)

`bash run_queries.sh` does all four in that order and creates `xmas_orders.db`.
To run them by hand:

```bash
sqlite3 xmas_orders.db < schema.sql
sqlite3 xmas_orders.db < insert_data.sql
sqlite3 xmas_orders.db < queries.sql
sqlite3 xmas_orders.db < transaction.sql
```

## Application Setup

Open a terminal in the `cut-list-manager` folder. Step 1 moves into the `app`
folder, and **every command after that is run from `app`**.

1. **Install Flask** (the virtual environment is optional but keeps things clean):

   ```bash
   cd app
   python3 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Create the database.** This builds a fresh `xmas_orders.db` in the
   `cut-list-manager` folder from `schema.sql` and `insert_data.sql`:

   ```bash
   flask --app app init-db
   ```

   Running it again resets the sample data. (`bash run_queries.sh`, run from
   the `cut-list-manager` folder, creates the same file.)

3. **Database connection.** By default the app uses `cut-list-manager/xmas_orders.db`.
   To use a different file, set the `CUTLIST_DB` environment variable to its
   path before starting the app. SQLite needs no passwords or credentials.
   If the database file is missing or empty, every page says so and shows
   the `init-db` command to run.

## Running the app

```bash
flask --app app run
```

Then open http://127.0.0.1:5000 in a browser. Press Ctrl+C to stop it.

To use it from a tablet or phone on the same Wi-Fi, start it with
`flask --app app run --host 0.0.0.0` and open `http://<this computer's IP>:5000`
on the other device.

## The six operations

The sample data's busiest day is **Dec 23, 2026**, so that's a good day to test with.

| # | Required type | Operation | Where to find it |
|---|---|---|---|
| 1 | Search or browse | **Customer search** by name or phone number (any format), with each customer's order count | **Customers** in the menu. Leave the search empty to browse everyone. |
| 2 | Related data | **Customer order history**: every order and item a customer has placed across seasons (joins customer_order, customer_items and product) | **Customers** → **View** on a customer |
| 3 | Add data | **New order**: add a new or existing customer's order, then add items with rib roast, tenderloin or charcuterie details | **New order** in the menu, then **Add an item** on the order page |
| 4 | Update or delete | **Edit an order**: change the pickup day, edit an item's quantity, weight or notes, remove an item, or cancel the whole order | **Open order** from the prep list or a customer's page |
| 5 | Summary or report | **Season reports**: rib roasts and total bones per pickup day, orders with items left to cut, what's been ordered vs. stock, and last year's customers who haven't ordered yet | **Reports** in the menu (pick a season at the top) |
| 6 | Additional | **Daily prep list**: everything to cut for one pickup day, filtered by category or customer, with buttons to mark items cut and orders ready or picked up (uses the `v_daily_prep_list` view) | **Prep list** (the home page) |

## Notes on the implementation

- **Parameterized SQL:** every query that uses a value from the user uses `?`
  placeholders. No SQL is built by pasting user input into a string.
- **Transactions:**
  - Creating an order for a **new** customer inserts the customer and the order
    together. If the order can't be saved, the customer isn't saved either.
  - Adding a rib roast, tenderloin or charcuterie board inserts the item and its
    detail row together, so there's never a rib roast with no bone count.
- **Rules from the design notes that the app enforces:**
  - Only the detail row matching the product's category is saved.
  - Items can't go over a product's `stock_limit` for the season (rib roasts are
    counted in bones). This is checked when adding an item and when changing
    its quantity.
  - The item's price is copied from the catalog when it's added.
- **Validation and errors:** forms check for missing names, bad phone numbers,
  invalid dates, non-numbers, out-of-range values (like 8 bones) and unknown
  products or customers. Database errors (a second order for the same customer
  on the same day, marking an order not ready after it's picked up, etc.) are
  shown as plain messages instead of raw errors. Missing records show a
  "doesn't exist" page.
- **Connections:** one connection per web request, with foreign keys turned on,
  closed automatically when the request ends (`app/db.py`).

## Database

`schema.sql`, `insert_data.sql` and `docs/erd.pdf` describe the database the
app uses.

- **Foreign keys:** SQLite only enforces foreign keys after
  `PRAGMA foreign_keys = ON`. Both SQL files run it at the top, and the app
  turns it on for every connection.
- **Delete rules:** deleting an order also deletes its items and their detail
  rows. A customer with orders, or a product that has been ordered, can't be
  deleted.
- **View `v_daily_prep_list`:** one row per item ordered, with the pickup date,
  customer, product, quantity, weight, and the rib roast, tenderloin or
  charcuterie details for that item. It joins customer_items, customer_order,
  customer, product and the three detail tables, and powers the Prep List page.
- **Indexes:**
  - `idx_order_pickup_date` on customer_order (pick_up_year, pick_up_month,
    pick_up_day): looking up every order for one pickup day (the prep list).
    The UNIQUE constraint on customer_order starts with customer_id, so its
    automatic index doesn't help a search by date alone.
  - `idx_items_order` on customer_items (order_id): joining orders to items
  - `idx_items_product` on customer_items (product_id): joining items to products
  - `idx_customer_name` on customer (name): looking up a customer by name

## Known Limitations

- Styling loads from a CDN, so without internet the pages work but are unstyled.
- There's no login; anyone who can reach the app can edit orders.
- SQLite allows one writer at a time, which is fine for a single shop but not
  for many simultaneous users.
- `flask --app app init-db` and `run_queries.sh` delete and rebuild
  `xmas_orders.db`, wiping any data entered through the app.
