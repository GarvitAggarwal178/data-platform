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


def transform_world_bank(**context):
    conn = get_db_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, raw_payload FROM staging.raw_world_bank
        WHERE id NOT IN (
            SELECT DISTINCT CAST(raw_source_id AS INT)
            FROM warehouse.fact_transactions
            WHERE raw_source_id ~ '^[0-9]+$'
        )
    """)
    rows = cursor.fetchall()
    print(f"Transforming {len(rows)} new World Bank records")

    inserted = 0
    for row_id, payload in rows:
        country   = payload.get("countryname", "Unknown")
        sector    = (payload.get("sector1") or {}).get("Name") or payload.get("mjsector_namecode", [{}])[0].get("name", "Unknown") if payload.get("mjsector_namecode") else "Unknown"
        org_name  = payload.get("borrower") or payload.get("projectname", "Unknown")
        amount    = float(str(payload.get("totalamt", 0)).replace(",", "").strip() or 0)
        year      = int(payload.get("boardapprovaldate", "2020-01-01")[:4]) if payload.get("boardapprovaldate") else 2020
        status    = payload.get("status", "unknown").lower()
        project_id = payload.get("id", str(row_id))

        # upsert geography
        cursor.execute("""
            INSERT INTO warehouse.dim_geography (country, region)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            RETURNING geo_id
        """, (country, payload.get("regionname", "")))
        geo = cursor.fetchone()
        if not geo:
            cursor.execute("SELECT geo_id FROM warehouse.dim_geography WHERE country = %s LIMIT 1", (country,))
            geo = cursor.fetchone()
        if not geo:
            continue
        geo_id = geo[0]

        # upsert organization
        cursor.execute("""
            INSERT INTO warehouse.dim_organization (org_name, org_type, sector)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING org_id
        """, (org_name, "borrower", sector))
        org = cursor.fetchone()
        if not org:
            cursor.execute("SELECT org_id FROM warehouse.dim_organization WHERE org_name = %s LIMIT 1", (org_name,))
            org = cursor.fetchone()
        if not org:
            continue
        org_id = org[0]

        # upsert time
        cursor.execute("""
            INSERT INTO warehouse.dim_time (full_date, day, month, quarter, year, month_name)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING time_id
        """, (f"{year}-01-01", 1, 1, 1, year, "January"))
        t = cursor.fetchone()
        if not t:
            cursor.execute("SELECT time_id FROM warehouse.dim_time WHERE year = %s LIMIT 1", (year,))
            t = cursor.fetchone()
        if not t:
            continue
        time_id = t[0]

        # upsert program
        cursor.execute("""
            INSERT INTO warehouse.dim_program (program_name, program_type, source)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING program_id
        """, (payload.get("projectname", "Unknown"), "loan", "World Bank"))
        prog = cursor.fetchone()
        if not prog:
            cursor.execute("SELECT program_id FROM warehouse.dim_program WHERE program_name = %s LIMIT 1", (payload.get("projectname", "Unknown"),))
            prog = cursor.fetchone()
        if not prog:
            continue
        program_id = prog[0]

        # insert fact
        cursor.execute("""
            INSERT INTO warehouse.fact_transactions
                (org_id, geo_id, time_id, program_id, amount_usd, currency, status, raw_source_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (org_id, geo_id, time_id, program_id, amount, "USD", status, str(row_id)))
        inserted += 1

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Inserted {inserted} World Bank records into warehouse")


def transform_sec_edgar(**context):
    conn = get_db_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, raw_payload FROM staging.raw_sec_edgar
    """)
    rows = cursor.fetchall()
    print(f"Transforming {len(rows)} SEC EDGAR records")

    inserted = 0
    for row_id, payload in rows:
        company  = payload.get("company", "Unknown")
        form     = payload.get("form", "Unknown")
        date_str = payload.get("date", "2020-01-01")
        accession = payload.get("_id", str(row_id))

        try:
            year = int(date_str[:4])
        except Exception:
            year = 2020

        # upsert geography (SEC Edgar = USA)
        cursor.execute("""
            INSERT INTO warehouse.dim_geography (country, region, iso_code)
            VALUES ('United States', 'North America', 'US')
            ON CONFLICT DO NOTHING
            RETURNING geo_id
        """)
        geo = cursor.fetchone()
        if not geo:
            cursor.execute("SELECT geo_id FROM warehouse.dim_geography WHERE iso_code = 'US' LIMIT 1")
            geo = cursor.fetchone()
        if not geo:
            continue
        geo_id = geo[0]

        cursor.execute("""
            INSERT INTO warehouse.dim_organization (org_name, org_type, sector)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING org_id
        """, (company, "corporation", "Finance"))
        org = cursor.fetchone()
        if not org:
            cursor.execute("SELECT org_id FROM warehouse.dim_organization WHERE org_name = %s LIMIT 1", (company,))
            org = cursor.fetchone()
        if not org:
            continue
        org_id = org[0]

        cursor.execute("""
            INSERT INTO warehouse.dim_time (full_date, day, month, quarter, year, month_name)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING time_id
        """, (date_str, 1, int(date_str[5:7]) if len(date_str) >= 7 else 1,
              (int(date_str[5:7]) - 1) // 3 + 1 if len(date_str) >= 7 else 1,
              year, "January"))
        t = cursor.fetchone()
        if not t:
            cursor.execute("SELECT time_id FROM warehouse.dim_time WHERE year = %s LIMIT 1", (year,))
            t = cursor.fetchone()
        if not t:
            continue
        time_id = t[0]

        cursor.execute("""
            INSERT INTO warehouse.dim_program (program_name, program_type, source)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING program_id
        """, (f"SEC Filing {form}", "filing", "SEC EDGAR"))
        prog = cursor.fetchone()
        if not prog:
            cursor.execute("SELECT program_id FROM warehouse.dim_program WHERE program_name = %s LIMIT 1", (f"SEC Filing {form}",))
            prog = cursor.fetchone()
        if not prog:
            continue
        program_id = prog[0]

        cursor.execute("""
            INSERT INTO warehouse.fact_transactions
                (org_id, geo_id, time_id, program_id, amount_usd, currency, status, raw_source_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (org_id, geo_id, time_id, program_id, 0.0, "USD", "filed", accession))
        inserted += 1

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Inserted {inserted} SEC EDGAR records into warehouse")


with DAG(
    dag_id="transform_to_warehouse",
    default_args=default_args,
    description="Transforms staging data into warehouse star schema",
    schedule_interval="0 8 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["transform", "warehouse"],
) as dag:

    wb_task = PythonOperator(
        task_id="transform_world_bank",
        python_callable=transform_world_bank,
    )

    sec_task = PythonOperator(
        task_id="transform_sec_edgar",
        python_callable=transform_sec_edgar,
    )

    wb_task >> sec_task