import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Quote } from "../api/types";

interface TrendChartProps {
  data: Quote[];
  dataKey: "current_price" | "pct_change";
  color?: string;
}

export function TrendChart({ data, dataKey, color = "#2563eb" }: TrendChartProps) {
  // History comes back newest-first from the API; charts read left-to-right chronologically.
  const chronological = [...data].reverse();
  const label = dataKey === "current_price" ? "Price ($)" : "% Change";

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={chronological} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-800" />
        <XAxis
          dataKey="ingestion_date"
          tick={{ fontSize: 12 }}
          className="fill-slate-500 dark:fill-slate-400"
        />
        <YAxis
          tick={{ fontSize: 12 }}
          className="fill-slate-500 dark:fill-slate-400"
          domain={["auto", "auto"]}
        />
        <Tooltip
          contentStyle={{ borderRadius: 8, fontSize: 13 }}
          formatter={(value) => {
            const num = Number(value);
            const formatted = dataKey === "pct_change" ? `${num.toFixed(2)}%` : `$${num.toFixed(2)}`;
            return [formatted, label];
          }}
        />
        <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
