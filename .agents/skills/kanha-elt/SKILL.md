---
name: kanha-elt
description: >-
  Data Engineering guidelines, architecture patterns, and best practices for
  building and maintaining the KanhaSushi ELT pipeline (Airflow, dbt, PostgreSQL/BigQuery,
  Star Schema, and Metabase). Use whenever working on ETL/ELT pipelines, data modeling,
  warehouse transformations, or data quality tests for KanhaSushi.
---

# KanhaSushi ELT Pipeline Skill & Engineering Guide

This skill standardizes the design, development, and maintenance of the **KanhaSushi Sales & Analytics ELT Data Platform**. It provides strict conventions for data ingestion, warehouse modeling, late-night operational business day calculations, and automated testing.

---

## 1. Core Architecture Principles

1. **ELT over ETL (In-Warehouse Compute):**
   * **Extract:** Pull incremental delta records from Supabase PostgreSQL using watermark timestamps (`updated_at`). Never perform transformations during extraction.
   * **Load:** Ingest raw records as-is into the **Raw/Bronze** warehouse layer (preserving raw JSONB payloads and source data structures).
   * **Transform:** Execute transformations inside the analytical warehouse using **dbt** (SQL) across **Silver (Staging)** and **Gold (Marts / Star Schema)** layers.
2. **Production Isolation:**
   * Never run analytical aggregation queries directly on the live Supabase OLTP database.
   * Use read-only query users or replica connections with short statement timeouts for extraction.
3. **Idempotency & Determinism:**
   * Every pipeline task must produce the exact same analytical state whether executed once or re-run multiple times for the same time window.
   * Fact tables must use surrogate keys and incremental merge strategies (e.g., `unique_key = 'order_id'`).

---

## 2. KanhaSushi Business Rules & Quirks

### A. Late-Night Business Day Calculation (10:00 AM Cutoff)
KanhaSushi operates from 14:00 to 02:00 (sometimes 04:00 AM). Therefore:
* A **Business Day** starts at **10:00:00 Bangkok Time (UTC+7)** and ends at **09:59:59 the following calendar day**.
* Any order or payment placed between `00:00` and `09:59` Bangkok time belongs to the **previous calendar day's shift**.

**Standard SQL Transformation (Bangkok UTC+7):**
```sql
-- Convert UTC timestamp to Bangkok time, then subtract 10 hours to get the business date
DATE(
    TIMEZONE('Asia/Bangkok', created_at) - INTERVAL '10 hours'
) AS business_date
```

### B. Multilingual JSONB Unnesting
Menu items, categories, and variants store localized strings in JSONB: `{"th": "...", "en": "..."}`.
* In the Staging layer, extract both languages into explicit relational columns: `name_th` and `name_en`.
* Always provide a fallback: `COALESCE(name->>'th', name->>'en', 'Unknown')`.

---

## 3. Data Warehouse Layers (Medallion Pattern)

```
[Supabase OLTP]
      │
      ▼ (Airflow Extract & Load)
[Bronze / Raw Layer] ──► raw_orders, raw_order_items, raw_payments, raw_menu_items
      │
      ▼ (dbt Staging Models)
[Silver / Staging Layer] ──► stg_orders, stg_order_items, stg_payments, stg_menu_items
      │
      ▼ (dbt Mart Models)
[Gold / Marts (Star Schema)] ──► fact_order_items, fact_payments, dim_menu_item, dim_business_date, dim_table
```

### Layer Definitions:
1. **Raw (Bronze):** Untouched tables with metadata columns added:
   * `_ingested_at`: UTC timestamp of ingestion.
   * `_source_table`: Name of the source table.
2. **Staging (Silver):** Cleansed and standardized views/ephemeral tables:
   * Type casting (UUIDs, timestamps, decimals).
   * JSONB extraction.
   * Timezone alignment to `Asia/Bangkok`.
3. **Marts (Gold - Star Schema):**
   * **`fact_order_items`**: Grain = 1 item ordered within an order.
   * **`fact_payments`**: Grain = 1 payment transaction per table.
   * **`dim_menu_item`**: Grain = 1 variant of a menu item.
   * **`dim_business_date`**: Grain = 1 operational business day.
   * **`dim_table`**: Grain = 1 physical dining table.

---

## 4. Airflow DAG Standards

1. Use the **TaskFlow API** (`@dag`, `@task`) for Python-based Airflow DAGs.
2. Schedule daily runs at **10:30 AM Bangkok Time** (`30 3 * * *` UTC) to ingest the completed shift.
3. Configure tasks with:
   * `retries = 3`
   * `retry_delay = timedelta(minutes=5)`
   * `catchup = False` (unless performing backfill runs).

---

## 5. Data Quality Gates (`dbt test`)

Every dbt model must pass automated tests before presentation to BI tools:
1. **Uniqueness & Non-Null:** Primary keys (`order_item_key`, `payment_id`, `variant_id`) must be `unique` and `not_null`.
2. **Value Integrity:**
   * `unit_price >= 0`
   * `quantity > 0`
   * `total_amount >= 0`
3. **Referential Integrity:** Foreign keys in fact tables must match primary keys in dimension tables (`variant_id` references `dim_menu_item.variant_id`).
