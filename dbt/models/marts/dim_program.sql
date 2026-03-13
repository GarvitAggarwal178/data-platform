with base as (
    select distinct
        project_name,
        sector_name,
        source
    from {{ ref('int_transactions_unioned') }}
    where project_name is not null
)

select
    {{ dbt_utils.generate_surrogate_key(['project_name', 'source']) }} as program_id,
    project_name    as program_name,
    sector_name     as program_type,
    source          as source
from base