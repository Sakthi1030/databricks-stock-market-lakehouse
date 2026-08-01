import { useState } from "react";
import { Link } from "react-router-dom";
import type { ColumnDef } from "@tanstack/react-table";
import { useMovers } from "../api/queries";
import type { MoverType, TopMover } from "../api/types";
import { DataTable } from "../components/DataTable";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ErrorState } from "../components/ErrorState";

const columns: ColumnDef<TopMover, any>[] = [
  { accessorKey: "rank", header: "Rank" },
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
    cell: ({ getValue }) => `$${getValue<number>()?.toFixed(2)}`,
  },
  {
    accessorKey: "pct_change",
    header: "% Change",
    cell: ({ getValue }) => {
      const value = getValue<number>();
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

const FILTERS: { label: string; value: MoverType | undefined }[] = [
  { label: "All", value: undefined },
  { label: "Gainers", value: "gainer" },
  { label: "Losers", value: "loser" },
];

export function Movers() {
  const [filter, setFilter] = useState<MoverType | undefined>(undefined);
  const movers = useMovers(filter);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Top Movers</h1>
        <div className="flex gap-1 rounded-lg border border-slate-200 p-1 dark:border-slate-800">
          {FILTERS.map((f) => (
            <button
              key={f.label}
              onClick={() => setFilter(f.value)}
              className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
                filter === f.value
                  ? "bg-brand-blue text-white"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {movers.isPending && <LoadingSpinner label="Loading movers..." />}
      {movers.isError && <ErrorState message="Couldn't load movers." onRetry={() => movers.refetch()} />}
      {movers.data && (
        <DataTable data={movers.data} columns={columns} searchPlaceholder="Search by symbol, name..." />
      )}
    </div>
  );
}
