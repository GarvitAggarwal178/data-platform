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


def fetch_oecd_data(**context):
    # OECD SDMX API: pulls official development assistance (ODA) data
    # DAC1 is the dataset for total flows by donor
    # docs: https://data.oecd.org/api/sdmx-json-documentation/
    url = "https://sdmx.oecd.org/public/rest/data/OECD.DCD.FSD,DF_DAC1,1.2/A.DPGC.206.USD.D.Q?startPeriod=2020&endPeriod=2023&format=jsondata"

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    data = response.json()
    context["ti"].xcom_push(key="oecd_data", value=data)
    print("Fetched OECD DAC1 data successfully")


def insert_to_staging(**context):
    data = context["ti"].xcom_pull(key="oecd_data", task_ids="fetch_oecd_data")

    if not data:
        print("No data to insert")
        return

    conn = get_db_conn()
    cursor = conn.cursor()

    # OECD returns one big nested object, store it as a single JSONB row
    # dbt will unpack the observations array later
    insert_query = """
        INSERT INTO staging.raw_oecd (raw_payload, ingested_at)
        VALUES (%s, %s)
    """
    cursor.execute(insert_query, (json.dumps(data), datetime.utcnow()))

    conn.commit()
    cursor.close()
    conn.close()
    print("Inserted OECD data into staging.raw_oecd")


with DAG(
    dag_id="oecd_ingestion",
    default_args=default_args,
    description="Pulls OECD ODA data into staging",
    schedule_interval="0 7 * * *",  # 7am so it runs after World Bank
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingestion", "oecd"],
) as dag:

    fetch_task = PythonOperator(
        task_id="fetch_oecd_data",
        python_callable=fetch_oecd_data,
    )

    insert_task = PythonOperator(
        task_id="insert_to_staging",
        python_callable=insert_to_staging,
    )

    fetch_task >> insert_task