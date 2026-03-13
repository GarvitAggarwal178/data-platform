import requests
import json
import psycopg2
import os
import sys
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

sys.path.insert(0, "/opt/airflow/data_quality")
from checkpoints.run_checkpoint import validate_world_bank

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


def fetch_world_bank_data(**context):
    url = "https://search.worldbank.org/api/v2/projects"
    params = {"format": "json", "source": "IBRD", "rows": 100, "os": 0}

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    projects = data.get("projects", {})
    project_list = [v for k, v in projects.items() if k != "total"]

    context["ti"].xcom_push(key="projects", value=project_list)
    print(f"Fetched {len(project_list)} projects from World Bank")


def validate_data(**context):
    project_list = context["ti"].xcom_pull(key="projects", task_ids="fetch_world_bank_data")

    passed = validate_world_bank(project_list)

    if not passed:
        # raising an exception fails the task, Airflow marks it red in the UI
        # and will retry based on default_args — then alert if still failing
        raise ValueError("World Bank data failed quality validation. Halting pipeline.")

    print("Validation passed")


def insert_to_staging(**context):
    project_list = context["ti"].xcom_pull(key="projects", task_ids="fetch_world_bank_data")

    if not project_list:
        print("No data to insert")
        return

    conn = get_db_conn()
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO staging.raw_world_bank (raw_payload, ingested_at)
        VALUES (%s, %s)
    """
    rows = [(json.dumps(project), datetime.utcnow()) for project in project_list]
    cursor.executemany(insert_query, rows)

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Inserted {len(rows)} rows into staging.raw_world_bank")


with DAG(
    dag_id="world_bank_ingestion",
    default_args=default_args,
    description="Pulls World Bank project data into staging",
    schedule_interval="0 6 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingestion", "world-bank"],
) as dag:

    fetch_task = PythonOperator(
        task_id="fetch_world_bank_data",
        python_callable=fetch_world_bank_data,
    )

    validate_task = PythonOperator(
        task_id="validate_data",
        python_callable=validate_data,
    )

    insert_task = PythonOperator(
        task_id="insert_to_staging",
        python_callable=insert_to_staging,
    )

    # now the pipeline is: fetch → validate → insert
    # if validate raises, insert never runs
    fetch_task >> validate_task >> insert_task