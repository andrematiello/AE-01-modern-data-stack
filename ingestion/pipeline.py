"""dlt ingestion — Yahoo Finance (yfinance) → DuckDB.

Loads real daily OHLCV prices and ticker metadata into the `raw` schema of a local DuckDB warehouse.
Prices use a merge write disposition (idempotent on ticker + date); metadata is replaced each run.

Run from the project root:
    python ingestion/pipeline.py
"""
from __future__ import annotations

import os

import dlt
import yfinance as yf

# A small, sector-diverse basket of large caps (enough to model, cheap to pull).
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "JPM", "XOM", "JNJ", "PG"]

# DuckDB file location. Shared with dbt via the DUCKDB_PATH env var so both write/read the same file.
DUCKDB_PATH = os.environ.get("DUCKDB_PATH", "warehouse.duckdb")
DESTINATION = dlt.destinations.duckdb(DUCKDB_PATH)


@dlt.resource(name="prices", write_disposition="merge", primary_key=("ticker", "date"))
def prices(tickers: list[str] = TICKERS, period: str = "2y"):
    """Daily OHLCV per ticker. One record per ticker per trading day."""
    for ticker in tickers:
        history = yf.Ticker(ticker).history(period=period, interval="1d", auto_adjust=False)
        if history.empty:
            continue
        history = history.reset_index()
        for row in history.itertuples(index=False):
            trade_date = getattr(row, "Date", None)
            yield {
                "ticker": ticker,
                "date": trade_date.date().isoformat() if hasattr(trade_date, "date") else str(trade_date),
                "open": float(row.Open),
                "high": float(row.High),
                "low": float(row.Low),
                "close": float(row.Close),
                "volume": int(row.Volume),
            }


@dlt.resource(name="tickers", write_disposition="replace")
def tickers(ticker_list: list[str] = TICKERS):
    """Descriptive metadata per ticker (name, sector, industry)."""
    for ticker in ticker_list:
        info = yf.Ticker(ticker).info or {}
        yield {
            "ticker": ticker,
            "name": info.get("shortName") or info.get("longName") or ticker,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
        }


def main() -> None:
    pipeline = dlt.pipeline(
        pipeline_name="market",
        destination=DESTINATION,
        dataset_name="raw",
    )
    load_info = pipeline.run([prices(), tickers()])
    print(load_info)


if __name__ == "__main__":
    main()
