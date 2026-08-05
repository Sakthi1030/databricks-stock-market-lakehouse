import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useCompanies, useQuoteHistory } from "../api/queries";
import { TrendChart } from "../components/TrendChart";
import { HistoryTable } from "../components/HistoryTable";
import { WatchlistStar } from "../components/WatchlistStar";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ErrorState } from "../components/ErrorState";
import { StatCard } from "../components/StatCard";

type ViewMode = "chart" | "table";

export function CompanyDetail() {
  const { symbol = "" } = useParams<{ symbol: string }>();
  const companies = useCompanies();
  const history = useQuoteHistory(symbol, 30);
  const [view, setView] = useState<ViewMode>("chart");

  const company = companies.data?.find((c) => c.symbol === symbol);
  const latest = history.data?.[0];

  return (
    <div className="space-y-6">
      <Link to="/companies" className="text-sm text-brand-blue hover:underline">
        ← Back to Companies
      </Link>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold">
            {company?.name ?? symbol} <span className="text-lg font-normal text-slate-400">({symbol})</span>
            <WatchlistStar symbol={symbol} />
          </h1>
          {company && (
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {company.industry} · {company.exchange} ·{" "}
              <a href={company.weburl ?? "#"} target="_blank" rel="noreferrer" className="hover:underline">
                {company.weburl}
              </a>
            </p>
          )}
        </div>
      </div>

      {history.isPending && <LoadingSpinner label="Loading price history..." />}
      {history.isError && (
        <ErrorState
          message={`Couldn't load history for ${symbol}.`}
          onRetry={() => history.refetch()}
        />
      )}

      {latest && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard label="Current Price" value={`$${latest.current_price?.toFixed(2)}`} color="blue" />
          <StatCard
            label="% Change"
            value={`${latest.pct_change?.toFixed(2)}%`}
            color={(latest.pct_change ?? 0) >= 0 ? "green" : "red"}
          />
          <StatCard label="Day High" value={`$${latest.day_high?.toFixed(2)}`} color="purple" />
          <StatCard label="Day Low" value={`$${latest.day_low?.toFixed(2)}`} color="teal" />
        </div>
      )}

      {history.data && history.data.length > 0 && (
        <>
          <div className="flex justify-end gap-1 rounded-lg border border-slate-200 p-1 dark:border-slate-800 w-fit ml-auto">
            {(["chart", "table"] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setView(mode)}
                className={`rounded-md px-3 py-1 text-sm font-medium capitalize transition-colors ${
                  view === mode
                    ? "bg-brand-blue text-white"
                    : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                }`}
              >
                {mode}
              </button>
            ))}
          </div>

          {view === "chart" ? (
            <div className="grid gap-6 lg:grid-cols-2">
              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                <h2 className="mb-2 font-semibold">Price Trend (30 days)</h2>
                <TrendChart data={history.data} dataKey="current_price" color="#2563eb" />
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                <h2 className="mb-2 font-semibold">% Change Trend (30 days)</h2>
                <TrendChart data={history.data} dataKey="pct_change" color="#7c3aed" />
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <h2 className="mb-2 font-semibold">Price History (30 days)</h2>
              <HistoryTable data={history.data} />
            </div>
          )}
        </>
      )}
    </div>
  );
}
