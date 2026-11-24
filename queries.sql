PRAGMA foreign_keys = ON;
.mode box

.print "--------------------------------Requirement 1--------------------------------"
-- Requirement 1: Filtering and Sorting
-- Shows the 2026 orders that haven't been picked up yet, soonest pickup first.
SELECT order_id, customer_id, pick_up_month, pick_up_day, is_ready
FROM customer_order
WHERE pick_up_year = 2026 AND is_picked_up = 0
ORDER BY pick_up_month, pick_up_day;

.print "--------------------------------Requirement 2--------------------------------"
-- Requirement 2: INNER JOIN
-- Shows the name and phone number of every customer picking up on 12/23/2026.
SELECT customer_order.order_id, customer.name, customer.phone
FROM customer_order
	INNER JOIN customer ON customer.customer_id = customer_order.customer_id
WHERE customer_order.pick_up_year = 2026
  AND customer_order.pick_up_month = 12
  AND customer_order.pick_up_day = 23
ORDER BY customer.name;

-- Requirement 3: LEFT JOIN
-- Shows the products that have never been ordered.
.print "--------------------------------Requirement 3--------------------------------"
SELECT product.product_id, product.product_name, product.grade
FROM product
	LEFT JOIN customer_items ON customer_items.product_id = product.product_id
WHERE customer_items.item_id IS NULL;

-- Requirement 4: Three-Table Join
-- Daily prep list for rib roast orders on 12/23/2026, who it's for, and how many bones it is.
.print "--------------------------------Requirement 4--------------------------------"
SELECT customer.name, rib_roast_detail.num_bones, rib_roast_detail.end_preference, customer_items.is_done
FROM customer_items
	JOIN rib_roast_detail ON rib_roast_detail.item_id = customer_items.item_id
	JOIN customer_order ON customer_order.order_id = customer_items.order_id
	JOIN customer ON customer.customer_id = customer_order.customer_id
WHERE customer_order.pick_up_year = 2026
  AND customer_order.pick_up_month = 12
  AND customer_order.pick_up_day = 23
ORDER BY rib_roast_detail.num_bones;

-- Requirement 5: Aggregate Query
-- Shows how many total rib roast orders and the total bones across all orders on 12/23/2026.
.print "--------------------------------Requirement 5--------------------------------"
SELECT COUNT(*) AS rib_roasts, SUM(rib_roast_detail.num_bones) AS total_bones
FROM rib_roast_detail
	JOIN customer_items ON customer_items.item_id = rib_roast_detail.item_id
	JOIN customer_order ON customer_order.order_id = customer_items.order_id
WHERE customer_order.pick_up_year = 2026
  AND customer_order.pick_up_month = 12
  AND customer_order.pick_up_day = 23;

-- Requirement 6: GROUP BY and HAVING
-- Shows the 2026 orders that still have items left to cut.
.print "--------------------------------Requirement 6--------------------------------"
SELECT customer_order.order_id, COUNT(*) AS items_on_order, SUM(customer_items.is_done) AS items_done
FROM customer_order
	JOIN customer_items ON customer_items.order_id = customer_order.order_id
WHERE customer_order.pick_up_year = 2026
GROUP BY customer_order.order_id
HAVING SUM(customer_items.is_done) < COUNT(*);

-- Requirement 7: Subquery
-- Shows the customers who ordered in 2025 but haven't ordered for 2026 yet.
.print "--------------------------------Requirement 7--------------------------------"
SELECT customer_id, name, phone
FROM customer
WHERE customer_id IN (SELECT customer_id FROM customer_order WHERE pick_up_year = 2025)
  AND customer_id NOT IN (SELECT customer_id FROM customer_order WHERE pick_up_year = 2026);

-- Requirement 8: Set Operation
-- Shows the customers who ordered in both 2025 and 2026.
.print "--------------------------------Requirement 8--------------------------------"
SELECT customer.customer_id, customer.name
FROM customer
	JOIN customer_order ON customer_order.customer_id = customer.customer_id
WHERE customer_order.pick_up_year = 2025
INTERSECT
SELECT customer.customer_id, customer.name
FROM customer
	JOIN customer_order ON customer_order.customer_id = customer.customer_id
WHERE customer_order.pick_up_year = 2026;

-- Requirement 9: View
-- Shows high-level view of everything still left to cut for 12/23/2026 across all categories.
-- Can show more fine-grained details if more columns are added to the SELECT
.print "--------------------------------Requirement 9--------------------------------"
SELECT name, phone, item_name, qty
FROM v_daily_prep_list
WHERE year = 2026 AND month = 12 AND day = 23 AND ready = 0
ORDER BY category;
