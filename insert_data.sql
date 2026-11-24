-- Cut List Manager - insert_data.sql
-- Run AFTER schema.sql.
-- All names, phone numbers, and prices are made up.
-- Created with the help of AI, I gave it my schemas and had it generate entries as suggested in class.
-- I had it base the dummy data on previous spreadsheets from prior years at work except obviously changing
-- names, phone numbers, and prices.

PRAGMA foreign_keys = ON;

-- customer
INSERT INTO customer (customer_id, name, alt_name, phone, alt_phone, notes) VALUES
 (1, 'Margaret Holloway', NULL,             '8655550101', NULL,         'Text when the order is ready'),
 (2, 'Dennis Okafor',     'Grace Okafor',   '8655550102', '8655550142', NULL),
 (3, 'Lucia Ferreira',    NULL,             '8655550103', NULL,         NULL),
 (4, 'Tom Brannigan',     'Ruth Brannigan', NULL,         '8655550143', 'No cell phone, call Ruth'),
 (5, 'Walt Simmons',      NULL,             '8655550105', NULL,         'Always wants the chuck end'),
 (6, 'Carol Pruitt',      NULL,             '8655550106', NULL,         NULL),
 (7, 'Gloria Treadway',   NULL,             '8655550107', NULL,         NULL),
 (8, 'Frank Delgado',     NULL,             '8655550108', NULL,         'Has not ordered yet');

-- product
INSERT INTO product (product_id, product_name, grade, is_frozen, category, sold_by, price_cents, is_perishable, is_active, stock_limit) VALUES
 (1,  'Standing Rib Roast',      'P',  0, 'rib_roast',   'lb',   3299, 1, 1, 40),
 (2,  'Standing Rib Roast',      'C',  0, 'rib_roast',   'lb',   2499, 1, 1, 24),
 (3,  'Beef Tenderloin',         'P',  0, 'tenderloin',  'lb',   3499, 1, 1, 8),
 (4,  'Beef Tenderloin',         'C',  0, 'tenderloin',  'lb',   2799, 1, 1, 1),
 (5,  'Filet Mignon',            'P',  0, 'beef',        'lb',   4499, 1, 1, NULL),
 (6,  'Ribeye',                  'P',  0, 'beef',        'lb',   3199, 1, 1, NULL),
 (7,  'Spiral Ham',              'NA', 0, 'pork',        'lb',    999, 1, 1, 20),
 (8,  'Whole Duck',              'NA', 0, 'poultry',     'each', 4499, 1, 1, 6),
 (9,  'Whole Turkey',            'NA', 0, 'poultry',     'lb',    499, 1, 1, 15),
 (10, 'Whole Turkey',            'NA', 1, 'poultry',     'lb',    349, 1, 1, NULL),
 (11, 'Small Charcuterie Board', 'NA', 0, 'charcuterie', 'each', 5500, 1, 1, 10),
 (12, 'Large Charcuterie Board', 'NA', 0, 'charcuterie', 'each', 9500, 1, 1, 8),
 (13, 'Demi-Glace',              'NA', 0, 'provisions',  'each', 1400, 1, 1, NULL),
 (14, 'Beef Hot Dogs',           'NA', 0, 'beef',        'lb',    799, 1, 0, NULL);

-- customer_order
INSERT INTO customer_order (order_id, customer_id, pick_up_month, pick_up_day, pick_up_year, is_ready, is_picked_up, notes) VALUES
 (1,  1, 12, 23, 2025, 1, 1, NULL),
 (2,  5, 12, 23, 2025, 1, 1, NULL),
 (3,  6, 12, 22, 2025, 1, 1, 'Paid in full'),
 (4,  1, 12, 23, 2026, 0, 0, 'Paid in full'),
 (5,  2, 12, 23, 2026, 0, 0, NULL),
 (6,  3, 12, 22, 2026, 1, 0, NULL),
 (7,  4, 12, 23, 2026, 0, 0, 'Paid $50 deposit'),
 (8,  5, 12, 23, 2026, 0, 0, NULL),
 (9,  7, 12, 23, 2026, 0, 0, NULL),
 (10, 7, 12, 24, 2026, 0, 0, 'Second pickup');

-- customer_items
INSERT INTO customer_items (item_id, order_id, product_id, quantity, weight_lb, thickness_in, unit_price_cents, is_done, notes) VALUES
 (1,  1,  1,  1, 9.0,   NULL, 3099, 1, NULL),
 (2,  1,  13, 1, NULL,  NULL, 1300, 1, NULL),
 (3,  2,  1,  1, 11.5,  NULL, 3099, 1, NULL),
 (4,  2,  7,  1, 8.0,   NULL,  899, 1, 'Glaze packet on the side'),
 (5,  3,  3,  1, 5.5,   NULL, 3299, 1, NULL),
 (6,  3,  11, 1, NULL,  NULL, 5000, 1, NULL),
 (7,  4,  1,  1, NULL,  NULL, 3299, 0, NULL),
 (8,  4,  13, 1, NULL,  NULL, 1400, 0, NULL),
 (9,  5,  8,  2, NULL,  NULL, 4499, 0, NULL),
 (10, 5,  12, 1, NULL,  NULL, 9500, 0, NULL),
 (11, 6,  5,  6, 0.625, NULL, 4499, 1, '10 oz filets'),
 (12, 6,  3,  1, 6.0,   NULL, 3499, 1, NULL),
 (13, 7,  1,  1, NULL,  NULL, 3299, 0, 'Biggest roast we have'),
 (14, 7,  3,  1, NULL,  NULL, 3499, 0, NULL),
 (15, 7,  7,  1, 9.0,   NULL,  999, 0, NULL),
 (16, 8,  1,  1, 11.0,  NULL, 3299, 1, NULL),
 (17, 8,  1,  1, NULL,  NULL, 3299, 0, 'Second roast, for the in-laws'),
 (18, 8,  6,  4, 1.0,   1.5,  3199, 0, NULL),
 (19, 9,  2,  1, NULL,  NULL, 2499, 0, NULL),
 (20, 9,  10, 1, 14.0,  NULL,  349, 0, 'Frozen is fine'),
 (21, 10, 11, 1, NULL,  NULL, 5500, 0, NULL),
 (22, 10, 4,  1, NULL,  NULL, 2799, 0, 'Seal the halves separately'),
 (23, 4,  12, 1, NULL,  NULL, 9500, 0, NULL);

-- rib_roast_detail
INSERT INTO rib_roast_detail (item_id, num_bones, frenched_bones, end_preference, bones_tied_on) VALUES
 (1,  4, 1, 'chuck', 0),
 (3,  5, 1, 'chuck', 1),
 (7,  4, 1, 'chuck', 0),
 (13, 7, 1, 'loin',  0),
 (16, 5, 1, 'chuck', 1),
 (17, 3, 1, 'chuck', 0),
 (19, 4, 0, 'none',  0);

-- tenderloin_detail
INSERT INTO tenderloin_detail (item_id, cut_style, filet_thickness_in, grind_trim) VALUES
 (5,  'whole',              NULL, 0),
 (12, 'filets',             2.0,  0),
 (14, 'chateau_and_filets', 1.5,  1),
 (22, 'halved',             NULL, 0);

-- charcuterie_detail
INSERT INTO charcuterie_detail (item_id, nut_option, meat_preferences, cheese_preferences) VALUES
 (6,  'none',     NULL,                 'Mild cheeses only'),
 (10, 'on_side',  'Soppressata, Speck', 'No blue cheese'),
 (21, 'included', NULL,                 'Blue is OK'),
 (23, 'included', NULL,                 NULL);
