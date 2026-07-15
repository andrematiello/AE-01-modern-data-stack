with calendar as (

    select * from {{ ref('int_trading_calendar') }}

)

select
    {{ dbt_utils.generate_surrogate_key(['trade_date']) }} as date_key,
    trade_date,
    year,
    month,
    day,
    day_of_week
from calendar
