import great_expectations as gx
from great_expectations.core.expectation_configuration import ExpectationConfiguration


def build_world_bank_suite(context) -> str:
    """
    Registers the World Bank expectation suite with the GX context.

    We use ExpectationConfiguration directly instead of the Validator pattern
    because we're defining rules, not validating data.
    The Validator pattern requires actual data at suite-build time —
    that's wrong here. Validation against real data happens in run.py.

    Returns the suite name so callers know what to reference.
    """
    suite_name = "world_bank_suite"

    # add_or_update_expectation_suite: create if it doesn't exist,
    # overwrite if it does — idempotent, safe to call multiple times
    suite = context.add_or_update_expectation_suite(
        expectation_suite_name=suite_name
    )

    # Every World Bank project must have an ID
    # Without an ID we can't deduplicate or join to other tables
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_not_be_null",
        kwargs={"column": "project_id"}
    ))

    # Amount must be a non-negative number
    # Negative amounts would indicate a data error — World Bank doesn't record
    # negative disbursements in this dataset
    # 100 billion USD ceiling catches any obviously wrong values
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_be_between",
        kwargs={
            "column": "amount_usd",
            "min_value": 0,
            "max_value": 100_000_000_000,
        }
    ))

    # Transaction date must exist — we use it for the time dimension in dbt
    # A missing date means we can't place this record on the timeline
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_not_be_null",
        kwargs={"column": "transaction_date"}
    ))

    # Row count check — if we get 0 rows the API probably failed silently
    # min=1 catches that, max=10000 catches runaway pagination bugs
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_table_row_count_to_be_between",
        kwargs={"min_value": 1, "max_value": 10_000}
    ))

    # Country name must exist and be a real string
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_not_be_null",
        kwargs={"column": "country_name"}
    ))

    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_value_lengths_to_be_between",
        kwargs={"column": "country_name", "min_value": 2, "max_value": 100}
    ))

    # save_expectation_suite persists the suite to GX's store
    # discard_failed_expectations=False means: keep all expectations
    # even if some fail during an interactive validation session
    context.save_expectation_suite(
        expectation_suite=suite,
        discard_failed_expectations=False
    )

    return suite_name