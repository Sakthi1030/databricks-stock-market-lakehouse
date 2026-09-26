import { AllCommunityModule, ModuleRegistry, themeQuartz, type ColDef } from "ag-grid-community";
import { AgGridReact } from "ag-grid-react";
import { motion } from "framer-motion";
import { ArrowUpRight, Crosshair, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import type { Candidate, IndexQuote } from "../api/types";
import { catalystLabel, pct, rupees, share, tone } from "../utils/format";
import { Card, Chip, Segmented, WatchStar } from "./ui";
import { ScoreBars, ScoreRing, Sparkline } from "./visuals";

ModuleRegistry.registerModules([AllCommunityModule]);

/** AG Grid themed straight from the CSS tokens, so it follows light/dark without a remount. */
export const gridTheme = themeQuartz.withParams({
  backgroundColor: "var(--panel)",
  foregroundColor: "var(--ink)",
  headerBackgroundColor: "var(--panel-2)",
  headerTextColor: "var(--ink-2)",
  borderColor: "var(--line)",
  rowHoverColor: "var(--panel-2)",
  oddRowBackgroundColor: "var(--panel)",
  accentColor: "var(--brand)",
  fontFamily: "var(--font-sans)",
  fontSize: 13,
  headerFontWeight: 600,
  wrapperBorderRadius: 0,
  wrapperBorder: false,
});

const SHORT_INDEX: Record<string, string> = { "NIFTY 50": "Nifty", "NIFTY Bank": "Bank", Sensex: "Sensex" };

export function IndexStrip({ indices }: { indices: Record<string, IndexQuote> }) {
  return (
    <div className="grid grid-cols-3 gap-2 sm:gap-3">
      {Object.entries(indices).map(([name, q], i) => (
        <motion.div
          key={name}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 * i }}
          className="rounded-xl border border-line bg-panel/70 px-3 py-2 backdrop-blur"
        >
          <div className="flex items-center justify-between gap-2">
            <span className="truncate text-[11px] font-medium text-ink-3">
              <span className="sm:hidden">{SHORT_INDEX[name] ?? name}</span>
              <span className="hidden sm:inline">{name}</span>
            </span>
            <span className={`num text-[11px] font-semibold ${tone(q.change_pct)}`}>{pct(q.change_pct)}</span>
          </div>
          <div className="num text-sm font-bold text-ink sm:text-base">{q.price.toLocaleString("en-IN")}</div>
          <Sparkline values={q.sparkline} className="mt-1 h-6 w-full" strokeWidth={1.4} />
        </motion.div>
      ))}
    </div>
  );
}

export function AiBrief({ brief, byGemini }: { brief: string; byGemini: boolean }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: 0.2 }}
      className="relative overflow-hidden rounded-2xl border border-brand/20 bg-gradient-to-br from-brand/10 via-panel to-accent/5 p-4 shadow-card sm:p-5"
    >
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-brand">
        <Sparkles className="h-4 w-4" />
        2 PM brief
        <span className="font-normal normal-case tracking-normal text-ink-3">
          · {byGemini ? "written by Gemini from today's facts" : "auto-summary (Gemini unavailable)"}
        </span>
      </div>
      <p className="mt-2 text-[15px] leading-relaxed text-ink">{brief}</p>
    </motion.div>
  );
}

export function PickCard({ c, index, targetPct }: { c: Candidate; index: number; targetPct: number }) {
  const navigate = useNavigate();
  return (
    <motion.article
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: 0.25 + index * 0.07, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -4 }}
      onClick={() => navigate(`/stock/${encodeURIComponent(c.symbol)}`)}
      className="group flex cursor-pointer flex-col rounded-2xl border border-line bg-panel p-4 shadow-card transition hover:border-brand/40"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="rounded-md bg-accent/15 px-1.5 py-0.5 text-[11px] font-bold text-accent">#{c.rank}</span>
            <Link
              to={`/stock/${encodeURIComponent(c.symbol)}`}
              onClick={(e) => e.stopPropagation()}
              className="font-mono text-base font-bold text-ink group-hover:text-brand"
            >
              {c.symbol}
            </Link>
            <WatchStar symbol={c.symbol} />
          </div>
          <div className="mt-0.5 truncate text-xs text-ink-3" title={c.name}>
            {c.name}
          </div>
        </div>
        <ScoreRing score={c.score} size={58} delay={0.3 + index * 0.07} />
      </div>

      <div className="mt-3 flex items-end justify-between gap-3">
        <div>
          <div className="num text-xl font-bold text-ink">{rupees(c.price)}</div>
          <div className={`num text-xs font-semibold ${tone(c.day_change_pct)}`}>{pct(c.day_change_pct)} today</div>
        </div>
        <Sparkline values={c.sparkline} className="h-10 w-28" />
      </div>

      <div className="mt-3 flex items-center justify-between rounded-xl bg-panel-2 px-3 py-2">
        <div className="flex items-center gap-2 text-xs text-ink-2">
          <Crosshair className="h-4 w-4 text-up" />
          Sell target <span className="text-ink-3">(+{targetPct}%)</span>
        </div>
        <div className="num text-sm font-bold text-up">{rupees(c.target_price)}</div>
      </div>
      <div className="mt-1.5 text-[11px] text-ink-3">
        Next-day high reached +{targetPct}% on <b className="text-ink-2">{share(c.reach_rate)}</b> of the last 120 days
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {c.catalysts.map((cat) => (
          <Chip key={cat} tone="brand">
            {catalystLabel(cat)}
          </Chip>
        ))}
        <Chip>{c.news_ids.length} headline{c.news_ids.length === 1 ? "" : "s"}</Chip>
      </div>
      <p className="mt-2 line-clamp-2 text-sm text-ink-2" title={c.headline}>
        {c.headline}
      </p>

      <div className="mt-auto pt-4">
        <ScoreBars scores={c.scores} delay={0.35 + index * 0.07} />
      </div>
    </motion.article>
  );
}

type Filter = "all" | "picks" | "watching" | "skipped";

export function CandidatesGrid({ candidates }: { candidates: Candidate[] }) {
  const navigate = useNavigate();
  const [filter, setFilter] = useState<Filter>("all");
  const rows = useMemo(
    () =>
      candidates.filter((c) =>
        filter === "picks" ? c.is_pick : filter === "skipped" ? !!c.skip_reason : filter === "watching" ? !c.is_pick && !c.skip_reason : true,
      ),
    [candidates, filter],
  );

  const columns = useMemo<ColDef<Candidate>[]>(
    () => [
      { headerName: "", width: 60, sortable: false, cellStyle: { display: "flex", alignItems: "center" }, cellRenderer: (p: { data?: Candidate }) => p.data && <WatchStar symbol={p.data.symbol} /> },
      { field: "rank", headerName: "#", width: 60 },
      {
        field: "symbol",
        headerName: "Stock",
        minWidth: 190,
        flex: 1.2,
        cellRenderer: (p: { data?: Candidate }) =>
          p.data && (
            <div className="flex flex-col justify-center leading-tight">
              <span className="font-mono font-bold text-ink">{p.data.symbol}</span>
              <span className="truncate text-[11px] text-ink-3">{p.data.name}</span>
            </div>
          ),
      },
      {
        field: "score",
        headerName: "Score",
        width: 130,
        sort: "desc",
        cellRenderer: (p: { value: number }) => (
          <div className="flex h-full items-center gap-2">
            <div className="h-1.5 w-14 overflow-hidden rounded-full bg-panel-2">
              <div className="h-full rounded-full bg-brand" style={{ width: `${p.value}%` }} />
            </div>
            <span className="num font-semibold">{p.value.toFixed(0)}</span>
          </div>
        ),
      },
      { field: "price", headerName: "Price", width: 110, type: "rightAligned", valueFormatter: (p) => rupees(p.value) },
      {
        field: "day_change_pct",
        headerName: "Today",
        width: 95,
        type: "rightAligned",
        cellRenderer: (p: { value: number | null }) => <span className={`num font-medium ${tone(p.value)}`}>{pct(p.value)}</span>,
      },
      { field: "target_price", headerName: "+1% target", width: 115, type: "rightAligned", valueFormatter: (p) => rupees(p.value) },
      { field: "reach_rate", headerName: "Reach", width: 90, type: "rightAligned", valueFormatter: (p) => share(p.value), headerTooltip: "Share of the last 120 days whose next-day high reached +1%" },
      { field: "volume_ratio", headerName: "Vol ×", width: 85, type: "rightAligned", valueFormatter: (p) => (p.value == null ? "–" : `${p.value.toFixed(1)}×`) },
      { field: "avg_traded_value_cr", headerName: "₹ cr/day", width: 100, type: "rightAligned", valueFormatter: (p) => (p.value == null ? "–" : p.value.toFixed(1)) },
      {
        headerName: "Status",
        minWidth: 170,
        flex: 1,
        valueGetter: (p) => (p.data?.is_pick ? "Pick" : p.data?.skip_reason || "Watching"),
        cellRenderer: (p: { data?: Candidate; value: string }) =>
          p.data?.is_pick ? <Chip tone="up">Pick</Chip> : p.data?.skip_reason ? <Chip tone="down">{p.value}</Chip> : <Chip>Watching</Chip>,
      },
      { field: "headline", headerName: "Top headline", minWidth: 260, flex: 2, tooltipField: "headline" },
    ],
    [],
  );

  return (
    <Card
      title="All candidates"
      icon={<ArrowUpRight className="h-4 w-4" />}
      padded={false}
      delay={0.3}
      action={
        <Segmented<Filter>
          value={filter}
          onChange={setFilter}
          options={[
            { value: "all", label: `All ${candidates.length}` },
            { value: "picks", label: "Picks" },
            { value: "watching", label: "Watching" },
            { value: "skipped", label: "Skipped" },
          ]}
        />
      }
    >
      <div className="h-[460px]">
        <AgGridReact<Candidate>
          theme={gridTheme}
          rowData={rows}
          columnDefs={columns}
          rowHeight={50}
          getRowId={(p) => p.data.symbol}
          onRowClicked={(e) => e.data && navigate(`/stock/${encodeURIComponent(e.data.symbol)}`)}
          rowClass="cursor-pointer"
          defaultColDef={{ sortable: true, resizable: true }}
          tooltipShowDelay={300}
        />
      </div>
    </Card>
  );
}
