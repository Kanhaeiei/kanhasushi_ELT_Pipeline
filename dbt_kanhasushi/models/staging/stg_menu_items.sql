WITH items AS (
    SELECT * FROM {{ source('raw', 'menu_items') }}
),
variants AS (
    SELECT * FROM {{ source('raw', 'menu_item_variants') }}
),
categories AS (
    SELECT * FROM {{ source('raw', 'categories') }}
)

SELECT
    v.id AS variant_id,
    m.id AS item_id,
    c.id AS category_id,
    -- JSONB Language Unnesting with safe fallbacks
    COALESCE(m.name->>'th', m.name->>'en', 'Unknown') AS item_name_th,
    COALESCE(m.name->>'en', m.name->>'th', 'Unknown') AS item_name_en,
    COALESCE(v.variant_name->>'th', v.variant_name->>'en', 'Regular') AS variant_name_th,
    COALESCE(v.variant_name->>'en', v.variant_name->>'th', 'Regular') AS variant_name_en,
    COALESCE(c.name->>'th', c.name->>'en', 'General') AS category_name_th,
    COALESCE(c.name->>'en', c.name->>'th', 'General') AS category_name_en,
    c.kitchen_type,
    v.regular_price,
    v.special_price,
    COALESCE(v.special_price, v.regular_price) AS effective_price,
    v.is_available AND m.is_available AS is_active
FROM variants v
JOIN items m ON v.menu_item_id = m.id
LEFT JOIN categories c ON m.category_id = c.id