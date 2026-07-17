"""dlt ingestion — Yahoo Finance (yfinance) → DuckDB (dev) or Snowflake (prod).

Loads real daily OHLCV prices and ticker metadata into the `raw` schema of the target warehouse.
Prices use a merge write disposition (idempotent on ticker + date); metadata is replaced each run.
Calls are wrapped in a bounded backoff to tolerate Yahoo rate limiting (HTTP 429).

The destination mirrors the dbt target: warehouse portability means pointing *both* the ingestion
and the transformation at the same warehouse — dbt alone cannot read sources that were never loaded.

Run from the project root:
    python ingestion/pipeline.py                          # dev  → DuckDB
    DESTINATION_TYPE=snowflake python ingestion/pipeline.py   # prod → Snowflake

Optional env vars: TICKERS (comma-separated), PERIOD, DLT_PIPELINE_NAME — defaults reproduce this
project's standard run, so sibling projects can reuse the pipeline without touching its dlt state.
"""
from __future__ import annotations

import os
import time

import dlt
import yfinance as yf

# A small, sector-diverse basket of large caps (enough to model, cheap to pull).
# Overridable via TICKERS (comma-separated) / PERIOD so other projects can reuse this pipeline.
TICKERS = [
    t.strip()
    for t in os.environ.get("TICKERS", "AAPL,MSFT,GOOGL,AMZN,NVDA,META,JPM,XOM,JNJ,PG").split(",")
    if t.strip()
]
PERIOD = os.environ.get("PERIOD", "2y")

# DuckDB file location, shared with dbt via DUCKDB_PATH so both read/write the same file.
DUCKDB_PATH = os.environ.get("DUCKDB_PATH", "warehouse.duckdb")
DESTINATION_TYPE = os.environ.get("DESTINATION_TYPE", "duckdb").lower()

# Schema that receives the raw load. dbt reads the same value in models/staging/_sources.yml,
# so both halves stay pointed at one place when the warehouse is shared with other projects.
RAW_SCHEMA = os.environ.get("RAW_SCHEMA", "raw")


def _build_destination():
    """Select the dlt destination to match the dbt target (dev=DuckDB, prod=Snowflake).

    Snowflake credentials come from SNOWFLAKE_* env vars — the same ones profiles.yml reads,
    so a single set of exported variables drives both halves of the pipeline. Never hardcode them.
    """
    if DESTINATION_TYPE == "duckdb":
        return dlt.destinations.duckdb(DUCKDB_PATH)

    if DESTINATION_TYPE == "snowflake":
        required = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD"]
        missing = [v for v in required if not os.environ.get(v)]
        if missing:
            raise SystemExit(f"DESTINATION_TYPE=snowflake requires: {', '.join(missing)}")
        return dlt.destinations.snowflake(
            credentials={
                "database": os.environ.get("SNOWFLAKE_DATABASE", "ANALYTICS"),
                "username": os.environ["SNOWFLAKE_USER"],
                "password": os.environ["SNOWFLAKE_PASSWORD"],
                "host": os.environ["SNOWFLAKE_ACCOUNT"],
                "warehouse": os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
                "role": os.environ.get("SNOWFLAKE_ROLE", "TRANSFORMER"),
            }
        )

    raise SystemExit(f"Unknown DESTINATION_TYPE '{DESTINATION_TYPE}' (expected: duckdb | snowflake)")


DESTINATION = _build_destination()


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
        # Overridable so a sibling project can run this pipeline against its own warehouse
        # without touching this project's local dlt state.
        pipeline_name=os.environ.get("DLT_PIPELINE_NAME", "market"),
        destination=DESTINATION,
        dataset_name=RAW_SCHEMA,
    )
    print(f"Loading into destination: {DESTINATION_TYPE} (raw schema: {RAW_SCHEMA})")
    load_info = pipeline.run([prices(), tickers()])
    print(load_info)


if __name__ == "__main__":
    main()
