# Stock Market Lakehouse & Analytics Platform

An end-to-end data engineering and analytics platform built on the **Medallion Architecture**, ingesting live stock market data daily from the Finnhub API, processing it through Bronze → Silver → Gold layers in Databricks (PySpark + Delta Lake), and serving it through Power BI and a React dashboard.

Built as a production-style portfolio project — not a tutorial. Demonstrates ETL design, incremental loading, data quality checks, REST API integration, dimensional modeling, DAX/time intelligence, and full-stack dashboard delivery.

## Architecture

```
Finnhub REST API
      │  (extract: auth, retry, logging)
      ▼
Bronze Layer (Delta)        raw, append-only, as-received
      │  (PySpark: clean, validate, dedupe, type-cast)
      ▼
Silver Layer (Delta)        cleaned, conformed, incremental merge/upsert
      │  (PySpark: aggregate, derive metrics, dimensional model)
      ▼
Gold Layer (Delta)          analytics-ready fact/dim tables
      │
      ├──► Power BI            (executive dashboard, DAX, drillthrough)
      └──► FastAPI ──► React   (interactive web dashboard)
```

## Tech Stack

| Layer | Tool |
|---|---|
| Compute / Processing | Databricks Community Edition, PySpark |
| Storage | Delta Lake |
| Orchestration | Databricks Jobs (or GitHub Actions fallback — see `docs/`) |
| Language | Python 3.x |
| Data Source | Finnhub REST API (stock quotes, candles, company profiles) |
| BI | Power BI |
| Frontend | React |
| Backend API | FastAPI |
| Version Control | GitHub |
| Testing | Pytest |

## Project Structure

```
├── databricks/         Databricks notebooks (bronze/silver/gold pipeline notebooks)
├── etl/
│   ├── extract/         API client: auth, pagination, retry, logging
│   ├── transform/        PySpark transformation logic per layer
│   ├── load/              Delta write/merge logic
│   └── utils/             Shared helpers (logging, config loader, schema defs)
├── bronze/               Bronze-layer PySpark scripts
├── silver/               Silver-layer PySpark scripts
├── gold/                 Gold-layer PySpark scripts (facts/dims/aggregations)
├── backend/              FastAPI app serving Gold data as REST endpoints
├── react/                React dashboard consuming the backend API
├── powerbi/              .pbix file + DAX measure documentation
├── config/               config.yaml — environment-agnostic pipeline settings
├── docs/                 Architecture diagrams, deployment guide, setup guide
└── tests/                Unit tests, data validation tests, API tests
```

## Status

- [x] Step 1 — Project foundation & environment setup
- [ ] Step 2 — Extract: Finnhub API client (auth, retry, logging)
- [ ] Step 3 — Bronze layer (raw ingestion to Delta)
- [ ] Step 4 — Silver layer (cleaning, validation, incremental merge)
- [ ] Step 5 — Gold layer (dimensional model, aggregations)
- [ ] Step 6 — Automation / scheduling
- [ ] Step 7 — Power BI dashboard
- [ ] Step 8 — FastAPI backend
- [ ] Step 9 — React frontend
- [ ] Step 10 — Testing
- [ ] Step 11 — Documentation & deployment guide

## Setup

See `docs/setup.md` (added in a later step). Quick start for now:

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # then fill in your FINNHUB_API_KEY
```
