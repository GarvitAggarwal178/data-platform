{#
  Override dbt's default schema naming behaviour.

  Default behaviour (what we DON'T want):
    final_schema = target_schema + "_" + custom_schema
    e.g. "public" + "_" + "warehouse" = "public_warehouse"

  This override (what we DO want):
    final_schema = custom_schema directly
    e.g. "warehouse" → writes to "warehouse" schema

  Why this matters:
    Our API queries warehouse.dim_geography, warehouse.fact_transactions etc.
    If dbt writes to public_warehouse instead, the API gets zero results
    with no error — the hardest kind of bug to debug.

  This is the official dbt-recommended pattern for single-developer projects.
  Source: https://docs.getdbt.com/docs/build/custom-schemas
#}

{% macro generate_schema_name(custom_schema_name, node) -%}

    {%- if custom_schema_name is none -%}
        {# No custom schema set — use the default target schema (e.g. "public") #}
        {{ target.schema }}

    {%- else -%}
        {# Custom schema is set — use it directly, strip any whitespace #}
        {{ custom_schema_name | trim }}

    {%- endif -%}

{%- endmacro %}