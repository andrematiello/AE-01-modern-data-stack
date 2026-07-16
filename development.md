# 🛤️ Development Track — Modern Data Stack End-to-End

Step-by-step guide. Estimated time: 3 weeks. This is the base project of the Analytics Engineering track —
the other three evolve from it. Built on **real market data** (yfinance), portable DuckDB → Snowflake.

**Status:** Phases 0–3 complete and verified. Phase 4 partly done (docs + lineage captured; the Snowflake
prod run is the open item). Phase 5 verified locally, publication pending.

---

## Phase 0 — Preparation (2-3 days)

- [x] Review ELT vs. ETL and the official dbt project structure (staging/intermediate/marts)
- [x] Pick the data source: yfinance basket of 10 tickers across sectors (prices + metadata)
- [x] Create the env with `uv` and install `dlt[duckdb]`, `dbt-duckdb`, `yfinance`
- [x] Create the repository (`ingestion/`, `dbt_project/`, `docs/`)

## Phase 1 — Ingestion with dlt (4-5 days)

- [x] Write `ingestion/pipeline.py`: dlt resources for `prices` (merge on ticker+date) and `tickers` (replace)
- [x] Run it, load into DuckDB (`raw` schema), confirm no duplication on a second run
- [x] Inspect the raw tables created in the warehouse

**Checkpoint:** ✅ raw market data in the warehouse, ingestion repeatable without duplication.
Verified: two consecutive runs both leave `raw.prices` at 5,010 rows with 0 duplicate `(ticker, date)` keys.

## Phase 2 — Staging layer (3-4 days)

- [x] Configure sources (`_sources.yml`) pointing at the raw tables
- [x] One staging model per source table: rename, type, standardize (no joins)
- [x] Naming convention `stg_<source>__<entity>`
- [x] Basic tests: `unique` + `not_null` on keys
- [x] `dbt build` green

## Phase 3 — Marts (5-6 days)

- [x] Define the fact grain BEFORE writing SQL (one row per ticker per trading day) — write it in the `.yml`
- [x] Build `fct_daily_prices`, `dim_tickers`, `dim_dates` (star schema)
- [x] Add a `daily_return` measure — computed in `int_daily_prices_enriched`, surfaced in the fact
- [x] `relationships` tests between fact and dimensions
- [x] Validate mart numbers against direct queries on the source (`raw.prices` 5,010 = `fct_daily_prices` 5,010)

**Checkpoint:** ✅ an analyst can build a dashboard from the marts alone, without touching raw data.

## Phase 4 — Snowflake portability + Documentation (2-3 days)

- [x] Add the `prod` (Snowflake) output to `profiles.yml`
- [x] Make the dlt destination follow the dbt target (`DESTINATION_TYPE=duckdb|snowflake`) — dbt alone
      cannot read sources that were never loaded into the cloud warehouse
- [x] Document the DuckDB↔Snowflake switch (ingestion destination + dbt target, not a profile alone)
- [x] Column/model descriptions in the `.yml` — **AI drafts, human reviews** (see README)
- [x] `dbt docs generate` runs and serves the model dictionary and lineage graph locally
- [x] Diagrams for the README: `docs/cover.png` and `docs/architecture.png`
- [ ] Run `dbt build --target prod` against the free trial and capture the evidence

## Phase 5 — Publish (1 day)

- [x] Clean-room reproduction (ingestion → dbt build → docs) — verified from an empty warehouse:
      5,010 / 501 / 10 rows, `Done. PASS=29 ERROR=0`
- [x] Fill the README with real numbers and the lineage graph
- [ ] Push (private for now) and prepare a LinkedIn post

---

## 📚 Concepts to master

- ELT and the Analytics Engineer role in the data team
- dbt structure: sources, models, `ref()`, materializations (view/table/incremental)
- Dimensional modeling: grain, facts, dimensions, star schema (Kimball basics)
- dlt: incremental/merge load, schema evolution
- Warehouse portability: one dbt project, DuckDB and Snowflake targets

## ⚠️ Common pitfalls

- Skipping the grain definition and finding out later the fact double-counts
- Putting joins in staging (breaks the convention any AE expects)
- `SELECT *` in models — always list columns explicitly
- Trusting AI-written column docs without reviewing them against the data
- Reading `Done. PASS=29` as a test count — that line sums models *and* tests. The real breakdown lives in
  `target/run_results.json` (`{'model': 7, 'test': 22}`). Publishing the console number is how a README
  ends up claiming more tests than exist.
- Assuming warehouse portability is a dbt-only concern — the ingestion has to point at the same target
