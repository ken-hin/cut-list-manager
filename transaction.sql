-- Transaction for entering a new order.
-- The order, its rib roast item, and the rib roast's bone count all have to
-- be saved together. If one insert fails, none of them should be saved, so
-- the shop never ends up with a rib roast on an order but no further details.
-- ROLLBACK is used instead of COMMIT, so the sample data isn't changed.

PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

INSERT INTO customer_order (order_id, customer_id, pick_up_month, pick_up_day, pick_up_year)
VALUES (11, 8, 12, 23, 2026);

INSERT INTO customer_items (item_id, order_id, product_id, quantity, unit_price_cents)
VALUES (24, 11, 1, 1, 3299);

INSERT INTO rib_roast_detail (item_id, num_bones, end_preference)
VALUES (24, 4, 'chuck');

ROLLBACK;
