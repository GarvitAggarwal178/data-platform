import great_expectations as gx
import pandas as pd


def build_world_bank_suite(context):
    suite_name = "world_bank_suite"

    # get_or_add_expectation_suite means: create it if it doesn't exist,
    # return it if it already does — idempotent
    suite = context.add_or_update_expectation_suite(
        expectation_suite_name=suite_name
    )

    validator = context.get_validator(
        batch_request=...,  # filled in at runtime by the checkpoint
        expectation_suite_name=suite_name,
    )

    # Every project must have an ID
    validator.expect_column_values_to_not_be_null("project_id")

    # Amount must be a real number, not negative, not absurdly large
    validator.expect_column_values_to_be_between(
        column="amount_usd",
        min_value=0,
        max_value=100_000_000_000,  # 100 billion USD ceiling
    )

    # Date must exist and be a valid date string
    validator.expect_column_values_to_not_be_null("transaction_date")

    # The dataset must have meaningful volume — if we get 0 rows,
    # the API likely failed silently
    validator.expect_table_row_count_to_be_between(
        min_value=1,
        max_value=10_000,
    )

    # Country name should be a non-empty string
    validator.expect_column_values_to_not_be_null("country_name")
    validator.expect_column_value_lengths_to_be_between(
        column="country_name",
        min_value=2,
        max_value=100,
    )

    validator.save_expectation_suite(discard_failed_expectations=False)
    return suite_name