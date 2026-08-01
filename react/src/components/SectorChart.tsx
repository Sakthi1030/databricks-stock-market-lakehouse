import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { SectorSummary } from "../api/types";

export function SectorChart({ data }: { data: SectorSummary[] }) {
  const sorted = [...data].sort((a, b) => (b.avg_pct_change ?? 0) - (a.avg_pct_change ?? 0));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={sorted} margin={{ top: 8, right: 16, left: 0, bottom: 40 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-800" />
        <XAxis
          dataKey="industry"
          tick={{ fontSize: 11 }}
          className="fill-slate-500 dark:fill-slate-400"
          angle={-30}
          textAnchor="end"
          interval={0}
        />
        <YAxis tick={{ fontSize: 12 }} className="fill-slate-500 dark:fill-slate-400" />
        <Tooltip
          contentStyle={{ borderRadius: 8, fontSize: 13 }}
          formatter={(value) => [`${Number(value).toFixed(2)}%`, "Avg % Change"]}
        />
        <Bar dataKey="avg_pct_change" radius={[4, 4, 0, 0]}>
          {sorted.map((entry) => (
            <Cell
              key={entry.industry}
              fill={(entry.avg_pct_change ?? 0) >= 0 ? "#16a34a" : "#dc2626"}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
