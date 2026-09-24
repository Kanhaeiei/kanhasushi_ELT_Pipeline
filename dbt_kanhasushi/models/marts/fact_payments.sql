{{ config(materialized='table') }}

SELECT
    payment_id,
    table_id,
    staff_id,
    business_date,
    total_amount,
    payment_method,
    paid_at_bkk
FROM {{ ref('stg_payments') }}