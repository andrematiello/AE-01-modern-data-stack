with source as (

    select * from {{ source('raw', 'tickers') }}

),

renamed as (

    select
        ticker,
        name     as ticker_name,
        sector,
        industry
    from source

)

select * from renamed
