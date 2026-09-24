WITH source AS (
    SELECT * FROM {{ source('raw', 'tables') }}
)

SELECT
    id AS table_id,
    table_number,
    status AS current_status,
    created_at
FROM source