-- Union all three sources into one consistent shape
-- This is ephemeral so it becomes a CTE in the final mart query
-- No table is created in the DB for this model

with world_bank as (
    select * from {{ ref('stg_world_bank') }}
),

oecd as (
    select * from {{ ref('stg_oecd') }}
),

sec_edgar as (
    select * from {{ ref('stg_sec_edgar') }}
),

unioned as (
    select * from world_bank
    union all
    select * from oecd
    union all
    select * from sec_edgar
)

select * from unioned