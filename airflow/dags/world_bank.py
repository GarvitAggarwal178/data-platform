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

    if not project_list or len(project_list) == 0:
        raise ValueError("No records returned from World Bank API")

    errors = []
    for i, p in enumerate(project_list):
        if not p.get("id"):
            errors.append(f"Row {i}: missing project id")

        raw_amount = p.get("totalamt", 0)
        try:
            float(str(raw_amount).replace(",", "").strip() or 0)
        except (TypeError, ValueError):
            errors.append(f"Row {i}: amount is not a number: {raw_amount}")

    if errors:
        raise ValueError(f"Validation failed with {len(errors)} errors:\n" + "\n".join(errors[:10]))

    print(f"Validation passed — {len(project_list)} records look clean")


def insert_to_staging(**context):
    project_list = context["ti"].xcom_pull(key="projects", task_ids="fetch_world_bank_data")

    if not project_list:
        print("No data to insert")
        return

    conn = get_db_conn()
    cursor = conn.cursor()

    # get existing project IDs already in staging — skip duplicates
    cursor.execute("SELECT raw_payload->>'id' FROM staging.raw_world_bank")
    existing_ids = {row[0] for row in cursor.fetchall()}
    print(f"Found {len(existing_ids)} existing project IDs in staging")

    new_projects = [p for p in project_list if p.get("id") not in existing_ids]
    print(f"New projects to insert: {len(new_projects)}")

    if not new_projects:
        print("No new data — skipping insert")
        cursor.close()
        conn.close()
        return

    rows = [(json.dumps(p), datetime.now(timezone.utc)) for p in new_projects]
    cursor.executemany(
        "INSERT INTO staging.raw_world_bank (raw_payload, ingested_at) VALUES (%s, %s)",
        rows
    )

    # update ingestion log
    cursor.execute("""
        INSERT INTO staging.ingestion_log (source, last_ingested_at, rows_inserted)
        VALUES ('world_bank', %s, %s)
        ON CONFLICT (source) DO UPDATE
            SET last_ingested_at = EXCLUDED.last_ingested_at,
                rows_inserted    = EXCLUDED.rows_inserted
    """, (datetime.now(timezone.utc), len(rows)))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Inserted {len(rows)} new rows into staging.raw_world_bank")


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

    fetch_task >> validate_task >> insert_task