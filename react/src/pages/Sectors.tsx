import type { ColumnDef } from "@tanstack/react-table";
import { useSectors } from "../api/queries";
import type { SectorSummary } from "../api/types";
import { SectorChart } from "../components/SectorChart";
import { DataTable } from "../components/DataTable";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ErrorState } from "../components/ErrorState";

const columns: ColumnDef<SectorSummary, any>[] = [
  { accessorKey: "industry", header: "Industry" },
  { accessorKey: "num_companies", header: "Companies" },
  {
    accessorKey: "avg_pct_change",
    header: "Avg % Change",
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
  {
    accessorKey: "total_market_cap_musd",
    header: "Total Market Cap ($M)",
    cell: ({ getValue }) => getValue<number>()?.toLocaleString(undefined, { maximumFractionDigits: 0 }),
  },
];

export function Sectors() {
  const sectors = useSectors();

  if (sectors.isPending) return <LoadingSpinner label="Loading sector data..." />;
  if (sectors.isError)
    return <ErrorState message="Couldn't load sector data." onRetry={() => sectors.refetch()} />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Sector Analysis</h1>

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <SectorChart data={sectors.data} />
      </div>

      <DataTable data={sectors.data} columns={columns} searchPlaceholder="Search industry..." />
    </div>
  );
}
