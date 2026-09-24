SELECT
    staff_id,
    staff_name,
    staff_email,
    staff_role
FROM {{ ref('stg_account') }}
