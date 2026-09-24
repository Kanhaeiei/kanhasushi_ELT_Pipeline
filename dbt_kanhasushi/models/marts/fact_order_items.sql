{{ config(materialized='table') }}

WITH items AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),
orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
)

SELECT
    items.order_item_id,
    items.order_id,
    orders.table_id,
    items.variant_id,
    orders.business_date,
    orders.session_id,
    orders.order_status,
    orders.order_type,
    orders.order_seq,
    items.quantity,
    items.unit_price,
    items.line_total,
    orders.order_hour_bkk,
    orders.created_at_bkk
FROM items
JOIN orders ON items.order_id = orders.order_id