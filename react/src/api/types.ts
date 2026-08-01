// Mirrors backend/schemas.py exactly — one field renamed there, both sides must move together.

export interface Company {
  sk_company: number;
  symbol: string;
  ticker: string | null;
  name: string | null;
  exchange: string | null;
  country: string | null;
  currency: string | null;
  industry: string | null;
  market_cap_musd: number | null;
  shareOutstanding: number | null;
  ipo: string | null;
  weburl: string | null;
}

export interface Quote {
  symbol: string;
  ingestion_date: string;
  current_price: number | null;
  price_change: number | null;
  pct_change: number | null;
  day_high: number | null;
  day_low: number | null;
  day_open: number | null;
  previous_close: number | null;
  daily_range: number | null;
}

export interface DailyMarketSummary {
  ingestion_date: string;
  num_companies: number;
  avg_pct_change: number | null;
  num_gainers: number;
  num_losers: number;
  avg_daily_range: number | null;
  best_pct_change: number | null;
  worst_pct_change: number | null;
}

export type MoverType = "gainer" | "loser";

export interface TopMover {
  ingestion_date: string;
  mover_type: MoverType;
  rank: number;
  symbol: string;
  name: string | null;
  industry: string | null;
  pct_change: number | null;
  current_price: number | null;
}

export interface SectorSummary {
  ingestion_date: string;
  industry: string;
  num_companies: number;
  avg_pct_change: number | null;
  total_market_cap_musd: number | null;
}
