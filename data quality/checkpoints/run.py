import great_expectations as gx
import pandas as pd
from great_expectations.core.batch import RuntimeBatchRequest


def validate_dataframe(df: pd.DataFrame, suite_name: str) -> bool:
    """
    Validates a pandas DataFrame against a named expectation suite.
    Returns True if all expectations pass, False otherwise.

    We use an in-memory (runtime) datasource here — no files written to disk,
    no database connection needed. GX just validates the DataFrame directly.
    """
    context = gx.get_context()

    # A RuntimeBatchRequest lets you pass an in-memory DataFrame to GX
    # instead of pointing it at a file or database table
    batch_request = RuntimeBatchRequest(
        datasource_name="runtime_datasource",
        data_connector_name="runtime_data_connector",
        data_asset_name=suite_name,
        batch_identifiers={"run_id": "airflow_run"},
        runtime_parameters={"batch_data": df},
    )

    checkpoint_result = context.run_checkpoint(
        checkpoint_name="runtime_checkpoint",
        validations=[
            {
                "batch_request": batch_request,
                "expectation_suite_name": suite_name,
            }
        ],
    )

    # checkpoint_result.success is True only if every single expectation passed
    return checkpoint_result.success


def validate_world_bank(records: list[dict]) -> bool:
    # Convert raw API records into a flat DataFrame for validation
    # We only pull out the fields GX needs to check — not the full JSONB
    rows = []
    for r in records:
        rows.append({
            "project_id":       r.get("id"),
            "country_name":     r.get("countryname"),
            "amount_usd":       r.get("totalamt", 0),
            "transaction_date": r.get("boardapprovaldate"),
            "source":           "World Bank",
        })

    df = pd.DataFrame(rows)
    return validate_dataframe(df, "world_bank_suite")


def validate_oecd(data: dict) -> bool:
    # OECD is one big nested object, so we do minimal unpacking just for validation
    # The goal here is: does this response look sane at all?
    try:
        series = data["dataSets"][0]["series"]
        count = sum(len(v["observations"]) for v in series.values())
        rows = [{"project_id": f"OECD-{i}", "amount_usd": 1, "source": "OECD"} for i in range(count)]
    except (KeyError, IndexError):
        rows = []

    df = pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["project_id", "amount_usd", "source"]
    )
    return validate_dataframe(df, "oecd_suite")


def validate_sec_edgar(hits: list[dict]) -> bool:
    rows = []
    for h in hits:
        src = h.get("_source", {})
        rows.append({
            "project_id":       h.get("_id"),
            "country_name":     "United States",
            "transaction_date": src.get("period_of_report"),
            "source":           "SEC EDGAR",
        })

    df = pd.DataFrame(rows)
    return validate_dataframe(df, "sec_edgar_suite")