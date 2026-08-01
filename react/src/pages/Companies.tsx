import { useMemo } from "react";
import { Link } from "react-router-dom";
import type { ColumnDef } from "@tanstack/react-table";
import { useCompanies, useLatestQuotes } from "../api/queries";
import { DataTable } from "../components/DataTable";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ErrorState } from "../components/ErrorState";

interface CompanyRow {
  symbol: string;
  name: string | null;
  industry: string | null;
  market_cap_musd: number | null;
  current_price: number | null;
  pct_change: number | null;
}

const columns: ColumnDef<CompanyRow, any>[] = [
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
  {
    accessorKey: "market_cap_musd",
    header: "Market Cap ($M)",
    cell: ({ getValue }) => {
      const value = getValue<number | null>();
      return value !== null ? value.toLocaleString(undefined, { maximumFractionDigits: 0 }) : "—";
    },
  },
];

export function Companies() {
  const companies = useCompanies();
  const quotes = useLatestQuotes();

  const rows = useMemo<CompanyRow[]>(() => {
    if (!companies.data) return [];
    const quoteBySymbol = new Map((quotes.data ?? []).map((q) => [q.symbol, q]));
    return companies.data.map((c) => ({
      symbol: c.symbol,
      name: c.name,
      industry: c.industry,
      market_cap_musd: c.market_cap_musd,
      current_price: quoteBySymbol.get(c.symbol)?.current_price ?? null,
      pct_change: quoteBySymbol.get(c.symbol)?.pct_change ?? null,
    }));
  }, [companies.data, quotes.data]);

  if (companies.isPending) return <LoadingSpinner label="Loading companies..." />;
  if (companies.isError)
    return <ErrorState message="Couldn't load companies." onRetry={() => companies.refetch()} />;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Companies</h1>
      <DataTable data={rows} columns={columns} searchPlaceholder="Search by symbol, name, industry..." />
    </div>
  );
}
