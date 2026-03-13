import requests
import json
import psycopg2
import os
from datetime import datetime, timezone, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

def get_db_conn():
    return psycopg2.connect(
        host="postgres",
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


def fetch_sec_edgar_data(**context):
    headers = {
        "User-Agent": "FinDataPlatform contact@example.com",
        "Accept-Encoding": "gzip, deflate",
        "Host": "data.sec.gov",
    }

    company_url = "https://data.sec.gov/submissions/CIK0000320193.json"
    response = requests.get(company_url, headers=headers, timeout=30)
    response.raise_for_status()
    company_data = response.json()

    recent = company_data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])

    hits = [
        {
            "_id": acc,
            "form": form,
            "date": date,
            "company": "Apple Inc",
            "cik": "0000320193"
        }
        for form, date, acc in zip(forms[:100], dates[:100], accessions[:100])
    ]

    context["ti"].xcom_push(key="edgar_hits", value=hits)
    print(f"Fetched {len(hits)} filings from SEC EDGAR")


def validate_data(**context):
    hits = context["ti"].xcom_pull(key="edgar_hits", task_ids="fetch_sec_edgar_data")

    if not hits:
        raise ValueError("SEC EDGAR returned 0 records")

    print(f"SEC EDGAR validation passed — {len(hits)} records")


def insert_to_staging(**context):
    hits = context["ti"].xcom_pull(key="edgar_hits", task_ids="fetch_sec_edgar_data")

    if not hits:
        print("No data to insert")
        return

    conn = get_db_conn()
    cursor = conn.cursor()

    # get existing accession IDs — skip duplicates
    cursor.execute("SELECT raw_payload->>'_id' FROM staging.raw_sec_edgar")
    existing_ids = {row[0] for row in cursor.fetchall()}
    print(f"Found {len(existing_ids)} existing accession IDs in staging")

    new_hits = [h for h in hits if h.get("_id") not in existing_ids]
    print(f"New filings to insert: {len(new_hits)}")

    if not new_hits:
        print("No new data — skipping insert")
        cursor.close()
        conn.close()
        return

    rows = [(json.dumps(h), datetime.now(timezone.utc)) for h in new_hits]
    cursor.executemany(
        "INSERT INTO staging.raw_sec_edgar (raw_payload, ingested_at) VALUES (%s, %s)",
        rows
    )

    cursor.execute("""
        INSERT INTO staging.ingestion_log (source, last_ingested_at, rows_inserted)
        VALUES ('sec_edgar', %s, %s)
        ON CONFLICT (source) DO UPDATE
            SET last_ingested_at = EXCLUDED.last_ingested_at,
                rows_inserted    = EXCLUDED.rows_inserted
    """, (datetime.now(timezone.utc), len(rows)))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Inserted {len(rows)} new rows into staging.raw_sec_edgar")


with DAG(
    dag_id="sec_edgar_ingestion",
    default_args=default_args,
    description="Pulls SEC EDGAR filing data into staging",
    schedule_interval="0 8 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingestion", "sec-edgar"],
) as dag:

    fetch_task = PythonOperator(
        task_id="fetch_sec_edgar_data",
        python_callable=fetch_sec_edgar_data,
    )

    validate_task = PythonOperator(
        task_id="validate_data",
        python_callable=validate_data,
    )

    insert_task = PythonOperator(
        task_id="insert_to_staging",
        python_callable=insert_to_staging,
    )

    fetch_task >> validate_task >> insert_task