"""dlt ingestion — Yahoo Finance (yfinance) → DuckDB.

Loads real daily OHLCV prices and ticker metadata into the `raw` schema of a local DuckDB warehouse.
Prices use a merge write disposition (idempotent on ticker + date); metadata is replaced each run.
Calls are wrapped in a bounded backoff to tolerate Yahoo rate limiting (HTTP 429).

Run from the project root:
    python ingestion/pipeline.py
"""
from __future__ import annotations

import os
import time

import dlt
import yfinance as yf

# A small, sector-diverse basket of large caps (enough to model, cheap to pull).
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "JPM", "XOM", "JNJ", "PG"]
PERIOD = "2y"

# DuckDB file location, shared with dbt via DUCKDB_PATH so both read/write the same file.
DUCKDB_PATH = os.environ.get("DUCKDB_PATH", "warehouse.duckdb")
DESTINATION = dlt.destinations.duckdb(DUCKDB_PATH)


def _with_retry(fn, attempts: int = 3, base_delay: float = 1.5):
    """Call fn() with bounded linear backoff; tolerate transient Yahoo rate limiting (HTTP 429)."""
    for attempt in range(attempts):
        try:
            result = fn()
            if result is not None:
                return result
        except Exception:
            pass
        time.sleep(base_delay * (attempt + 1))
    return None


@dlt.resource(name="prices", write_disposition="merge", primary_key=("ticker", "date"))
def prices():
    """Daily OHLCV per ticker. One record per ticker per trading day."""
    for ticker in TICKERS:
        history = _with_retry(
            lambda t=ticker: yf.Ticker(t).history(period=PERIOD, interval="1d", auto_adjust=False),
            attempts=4,
        )
        if history is None or history.empty:
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
        time.sleep(1.0)


@dlt.resource(name="tickers", write_disposition="replace")
def tickers():
    """Descriptive metadata per ticker (name, sector, industry)."""
    for ticker in TICKERS:
        info = _with_retry(lambda t=ticker: yf.Ticker(t).info, attempts=2) or {}
        yield {
            "ticker": ticker,
            "name": info.get("shortName") or info.get("longName") or ticker,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
        }
        time.sleep(0.5)


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
