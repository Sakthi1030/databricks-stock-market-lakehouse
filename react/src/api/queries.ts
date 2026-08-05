import { useQueries, useQuery } from "@tanstack/react-query";
import { apiClient } from "./client";
import type {
  Company,
  DailyMarketSummary,
  MoverType,
  Quote,
  SectorSummary,
  TopMover,
} from "./types";

// Centralized query keys — avoids typo'd cache-key mismatches between components that read
// the same data and any future code that needs to invalidate/refetch it.
export const queryKeys = {
  companies: ["companies"] as const,
  latestQuotes: ["quotes", "latest"] as const,
  quoteHistory: (symbol: string, days: number) => ["quotes", "history", symbol, days] as const,
  latestSummary: ["summary", "latest"] as const,
  movers: (moverType?: MoverType) => ["movers", moverType ?? "all"] as const,
  sectors: ["sectors"] as const,
};

export function useCompanies() {
  return useQuery({
    queryKey: queryKeys.companies,
    queryFn: async () => (await apiClient.get<Company[]>("/api/companies")).data,
  });
}

export function useLatestQuotes() {
  return useQuery({
    queryKey: queryKeys.latestQuotes,
    queryFn: async () => (await apiClient.get<Quote[]>("/api/quotes/latest")).data,
  });
}

export function useQuoteHistory(symbol: string, days = 30) {
  return useQuery({
    queryKey: queryKeys.quoteHistory(symbol, days),
    queryFn: async () =>
      (await apiClient.get<Quote[]>("/api/quotes/history", { params: { symbol, days } })).data,
    enabled: Boolean(symbol),
  });
}

// For a fixed, known symbol, useQuoteHistory (a plain useQuery) is the right tool. Here the
// *number* of symbols varies at runtime (however many the user has selected to compare) —
// hooks can't be called in a loop for a variable-length list, so useQueries is the
// purpose-built TanStack Query API for exactly this "N queries where N is dynamic" case.
export function useMultipleQuoteHistories(symbols: string[], days = 30) {
  return useQueries({
    queries: symbols.map((symbol) => ({
      queryKey: queryKeys.quoteHistory(symbol, days),
      queryFn: async () =>
        (await apiClient.get<Quote[]>("/api/quotes/history", { params: { symbol, days } })).data,
      enabled: Boolean(symbol),
    })),
  });
}

export function useLatestSummary(options?: { refetchInterval?: number | false }) {
  return useQuery({
    queryKey: queryKeys.latestSummary,
    queryFn: async () => (await apiClient.get<DailyMarketSummary>("/api/summary/latest")).data,
    refetchInterval: options?.refetchInterval ?? false,
  });
}

export function useMovers(moverType?: MoverType) {
  return useQuery({
    queryKey: queryKeys.movers(moverType),
    queryFn: async () =>
      (
        await apiClient.get<TopMover[]>("/api/movers", {
          params: moverType ? { mover_type: moverType } : undefined,
        })
      ).data,
  });
}

export function useSectors() {
  return useQuery({
    queryKey: queryKeys.sectors,
    queryFn: async () => (await apiClient.get<SectorSummary[]>("/api/sectors")).data,
  });
}
