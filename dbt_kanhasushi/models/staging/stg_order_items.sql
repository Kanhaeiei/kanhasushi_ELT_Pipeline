WITH source AS (
    SELECT * FROM {{ source('raw', 'order_items') }}
),

renamed AS (
    SELECT
        id AS order_item_id,
        order_id,
        menu_item_variants_id AS variant_id,
        quantity,
        price_at_order AS unit_price,
        (quantity * price_at_order) AS line_total,
        note AS item_note
    FROM source
)

SELECT * FROM renamed