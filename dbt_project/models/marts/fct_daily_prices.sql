with prices as (

    select * from {{ ref('int_daily_prices_enriched') }}

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
from prices p
inner join {{ ref('dim_tickers') }} t on p.ticker = t.ticker
inner join {{ ref('dim_dates') }} d on p.trade_date = d.trade_date
