import great_expectations as gx


def build_oecd_suite(context):
    suite_name = "oecd_suite"

    suite = context.add_or_update_expectation_suite(
        expectation_suite_name=suite_name
    )

    validator = context.get_validator(
        batch_request=...,
        expectation_suite_name=suite_name,
    )

    validator.expect_column_values_to_not_be_null("project_id")

    # OECD amounts should be positive — zero means no aid flow recorded,
    # which we filter in dbt anyway, but here we catch truly bad data
    validator.expect_column_values_to_be_between(
        column="amount_usd",
        min_value=0,
        max_value=500_000_000_000,
    )

    # OECD data should always have at least some records
    validator.expect_table_row_count_to_be_between(min_value=1, max_value=100_000)

    validator.expect_column_values_to_not_be_null("source")

    validator.save_expectation_suite(discard_failed_expectations=False)
    return suite_name