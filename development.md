# 🛤️ Development Track — Modern Data Stack End-to-End

Step-by-step guide. Estimated time: 3 weeks. This is the base project of the Analytics Engineering track —
the other three evolve from it. Built on **real market data** (yfinance), portable DuckDB → Snowflake.

---

## Phase 0 — Preparation (2-3 days)

- [ ] Review ELT vs. ETL and the official dbt project structure (staging/intermediate/marts)
- [ ] Pick the data source: yfinance basket of 10 tickers across sectors (prices + metadata)
- [ ] Create the env with `uv` and install `dlt[duckdb]`, `dbt-duckdb`, `yfinance`
- [ ] Create the repository (`ingestion/`, `dbt_project/`, `docs/`)

## Phase 1 — Ingestion with dlt (4-5 days)

- [ ] Write `ingestion/pipeline.py`: dlt resources for `prices` (merge on ticker+date) and `tickers` (replace)
- [ ] Run it, load into DuckDB (`raw` schema), confirm no duplication on a second run
- [ ] Inspect the raw tables created in the warehouse

**Checkpoint:** raw market data in the warehouse, ingestion repeatable without duplication.

## Phase 2 — Staging layer (3-4 days)

- [ ] Configure sources (`_sources.yml`) pointing at the raw tables
- [ ] One staging model per source table: rename, type, standardize (no joins)
- [ ] Naming convention `stg_<source>__<entity>`
- [ ] Basic tests: `unique` + `not_null` on keys
- [ ] `dbt build` green

## Phase 3 — Marts (5-6 days)

- [ ] Define the fact grain BEFORE writing SQL (one row per ticker per trading day) — write it in the `.yml`
- [ ] Build `fct_daily_prices`, `dim_tickers`, `dim_dates` (star schema)
- [ ] Add a `daily_return` measure in the fact
- [ ] `relationships` tests between fact and dimensions
- [ ] Validate mart numbers against direct queries on the source

**Checkpoint:** an analyst can build a dashboard from the marts alone, without touching raw data.

## Phase 4 — Snowflake portability + Documentation (2-3 days)

- [ ] Add the `prod` (Snowflake) output to `profiles.yml`; run `dbt build --target prod` on the free trial
- [ ] Document the DuckDB↔Snowflake switch (same models, one profile)
- [ ] Column/model descriptions in the `.yml` — **AI drafts, human reviews** (see README)
- [ ] `dbt docs generate` + capture the lineage graph for the README

## Phase 5 — Publish (1 day)

- [ ] Clean-room reproduction (ingestion → dbt build → docs)
- [ ] Fill the README with real numbers and screenshots
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
