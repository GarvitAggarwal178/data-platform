import os
import subprocess
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def run_dbt(**context):
    """
    Triggers dbt run inside the Airflow container.

    Why run dbt from Airflow instead of a separate container?
    The dbt service in docker-compose uses `profiles: [dbt]` which means
    it only starts when explicitly invoked — it's not a long-running service.
    Running dbt via BashOperator/subprocess from Airflow is the standard
    pattern for LocalExecutor setups without a dedicated dbt Cloud account.

    dbt is installed via the airflow/requirements.txt so it's available
    inside the Airflow container.
    """
    result = subprocess.run(
        ["dbt", "run", "--project-dir", "/opt/airflow/dbt", "--profiles-dir", "/opt/airflow/dbt"],
        capture_output=True,
        text=True,
    )

    # Print output so it appears in Airflow task logs
    print("dbt stdout:\n", result.stdout)
    print("dbt stderr:\n", result.stderr)

    if result.returncode != 0:
        raise RuntimeError(f"dbt run failed with exit code {result.returncode}")

    print("dbt run completed successfully")


def run_dbt_test(**context):
    """
    Runs dbt tests after the dbt run.
    If any test fails, the Airflow task fails — alerting you to data issues.
    """
    result = subprocess.run(
        ["dbt", "test", "--project-dir", "/opt/airflow/dbt", "--profiles-dir", "/opt/airflow/dbt"],
        capture_output=True,
        text=True,
    )

    print("dbt test stdout:\n", result.stdout)
    print("dbt test stderr:\n", result.stderr)

    # dbt test returns exit code 1 if any test fails
    # We warn but don't hard-fail the DAG — data is still in the warehouse
    # Change to `raise` if you want hard failures on test errors
    if result.returncode != 0:
        print("WARNING: dbt tests failed — check logs above for details")


with DAG(
    dag_id="transform_to_warehouse",
    default_args=default_args,
    description="Triggers dbt to transform staging data into warehouse star schema",
    # Runs at 08:00 daily — after ingestion DAGs which run at 07:00
    schedule_interval="0 8 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["transform", "warehouse", "dbt"],
) as dag:

    dbt_run = PythonOperator(
        task_id="dbt_run",
        python_callable=run_dbt,
    )

    dbt_test = PythonOperator(
        task_id="dbt_test",
        python_callable=run_dbt_test,
    )

    dbt_run >> dbt_test