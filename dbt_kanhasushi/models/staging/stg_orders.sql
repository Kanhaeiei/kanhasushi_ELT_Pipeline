WITH source AS (
    SELECT * FROM {{ source('raw', 'orders') }}
),

renamed AS (
    SELECT
        id AS order_id,
        table_id,
        session_id,
        status AS order_status,
        order_type,
        order_seq,
        note AS order_note,
        created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Bangkok' AS created_at_bkk,
        updated_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Bangkok' AS updated_at_bkk,
        -- Late-Night 10:00 AM Bangkok Cutoff Calculation
        DATE((created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Bangkok') - INTERVAL '10 hours') AS business_date,
        -- Hour of day in Bangkok
        EXTRACT(HOUR FROM (created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Bangkok')) AS order_hour_bkk
    FROM source
)

SELECT * FROM renamed