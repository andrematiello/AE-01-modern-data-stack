with tickers as (

    select * from {{ ref('stg_market__tickers') }}

)

select
    {{ dbt_utils.generate_surrogate_key(['ticker']) }} as ticker_key,
    ticker,
    ticker_name,
    coalesce(sector, 'Unknown')   as sector,
    coalesce(industry, 'Unknown') as industry
from tickers
