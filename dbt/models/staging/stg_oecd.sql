with source as (
    select raw_payload, ingested_at
    from {{ source('staging', 'raw_oecd') }}
),

observations as (
    select
        obs_key.key                                         as time_period_index,
        (obs_value.value->0)::numeric                       as amount_usd,
        raw_payload->'structure'->'dimensions'->'observation'
            ->0->'values'                                   as time_values,
        ingested_at
    from source,
        jsonb_each(
            raw_payload->'dataSets'->0->'series'
        ) as series_entry(series_key, series_value),
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
        coalesce(
            (
                (time_values->>(time_period_index::int)::int)::jsonb->>'id'
            )::int,
            2020
        )::text || '-01-01'                                 as transaction_date,
        'OECD'                                              as source,
        ingested_at
    from observations
    where amount_usd is not null and amount_usd > 0
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
    transaction_date::date  as transaction_date,
    source,
    ingested_at
from cleaned