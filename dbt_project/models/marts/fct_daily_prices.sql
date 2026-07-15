with prices as (

    select * from {{ ref('stg_market__prices') }}

),

with_return as (

    select
        *,
        (close_price
            / nullif(lag(close_price) over (partition by ticker order by trade_date), 0)
        ) - 1 as daily_return
    from prices

)

select
    {{ dbt_utils.generate_surrogate_key(['p.ticker', 'p.trade_date']) }} as daily_price_key,
    d.date_key,
    t.ticker_key,
    p.ticker,
    p.trade_date,
    p.open_price,
    p.high_price,
    p.low_price,
    p.close_price,
    p.volume,
    p.daily_return
from with_return p
inner join {{ ref('dim_tickers') }} t on p.ticker = t.ticker
inner join {{ ref('dim_dates') }} d on p.trade_date = d.trade_date
