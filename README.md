![Modern Data Stack ELT — from raw market data to BI-ready dimensional models with dlt, dbt, DuckDB and Snowflake](docs/cover.png)

# 🧩 Modern Data Stack End-to-End — ELT with dlt, dbt & DuckDB

> A complete ELT pipeline on the modern Analytics Engineering stack: declarative ingestion with dlt,
> layered transformation with dbt, and a dimensional model ready for BI — built on **real stock-market
> data** and portable from DuckDB (dev) to **Snowflake** (prod).

**✅ Verified build:** `dbt build` → **7 models + 22 tests, 0 errors** on real market data —
10 tickers, ~2 years, **5,010** daily rows.

**✅ Verified on both warehouses:** the same models run green on **DuckDB** (dev) *and* **Snowflake**
(prod) — 7 models, 22 tests, 0 errors on each, same 5,010 / 501 / 10 rows. Portability is measured,
not asserted: see [Warehouse portability, proven](#-warehouse-portability-proven).

---

## 🍳 In plain English (no tech background needed)

**The analogy:** this is a **commercial kitchen**. Raw, messy ingredients go in one end; a plated dish comes
out the other. This project is the whole kitchen — not the dish.

**The problem it solves.** Say the business wants to answer *"did Apple stock go up or down on Tuesday?"*
Raw market data arrives as a pile of loose numbers with unhelpful names, no structure, and it changes every
day. If every analyst fetches that data themselves, each one arrives at a different answer — and nobody
knows which is right. That's the classic failure: *three dashboards, three answers to the same question.*

**What it delivers.** Three trustworthy tables that anyone can plug into a BI tool and chart **without
writing a line of code**:

| Table | What's in it |
| --- | --- |
| `fct_daily_prices` | **5,010 rows** — one per stock per day (open, close, volume, and how much it moved) |
| `dim_tickers` | the **10 companies** (name, sector, industry) |
| `dim_dates` | the **501 days** the market was actually open |

That shape — one "facts" table in the middle, ringed by "description" tables — is called a **star schema**.
It's the industry standard because it makes charts fast and questions easy: *"average return **by sector**"*
becomes a click instead of a project.

**The four steps, and the tool behind each:**

| Step | What happens | Tool | Why that tool |
| --- | --- | --- | --- |
| 1. Fetch | Pulls daily prices for 10 stocks from Yahoo Finance | **dlt** | Knows how not to duplicate — run it twice and it's still 5,010 rows (verified) |
| 2. Store | Lands the raw data in a "warehouse" | **DuckDB** (dev) / **Snowflake** (prod) | DuckDB is free and runs on a laptop; Snowflake is what companies actually run |
| 3. Clean & organize | Renames, fixes types, computes returns, builds the star schema | **dbt** | Transformation as version-controlled SQL — every change is auditable in Git |
| 4. Prove it's right | Runs 22 automatic checks on every build | **dbt tests** | If something breaks it fails immediately, instead of quietly becoming a wrong number on a dashboard |

**The part that matters most, and that a non-technical reader wouldn't spot:** step 3 is split into **three
layers** (`staging → intermediate → marts`), like an assembly line where each station does exactly one job.
That isn't decoration — it's what lets someone else read the code and change it without breaking everything
downstream. The architecture diagram below shows those layers.

**Why it matters for a data team:** the same code runs on a laptop at zero cost and on a production cloud
warehouse. One codebase, two destinations.

---

## 📋 Table of Contents

- [In plain English](#-in-plain-english-no-tech-background-needed)
- [Context](#-context)
- [Business Problem](#-business-problem)
- [Architecture](#️-architecture)
- [Data](#️-data)
- [Methodology](#-methodology)
- [Dimensional Model](#-dimensional-model)
- [Results](#-results-verified-build)
- [Warehouse portability, proven](#-warehouse-portability-proven)
- [Design Decisions](#-design-decisions)
- [Tech Stack](#️-tech-stack)
- [Repository Structure](#-repository-structure)
- [How to Reproduce](#️-how-to-reproduce)
- [AI & Responsible Use](#-ai--responsible-use)
- [Next Steps](#-next-steps)
- [Contact](#-contact)

---

## 🎯 Context

Modern data teams dropped hand-crafted ETL in favor of ELT: load first, transform inside the warehouse with
version-controlled SQL. This project implements that pattern end-to-end, from raw market data to a
BI-ready star schema — the foundation the other Analytics Engineering projects build on.

## ❓ Business Problem

How do we turn raw stock-market data (daily prices + ticker metadata) into trustworthy, versioned,
documented analytical models that a BI team can consume without rework — and keep the same models running
on both a zero-cost local warehouse and a production cloud warehouse?

## 🏗️ Architecture

![Project architecture: Yahoo Finance ingested by dlt into DuckDB (dev) or Snowflake (prod), transformed by dbt through staging, intermediate and marts into a BI-ready star schema](docs/architecture.png)

**Warehouse portability is a property of the whole pipeline, not just dbt.** Both halves point at the same
target: the dlt destination is selected by `DESTINATION_TYPE`, and dbt switches with `--target`. Swapping
only the dbt profile would leave it querying a warehouse where the raw tables were never loaded.

## 🗂️ Data

- **Source:** Yahoo Finance via `yfinance` (free, no API key) — daily OHLCV prices + ticker metadata
  (name, sector, industry) for a basket of 10 sector-diverse large caps.
- **Volume (current build):** 10 tickers × ~2 years = **5,010 daily price rows**, covering
  **2024-07-15 → 2026-07-14** (501 trading days).
- **Grain of raw prices:** one row per ticker per trading day.
- **Entities:** `prices` (time series), `tickers` (descriptive metadata).
- **The window rolls:** the pipeline pulls `period="2y"` relative to the run date, so a reproduction run
  later will report a later window and a slightly different row count. The figures above are the snapshot
  of the documented build, not a constant.
- **Known limitations:** prices are unadjusted (`auto_adjust=False`), so splits and dividends are not
  back-propagated; `daily_return` is therefore a raw close-to-close change, not a total return.

## 🔍 Methodology

**Kimball dimensional modeling** on an ELT backbone:

1. **Ingestion (dlt):** incremental load of prices (merge on `ticker + date`) and ticker metadata into the
   warehouse — no duplication on re-run.
2. **Staging (dbt):** one model per source table — rename, type, standardize. No joins here.
3. **Intermediate (dbt):** business logic and enrichments — `daily_return`, calendar attributes.
4. **Marts (dbt):** star schema — fact and dimension tables ready for BI.
5. **Documentation & lineage:** `dbt docs` with model/column descriptions and the lineage graph above.

## ⭐ Dimensional Model

Star schema:

- **Fact:** `fct_daily_prices` — grain = **one row per ticker per trading day** (open, high, low, close,
  volume, daily return).
- **Dimensions:** `dim_tickers` (name, sector, industry), `dim_dates` (calendar attributes).
- Grain and join keys documented in the model `.yml`.

The grain was written down before the SQL, and the fact carries a surrogate key built from
`ticker + trade_date` — a `unique` test on that key is what proves the grain holds.

## ✅ Results (verified build)

`dbt build` runs clean on real market data — **7 models, 22 tests, 0 errors**:

| Model | Layer | Rows | Grain |
| --- | --- | --- | --- |
| `fct_daily_prices` | mart | 5,010 | one row per ticker per trading day |
| `dim_tickers` | mart | 10 | one row per ticker |
| `dim_dates` | mart | 501 | one row per trading day |

Models by layer: **2 staging** (views) · **2 intermediate** (views) · **3 marts** (tables).

Tests: `not_null` + `unique` on every key and `relationships` from the fact to both dimensions —
**22 passing, 0 failing**.

> Counts come from `target/run_results.json` (`{'model': 7, 'test': 22}`), not from dbt's console summary —
> the `Done. PASS=29` line sums models *and* tests, and reading it as a test count is an easy way to publish
> a number that isn't true.

## ❄️ Warehouse portability, proven

The same project was run end-to-end against **both** warehouses — ingestion and transformation, not just a
profile switch:

| | DuckDB (dev) | Snowflake (prod) |
| --- | --- | --- |
| Ingestion | `python ingestion/pipeline.py` | `DESTINATION_TYPE=snowflake python ingestion/pipeline.py` |
| Transformation | `dbt build` | `dbt build --target prod` |
| Result | 7 models · 22 tests · **0 errors** | 7 models · 22 tests · **0 errors** |
| `fct_daily_prices` | 5,010 | 5,010 |
| `dim_dates` / `dim_tickers` | 501 / 10 | 501 / 10 |

**The interesting part is where the two didn't match.** Comparing the marts row by row over the window
present in both loads (5,000 rows):

- `close_price`: **identical on all 5,000 rows** — the transformation is deterministic across engines.
- `volume`: different on exactly **10 rows**, all on the *same* date — the last trading day of the earlier
  load, one row per ticker, each revised slightly upward.

That is not a pipeline bug: the two loads ran ~22 hours apart, and Yahoo consolidates a session's volume
after the close. The live source moved; the code didn't. It also demonstrates the `period="2y"` rolling
window in practice — the two loads cover `2024-07-15 → 2026-07-14` and `2024-07-16 → 2026-07-15`, the same
5,010 rows over a window shifted by one day. Comparing engines on live data means pinning the window first,
or you end up debugging the stock market instead of your SQL.

## 🤔 Design Decisions

- **ELT over ETL:** transformation is versioned SQL inside the warehouse, auditable via Git.
- **dlt over hand-rolled scripts:** declarative ingestion with schema evolution and incremental load built in.
- **DuckDB (dev) + Snowflake (prod) on the same dbt project:** zero-cost local development, one target
  switch to a production cloud warehouse — demonstrates **warehouse portability**.
- **staging / intermediate / marts:** the official dbt convention, legible to any Analytics Engineer.
  Business logic lives in `intermediate/`, so marts stay thin — keys and joins only.
- **`dim_dates` built from observed trading days, not a full date spine:** the calendar contains only days
  the market was actually open, so a missing date is a real signal rather than an expected gap.

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
- `dbt_project/models/intermediate/` — business logic and enrichments
- `dbt_project/models/marts/` — facts and dimensions
- `dbt_project/` — `dbt_project.yml`, `profiles.yml` (dev/prod), `packages.yml`
- `docs/` — lineage graph

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
dbt build --profiles-dir .        # dev target = DuckDB

# 4. Generate docs + lineage
dbt docs generate --profiles-dir . && dbt docs serve --profiles-dir .
```

### Running against Snowflake

Point **both** the ingestion and dbt at the cloud warehouse:

```bash
export SNOWFLAKE_ACCOUNT=... SNOWFLAKE_USER=... SNOWFLAKE_PASSWORD=...
export SNOWFLAKE_DATABASE=ANALYTICS SNOWFLAKE_WAREHOUSE=COMPUTE_WH SNOWFLAKE_ROLE=TRANSFORMER

DESTINATION_TYPE=snowflake python ingestion/pipeline.py   # load raw into Snowflake
cd dbt_project && dbt build --target prod --profiles-dir . # same models, cloud warehouse
```

Credentials are read from environment variables only — nothing is committed.

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
