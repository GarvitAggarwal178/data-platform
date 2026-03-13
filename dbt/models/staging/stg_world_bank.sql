with source as (
    select raw_payload, ingested_at
    from {{ source('staging', 'raw_world_bank') }}
),

cleaned as (
    select
        raw_payload->>'id'                          as project_id,
        raw_payload->>'project_name'                as project_name,
        raw_payload->>'countryname'                 as country_name,
        raw_payload->>'countryshortname'            as country_code,
        raw_payload->>'regionname'                  as region_name,
        raw_payload->>'sector1'                     as sector_raw,
        -- sector is a nested object, pull just the name
        raw_payload->'sector1'->>'Name'             as sector_name,
        raw_payload->>'status'                      as status,
        -- cast string to numeric, default to 0 if null
        coalesce(
            (raw_payload->>'totalamt')::numeric, 0
        )                                           as amount_usd,
        -- parse ISO date string to actual date
        (raw_payload->>'boardapprovaldate')::date   as transaction_date,
        'World Bank'                                as source,
        ingested_at
    from source
    -- drop rows with no project ID or amount — unusable for analysis
    where raw_payload->>'id' is not null
      and raw_payload->>'totalamt' is not null
)

select * from cleaned