WITH date_series AS (
    SELECT generate_series(
        '2025-01-01'::date,
        '2030-12-31'::date,
        '1 day'::interval
    )::date AS business_date
)

SELECT
    business_date,
    EXTRACT(YEAR FROM business_date)::int AS year,
    EXTRACT(MONTH FROM business_date)::int AS month,
    EXTRACT(DAY FROM business_date)::int AS day,
    EXTRACT(ISODOW FROM business_date)::int AS day_of_week,
    TO_CHAR(business_date, 'Day') AS day_name,
    TO_CHAR(business_date, 'Month') AS month_name,
    CASE 
        WHEN EXTRACT(ISODOW FROM business_date) IN (5, 6, 7) THEN TRUE 
        ELSE FALSE 
    END AS is_weekend_rush
FROM date_series