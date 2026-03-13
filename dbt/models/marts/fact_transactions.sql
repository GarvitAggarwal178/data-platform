with transactions as (
    select
        *,
        row_number() over (
            partition by project_id, source
            order by ingested_at desc
        ) as rn
    from {{ ref('int_transactions_unioned') }}
),

-- keep only the most recent record per project+source
deduped as (
    select * from transactions where rn = 1
),

geo as (
    select * from {{ ref('dim_geography') }}
),

org as (
    select * from {{ ref('dim_organization') }}
),

time as (
    select * from {{ ref('dim_time') }}
),

program as (
    select * from {{ ref('dim_program') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['t.project_id', 't.source']) }} as transaction_id,
        o.org_id,
        g.geo_id,
        ti.time_id,
        p.program_id,
        t.amount_usd,
        'USD'           as currency,
        1.0             as exchange_rate,
        t.status,
        t.project_id    as raw_source_id
    from deduped t
    left join geo g
        on g.country = t.country_name
        and g.region = t.region_name
    left join org o
        on o.org_name = t.project_name
        and o.registration_no = t.source
    left join time ti
        on ti.full_date = t.transaction_date
    left join program p
        on p.program_name = t.project_name
        and p.source = t.source
)

select * from final