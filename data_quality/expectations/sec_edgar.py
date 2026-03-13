import great_expectations as gx
from great_expectations.core.expectation_configuration import ExpectationConfiguration


def build_sec_edgar_suite(context) -> str:
    """
    Registers the SEC EDGAR expectation suite.

    SEC EDGAR data is Apple Inc (CIK 0000320193) filing records.
    Every record is a US filing — country_name is always "United States".
    project_id is the accession number from SEC.
    """
    suite_name = "sec_edgar_suite"

    suite = context.add_or_update_expectation_suite(
        expectation_suite_name=suite_name
    )

    # Accession number is the SEC's unique filing ID
    # Format: XXXXXXXXXX-YY-ZZZZZZ (e.g. 0000320193-23-000064)
    # If null, we have no way to deduplicate this record
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_not_be_null",
        kwargs={"column": "project_id"}
    ))

    # All SEC filings are US-based by definition
    # If we see anything other than "United States" something is wrong
    # with our data extraction logic
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_be_in_set",
        kwargs={
            "column": "country_name",
            "value_set": ["United States"]
        }
    ))

    # Filing date must exist — it's how we assign the time dimension
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_column_values_to_not_be_null",
        kwargs={"column": "transaction_date"}
    ))

    # Row count — we pull 100 filings per run (zip of forms/dates/accessions)
    # min=1 catches API failure, max=50000 catches runaway loops
    suite.add_expectation(ExpectationConfiguration(
        expectation_type="expect_table_row_count_to_be_between",
        kwargs={"min_value": 1, "max_value": 50_000}
    ))

    context.save_expectation_suite(
        expectation_suite=suite,
        discard_failed_expectations=False
    )

    return suite_name