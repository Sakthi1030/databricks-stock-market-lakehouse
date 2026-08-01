"""Pydantic response models — mirror the Gold table shapes, not the raw Delta schemas."""
from typing import Optional

from pydantic import BaseModel


class Company(BaseModel):
    sk_company: int
    symbol: str
    ticker: Optional[str] = None
    name: Optional[str] = None
    exchange: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    industry: Optional[str] = None
    market_cap_musd: Optional[float] = None
    shareOutstanding: Optional[float] = None
    ipo: Optional[str] = None
    weburl: Optional[str] = None


class Quote(BaseModel):
    symbol: str
    ingestion_date: str
    current_price: Optional[float] = None
    price_change: Optional[float] = None
    pct_change: Optional[float] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    day_open: Optional[float] = None
    previous_close: Optional[float] = None
    daily_range: Optional[float] = None


class DailyMarketSummary(BaseModel):
    ingestion_date: str
    num_companies: int
    avg_pct_change: Optional[float] = None
    num_gainers: int
    num_losers: int
    avg_daily_range: Optional[float] = None
    best_pct_change: Optional[float] = None
    worst_pct_change: Optional[float] = None


class TopMover(BaseModel):
    ingestion_date: str
    mover_type: str
    rank: int
    symbol: str
    name: Optional[str] = None
    industry: Optional[str] = None
    pct_change: Optional[float] = None
    current_price: Optional[float] = None


class SectorSummary(BaseModel):
    ingestion_date: str
    industry: str
    num_companies: int
    avg_pct_change: Optional[float] = None
    total_market_cap_musd: Optional[float] = None
