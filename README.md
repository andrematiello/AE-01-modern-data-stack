# 🧩 Modern Data Stack End-to-End — ELT with dlt, dbt & DuckDB

> A complete ELT pipeline on the modern Analytics Engineering stack: declarative ingestion with dlt,
> layered transformation with dbt, and a dimensional model ready for BI — built on **real stock-market
> data** and portable from DuckDB (dev) to **Snowflake** (prod) with a single profile switch.

**✅ Verified build:** `dbt build` → **23/23 tests passing** on real data — 10 tickers, ~2 years,
**5,010** daily rows. *(Lineage graph screenshot to be added.)*

---

## 📋 Table of Contents

- Context
- Business Problem
- Architecture
- Data
- Methodology
- Dimensional Model
- Design Decisions
- Tech Stack
- Repository Structure
- How to Reproduce
- AI & Responsible Use
- Next Steps
- Contact

---

## 🎯 Context

Modern data teams dropped hand-crafted ETL in favor of ELT: load first, transform inside the warehouse with
version-controlled SQL. This project implements that pattern end-to-end, from raw market data to a
BI-ready star schema — the foundation the other Analytics Engineering projects build on.

## ❓ Business Problem

How do we turn raw stock-market data (daily prices + ticker metadata) into trustworthy, versioned,
documented analytical models that a BI team can consume without rework — and prove the same models run on
both a zero-cost local warehouse and a production cloud warehouse?

## 🏗️ Architecture

Flow: **yfinance / Alpha Vantage API** → declarative ingestion with **dlt** (incremental/merge) → warehouse
(**DuckDB** local dev · **Snowflake** prod) → layered transformation with **dbt** (staging → intermediate →
marts) → BI consumption.

*(Add the architecture diagram and the dbt lineage graph here.)*

## 🗂️ Data

- **Source:** Yahoo Finance via `yfinance` (free, no API key) — daily OHLCV prices + ticker metadata
  (name, sector, industry) for a basket of 10 sector-diverse large caps.
- **Volume (current build):** 10 tickers × ~2 years ≈ **5,010 daily price rows**.
- **Grain of raw prices:** one row per ticker per trading day.
- **Entities:** `prices` (time series), `tickers` (descriptive metadata).
- **Known limitations:** adjusted vs. unadjusted close; corporate actions; occasional gaps for delisted
  tickers.

## 🔍 Methodology

**Kimball dimensional modeling** on an ELT backbone:

1. **Ingestion (dlt):** incremental load of prices (merge on `ticker + date`) and ticker metadata into the
   warehouse — no duplication on re-run.
2. **Staging (dbt):** one model per source table — rename, type, standardize. No joins here.
3. **Intermediate (dbt):** business logic and enrichments (e.g., daily return, calendar attributes).
4. **Marts (dbt):** star schema — fact and dimension tables ready for BI.
5. **Documentation & lineage:** `dbt docs` with model/column descriptions and the lineage graph.

## ⭐ Dimensional Model

Star schema:

- **Fact:** `fct_daily_prices` — grain = **one row per ticker per trading day** (open, high, low, close,
  volume, daily return).
- **Dimensions:** `dim_tickers` (name, sector, industry), `dim_dates` (calendar attributes).
- Grain and join keys documented in the model `.yml`.

## ✅ Results (verified build)

`dbt build` runs clean on real market data — **PASS=23, ERROR=0**:

| Model | Rows | Grain |
| --- | --- | --- |
| `fct_daily_prices` | 5,010 | one row per ticker per trading day |
| `dim_tickers` | 10 | one row per ticker |
| `dim_dates` | 501 | one row per trading day |

Tests: `not_null` + `unique` on every key and `relationships` from the fact to both dimensions —
**23/23 passing**.

## 🤔 Design Decisions

- **ELT over ETL:** transformation is versioned SQL inside the warehouse, auditable via Git.
- **dlt over hand-rolled scripts:** declarative ingestion with schema evolution and incremental load built in.
- **DuckDB (dev) + Snowflake (prod) on the same dbt project:** zero-cost local development, one profile
  switch to a production cloud warehouse — demonstrates **warehouse portability** (D-006).
- **staging / intermediate / marts:** the official dbt convention, legible to any Analytics Engineer.

## 🛠️ Tech Stack

| Category | Tool |
| --- | --- |
| Ingestion (EL) | dlt |
| Warehouse | DuckDB (dev) · Snowflake (prod) |
| Transformation (T) | dbt Core |
| Languages | SQL, Python, Jinja |
| Packages | dbt_utils |
| Versioning | Git / GitHub |

## 📁 Repository Structure

- `ingestion/` — dlt pipeline (yfinance → warehouse)
- `dbt_project/models/staging/` — staging models + sources
- `dbt_project/models/marts/` — facts and dimensions
- `dbt_project/` — `dbt_project.yml`, `profiles.yml` (dev/prod), `packages.yml`
- `docs/` — diagrams and lineage screenshots

## ⚙️ How to Reproduce

```bash
# 1. Create the environment (uv)
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt

# 2. Ingest real market data into DuckDB
python ingestion/pipeline.py

# 3. Build the models and tests
cd dbt_project
dbt deps
dbt build            # dev target = DuckDB

# 4. Generate docs + lineage
dbt docs generate && dbt docs serve
```

To run against Snowflake instead, set the `SNOWFLAKE_*` environment variables and run `dbt build --target prod`.

## 🧠 AI & Responsible Use

Subtle, validated use of AI: an LLM drafts the **first version of the column descriptions** in the dbt
`schema.yml` files from the data profile; every description is then **reviewed and corrected by hand**
before commit. AI accelerates documentation; the human owns correctness.

## 🚀 Next Steps

- Advanced tests + CI (natural evolution: project **AE-02**).
- Connect a BI tool to the marts for real consumption.
- Add a semantic layer over the marts (project **AE-03**).

## 📬 Contact

LinkedIn | Portfolio | Email
