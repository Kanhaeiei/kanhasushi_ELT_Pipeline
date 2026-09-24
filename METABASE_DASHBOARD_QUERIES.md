# Metabase SQL Dashboard Cookbook — KanhaSushi Analytics

Copy and paste these SQL queries into Metabase cards to build the **KanhaSushi Sales & Operations Dashboard**. All queries run directly against the **Gold Layer (Analytics Marts / Star Schema)**.

---

### Card 1: Daily Revenue & Order Volume
* **Visualization:** Line or Combined Bar + Line Chart
* **X-Axis:** `business_date`
* **Y-Axes:** `gross_revenue` (Bar), `total_orders` (Line)

```sql
SELECT 
    f.business_date,
    d.day_name,
    d.is_weekend_rush,
    COUNT(DISTINCT f.order_id) AS total_orders,
    SUM(f.line_total) AS gross_revenue,
    ROUND(SUM(f.line_total) / NULLIF(COUNT(DISTINCT f.order_id), 0), 2) AS average_order_value
FROM analytics.fact_order_items f
JOIN analytics.dim_business_date d ON f.business_date = d.business_date
WHERE f.order_status != 'cancelled'
GROUP BY f.business_date, d.day_name, d.is_weekend_rush
ORDER BY f.business_date DESC
LIMIT 30;
```

---

### Card 2: Top 10 Best-Selling Menu Items
* **Visualization:** Horizontal Bar Chart or Table

```sql
SELECT 
    m.item_name_th,
    m.item_name_en,
    m.variant_name_th,
    m.category_name_th,
    SUM(f.quantity) AS total_quantity_sold,
    SUM(f.line_total) AS total_revenue
FROM analytics.fact_order_items f
JOIN analytics.dim_menu_item m ON f.variant_id = m.variant_id
WHERE f.order_status != 'cancelled'
GROUP BY m.item_name_th, m.item_name_en, m.variant_name_th, m.category_name_th
ORDER BY total_revenue DESC
LIMIT 10;
```

---

### Card 3: Hourly Order Rush (Dinner vs. Late-Night Rush)
* **Visualization:** Bar Chart or Heatmap
* **X-Axis:** `order_hour_bkk` (0 - 23)
* **Y-Axis:** `order_count`

```sql
SELECT 
    order_hour_bkk,
    CASE 
        WHEN order_hour_bkk BETWEEN 14 AND 17 THEN 'Afternoon (14:00 - 17:59)'
        WHEN order_hour_bkk BETWEEN 18 AND 21 THEN 'Dinner Rush (18:00 - 21:59)'
        WHEN order_hour_bkk >= 22 OR order_hour_bkk <= 4 THEN 'Late-Night Rush (22:00 - 04:00)'
        ELSE 'Closed / Morning'
    END AS shift_window,
    COUNT(DISTINCT order_id) AS order_count,
    SUM(line_total) AS total_sales
FROM analytics.fact_order_items
WHERE order_status != 'cancelled'
GROUP BY order_hour_bkk
ORDER BY order_hour_bkk;
```

---

### Card 4: Payment Methods Distribution (Cash vs. PromptPay)
* **Visualization:** Pie / Donut Chart

```sql
SELECT 
    payment_method,
    COUNT(*) AS transaction_count,
    SUM(total_amount) AS total_collected,
    ROUND(100.0 * SUM(total_amount) / SUM(SUM(total_amount)) OVER(), 2) AS percentage_of_revenue
FROM analytics.fact_payments
GROUP BY payment_method;
```

---

### Card 5: Dine-In vs. Takeaway Sales Split
* **Visualization:** Stacked Bar or Donut Chart

```sql
SELECT 
    COALESCE(order_type, 'eat_in') AS order_type,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(line_total) AS total_revenue
FROM analytics.fact_order_items
WHERE order_status != 'cancelled'
GROUP BY order_type;
```

---

### Card 6: Table Performance & Average Ticket Size
* **Visualization:** Table or Bar Chart

```sql
SELECT 
    t.table_number,
    COUNT(DISTINCT p.payment_id) AS total_turns,
    SUM(p.total_amount) AS total_revenue,
    ROUND(AVG(p.total_amount), 2) AS avg_spend_per_table
FROM analytics.fact_payments p
JOIN analytics.dim_table t ON p.table_id = t.table_id
GROUP BY t.table_number
ORDER BY total_revenue DESC;
```
