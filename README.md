# KanhaSushi Sales Analytics ELT Data Platform

Production-ready **ELT Data Pipeline** and **Analytical Star Schema** designed for KanhaSushi. Built with **Apache Airflow**, **dbt (data build tool)**, **PostgreSQL (OLAP Warehouse)**, and **Metabase**.

---

## 🏛 Architecture Overview

```
[OLTP: Supabase PostgreSQL]
           │
           │ (1. Incremental Extract via Watermark: updated_at)
           ▼
[Apache Airflow Orchestrator]
           │
           │ (2. Load Raw As-Is)
           ▼
[Warehouse: Raw / Bronze Layer] (raw_orders, raw_payments, raw_menu_items)
           │
           │ (3. dbt Staging / Silver Layer: JSONB Unnesting & 10:00 AM Cutoff)
           ▼
[Warehouse: Staging / Silver Layer] (stg_orders, stg_payments, stg_menu_items)
           │
           │ (4. dbt Marts / Gold Layer: Star Schema Modeling)
           ▼
[Warehouse: Marts / Gold Layer] (fact_order_items, fact_payments, dim_*)
           │
           │ (5. dbt test Quality Assurance)
           ▼
[BI Dashboard: Metabase / Superset]
```

---

## 📂 Project Structure

```
kanhasushi-elt/
├── docker-compose.yml             # Orchestration: Airflow + Warehouse Postgres + Metabase
├── requirements.txt               # Python runtime dependencies
├── .env.example                   # Environment variable template
├── dags/
│   └── kanha_sales_elt_dag.py     # Production Airflow DAG (TaskFlow API)
├── scripts/
│   └── extract_supabase.py        # Incremental extraction engine
└── dbt_kanhasushi/
    ├── dbt_project.yml            # dbt project definition
    └── models/
        ├── staging/               # Silver Layer: Type casting & JSONB unnesting
        │   ├── sources.yml
        │   ├── stg_orders.sql
        │   ├── stg_order_items.sql
        │   ├── stg_payments.sql
        │   └── stg_menu_items.sql
        └── marts/                 # Gold Layer: Kimball Star Schema
            ├── dim_menu_item.sql
            ├── dim_business_date.sql
            ├── dim_table.sql
            ├── fact_order_items.sql
            └── fact_payments.sql
```

---

## 🚀 Quick Start with Docker Compose

### 1. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your Supabase credentials:
```bash
cp .env.example .env
```

### 2. Launch the Platform
Start the entire data stack (Warehouse, Airflow, Metabase):
```bash
docker compose up -d
```

### 3. Access Services
* **Airflow Web UI:** [http://localhost:8080](http://localhost:8080) (Default: `airflow` / `airflow`)
* **Metabase BI:** [http://localhost:3000](http://localhost:3000) (Connects directly to the analytical warehouse)
* **Warehouse Postgres:** `localhost:5433` (Database: `kanha_analytics`)

---

## ⏰ Business Day Cutoff Logic

Because KanhaSushi operates late into the night (14:00 – 02:00 / 04:00 AM), a standard calendar date would incorrectly split a single night's shift across two days.

This pipeline applies a **10:00 AM Bangkok Time (UTC+7)** cutoff:
* Orders placed between `14:00` and `23:59` on Friday belong to **Friday**.
* Orders placed between `00:00` and `09:59` on Saturday morning belong to **Friday's shift**.
* Shift rollover occurs cleanly at **10:00 AM**.


<img width="1850" height="978" alt="image" src="https://github.com/user-attachments/assets/d4b83b53-b302-4871-acba-843a51a4b6fd" />
<img width="1844" height="969" alt="image" src="https://github.com/user-attachments/assets/1c404172-5afc-40f5-b1d6-3282b326e825" />

