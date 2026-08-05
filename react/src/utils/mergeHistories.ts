interface HistoryPoint {
  ingestion_date: string;
  current_price: number | null;
}

interface HistoryQueryResult {
  data?: HistoryPoint[];
}

/** Pivots per-company quote-history arrays into one wide array keyed by date, suitable for a
 * multi-line Recharts chart (one row per date, one column per company) or a comparison table.
 * Dates where only some companies have data are filled with a missing key rather than
 * dropped, so the chart/table can render a gap instead of silently misaligning series.
 */
export function mergeHistoriesByDate(
  symbols: string[],
  histories: HistoryQueryResult[],
): Record<string, string | number | null>[] {
  const byDate = new Map<string, Record<string, string | number | null>>();

  symbols.forEach((symbol, i) => {
    const rows = histories[i]?.data ?? [];
    rows.forEach((row) => {
      const existing = byDate.get(row.ingestion_date) ?? { date: row.ingestion_date };
      existing[symbol] = row.current_price;
      byDate.set(row.ingestion_date, existing);
    });
  });

  return Array.from(byDate.values()).sort((a, b) => String(a.date).localeCompare(String(b.date)));
}
