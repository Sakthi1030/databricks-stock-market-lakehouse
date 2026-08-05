import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { WatchlistProvider, useWatchlist } from "./useWatchlist";

describe("useWatchlist", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("starts empty when nothing is stored", () => {
    const { result } = renderHook(() => useWatchlist(), { wrapper: WatchlistProvider });
    expect(result.current.symbols).toEqual([]);
  });

  it("loads previously stored symbols on mount", () => {
    window.localStorage.setItem("watchlist", JSON.stringify(["AAPL", "MSFT"]));
    const { result } = renderHook(() => useWatchlist(), { wrapper: WatchlistProvider });
    expect(result.current.symbols).toEqual(["AAPL", "MSFT"]);
  });

  it("toggle adds a symbol that isn't watched yet", () => {
    const { result } = renderHook(() => useWatchlist(), { wrapper: WatchlistProvider });

    act(() => result.current.toggle("AAPL"));

    expect(result.current.symbols).toEqual(["AAPL"]);
    expect(result.current.isWatched("AAPL")).toBe(true);
  });

  it("toggle removes a symbol that's already watched", () => {
    const { result } = renderHook(() => useWatchlist(), { wrapper: WatchlistProvider });

    act(() => result.current.toggle("AAPL"));
    act(() => result.current.toggle("AAPL"));

    expect(result.current.symbols).toEqual([]);
    expect(result.current.isWatched("AAPL")).toBe(false);
  });

  it("persists changes to localStorage", () => {
    const { result } = renderHook(() => useWatchlist(), { wrapper: WatchlistProvider });

    act(() => result.current.toggle("AAPL"));

    expect(JSON.parse(window.localStorage.getItem("watchlist")!)).toEqual(["AAPL"]);
  });

  it("does not crash when localStorage holds invalid JSON", () => {
    window.localStorage.setItem("watchlist", "{not valid json");
    const { result } = renderHook(() => useWatchlist(), { wrapper: WatchlistProvider });
    expect(result.current.symbols).toEqual([]);
  });

  it("throws when used outside a WatchlistProvider", () => {
    expect(() => renderHook(() => useWatchlist())).toThrow(
      "useWatchlist must be used within a WatchlistProvider",
    );
  });
});
