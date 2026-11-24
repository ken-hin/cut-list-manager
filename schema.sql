-- Cut List Manager - schema.sql
-- Run first after creating the DB.

PRAGMA foreign_keys = ON;

-- Drop everything so the database can be rebuilt from scratch.
DROP VIEW IF EXISTS v_daily_prep_list;

DROP TABLE IF EXISTS charcuterie_detail;
DROP TABLE IF EXISTS tenderloin_detail;
DROP TABLE IF EXISTS rib_roast_detail;
DROP TABLE IF EXISTS customer_items;
DROP TABLE IF EXISTS customer_order;
DROP TABLE IF EXISTS product;
DROP TABLE IF EXISTS customer;

-- TABLES
CREATE TABLE customer (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    alt_name TEXT,
    phone TEXT CHECK
      (length(phone) = 10),     -- 10 digits, no dashes
    alt_phone TEXT CHECK
      (length(alt_phone) = 10),
    notes TEXT
);

CREATE TABLE product (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    grade TEXT NOT NULL DEFAULT 'NA' CHECK
      (grade IN ('P', 'C', 'AUS', 'JPN', 'NA')),
    is_frozen INTEGER NOT NULL DEFAULT 0 CHECK
      (is_frozen IN (0, 1)),
    category TEXT NOT NULL CHECK
      (category IN ('rib_roast', 'tenderloin', 'beef', 'pork', 'poultry', 'charcuterie', 'provisions')),
    sold_by TEXT NOT NULL CHECK
      (sold_by IN ('lb', 'each')),
    price_cents INTEGER NOT NULL CHECK
      (price_cents >= 0),
    is_perishable INTEGER NOT NULL DEFAULT 1 CHECK
      (is_perishable IN (0, 1)),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK
      (is_active IN (0, 1)),
    -- Total the shop has for the product.
    stock_limit   INTEGER CHECK (stock_limit >= 0),
    UNIQUE (product_name, grade, is_frozen)
);

CREATE TABLE customer_order (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    pick_up_month INTEGER NOT NULL CHECK
      (pick_up_month BETWEEN 1 AND 12),
    pick_up_day INTEGER NOT NULL CHECK
      (pick_up_day BETWEEN 1 AND 31),
    pick_up_year INTEGER NOT NULL,
    is_ready INTEGER NOT NULL DEFAULT 0 CHECK
      (is_ready IN (0, 1)),
    is_picked_up INTEGER NOT NULL DEFAULT 0 CHECK
      (is_picked_up IN (0, 1)),
    notes TEXT,
    -- A customer who has orders can't be deleted.
    FOREIGN KEY (customer_id) REFERENCES
      customer (customer_id) ON DELETE RESTRICT,
    -- One order per customer per pickup day.
    UNIQUE (customer_id, pick_up_month, pick_up_day, pick_up_year),
    -- An order can't be picked up before it's ready.
    CHECK (is_picked_up <= is_ready)
);

-- Junction table between customer_order and product.
CREATE TABLE customer_items (
    item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1 CHECK
      (quantity > 0),
    weight_lb REAL CHECK -- pounds per piece
      (weight_lb > 0),
    thickness_in REAL CHECK
      (thickness_in > 0),
    unit_price_cents INTEGER NOT NULL CHECK -- price when ordered
      (unit_price_cents >= 0),
    is_done INTEGER NOT NULL DEFAULT 0 CHECK
      (is_done IN (0, 1)),
    notes TEXT,
    -- Deleting an order deletes its items.
    FOREIGN KEY (order_id) REFERENCES
      customer_order (order_id) ON DELETE CASCADE,
    -- A product that has been ordered can't be deleted.
    FOREIGN KEY (product_id) REFERENCES
      product (product_id) ON DELETE RESTRICT
);

-- item_id is both the primary key and the foreign key, so each item can have at most one detail row.
-- Deleting an item deletes its detail row.
CREATE TABLE rib_roast_detail (
    item_id INTEGER PRIMARY KEY,
    num_bones INTEGER NOT NULL CHECK
      (num_bones BETWEEN 2 AND 7),
    frenched_bones INTEGER NOT NULL DEFAULT 1 CHECK
      (frenched_bones IN (0, 1)),
    end_preference TEXT NOT NULL DEFAULT 'none' CHECK
      (end_preference IN ('none', 'chuck', 'loin')),
    bones_tied_on INTEGER NOT NULL DEFAULT 0 CHECK
      (bones_tied_on IN (0, 1)),
    FOREIGN KEY (item_id) REFERENCES
      customer_items (item_id) ON DELETE CASCADE
);

CREATE TABLE tenderloin_detail (
    item_id INTEGER PRIMARY KEY,
    cut_style TEXT NOT NULL DEFAULT 'whole' CHECK
      (cut_style IN ('whole', 'halved', 'filets', 'chateau', 'chateau_and_filets')),
    filet_thickness_in REAL CHECK
      (filet_thickness_in > 0),
    grind_trim INTEGER NOT NULL DEFAULT 0 CHECK
      (grind_trim IN (0, 1)),
    FOREIGN KEY (item_id) REFERENCES
      customer_items (item_id) ON DELETE CASCADE
);

CREATE TABLE charcuterie_detail (
    item_id INTEGER PRIMARY KEY,
    nut_option TEXT NOT NULL DEFAULT 'included' CHECK
      (nut_option IN ('included', 'on_side', 'none')),
    meat_preferences TEXT,
    cheese_preferences TEXT,
    FOREIGN KEY (item_id) REFERENCES
      customer_items (item_id) ON DELETE CASCADE
);

-- INDEXES
-- Finding every order for one pickup day (the daily prep list).
CREATE INDEX idx_order_pickup_date ON customer_order (pick_up_year, pick_up_month, pick_up_day);
-- Joining orders to their items, and items to their products.
CREATE INDEX idx_items_order ON customer_items (order_id);
CREATE INDEX idx_items_product ON customer_items (product_id);
-- Looking up a customer by name.
CREATE INDEX idx_customer_name ON customer (name);

-- VIEWS
-- Daily prep list: every item on every order with the customer, pickup date and the rib roast,
-- tenderloin or charcuterie details.
CREATE VIEW v_daily_prep_list AS
SELECT o.pick_up_year AS year,
       o.pick_up_month AS month,
       o.pick_up_day AS day,
       o.order_id AS order_id,
       c.name AS name,
       c.phone AS phone,
       ci.item_id AS item_id,
       p.category AS category,
       p.product_name AS item_name,
       p.grade AS grade,
       ci.quantity AS qty,
       ci.weight_lb AS lbs,
       ci.thickness_in AS in_thick,
       r.num_bones AS bones,
       r.end_preference AS loin_end,
       t.cut_style AS cut_specs,
       t.grind_trim AS grind_trimmings,
       ch.nut_option AS nuts,
       ci.notes AS notes,
       ci.is_done AS ready
FROM customer_items ci
JOIN customer_order o ON o.order_id = ci.order_id
JOIN customer c ON c.customer_id = o.customer_id
JOIN product p ON p.product_id = ci.product_id
LEFT JOIN rib_roast_detail r ON r.item_id = ci.item_id
LEFT JOIN tenderloin_detail t ON t.item_id = ci.item_id
LEFT JOIN charcuterie_detail ch ON ch.item_id = ci.item_id;
