{{ config(
    materialized='incremental',
    unique_key='project_id'
) }}

with source as (
    select raw_payload, ingested_at
    from {{ source('staging', 'raw_world_bank') }}

    {% if is_incremental() %}
        -- incremental: only process rows ingested since last dbt run
        -- this prevents reprocessing the entire staging table every time
        where ingested_at > (select max(ingested_at) from {{ this }})
    {% endif %}
),

cleaned as (
    select
        raw_payload->>'id'                                              as project_id,
        raw_payload->>'project_name'                                    as project_name,
        raw_payload->>'countryname'                                     as country_name,
        raw_payload->>'countryshortname'                                as country_code,
        raw_payload->>'regionname'                                      as region_name,
        raw_payload->'sector1'->>'Name'                                 as sector_name,
        raw_payload->>'status'                                          as status,
        coalesce(
            nullif(replace(raw_payload->>'totalamt', ',', ''), '')::numeric,
            0
        )                                                               as amount_usd,
        (raw_payload->>'boardapprovaldate')::date                       as transaction_date,
        'World Bank'                                                    as source,
        ingested_at
    from source
    where raw_payload->>'id' is not null
      and raw_payload->>'totalamt' is not null
),

deduplicated as (
    -- The World Bank API returns the same projects across multiple calls.
    -- Even with DAG-level deduplication on staging inserts, the same
    -- project_id can appear in different ingestion batches.
    -- ROW_NUMBER() partitioned by project_id keeps only the most recent
    -- ingestion of each project — the one with the latest ingested_at.
    select
        *,
        row_number() over (
            partition by project_id
            order by ingested_at desc
        ) as rn
    from cleaned
)

select
    project_id,
    project_name,
    country_name,
    country_code,
    region_name,
    sector_name,
    status,
    amount_usd,
    transaction_date,
    source,
    ingested_at
from deduplicated
where rn = 1
-- rn = 1 means: keep only the most recent row per project_id
-- all other duplicates are filtered out before they reach downstream models