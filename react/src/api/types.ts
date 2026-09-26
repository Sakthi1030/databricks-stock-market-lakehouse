/** Every endpoint says which path served it: the Databricks Gold marts or the raw zone fallback. */
export type DataSource = "databricks" | "raw";

export interface Served<T> {
  source: DataSource;
  data: T;
}

export type NewsSource = "nse" | "rss" | "google_news" | "reddit";

export interface IndexQuote {
  price: number;
  change_pct: number;
  sparkline: number[];
}

export interface ScoreParts {
  news: number;
  reach: number;
  momentum: number;
  volume: number;
}

export interface Candidate {
  symbol: string;
  name: string;
  news_ids: string[];
  news_score: number;
  reach_rate: number | null;
  day_change_pct: number | null;
  volume_ratio: number | null;
  avg_traded_value_cr: number | null;
  price: number | null;
  prev_close: number | null;
  target_price: number | null;
  scores: ScoreParts;
  score: number;
  rank: number;
  is_pick: boolean;
  skip_reason: string;
  catalysts: string[];
  headline: string;
  sparkline: number[];
}

export interface TrackRecordSummary {
  days: number;
  picks: number;
  pick_hits: number;
  pick_hit_rate: number | null;
  other_hit_rate: number | null;
}

export interface TodayRun {
  market_date: string;
  run_at: string;
  target_pct: number;
  brief: string;
  indices: Record<string, IndexQuote>;
  stats: {
    headlines: number;
    matched_stocks: number;
    by_source: Record<NewsSource, number>;
    classified_by_gemini: number;
  };
  candidates: Candidate[];
  track_record: TrackRecordSummary;
}

export interface NewsItem {
  id: string;
  date: string;
  source: NewsSource;
  outlet: string;
  title: string;
  url: string;
  published: string;
  summary: string;
  symbols: string[];
  category: string;
  sentiment: number;
  impact: number;
  catalyst: string;
  reason: string;
  classified_by: string;
}

export interface TrackRecordDay {
  trade_date: string;
  picks: number;
  pick_hits: number;
  others: number;
  other_hits: number;
  pick_hit_rate: number | null;
  other_hit_rate: number | null;
  pick_avg_max_gain_pct: number | null;
  rolling_20d_pick_hit_rate: number | null;
}

export interface HitRate {
  trades: number;
  hits: number;
  hit_rate: number | null;
  avg_max_gain_pct: number | null;
  avg_close_return_pct: number | null;
}

export interface Analytics {
  by_catalyst: (HitRate & { catalyst: string; is_pick: boolean })[];
  by_score_band: (HitRate & { score_band: string })[];
  by_source: (HitRate & { source: NewsSource })[];
}

export interface PickPerformance {
  trade_date: string;
  symbol: string;
  name: string;
  rank: number | null;
  is_pick: boolean;
  score: number | null;
  score_band: string | null;
  skip_reason: string;
  catalysts: string[];
  headline: string;
  price: number | null;
  target_price: number | null;
  day_change_pct: number | null;
  reach_rate: number | null;
  graded: boolean;
  hit: boolean | null;
  next_trade_date: string | null;
  next_high: number | null;
  max_gain_pct: number | null;
  close_return_pct: number | null;
}

export interface Bar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface StockDetail {
  symbol: string;
  name: string;
  price: number | null;
  bars: Bar[];
  appearances: PickPerformance[];
  news: NewsItem[];
}
