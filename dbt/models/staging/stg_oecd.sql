with source as (
    select raw_payload, ingested_at
    from {{ source('staging', 'raw_oecd') }}
),

-- OECD stores data in SDMX format: observations are arrays of arrays
-- structure: dataSets[0].series["0:0:0:0"].observations{"0": [value, ...]}
-- we need to unpack this into rows
observations as (
    select
        -- jsonb_each unpacks a JSON object into (key, value) rows
        obs_key.key                                         as time_period_index,
        (obs_value.value->0)::numeric                       as amount_usd,
        raw_payload->'structure'->'dimensions'->'series'    as series_dims,
        ingested_at
    from source,
        -- unnest the series object into individual series
        jsonb_each(
            raw_payload->'dataSets'->0->'series'
        ) as series_entry(series_key, series_value),
        -- unnest observations within each series
        jsonb_each(series_value->'observations') as obs_key(key, _),
        lateral (
            select series_value->'observations'->obs_key.key as value
        ) as obs_value
),

cleaned as (
    select
        'OECD-' || time_period_index                        as project_id,
        'OECD Development Aid'                              as project_name,
        'Multiple'                                          as country_name,
        null::varchar                                       as country_code,
        'Global'                                            as region_name,
        'Development Assistance'                            as sector_name,
        'disbursed'                                         as status,
        coalesce(amount_usd, 0)                             as amount_usd,
        current_date                                        as transaction_date,
        'OECD'                                              as source,
        ingested_at
    from observations
    where amount_usd is not null and amount_usd > 0
)

select * from cleaned