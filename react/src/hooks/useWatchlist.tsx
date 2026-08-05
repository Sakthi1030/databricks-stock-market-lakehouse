import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

const STORAGE_KEY = "watchlist";

interface WatchlistContextValue {
  symbols: string[];
  isWatched: (symbol: string) => boolean;
  toggle: (symbol: string) => void;
}

const WatchlistContext = createContext<WatchlistContextValue | undefined>(undefined);

function loadInitial(): string[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    // Corrupted or hand-edited localStorage shouldn't crash the app — just start empty.
    return [];
  }
}

export function WatchlistProvider({ children }: { children: ReactNode }) {
  const [symbols, setSymbols] = useState<string[]>(loadInitial);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(symbols));
  }, [symbols]);

  const isWatched = (symbol: string) => symbols.includes(symbol);

  const toggle = (symbol: string) => {
    setSymbols((prev) => (prev.includes(symbol) ? prev.filter((s) => s !== symbol) : [...prev, symbol]));
  };

  return (
    <WatchlistContext.Provider value={{ symbols, isWatched, toggle }}>{children}</WatchlistContext.Provider>
  );
}

export function useWatchlist() {
  const context = useContext(WatchlistContext);
  if (!context) throw new Error("useWatchlist must be used within a WatchlistProvider");
  return context;
}
