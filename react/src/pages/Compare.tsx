import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useCompanies, useMultipleQuoteHistories } from "../api/queries";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ErrorState } from "../components/ErrorState";
import { mergeHistoriesByDate } from "../utils/mergeHistories";

const LINE_COLORS = ["#2563eb", "#16a34a", "#dc2626", "#f59e0b", "#7c3aed", "#0891b2"];
const MAX_COMPARE = 6;

export function Compare() {
  const companies = useCompanies();
  const [selected, setSelected] = useState<string[]>([]);
  const histories = useMultipleQuoteHistories(selected);

  const chartData = useMemo(() => mergeHistoriesByDate(selected, histories), [selected, histories]);

  const toggle = (symbol: string) => {
    setSelected((prev) => {
      if (prev.includes(symbol)) return prev.filter((s) => s !== symbol);
      if (prev.length >= MAX_COMPARE) return prev; // cap it so the chart stays readable
      return [...prev, symbol];
    });
  };

  if (companies.isPending) return <LoadingSpinner label="Loading companies..." />;
  if (companies.isError)
    return <ErrorState message="Couldn't load companies." onRetry={() => companies.refetch()} />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Compare Companies</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Select up to {MAX_COMPARE} companies to overlay their price trends.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {companies.data.map((c) => {
          const isSelected = selected.includes(c.symbol);
          return (
            <button
              key={c.symbol}
              onClick={() => toggle(c.symbol)}
              disabled={!isSelected && selected.length >= MAX_COMPARE}
              className={`rounded-full border px-3 py-1 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${
                isSelected
                  ? "border-brand-blue bg-brand-blue text-white"
                  : "border-slate-300 text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
              }`}
            >
              {c.symbol}
            </button>
          );
        })}
      </div>

      {selected.length === 0 && (
        <div className="rounded-xl border border-dashed border-slate-300 p-10 text-center text-slate-500 dark:border-slate-700 dark:text-slate-400">
          Pick a few companies above to see them compared.
        </div>
      )}

      {selected.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <ResponsiveContainer width="100%" height={360}>
            <LineChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-800" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} className="fill-slate-500 dark:fill-slate-400" />
              <YAxis tick={{ fontSize: 12 }} className="fill-slate-500 dark:fill-slate-400" domain={["auto", "auto"]} />
              <Tooltip
                contentStyle={{ borderRadius: 8, fontSize: 13 }}
                formatter={(value) => (value == null ? ["—", ""] : [`$${Number(value).toFixed(2)}`, ""])}
              />
              <Legend />
              {selected.map((symbol, i) => (
                <Line
                  key={symbol}
                  type="monotone"
                  dataKey={symbol}
                  stroke={LINE_COLORS[i % LINE_COLORS.length]}
                  strokeWidth={2}
                  dot={false}
                  connectNulls
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {selected.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-800/50 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3 font-medium">Date</th>
                {selected.map((symbol) => (
                  <th key={symbol} className="px-4 py-3 font-medium">
                    {symbol}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {chartData.map((row) => (
                <tr key={String(row.date)} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                  <td className="px-4 py-2.5">{row.date}</td>
                  {selected.map((symbol) => (
                    <td key={symbol} className="px-4 py-2.5">
                      {row[symbol] != null ? `$${Number(row[symbol]).toFixed(2)}` : "—"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
