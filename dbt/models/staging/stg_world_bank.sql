{{ config(
    materialized='incremental',
    unique_key='project_id'
) }}

with source as (
    select raw_payload, ingested_at
    from {{ source('staging', 'raw_world_bank') }}

    {% if is_incremental() %}
        -- only pick up rows ingested since the last dbt run
        where ingested_at > (select max(ingested_at) from {{ this }})
    {% endif %}
),

cleaned as (
    select
        raw_payload->>'id'                                                  as project_id,
        raw_payload->>'project_name'                                        as project_name,
        raw_payload->>'countryname'                                         as country_name,
        raw_payload->>'countryshortname'                                    as country_code,
        raw_payload->>'regionname'                                          as region_name,
        raw_payload->'sector1'->>'Name'                                     as sector_name,
        raw_payload->>'status'                                              as status,
        coalesce(
            nullif(replace(raw_payload->>'totalamt', ',', ''), '')::numeric,
            0
        )                                                                   as amount_usd,
        (raw_payload->>'boardapprovaldate')::date                           as transaction_date,
        'World Bank'                                                        as source,
        ingested_at
    from source
    where raw_payload->>'id' is not null
      and raw_payload->>'totalamt' is not null
)

select * from cleaned