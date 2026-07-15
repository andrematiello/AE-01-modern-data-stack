with prices as (

    select * from {{ ref('stg_market__prices') }}

),

enriched as (

    select
        ticker,
        trade_date,
        open_price,
        high_price,
        low_price,
        close_price,
        volume,
        (close_price
            / nullif(lag(close_price) over (partition by ticker order by trade_date), 0)
        ) - 1 as daily_return
    from prices

)

select * from enriched
