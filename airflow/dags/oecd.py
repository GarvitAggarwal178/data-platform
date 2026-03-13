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


def fetch_oecd_data(**context):
    # OECD ODA data via their working stats API
    url = "https://stats.oecd.org/SDMX-JSON/data/TABLE1/BDVAD.AMOUNTFLOW.206.USD.Q/all"
    params = {
        "startTime": "2020",
        "endTime": "2023",
        "dimensionAtObservation": "allDimensions",
    }

    headers = {"Accept": "application/json"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        # fallback — use World Bank ODA dataset if OECD is down
        print(f"OECD primary URL failed: {e}. Trying fallback...")
        fallback_url = "https://api.worldbank.org/v2/en/indicator/DC.ODA.TOTL.CD"
        params = {"format": "json", "per_page": 100, "mrv": 5}
        response = requests.get(fallback_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

    context["ti"].xcom_push(key="oecd_data", value=data)
    print("Fetched OECD/ODA data successfully")


def validate_data(**context):
    data = context["ti"].xcom_pull(key="oecd_data", task_ids="fetch_oecd_data")

    if not data:
        raise ValueError("No data returned from OECD API")

    if isinstance(data, list):
        # World Bank fallback returns a list [metadata, data]
        if len(data) < 2:
            raise ValueError("World Bank fallback response too short")
        print(f"OECD/ODA validation passed (World Bank fallback)")
    else:
        print("OECD validation passed")


def insert_to_staging(**context):
    data = context["ti"].xcom_pull(key="oecd_data", task_ids="fetch_oecd_data")

    if not data:
        print("No data to insert")
        return

    conn = get_db_conn()
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO staging.raw_oecd (raw_payload, ingested_at)
        VALUES (%s, %s)
    """
    cursor.execute(insert_query, (json.dumps(data), datetime.now(timezone.utc)))

    conn.commit()
    cursor.close()
    conn.close()
    print("Inserted OECD data into staging.raw_oecd")


with DAG(
    dag_id="oecd_ingestion",
    default_args=default_args,
    description="Pulls OECD ODA data into staging",
    schedule_interval="0 7 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingestion", "oecd"],
) as dag:

    fetch_task = PythonOperator(
        task_id="fetch_oecd_data",
        python_callable=fetch_oecd_data,
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