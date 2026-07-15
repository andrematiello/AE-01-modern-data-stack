with trading_dates as (

    select distinct trade_date
    from {{ ref('stg_market__prices') }}

),

with_attributes as (

    select
        trade_date,
        extract(year  from trade_date) as year,
        extract(month from trade_date) as month,
        extract(day   from trade_date) as day,
        extract(dow   from trade_date) as day_of_week
    from trading_dates

)

select * from with_attributes
