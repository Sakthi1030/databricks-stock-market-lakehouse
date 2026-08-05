import type { Quote } from "../api/types";

export function HistoryTable({ data }: { data: Quote[] }) {
  return (
    <div className="max-h-[280px] overflow-y-auto">
      <table className="w-full text-left text-sm">
        <thead className="sticky top-0 bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-800 dark:text-slate-400">
          <tr>
            <th className="px-3 py-2 font-medium">Date</th>
            <th className="px-3 py-2 font-medium">Price</th>
            <th className="px-3 py-2 font-medium">% Change</th>
            <th className="px-3 py-2 font-medium">High</th>
            <th className="px-3 py-2 font-medium">Low</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
          {data.map((row) => (
            <tr key={row.ingestion_date} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
              <td className="px-3 py-2">{row.ingestion_date}</td>
              <td className="px-3 py-2">{row.current_price != null ? `$${row.current_price.toFixed(2)}` : "—"}</td>
              <td className="px-3 py-2">
                {row.pct_change != null ? (
                  <span className={row.pct_change >= 0 ? "text-brand-green" : "text-brand-red"}>
                    {row.pct_change >= 0 ? "+" : ""}
                    {row.pct_change.toFixed(2)}%
                  </span>
                ) : (
                  "—"
                )}
              </td>
              <td className="px-3 py-2">{row.day_high != null ? `$${row.day_high.toFixed(2)}` : "—"}</td>
              <td className="px-3 py-2">{row.day_low != null ? `$${row.day_low.toFixed(2)}` : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
