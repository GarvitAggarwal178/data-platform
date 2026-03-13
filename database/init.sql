CREATE SCHEMA IF NOT EXISTS warehouse;

-- Geography dimension: where the money flows
-- geo_id is VARCHAR(64) because dbt generates MD5 surrogate keys (32-char hex strings)
-- SERIAL would break here — dbt writes 'a3f4b2...' not 1,2,3
CREATE TABLE IF NOT EXISTS warehouse.dim_geography (
    geo_id      VARCHAR(64) PRIMARY KEY,
    country     VARCHAR(100) NOT NULL,
    region      VARCHAR(100),
    state       VARCHAR(100),
    city        VARCHAR(100),
    iso_code    VARCHAR(10)
);

-- Organization dimension: who receives or disburses
CREATE TABLE IF NOT EXISTS warehouse.dim_organization (
    org_id          VARCHAR(64) PRIMARY KEY,
    org_name        VARCHAR(255) NOT NULL,
    org_type        VARCHAR(50),   -- NGO, government, multilateral
    sector          VARCHAR(100),  -- education, health, infrastructure
    registration_no VARCHAR(100)
);

-- Time dimension: when it happened
-- We store this broken down so queries like "all Q3 grants" are trivial
CREATE TABLE IF NOT EXISTS warehouse.dim_time (
    time_id     VARCHAR(64) PRIMARY KEY,
    full_date   DATE NOT NULL,
    day         INT,
    month       INT,
    quarter     INT,
    year        INT,
    month_name  VARCHAR(20)
);

-- Program dimension: what initiative the money belongs to
CREATE TABLE IF NOT EXISTS warehouse.dim_program (
    program_id      VARCHAR(64) PRIMARY KEY,
    program_name    VARCHAR(255) NOT NULL,
    program_type    VARCHAR(100),  -- grant, loan, subsidy
    source          VARCHAR(100)   -- World Bank, OECD, SEC EDGAR
);

-- Fact table: the actual financial transactions
-- FKs are VARCHAR(64) to match the surrogate key PKs above
CREATE TABLE IF NOT EXISTS warehouse.fact_transactions (
    transaction_id  VARCHAR(64) PRIMARY KEY,
    org_id          VARCHAR(64) REFERENCES warehouse.dim_organization(org_id),
    geo_id          VARCHAR(64) REFERENCES warehouse.dim_geography(geo_id),
    time_id         VARCHAR(64) REFERENCES warehouse.dim_time(time_id),
    program_id      VARCHAR(64) REFERENCES warehouse.dim_program(program_id),
    amount_usd      NUMERIC(18, 2) NOT NULL,
    currency        VARCHAR(10),
    exchange_rate   NUMERIC(10, 6),
    status          VARCHAR(50),   -- disbursed, committed, cancelled
    raw_source_id   VARCHAR(255)   -- original ID from the source API
);

-- Raw staging tables — data lands here exactly as it comes from APIs
-- Messy, unvalidated. dbt will clean this into the warehouse schema.
-- SERIAL is correct here — these are internal IDs, not dbt surrogate keys
CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.raw_world_bank (
    id              SERIAL PRIMARY KEY,
    ingested_at     TIMESTAMP DEFAULT NOW(),
    raw_payload     JSONB
);

CREATE TABLE IF NOT EXISTS staging.raw_oecd (
    id              SERIAL PRIMARY KEY,
    ingested_at     TIMESTAMP DEFAULT NOW(),
    raw_payload     JSONB
);

CREATE TABLE IF NOT EXISTS staging.raw_sec_edgar (
    id              SERIAL PRIMARY KEY,
    ingested_at     TIMESTAMP DEFAULT NOW(),
    raw_payload     JSONB
);

-- Tracks when each source was last successfully ingested
-- ON CONFLICT (source) DO UPDATE in the DAGs means one row per source, upserted
CREATE TABLE IF NOT EXISTS staging.ingestion_log (
    source           VARCHAR(100) PRIMARY KEY,
    last_ingested_at TIMESTAMP,
    rows_inserted    INT
);