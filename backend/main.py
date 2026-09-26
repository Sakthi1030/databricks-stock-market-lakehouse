"""FastAPI backend for the NSE News Radar site.

Today's picks come straight from the raw zone (the 2 PM run's output); history and analytics
come from the Databricks Gold marts, falling back to the same numbers computed from the raw zone
whenever the warehouse is asleep. Every response says which path served it.
"""
import os
import re
import time
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend import db, raw
from radar.prices import fetch_chart

app = FastAPI(title="NSE News Radar API", version="2.0.0")

default_origins = "http://localhost:5173,http://localhost:3000"
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", default_origins).split(","),
    allow_methods=["GET"],
    allow_headers=["*"],
)

SYMBOL = re.compile(r"^[A-Z0-9&\-]{1,20}$")
_charts: dict[str, tuple[float, dict]] = {}


def served(data, source: str) -> dict:
    return {"source": source, "data": data}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/today")
def today():
    run = raw.latest()
    if not run:
        raise HTTPException(status_code=404, detail="No radar run yet")
    return served({k: v for k, v in run.items() if k != "news"}, "raw")


@app.get("/api/news")
def news(symbol: Optional[str] = None, source: Optional[str] = None, days: int = Query(default=2, ge=1, le=30)):
    rows = raw.news()
    dates = sorted({n["date"] for n in rows})[-days:]
    rows = [n for n in rows if n["date"] in dates]
    if symbol:
        rows = [n for n in rows if symbol.upper() in (n.get("symbols") or [])]
    if source:
        rows = [n for n in rows if n["source"] == source]
    return served(sorted(rows, key=lambda n: n["published"], reverse=True)[:400], "raw")


@app.get("/api/track-record")
def track_record():
    rows = db.gold(f"SELECT * FROM {db.SCHEMA}.gold_track_record_daily ORDER BY trade_date")
    if rows is not None:
        return served(rows, "databricks")
    return served(raw.track_record_daily(raw.pick_performance()), "raw")


@app.get("/api/analytics")
def analytics():
    parts = {name: db.gold(f"SELECT * FROM {db.SCHEMA}.gold_hit_rate_{name}")
             for name in ("by_catalyst", "by_score_band", "by_source")}
    if all(v is not None for v in parts.values()):
        return served(parts, "databricks")
    return served(raw.analytics(raw.pick_performance(), raw.news()), "raw")


@app.get("/api/history")
def history(days: int = Query(default=60, ge=1, le=365)):
    rows = db.gold(f"SELECT * FROM {db.SCHEMA}.gold_pick_performance "
                   f"WHERE trade_date >= date_sub(current_date(), {days}) ORDER BY trade_date DESC, rank")
    if rows is not None:
        return served(rows, "databricks")
    perf = raw.pick_performance()
    dates = set(sorted({r["trade_date"] for r in perf})[-days:])
    rows = [r for r in perf if r["trade_date"] in dates]
    return served(sorted(rows, key=lambda r: (r["trade_date"], -(r["rank"] or 0)), reverse=True), "raw")


@app.get("/api/stock/{symbol}")
def stock(symbol: str, range: str = Query(default="6mo", pattern="^(1mo|3mo|6mo|1y)$")):
    symbol = symbol.upper()
    if not SYMBOL.match(symbol):
        raise HTTPException(status_code=400, detail="Invalid symbol")
    key = f"{symbol}:{range}"
    hit = _charts.get(key)
    if not hit or time.time() - hit[0] > 300:
        try:
            hit = _charts[key] = (time.time(), fetch_chart(symbol, range_=range))
        except Exception:
            raise HTTPException(status_code=404, detail=f"No price data for '{symbol}'")
    chart = hit[1]
    appearances = [r for r in raw.pick_performance() if r["symbol"] == symbol]
    return served({
        "symbol": symbol,
        "name": next((r["name"] for r in appearances), chart["meta"].get("longName") or symbol),
        "price": chart["meta"].get("regularMarketPrice"),
        "bars": chart["bars"],
        "appearances": sorted(appearances, key=lambda r: r["trade_date"], reverse=True),
        "news": sorted((n for n in raw.news() if symbol in (n.get("symbols") or [])),
                       key=lambda n: n["published"], reverse=True)[:40],
    }, "raw")
