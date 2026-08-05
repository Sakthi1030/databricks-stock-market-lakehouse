import { useEffect, useState } from "react";

interface AutoRefreshBarProps {
  lastUpdated: number | undefined; // from React Query's dataUpdatedAt (ms since epoch, 0 if never fetched)
  isFetching: boolean;
  onRefresh: () => void;
  autoRefresh: boolean;
  onAutoRefreshChange: (enabled: boolean) => void;
}

function formatRelativeTime(timestampMs: number, nowMs: number): string {
  const seconds = Math.max(0, Math.floor((nowMs - timestampMs) / 1000));
  if (seconds < 5) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
}

export function AutoRefreshBar({
  lastUpdated,
  isFetching,
  onRefresh,
  autoRefresh,
  onAutoRefreshChange,
}: AutoRefreshBarProps) {
  // Ticks once a second purely to re-render the relative-time label ("Xs ago") — the data
  // itself only changes when a real refetch completes.
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="flex flex-wrap items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
      <span>
        {isFetching ? "Refreshing…" : lastUpdated ? `Updated ${formatRelativeTime(lastUpdated, now)}` : ""}
      </span>
      <button
        onClick={onRefresh}
        disabled={isFetching}
        className="rounded-md border border-slate-300 px-2.5 py-1 text-xs font-medium hover:bg-slate-100 disabled:opacity-50 dark:border-slate-700 dark:hover:bg-slate-800"
      >
        Refresh now
      </button>
      <label className="flex items-center gap-1.5 text-xs">
        <input
          type="checkbox"
          checked={autoRefresh}
          onChange={(e) => onAutoRefreshChange(e.target.checked)}
          className="rounded"
        />
        Auto-refresh (60s)
      </label>
    </div>
  );
}
