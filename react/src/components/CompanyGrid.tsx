import { useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { AgGridReact } from "ag-grid-react";
import {
  ModuleRegistry,
  AllCommunityModule,
  themeQuartz,
  colorSchemeDark,
  type ColDef,
} from "ag-grid-community";
import { useTheme } from "../hooks/useTheme";
import { WatchlistStar } from "./WatchlistStar";

ModuleRegistry.registerModules([AllCommunityModule]);

const lightTheme = themeQuartz;
const darkTheme = themeQuartz.withPart(colorSchemeDark);

export interface CompanyGridRow {
  symbol: string;
  name: string | null;
  industry: string | null;
  market_cap_musd: number | null;
  current_price: number | null;
  pct_change: number | null;
}

export function CompanyGrid({ data }: { data: CompanyGridRow[] }) {
  const { theme } = useTheme();
  const gridRef = useRef<AgGridReact<CompanyGridRow>>(null);
  const [quickFilter, setQuickFilter] = useState("");

  const columnDefs = useMemo<ColDef<CompanyGridRow>[]>(
    () => [
      {
        headerName: "",
        field: "symbol",
        pinned: "left",
        width: 56,
        sortable: false,
        filter: false,
        cellRenderer: (params: { data?: CompanyGridRow }) =>
          params.data ? <WatchlistStar symbol={params.data.symbol} /> : null,
      },
      {
        field: "symbol",
        headerName: "Symbol",
        pinned: "left",
        width: 110,
        cellRenderer: (params: { value: string }) => (
          <Link to={`/companies/${params.value}`} className="font-semibold text-brand-blue hover:underline">
            {params.value}
          </Link>
        ),
      },
      { field: "name", headerName: "Company", flex: 1, minWidth: 160 },
      { field: "industry", headerName: "Industry", flex: 1, minWidth: 140 },
      {
        field: "current_price",
        headerName: "Price",
        width: 120,
        valueFormatter: (params) => (params.value != null ? `$${params.value.toFixed(2)}` : "—"),
      },
      {
        field: "pct_change",
        headerName: "% Change",
        width: 120,
        cellRenderer: (params: { value: number | null }) => {
          if (params.value == null) return "—";
          const positive = params.value >= 0;
          return (
            <span className={positive ? "text-brand-green" : "text-brand-red"}>
              {positive ? "+" : ""}
              {params.value.toFixed(2)}%
            </span>
          );
        },
      },
      {
        field: "market_cap_musd",
        headerName: "Market Cap ($M)",
        width: 160,
        valueFormatter: (params) =>
          params.value != null ? params.value.toLocaleString(undefined, { maximumFractionDigits: 0 }) : "—",
      },
    ],
    [],
  );

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <input
          value={quickFilter}
          onChange={(e) => setQuickFilter(e.target.value)}
          placeholder="Search by symbol, name, industry..."
          className="w-full max-w-xs rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
        />
        <button
          onClick={() => gridRef.current?.api.exportDataAsCsv({ fileName: "companies.csv" })}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
        >
          Export CSV
        </button>
      </div>

      <div style={{ height: 520 }}>
        <AgGridReact<CompanyGridRow>
          ref={gridRef}
          theme={theme === "dark" ? darkTheme : lightTheme}
          rowData={data}
          columnDefs={columnDefs}
          quickFilterText={quickFilter}
          pagination
          paginationPageSize={15}
          paginationPageSizeSelector={[15, 30, 50]}
          animateRows
        />
      </div>
    </div>
  );
}
