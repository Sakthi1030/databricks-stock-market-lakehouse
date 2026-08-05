import { useState } from "react";
import { Link } from "react-router-dom";
import { useLatestSummary, useMovers } from "../api/queries";
import { StatCard } from "../components/StatCard";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ErrorState } from "../components/ErrorState";
import { AutoRefreshBar } from "../components/AutoRefreshBar";

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString(undefined, {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export function Dashboard() {
  const [autoRefresh, setAutoRefresh] = useState(false);
  const summary = useLatestSummary({ refetchInterval: autoRefresh ? 60_000 : false });
  const gainers = useMovers("gainer");
  const losers = useMovers("loser");

  if (summary.isPending) return <LoadingSpinner label="Loading market summary..." />;
  if (summary.isError)
    return (
      <ErrorState
        message="Couldn't load the market summary. Is the API running?"
        onRetry={() => summary.refetch()}
      />
    );

  const data = summary.data;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Executive Summary</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">{formatDate(data.ingestion_date)}</p>
        </div>
        <AutoRefreshBar
          lastUpdated={summary.dataUpdatedAt}
          isFetching={summary.isFetching}
          onRefresh={() => summary.refetch()}
          autoRefresh={autoRefresh}
          onAutoRefreshChange={setAutoRefresh}
        />
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <StatCard label="Companies" value={String(data.num_companies)} color="blue" />
        <StatCard label="Gainers" value={String(data.num_gainers)} color="green" />
        <StatCard label="Losers" value={String(data.num_losers)} color="red" />
        <StatCard label="Avg % Change" value={`${data.avg_pct_change?.toFixed(2)}%`} color="amber" />
        <StatCard label="Best % Change" value={`${data.best_pct_change?.toFixed(2)}%`} color="purple" />
        <StatCard label="Worst % Change" value={`${data.worst_pct_change?.toFixed(2)}%`} color="teal" />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <MoversPanel title="Top Gainers" query={gainers} accent="text-brand-green" />
        <MoversPanel title="Top Losers" query={losers} accent="text-brand-red" />
      </div>
    </div>
  );
}

function MoversPanel({
  title,
  query,
  accent,
}: {
  title: string;
  query: ReturnType<typeof useMovers>;
  accent: string;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-semibold">{title}</h2>
        <Link to="/movers" className="text-xs text-brand-blue hover:underline">
          View all →
        </Link>
      </div>

      {query.isPending && <LoadingSpinner label="Loading..." />}
      {query.isError && <ErrorState message="Couldn't load movers." onRetry={() => query.refetch()} />}

      {query.data && (
        <ul className="divide-y divide-slate-100 dark:divide-slate-800">
          {query.data.map((mover) => (
            <li key={mover.symbol} className="flex items-center justify-between py-2 text-sm">
              <div>
                <Link to={`/companies/${mover.symbol}`} className="font-medium hover:underline">
                  {mover.symbol}
                </Link>
                <span className="ml-2 text-slate-500 dark:text-slate-400">{mover.name}</span>
              </div>
              <span className={`font-semibold ${accent}`}>
                {mover.pct_change !== null && mover.pct_change >= 0 ? "+" : ""}
                {mover.pct_change?.toFixed(2)}%
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
