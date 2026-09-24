"""
KanhaSushi Incremental Extractor
Pulls delta records from Supabase REST API and loads raw data into the OLAP Warehouse (PostgreSQL)
"""

import os
import json
import logging
from datetime import datetime, timedelta
import requests
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

WAREHOUSE_HOST = os.getenv("WAREHOUSE_HOST", "warehouse")
WAREHOUSE_PORT = int(os.getenv("WAREHOUSE_PORT", "5432"))
WAREHOUSE_DB = os.getenv("WAREHOUSE_DB", "kanha_analytics")
WAREHOUSE_USER = os.getenv("WAREHOUSE_USER", "kanha_admin")
WAREHOUSE_PASSWORD = os.getenv("WAREHOUSE_PASSWORD", "kanha_secure_password_123")

# Supabase REST API has a URL length limit — batch IDs to avoid 414 URI Too Long
SUPABASE_ID_BATCH_SIZE = 50


def get_warehouse_connection():
    return psycopg2.connect(
        host=WAREHOUSE_HOST,
        port=WAREHOUSE_PORT,
        dbname=WAREHOUSE_DB,
        user=WAREHOUSE_USER,
        password=WAREHOUSE_PASSWORD,
    )


PAGE_SIZE = 1000  # Supabase PostgREST hard cap per request


def fetch_from_supabase(endpoint: str, params: dict = None) -> list:
    """
    Fetch ALL rows from Supabase REST API using pagination via the Range header.
    Supabase caps each response at 1000 rows — we loop through all pages until done.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment")

    base_headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Accept-Profile": "public",
        "Prefer": "count=none",
    }
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/{endpoint}"
    all_rows = []
    offset = 0

    while True:
        # Range header: "from-to" (both inclusive), e.g. "0-999" fetches rows 0..999
        range_end = offset + PAGE_SIZE - 1
        headers = {**base_headers, "Range": f"{offset}-{range_end}"}
        response = requests.get(url, headers=headers, params=params, timeout=60)
        response.raise_for_status()
        page = response.json()

        if not page:
            break  # No more rows

        all_rows.extend(page)
        logging.info(f"  [{endpoint}] fetched page offset={offset}, got {len(page)} rows (total so far: {len(all_rows)})")

        if len(page) < PAGE_SIZE:
            break  # Last page — fewer rows than page size means we're done

        offset += PAGE_SIZE  # Advance to next page

    return all_rows


def fetch_child_records_by_parent_ids(endpoint: str, fk_col: str, parent_ids: list) -> list:
    """
    Fetch child records matching a list of parent IDs, batched to avoid 414 URI Too Long.
    Supabase uses PostgREST `col=in.(id1,id2,...)` filter which is URL-length sensitive.
    """
    all_records = []
    for i in range(0, len(parent_ids), SUPABASE_ID_BATCH_SIZE):
        batch = parent_ids[i: i + SUPABASE_ID_BATCH_SIZE]
        id_list = ",".join(batch)
        records = fetch_from_supabase(endpoint, {
            "select": "*",
            fk_col: f"in.({id_list})",
        })
        all_records.extend(records)
        logging.info(f"Fetched batch {i // SUPABASE_ID_BATCH_SIZE + 1}: {len(records)} rows from {endpoint}")
    return all_records


def upsert_records(cursor, table_name: str, records: list, id_col: str = "id"):
    """Generic idempotent upsert into raw schema"""
    if not records:
        logging.info(f"No records to upsert for {table_name}")
        return

    cols = list(records[0].keys())
    # Format JSONB objects as strings for Postgres
    values = []
    for r in records:
        row = []
        for c in cols:
            val = r.get(c)
            if isinstance(val, (dict, list)):
                row.append(json.dumps(val))
            else:
                row.append(val)
        values.append(row)

    col_names = ", ".join(cols)
    non_id_cols = [col for col in cols if col != id_col]
    if non_id_cols:
        update_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in non_id_cols])
        conflict_action = f"DO UPDATE SET {update_clause}, _ingested_at = CURRENT_TIMESTAMP"
    else:
        conflict_action = "DO NOTHING"

    query = f"""
        INSERT INTO raw.{table_name} ({col_names}, _ingested_at)
        VALUES %s
        ON CONFLICT ({id_col}) {conflict_action};
    """

    template = f"({', '.join(['%s'] * len(cols))}, CURRENT_TIMESTAMP)"
    execute_values(cursor, query, values, template=template)
    logging.info(f"Successfully upserted {len(records)} rows into raw.{table_name}")


def run_extraction(watermark_lookback_days: int = 3):
    """Main extraction pipeline run by Airflow"""
    lookback_date = (datetime.utcnow() - timedelta(days=watermark_lookback_days)).isoformat()
    logging.info(f"Starting extraction with watermark lookback: {lookback_date}")

    conn = get_warehouse_connection()
    try:
        with conn.cursor() as cur:
            # 1. Master / Dimension Tables (Full snapshot extraction — no watermark needed)
            dimension_tables = [
                "categories",
                "menu_items",
                "menu_item_variants",
                "menu_item_option_groups",
                "menu_item_options",
                "tables",
                "account",
            ]
            for tbl in dimension_tables:
                data = fetch_from_supabase(tbl, {"select": "*"})
                upsert_records(cur, tbl, data)

            # 2. Transactional Tables (Incremental Watermarking by updated_at / paid_at)

            # Orders: fetch those updated within watermark window
            orders = fetch_from_supabase("orders", {
                "select": "*",
                "updated_at": f"gte.{lookback_date}",
            })
            upsert_records(cur, "orders", orders)

            if orders:
                order_ids = [str(o["id"]) for o in orders]
                logging.info(f"Fetching order_items for {len(order_ids)} orders (batched)...")
                # BATCH the child lookup — avoid 414 URI Too Long with hundreds of UUIDs
                order_items = fetch_child_records_by_parent_ids("order_items", "order_id", order_ids)
                upsert_records(cur, "order_items", order_items)

            # Payments: paid within watermark window
            payments = fetch_from_supabase("payments", {
                "select": "*",
                "paid_at": f"gte.{lookback_date}",
            })
            upsert_records(cur, "payments", payments)

            if payments:
                payment_ids = [str(p["id"]) for p in payments]
                logging.info(f"Fetching payment_items for {len(payment_ids)} payments (batched)...")
                # BATCH the child lookup
                payment_items = fetch_child_records_by_parent_ids("payment_items", "payment_id", payment_ids)
                upsert_records(cur, "payment_items", payment_items)

        conn.commit()
        logging.info("Extraction and Loading to Raw schema completed successfully.")
    except Exception as e:
        conn.rollback()
        logging.error(f"Extraction failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_extraction()
