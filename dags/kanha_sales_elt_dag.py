"""
Airflow DAG: KanhaSushi Sales ELT Pipeline
Runs daily at 10:30 AM Bangkok Time (03:30 AM UTC), 30 minutes after the restaurant business day cutoff.
"""

from datetime import datetime, timedelta
import os
import subprocess
from airflow.decorators import dag, task

DBT_PROJECT_DIR = "/opt/airflow/dbt_kanhasushi"

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

@dag(
    dag_id="kanhasushi_sales_elt",
    default_args=default_args,
    description="Daily ELT pipeline: Supabase -> Warehouse Raw -> dbt Staging/Marts -> Data Quality Tests",
    schedule_interval="30 3 * * *",  # 03:30 UTC = 10:30 Bangkok Time (UTC+7)
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["kanhasushi", "sales", "elt", "dbt"],
)
def kanhasushi_elt_pipeline():

    @task()
    def extract_and_load():
        """Extract incremental delta from Supabase and load into raw schema"""
        import sys
        if "/opt/airflow" not in sys.path:
            sys.path.insert(0, "/opt/airflow")
        from scripts.extract_supabase import run_extraction
        run_extraction(watermark_lookback_days=3)

    @task()
    def dbt_run_staging():
        """Execute dbt Staging models (Silver layer)"""
        cmd = f"dbt run --project-dir {DBT_PROJECT_DIR} --profiles-dir {DBT_PROJECT_DIR} --select staging"
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)

    @task()
    def dbt_run_marts():
        """Execute dbt Marts models (Gold layer - Star Schema)"""
        cmd = f"dbt run --project-dir {DBT_PROJECT_DIR} --profiles-dir {DBT_PROJECT_DIR} --select marts"
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)

    @task()
    def dbt_test():
        """Execute automated data quality tests"""
        cmd = f"dbt test --project-dir {DBT_PROJECT_DIR} --profiles-dir {DBT_PROJECT_DIR}"
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)

    # Task dependency graph
    el = extract_and_load()
    stg = dbt_run_staging()
    marts = dbt_run_marts()
    test = dbt_test()

    el >> stg >> marts >> test

kanhasushi_elt_pipeline()
