SELECT
    table_id,
    table_number,
    current_status
FROM {{ ref('stg_tables') }}
