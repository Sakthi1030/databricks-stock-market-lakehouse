import { useQuery } from "@tanstack/react-query";
import { apiClient } from "./client";
import type {
  Analytics,
  NewsItem,
  NewsSource,
  PickPerformance,
  Served,
  StockDetail,
  TodayRun,
  TrackRecordDay,
} from "./types";

const get = async <T,>(url: string, params?: object) => (await apiClient.get<Served<T>>(url, { params })).data;

export const keys = {
  today: ["today"] as const,
  news: (days: number, source?: NewsSource) => ["news", days, source ?? "all"] as const,
  trackRecord: ["track-record"] as const,
  analytics: ["analytics"] as const,
  history: (days: number) => ["history", days] as const,
  stock: (symbol: string, range: string) => ["stock", symbol, range] as const,
};

export const useToday = () => useQuery({ queryKey: keys.today, queryFn: () => get<TodayRun>("/api/today") });

export const useNews = (days = 2, source?: NewsSource) =>
  useQuery({ queryKey: keys.news(days, source), queryFn: () => get<NewsItem[]>("/api/news", { days, source }) });

// Analytics may be served from the raw fallback while the warehouse wakes; refetch soon after
// so the page upgrades to the Gold marts on its own.
const upgradeToGold = (query: { state: { data?: Served<unknown> } }) =>
  query.state.data?.source === "raw" ? 45_000 : false;

export const useTrackRecord = () =>
  useQuery({
    queryKey: keys.trackRecord,
    queryFn: () => get<TrackRecordDay[]>("/api/track-record"),
    refetchInterval: upgradeToGold,
  });

export const useAnalytics = () =>
  useQuery({ queryKey: keys.analytics, queryFn: () => get<Analytics>("/api/analytics"), refetchInterval: upgradeToGold });

export const useHistory = (days = 60) =>
  useQuery({
    queryKey: keys.history(days),
    queryFn: () => get<PickPerformance[]>("/api/history", { days }),
    refetchInterval: upgradeToGold,
  });

export const useStock = (symbol: string, range = "6mo") =>
  useQuery({
    queryKey: keys.stock(symbol, range),
    queryFn: () => get<StockDetail>(`/api/stock/${encodeURIComponent(symbol)}`, { range }),
    enabled: !!symbol,
  });
