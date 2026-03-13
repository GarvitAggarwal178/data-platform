# Financial Data Platform

A fully containerised end-to-end data platform that ingests public financial data from three sources — **World Bank**, **OECD**, and **SEC EDGAR** — transforms it through a star-schema data warehouse using dbt, and serves it via a REST API to a React dashboard.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Network                           │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐   │
│  │  Airflow │───▶│ Postgres │◀──│   dbt    │    │   API    │   │
│  │ (8080)   │    │ (5433)   │    │          │    │  (8000)  │   │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘   │
│       │               │                               │         │
│  Ingest DAGs     staging + warehouse            FastAPI +       │
│  run at 07:00    schemas in Postgres            SQLAlchemy      │
│                                                      │          │
│                                               ┌──────────┐      │
│                                               │ Frontend │      │
│                                               │  (3000)  │      │
│                                               └──────────┘      │
│                                               React + Recharts  │
│                                                                 │
│  ┌──────────┐                                                   │
│  │ Metabase │  (3001)  — optional BI tool                       │
│  └──────────┘                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
External APIs
    │
    ▼
Airflow DAGs (ingestion)
    │  world_bank_ingestion  → staging.raw_world_bank
    │  oecd_ingestion        → staging.raw_oecd
    │  sec_edgar_ingestion   → staging.raw_sec_edgar
    ▼
dbt (transformation)
    │  staging models  → stg_world_bank, stg_oecd, stg_sec_edgar
    │  intermediate    → int_transactions_unioned
    │  mart dims       → dim_geography, dim_organization, dim_time, dim_program
    │  mart fact       → fact_transactions
    ▼
FastAPI
    │  reads from warehouse schema via SQLAlchemy
    ▼
React Dashboard
    │  stat cards, bar chart, line chart, transactions table
```

---

## Services & Ports

| Service | URL | Credentials |
|---|---|---|
| **Frontend** | http://localhost:3000 | — |
| **API** | http://localhost:8000 | — |
| **API Docs (Swagger)** | http://localhost:8000/docs | — |
| **Airflow** | http://localhost:8080 | `admin` / `admin` |
| **Metabase** | http://localhost:3001 | set on first run |
| **PostgreSQL** | `localhost:5433` | see `.env` |

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v24+)
- [Git](https://git-scm.com/)
- 4 GB RAM allocated to Docker (8 GB recommended)

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/GarvitAggarwal178/data-platform.git
cd data-platform
```

### 2. Create your environment file

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=findata
VITE_API_URL=http://localhost:8000
```

### 3. Start all services

```bash
docker-compose up --build
```

This builds and starts: Postgres, Airflow, API, Frontend, Metabase.  
First build takes ~3–5 minutes.

### 4. Trigger the ingestion DAGs

Open **http://localhost:8080** → login `admin / admin`

Trigger each DAG in order by clicking the ▶️ button:

1. `world_bank_ingestion` — waits for ✅ green
2. `sec_edgar_ingestion` — waits for ✅ green
3. `oecd_ingestion` — waits for ✅ green
4. `transform_to_warehouse` — runs dbt, populates warehouse

### 5. Open the dashboard

**http://localhost:3000**

---

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `POSTGRES_USER` | PostgreSQL username | `admin` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `password123` |
| `POSTGRES_DB` | Database name | `findata` |
| `VITE_API_URL` | API base URL baked into frontend at build time | `http://localhost:8000` |

---

## API Reference

Base URL: `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

---

### Health

#### `GET /health`

Returns API health status.

**Response**
```json
{ "status": "ok" }
```

---

### Transactions

#### `GET /api/v1/transactions`

Returns a paginated list of transactions joined with all dimension tables.

**Query Parameters**

| Parameter | Type | Description |
|---|---|---|
| `country` | `string` | Filter by country name (partial match) |
| `sector` | `string` | Filter by sector (partial match) |
| `year` | `integer` | Filter by year e.g. `2024` |
| `min_amount` | `float` | Minimum transaction amount in USD |
| `max_amount` | `float` | Maximum transaction amount in USD |
| `source` | `string` | Data source: `World Bank`, `OECD`, `SEC EDGAR` |
| `limit` | `integer` | Max records to return (default: `100`, max: `1000`) |
| `offset` | `integer` | Pagination offset (default: `0`) |

**Example**
```bash
curl "http://localhost:8000/api/v1/transactions?source=World+Bank&year=2024&limit=10"
```

**Response**
```json
{
  "data": [
    {
      "transaction_id": "40478293c1b567a1c4530723784e51da",
      "amount_usd": 240000000,
      "currency": "USD",
      "status": "active",
      "raw_source_id": "P123456",
      "country": "India",
      "region": "South Asia",
      "org_name": "Ministry of Finance, India",
      "sector": "Infrastructure",
      "full_date": "2024-03-15",
      "year": 2024,
      "quarter": 1,
      "program_name": "India Infrastructure Development Project",
      "source": "World Bank"
    }
  ],
  "count": 1
}
```

---

#### `GET /api/v1/transactions/summary`

Returns aggregated totals grouped by sector, source, and year. Used by the dashboard charts.

**Query Parameters**

| Parameter | Type | Description |
|---|---|---|
| `country` | `string` | Filter by country name |
| `year` | `integer` | Filter by year |

**Example**
```bash
curl "http://localhost:8000/api/v1/transactions/summary"
```

**Response**
```json
{
  "data": [
    {
      "sector": "Infrastructure",
      "source": "World Bank",
      "year": 2024,
      "total_amount": 21011460000,
      "transaction_count": 101
    }
  ]
}
```

---

### Geography

#### `GET /api/v1/geography/countries`

Returns a list of all unique countries in the warehouse.

**Example**
```bash
curl "http://localhost:8000/api/v1/geography/countries"
```

**Response**
```json
{
  "data": [
    { "country": "India", "region": "South Asia" },
    { "country": "Nigeria", "region": "Sub-Saharan Africa" }
  ]
}
```

---

## Data Sources

### World Bank — IBRD Projects
- **Source**: [World Bank Projects API](https://search.worldbank.org/api/v2/projects)
- **DAG**: `world_bank_ingestion` — runs daily at 07:00
- **Raw table**: `staging.raw_world_bank`
- **Fields used**: `id`, `countryname`, `totalamt`, `boardapprovaldate`, `sector1`, `projectname`, `status`
- **Staging model**: `dbt/models/staging/stg_world_bank.sql`

### OECD — Official Development Assistance
- **Source**: [OECD SDMX API](https://stats.oecd.org/SDMX-JSON/data/TABLE1)
- **DAG**: `oecd_ingestion` — runs daily at 07:00
- **Raw table**: `staging.raw_oecd`
- **Format**: SDMX-JSON, unpacked per observation
- **Staging model**: `dbt/models/staging/stg_oecd.sql`

### SEC EDGAR — Corporate Filings (Apple Inc)
- **Source**: [SEC EDGAR Full-Text Search API](https://efts.sec.gov/LATEST/search-index)
- **DAG**: `sec_edgar_ingestion` — runs daily at 07:00
- **Raw table**: `staging.raw_sec_edgar`
- **CIK**: `0000320193` (Apple Inc)
- **Fields used**: `_id` (accession number), `form`, `date`, `company`
- **Staging model**: `dbt/models/staging/stg_sec_edgar.sql`

---

## Database Schema

### Staging Schema (`staging`)

| Table | Description |
|---|---|
| `raw_world_bank` | Raw JSONB payloads from World Bank API |
| `raw_oecd` | Raw JSONB payloads from OECD SDMX API |
| `raw_sec_edgar` | Raw JSONB payloads from SEC EDGAR API |
| `ingestion_log` | Tracks last successful ingestion per source |

### Warehouse Schema (`warehouse`) — Star Schema

| Table | Type | Description |
|---|---|---|
| `dim_geography` | Dimension | Countries and regions |
| `dim_organization` | Dimension | Borrowers, corporations, governments |
| `dim_time` | Dimension | Calendar dates with day/month/quarter/year |
| `dim_program` | Dimension | Projects, loans, and filing programs |
| `fact_transactions` | Fact | Financial transactions linking all dimensions |

#### `fact_transactions` columns

| Column | Type | Description |
|---|---|---|
| `transaction_id` | `VARCHAR(64)` PK | dbt surrogate key (MD5 of project_id + source) |
| `org_id` | `VARCHAR(64)` FK | Links to `dim_organization` |
| `geo_id` | `VARCHAR(64)` FK | Links to `dim_geography` |
| `time_id` | `VARCHAR(64)` FK | Links to `dim_time` |
| `program_id` | `VARCHAR(64)` FK | Links to `dim_program` |
| `amount_usd` | `NUMERIC(18,2)` | Transaction value in USD |
| `currency` | `VARCHAR(10)` | Always `USD` |
| `status` | `VARCHAR(50)` | e.g. `active`, `disbursed`, `filed` |
| `raw_source_id` | `VARCHAR(255)` | Original ID from source system |

---

## dbt Models

```
dbt/models/
├── staging/
│   ├── sources.yml              # Declares staging.raw_* source tables
│   ├── schema.yml               # Tests: not_null, unique, accepted_values
│   ├── stg_world_bank.sql       # Incremental, deduplicates on project_id
│   ├── stg_oecd.sql             # Unpacks SDMX-JSON observations
│   └── stg_sec_edgar.sql        # Normalises EDGAR filing records
├── intermediate/
│   └── int_transactions_unioned.sql  # UNION ALL of all three staging models
└── marts/
    ├── dim_geography.sql        # Distinct countries + regions
    ├── dim_organization.sql     # Distinct orgs + sectors
    ├── dim_time.sql             # Distinct dates with calendar attributes
    ├── dim_program.sql          # Distinct programs + sources
    └── fact_transactions.sql    # Final fact table with FK lookups
```

### Running dbt manually

```bash
# Compile only (no DB writes) — check for syntax errors
docker-compose run --rm dbt compile

# Full run
docker-compose run --rm dbt run

# Full refresh — drops and recreates all tables from scratch
docker-compose run --rm dbt run --full-refresh

# Run tests
docker-compose run --rm dbt test

# Check source freshness
docker-compose run --rm dbt source freshness
```

---

## Airflow DAGs

| DAG | Schedule | Description |
|---|---|---|
| `world_bank_ingestion` | `0 7 * * *` (07:00 daily) | Fetches 100 World Bank IBRD projects into `staging.raw_world_bank` |
| `sec_edgar_ingestion` | `0 7 * * *` (07:00 daily) | Fetches Apple Inc SEC filings into `staging.raw_sec_edgar` |
| `oecd_ingestion` | `0 7 * * *` (07:00 daily) | Fetches OECD ODA data into `staging.raw_oecd` |
| `transform_to_warehouse` | `0 8 * * *` (08:00 daily) | Triggers `dbt run` + `dbt test` to populate warehouse |

---

## Project Structure

```
data-platform/
├── airflow/
│   ├── dags/
│   │   ├── world_bank.py          # World Bank ingestion DAG
│   │   ├── sec_edgar.py           # SEC EDGAR ingestion DAG
│   │   ├── oecd.py                # OECD ingestion DAG
│   │   └── transform.py           # dbt trigger DAG
│   ├── Dockerfile
│   ├── entrypoint.sh
│   └── requirements.txt
├── api/
│   ├── routes/
│   │   ├── transactions.py        # /api/v1/transactions endpoints
│   │   └── geography.py           # /api/v1/geography endpoints
│   ├── models.py                  # SQLAlchemy ORM models
│   ├── database.py                # Async DB connection
│   ├── main.py                    # FastAPI app + CORS config
│   ├── Dockerfile
│   └── requirements.txt
├── database/
│   └── init.sql                   # Creates staging + warehouse schemas on first run
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
│   ├── dbt_project.yml
│   └── profiles.yml
├── frontend/
│   ├── src/
│   │   ├── api/client.js          # Axios instance — reads VITE_API_URL
│   │   ├── hooks/                 # useTransactions, useSummary, useCountries
│   │   ├── components/            # StatCard, TransactionsTable, charts
│   │   └── App.jsx                # Main dashboard layout
│   ├── Dockerfile                 # Multi-stage: Vite build → nginx serve
│   ├── package.json
│   └── vite.config.js
├── data_quality/
│   └── gx/                        # Great Expectations suites
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Common Commands

```bash
# Start everything
docker-compose up --build

# Start in background
docker-compose up --build -d

# Stop everything (keep data)
docker-compose down

# Stop and wipe database volume (fresh start)
docker-compose down -v

# Rebuild only the frontend (after env var changes)
docker-compose up --build --no-deps frontend

# View API logs
docker-compose logs -f api

# View Airflow logs
docker-compose logs -f airflow

# Connect to Postgres directly
docker exec -it dataplatform-postgres-1 psql -U admin -d findata

# Check row counts in all tables
docker exec -it dataplatform-postgres-1 psql -U admin -d findata -c "
SELECT 'fact_transactions' as tbl, count(*) FROM warehouse.fact_transactions
UNION ALL SELECT 'dim_geography', count(*) FROM warehouse.dim_geography
UNION ALL SELECT 'dim_organization', count(*) FROM warehouse.dim_organization
UNION ALL SELECT 'dim_time', count(*) FROM warehouse.dim_time
UNION ALL SELECT 'dim_program', count(*) FROM warehouse.dim_program
UNION ALL SELECT 'raw_world_bank', count(*) FROM staging.raw_world_bank
UNION ALL SELECT 'raw_oecd', count(*) FROM staging.raw_oecd
UNION ALL SELECT 'raw_sec_edgar', count(*) FROM staging.raw_sec_edgar;"
```

---

## Troubleshooting

### Frontend shows all zeros

The Vite frontend bakes `VITE_API_URL` into the static bundle at build time.  
If it's wrong, the browser calls the wrong API URL.

**Fix:**
1. Set `VITE_API_URL=http://localhost:8000` in your `.env`
2. Rebuild: `docker-compose up --build --no-deps frontend`

### `{"data":[]}` from the API

The warehouse tables are empty. Run the Airflow DAGs in order:
1. All three ingestion DAGs
2. `transform_to_warehouse`

Then verify: `curl http://localhost:8000/api/v1/transactions/summary`

### dbt `source 'staging' is not found`

The `sources.yml` file is missing. It should exist at `dbt/models/staging/sources.yml`.

### Airflow DAG not appearing

DAG files must be in `airflow/dags/`. The folder is mounted as a volume so changes are picked up automatically within ~30 seconds.

### `docker-compose run --rm dbt` gives `No such command 'dbt'`

The dbt container's entrypoint is already `dbt`. Run:
```bash
docker-compose run --rm dbt compile   # not: dbt dbt compile
docker-compose run --rm dbt run
```

### Orphan container warnings

Safe to ignore, or clean up with:
```bash
docker-compose down --remove-orphans
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Ingestion | Apache Airflow 2.x (LocalExecutor) |
| Raw Storage | PostgreSQL 15 (JSONB) |
| Transformation | dbt-core 1.7 + dbt-postgres |
| Data Quality | Great Expectations |
| API | FastAPI + SQLAlchemy (async) + Uvicorn |
| Frontend | React 18 + Vite + Recharts + Tailwind CSS |
| BI Tool | Metabase |
| Containerisation | Docker + Docker Compose |
