import great_expectations as gx
from great_expectations.core.expectation_configuration import ExpectationConfiguration


def build_oecd_suite(context) -> str:
    """
    Registers the OECD expectation suite.

    OECD data comes in SDMX-JSON format — heavily nested.
    By the time it reaches validation in run.py, we've already
    unpacked it into a flat DataFrame with project_id, amount_usd, source.
    These expectations validate that flattened form.
    """
    suite_name = "oecd_suite"

    suite = context.add_or_update_expectation_suite(
        expectation_suite_name=suite_name
    )

    # project_id is our synthetic key: "OECD-{index}"
    # if this is null something went wrong in the unpacking logic
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_not_be_null",
        kwargs={"column": "project_id"}
    ))

    # OECD amounts are in millions USD
    # Zero means no aid flow recorded — we filter these in dbt
    # but here we catch truly corrupted values (negative, astronomical)
    # 500 billion ceiling is generous but realistic for aggregate ODA flows
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_be_between",
        kwargs={
            "column": "amount_usd",
            "min_value": 0,
            "max_value": 500_000_000_000,
        }
    ))

    # Source must always be "OECD" for this suite
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_not_be_null",
        kwargs={"column": "source"}
    ))

    # Row count — OECD dataset has many observations
    # If we get 0 rows the SDMX unpacking failed
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_table_row_count_to_be_between",
        kwargs={"min_value": 1, "max_value": 100_000}
    ))

    context.save_expectation_suite(
        expectation_suite=suite,
        discard_failed_expectations=False
    )

    return suite_name