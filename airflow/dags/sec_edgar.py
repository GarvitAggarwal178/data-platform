import requests
import json
import psycopg2
import os
from datetime import datetime, timedelta
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
    # SEC EDGAR full-text search API
    # We search for nonprofit grant disclosures in recent filings
    # SEC requires a User-Agent header identifying your app — it's in their ToS
    headers = {
        "User-Agent": "FinDataPlatform contact@example.com",
        "Accept": "application/json",
    }

    # Search for 10-K filings from nonprofit organizations
    url = "https://efts.sec.gov/LATEST/search-index?q=%22grant%22&dateRange=custom&startdt=2023-01-01&enddt=2024-01-01&forms=990"

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()
    hits = data.get("hits", {}).get("hits", [])

    context["ti"].xcom_push(key="edgar_hits", value=hits)
    print(f"Fetched {len(hits)} filings from SEC EDGAR")


def insert_to_staging(**context):
    hits = context["ti"].xcom_pull(key="edgar_hits", task_ids="fetch_sec_edgar_data")

    if not hits:
        print("No data to insert")
        return

    conn = get_db_conn()
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO staging.raw_sec_edgar (raw_payload, ingested_at)
        VALUES (%s, %s)
    """

    rows = [(json.dumps(hit), datetime.utcnow()) for hit in hits]
    cursor.executemany(insert_query, rows)

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Inserted {len(rows)} rows into staging.raw_sec_edgar")


with DAG(
    dag_id="sec_edgar_ingestion",
    default_args=default_args,
    description="Pulls SEC EDGAR nonprofit filing data into staging",
    schedule_interval="0 8 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingestion", "sec-edgar"],
) as dag:

    fetch_task = PythonOperator(
        task_id="fetch_sec_edgar_data",
        python_callable=fetch_sec_edgar_data,
    )

    insert_task = PythonOperator(
        task_id="insert_to_staging",
        python_callable=insert_to_staging,
    )

    fetch_task >> insert_task