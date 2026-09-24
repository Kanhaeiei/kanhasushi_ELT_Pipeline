WITH source AS (
    SELECT * FROM {{ source('raw', 'account') }}
)

SELECT
    id AS staff_id,
    name AS staff_name,
    email AS staff_email,
    role AS staff_role,
    created_at
FROM source