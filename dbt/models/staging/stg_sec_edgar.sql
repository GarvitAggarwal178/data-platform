with source as (
    select raw_payload, ingested_at
    from {{ source('staging', 'raw_sec_edgar') }}
),

cleaned as (
    select
        raw_payload->>'_id'                         as project_id,
        raw_payload->>'display_names'               as project_name,
        'United States'                             as country_name,
        'US'                                        as country_code,
        'North America'                             as region_name,
        'Nonprofit / Grant'                         as sector_name,
        'disbursed'                                 as status,
        -- SEC filings don't have a simple amount field, default 0
        0::numeric                                  as amount_usd,
        coalesce(
            (raw_payload->>'period_of_report')::date,
            current_date
        )                                           as transaction_date,
        'SEC EDGAR'                                 as source,
        ingested_at
    from source
    where raw_payload->>'_id' is not null
)

select * from cleaned