import { useMemo } from "react";
import { Link } from "react-router-dom";
import type { ColumnDef } from "@tanstack/react-table";
import { useCompanies, useLatestQuotes } from "../api/queries";
import { useWatchlist } from "../hooks/useWatchlist";
import { DataTable } from "../components/DataTable";
import { WatchlistStar } from "../components/WatchlistStar";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ErrorState } from "../components/ErrorState";

interface WatchlistRow {
  symbol: string;
  name: string | null;
  industry: string | null;
  current_price: number | null;
  pct_change: number | null;
}

const columns: ColumnDef<WatchlistRow, any>[] = [
  {
    id: "star",
    header: "",
    cell: ({ row }) => <WatchlistStar symbol={row.original.symbol} />,
  },
  {
    accessorKey: "symbol",
    header: "Symbol",
    cell: ({ row }) => (
      <Link to={`/companies/${row.original.symbol}`} className="font-semibold text-brand-blue hover:underline">
        {row.original.symbol}
      </Link>
    ),
  },
  { accessorKey: "name", header: "Company" },
  { accessorKey: "industry", header: "Industry" },
  {
    accessorKey: "current_price",
    header: "Price",
    cell: ({ getValue }) => {
      const value = getValue<number | null>();
      return value !== null ? `$${value.toFixed(2)}` : "—";
    },
  },
  {
    accessorKey: "pct_change",
    header: "% Change",
    cell: ({ getValue }) => {
      const value = getValue<number | null>();
      if (value === null) return "—";
      const positive = value >= 0;
      return (
        <span className={positive ? "text-brand-green" : "text-brand-red"}>
          {positive ? "+" : ""}
          {value.toFixed(2)}%
        </span>
      );
    },
  },
];

export function Watchlist() {
  const { symbols } = useWatchlist();
  const companies = useCompanies();
  const quotes = useLatestQuotes();

  const rows = useMemo<WatchlistRow[]>(() => {
    if (!companies.data) return [];
    const quoteBySymbol = new Map((quotes.data ?? []).map((q) => [q.symbol, q]));
    return companies.data
      .filter((c) => symbols.includes(c.symbol))
      .map((c) => ({
        symbol: c.symbol,
        name: c.name,
        industry: c.industry,
        current_price: quoteBySymbol.get(c.symbol)?.current_price ?? null,
        pct_change: quoteBySymbol.get(c.symbol)?.pct_change ?? null,
      }));
  }, [companies.data, quotes.data, symbols]);

  if (companies.isPending) return <LoadingSpinner label="Loading watchlist..." />;
  if (companies.isError)
    return <ErrorState message="Couldn't load companies." onRetry={() => companies.refetch()} />;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Watchlist</h1>

      {symbols.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 p-10 text-center text-slate-500 dark:border-slate-700 dark:text-slate-400">
          <p className="text-3xl">☆</p>
          <p className="mt-2 text-sm">
            No companies starred yet. Click the star icon next to any company in{" "}
            <Link to="/companies" className="text-brand-blue hover:underline">
              Companies
            </Link>{" "}
            to add it here.
          </p>
        </div>
      ) : (
        <DataTable data={rows} columns={columns} searchPlaceholder="Search your watchlist..." />
      )}
    </div>
  );
}
