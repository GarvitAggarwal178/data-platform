with base as (
    select distinct
        country_name,
        country_code,
        region_name
    from {{ ref('int_transactions_unioned') }}
    where country_name is not null
)

select
    {{ dbt_utils.generate_surrogate_key(['country_name', 'region_name']) }} as geo_id,
    country_name    as country,
    region_name     as region,
    country_code    as iso_code,
    null::varchar   as state,
    null::varchar   as city
from base