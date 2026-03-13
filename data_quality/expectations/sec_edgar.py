import great_expectations as gx


def build_sec_edgar_suite(context):
    suite_name = "sec_edgar_suite"

    suite = context.add_or_update_expectation_suite(
        expectation_suite_name=suite_name
    )

    validator = context.get_validator(
        batch_request=...,
        expectation_suite_name=suite_name,
    )

    validator.expect_column_values_to_not_be_null("project_id")

    # SEC filings should always be US-based
    validator.expect_column_values_to_be_in_set(
        column="country_name",
        value_set=["United States"],
    )

    validator.expect_column_values_to_not_be_null("transaction_date")

    validator.expect_table_row_count_to_be_between(min_value=1, max_value=50_000)

    validator.save_expectation_suite(discard_failed_expectations=False)
    return suite_name