-- ==============================================================================
-- KanhaSushi OLAP Warehouse Initialization
-- Based on the exact Supabase schema relations
-- ==============================================================================

-- 1. Create Databases
SELECT 'CREATE DATABASE airflow_metadata'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow_metadata')\gexec

SELECT 'CREATE DATABASE kanha_analytics'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'kanha_analytics')\gexec

-- 2. Connect to the analytical warehouse
\c kanha_analytics;

-- 3. Create Medallion Architecture Schemas
CREATE SCHEMA IF NOT EXISTS raw;        -- Bronze: Raw landing from Supabase
CREATE SCHEMA IF NOT EXISTS staging;    -- Silver: Cleaned, typecast, JSONB unnested
CREATE SCHEMA IF NOT EXISTS analytics;  -- Gold: Star Schema (Facts & Dimensions)

-- 4. Pre-create Raw Tables matching Supabase Schema exactly
-- (Airflow will load data directly into these raw tables)

CREATE TABLE IF NOT EXISTS raw.categories (
    id UUID PRIMARY KEY,
    name JSONB,
    sort_order INT,
    kitchen_type VARCHAR(50),
    _ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.menu_items (
    id UUID PRIMARY KEY,
    category_id UUID,
    name JSONB,
    image_url TEXT,
    is_available BOOLEAN,
    _ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.menu_item_variants (
    id UUID PRIMARY KEY,
    menu_item_id UUID,
    variant_name JSONB,
    regular_price NUMERIC(10,2),
    special_price NUMERIC(10,2),
    is_available BOOLEAN,
    _ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.menu_item_option_groups (
    id UUID PRIMARY KEY,
    menu_item_id UUID,
    name JSONB,
    is_required BOOLEAN,
    max_select INT,
    sort_order INT,
    created_at TIMESTAMP,
    _ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.menu_item_options (
    id UUID PRIMARY KEY,
    option_group_id UUID,
    name JSONB,
    sort_order INT,
    created_at TIMESTAMP,
    _ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.tables (
    id UUID PRIMARY KEY,
    table_number INT,
    status VARCHAR(50),
    created_at TIMESTAMP,
    _ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.customer_sessions (
    id UUID PRIMARY KEY,
    table_id UUID,
    created_at TIMESTAMP,
    session_token TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    _ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.orders (
    id UUID PRIMARY KEY,
    table_id UUID,
    session_id UUID,
    status VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    note TEXT,
    order_seq INT,
    order_type VARCHAR(50),
    _ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.order_items (
    id UUID PRIMARY KEY,
    order_id UUID,
    menu_item_variants_id UUID,
    quantity INT,
    price_at_order NUMERIC(10,2),
    note TEXT,
    _ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.order_item_options (
    id UUID PRIMARY KEY,
    order_item_id UUID,
    option_group_id UUID,
    option_id UUID,
    group_name JSONB,
    option_name JSONB,
    created_at TIMESTAMP,
    _ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.payments (
    id UUID PRIMARY KEY,
    tables_id UUID,
    closed_by UUID,
    total_amount NUMERIC(10,2),
    payment_method VARCHAR(50),
    paid_at TIMESTAMP,
    _ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.payment_items (
    id UUID PRIMARY KEY,
    payment_id UUID,
    menu_item_name JSONB,
    quantity INT,
    price NUMERIC(10,2),
    _ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.account (
    id UUID PRIMARY KEY,
    email VARCHAR(255),
    name VARCHAR(255),
    role VARCHAR(50),
    created_at TIMESTAMP,
    _ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.activity_logs (
    id UUID PRIMARY KEY,
    staff_id UUID,
    action VARCHAR(100),
    target_table VARCHAR(100),
    target_id UUID,
    payload JSONB,
    created_at TIMESTAMP,
    _ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Grant privileges
GRANT ALL ON SCHEMA raw TO kanha_admin;
GRANT ALL ON SCHEMA staging TO kanha_admin;
GRANT ALL ON SCHEMA analytics TO kanha_admin;
GRANT ALL ON ALL TABLES IN SCHEMA raw TO kanha_admin;
