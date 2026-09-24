WITH source AS (
    SELECT * FROM {{ source('raw', 'payments') }}
),

renamed AS (
    SELECT
        id AS payment_id,
        tables_id AS table_id,
        closed_by AS staff_id,
        total_amount,
        payment_method,
        paid_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Bangkok' AS paid_at_bkk,
        -- Business day cutoff logic for payments
        DATE((paid_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Bangkok') - INTERVAL '10 hours') AS business_date
    FROM source
)

SELECT * FROM renamed