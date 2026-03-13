-- dbt_utils package provides this but we define our own
-- so there's no external dependency needed
-- A surrogate key is a hash of the natural key columns
-- used when there's no single clean primary key in the source data

{% macro generate_surrogate_key(field_list) %}
    md5(
        concat_ws('|',
            {% for field in field_list %}
                coalesce(cast({{ field }} as varchar), '_null_')
                {% if not loop.last %},{% endif %}
            {% endfor %}
        )
    )
{% endmacro %}