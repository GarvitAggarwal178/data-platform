with base as (
    select distinct
        project_name,
        sector_name,
        source
    from {{ ref('int_transactions_unioned') }}
    where project_name is not null
)

select
    {{ dbt_utils.generate_surrogate_key(['project_name', 'source']) }} as org_id,
    project_name    as org_name,
    'NGO/Government' as org_type,
    sector_name     as sector,
    source          as registration_no
from base