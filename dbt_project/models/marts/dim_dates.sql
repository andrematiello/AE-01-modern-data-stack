with trading_dates as (

    select distinct trade_date
    from {{ ref('stg_market__prices') }}

)

select
    {{ dbt_utils.generate_surrogate_key(['trade_date']) }} as date_key,
    trade_date,
    extract(year  from trade_date) as year,
    extract(month from trade_date) as month,
    extract(day   from trade_date) as day,
    extract(dow   from trade_date) as day_of_week
from trading_dates
