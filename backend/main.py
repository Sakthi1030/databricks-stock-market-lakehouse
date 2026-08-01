"""FastAPI backend serving the Gold layer to the React frontend.

Reads directly from the same Databricks SQL Warehouse Power BI connects to — Gold is the
single source of truth for both, so the two never drift out of sync with each other.
"""
import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.db import run_query
from backend.schemas import Company, DailyMarketSummary, Quote, SectorSummary, TopMover

load_dotenv()

app = FastAPI(title="Stock Market Lakehouse API", version="1.0.0")

# ALLOWED_ORIGINS is a comma-separated list set per-environment (e.g. the deployed Vercel URL
# in production) — defaults to local dev ports so nothing extra is needed to run this locally.
default_origins = "http://localhost:5173,http://localhost:3000"
allowed_origins = os.environ.get("ALLOWED_ORIGINS", default_origins).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/companies", response_model=list[Company])
def get_companies():
    return run_query("SELECT * FROM workspace.default.dim_company ORDER BY name")


@app.get("/api/quotes/latest", response_model=list[Quote])
def get_latest_quotes():
    query = """
        SELECT symbol, ingestion_date, current_price, price_change, pct_change,
               day_high, day_low, day_open, previous_close, daily_range
        FROM workspace.default.fact_daily_quotes
        WHERE ingestion_date = (SELECT MAX(ingestion_date) FROM workspace.default.fact_daily_quotes)
        ORDER BY pct_change DESC
    """
    return run_query(query)


@app.get("/api/quotes/history", response_model=list[Quote])
def get_quote_history(symbol: str, days: int = 30):
    # `symbol` is user-supplied — always parameterized, never string-interpolated into SQL.
    # `days` is safe to interpolate directly: FastAPI's `int` type hint already rejects any
    # non-integer value before this function body ever runs.
    query = f"""
        SELECT symbol, ingestion_date, current_price, price_change, pct_change,
               day_high, day_low, day_open, previous_close, daily_range
        FROM workspace.default.fact_daily_quotes
        WHERE symbol = :symbol
        ORDER BY ingestion_date DESC
        LIMIT {days}
    """
    rows = run_query(query, {"symbol": symbol})
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data found for symbol '{symbol}'")
    return rows


@app.get("/api/summary/latest", response_model=DailyMarketSummary)
def get_latest_summary():
    query = """
        SELECT ingestion_date, num_companies, avg_pct_change, num_gainers, num_losers,
               avg_daily_range, best_pct_change, worst_pct_change
        FROM workspace.default.daily_market_summary
        ORDER BY ingestion_date DESC
        LIMIT 1
    """
    rows = run_query(query)
    if not rows:
        raise HTTPException(status_code=404, detail="No summary data available")
    return rows[0]


@app.get("/api/movers", response_model=list[TopMover])
def get_top_movers(mover_type: Optional[str] = Query(default=None, pattern="^(gainer|loser)$")):
    query = """
        SELECT ingestion_date, mover_type, rank, symbol, name, industry, pct_change, current_price
        FROM workspace.default.top_movers
        WHERE ingestion_date = (SELECT MAX(ingestion_date) FROM workspace.default.top_movers)
    """
    parameters = None
    if mover_type:
        query += " AND mover_type = :mover_type"
        parameters = {"mover_type": mover_type}
    query += " ORDER BY mover_type, rank"
    return run_query(query, parameters)


@app.get("/api/sectors", response_model=list[SectorSummary])
def get_sectors():
    query = """
        SELECT ingestion_date, industry, num_companies, avg_pct_change, total_market_cap_musd
        FROM workspace.default.sector_summary
        WHERE ingestion_date = (SELECT MAX(ingestion_date) FROM workspace.default.sector_summary)
        ORDER BY avg_pct_change DESC
    """
    return run_query(query)
