with base as (
    select distinct transaction_date
    from {{ ref('int_transactions_unioned') }}
    where transaction_date is not null
)

select
    {{ dbt_utils.generate_surrogate_key(['transaction_date']) }}     as time_id,
    transaction_date                                                  as full_date,
    extract(day from transaction_date)::int                           as day,
    extract(month from transaction_date)::int                         as month,
    extract(quarter from transaction_date)::int                       as quarter,
    extract(year from transaction_date)::int                          as year,
    to_char(transaction_date, 'Month')                                as month_name
from base