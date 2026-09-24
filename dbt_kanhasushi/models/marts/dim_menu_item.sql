SELECT
    variant_id,
    item_id,
    category_id,
    item_name_th,
    item_name_en,
    variant_name_th,
    variant_name_en,
    category_name_th,
    category_name_en,
    kitchen_type,
    regular_price,
    special_price,
    effective_price,
    is_active
FROM {{ ref('stg_menu_items') }}
