import type { ColDef } from "ag-grid-community";
import { AgGridReact } from "ag-grid-react";
import { CalendarDays, CheckCircle2, CircleDashed, Gauge, Hourglass, Layers, Scale, Target, TrendingUp, XCircle } from "lucide-react";
import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useAnalytics, useHistory, useTrackRecord } from "../api/queries";
import type { Analytics, PickPerformance, TrackRecordDay } from "../api/types";
import { EChart } from "../components/charts/EChart";
import { gridTheme } from "../components/radar";
import { Card, Chip, EmptyState, ErrorState, PageSkeleton, SourceBadge } from "../components/ui";
import { KpiCard } from "../components/visuals";
import { useChartColors } from "../hooks/useChartColors";
import { catalystLabel, pct, rupees, shortDate, SOURCE_LABEL } from "../utils/format";

export function TrackRecordPage() {
  const record = useTrackRecord();
  const analytics = useAnalytics();
  const history = useHistory(120);

  if (record.isPending || history.isPending) return <PageSkeleton label="Loading the track record…" />;
  if (record.isError || history.isError)
    return <ErrorState message="Couldn't load the track record." onRetry={() => { record.refetch(); history.refetch(); }} />;

  const days = record.data.data;
  const rows = history.data.data;
  const graded = rows.filter((r) => r.graded);
  const picks = graded.filter((r) => r.is_pick);
  const others = graded.filter((r) => !r.is_pick);
  const rate = (xs: PickPerformance[]) => (xs.length ? (100 * xs.filter((x) => x.hit).length) / xs.length : null);
  const avgGain = picks.length ? picks.reduce((s, r) => s + (r.max_gain_pct ?? 0), 0) / picks.length : null;
  const pending = rows.filter((r) => !r.graded && r.is_pick).length;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-ink">Track record</h1>
          <p className="mt-1 max-w-2xl text-sm text-ink-2">
            Every scored stock is graded the next trading day: a <b className="text-ink">hit</b> means its high reached +1% above
            the 2 PM price. Picks are compared with the stocks that had good news but ranked lower, so you can see if the
            score adds anything.
          </p>
        </div>
        <SourceBadge source={record.data.source} />
      </div>

      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <KpiCard index={0} label="Pick hit rate" value={rate(picks)} format={(v) => `${v.toFixed(0)}%`} icon={<Target className="h-4 w-4" />} accent="up" sub={`${picks.filter((p) => p.hit).length} of ${picks.length} picks`} />
        <KpiCard index={1} label="Other candidates" value={rate(others)} format={(v) => `${v.toFixed(0)}%`} icon={<Scale className="h-4 w-4" />} sub="same news filter, lower score" />
        <KpiCard index={2} label="Avg best move next day" value={avgGain} format={(v) => pct(v)} icon={<TrendingUp className="h-4 w-4" />} accent="accent" sub="picks, high vs 2 PM price" />
        <KpiCard index={3} label="Trading days graded" value={days.length} icon={<CalendarDays className="h-4 w-4" />} sub={pending ? `${pending} picks waiting for tomorrow` : "up to date"} />
      </div>

      {graded.length === 0 ? (
        <Card>
          <EmptyState icon={<Hourglass className="h-6 w-6" />} title="The first results arrive after the next close">
            Picks are graded at 3:52 PM on the following trading day. This page fills in on its own from then on:
            daily hit rates, a calendar, and which scores, sources and catalysts actually worked.
          </EmptyState>
        </Card>
      ) : (
        <>
          <div className="grid gap-4 lg:grid-cols-5">
            <DailyChart days={days} className="lg:col-span-3" />
            <CalendarChart days={days} className="lg:col-span-2" />
          </div>
          {analytics.data && <AnalyticsCharts a={analytics.data.data} />}
        </>
      )}

      <HistoryGrid rows={rows} />
    </div>
  );
}

function DailyChart({ days, className }: { days: TrackRecordDay[]; className?: string }) {
  const c = useChartColors();
  const option = useMemo(
    () => ({
      tooltip: { trigger: "axis", backgroundColor: c.panel, borderColor: c.line, textStyle: { color: c.ink } },
      legend: { top: 0, textStyle: { color: c.ink2, fontSize: 11 }, itemWidth: 10, itemHeight: 8 },
      grid: { left: 8, right: 8, top: 36, bottom: 8, containLabel: true },
      xAxis: { type: "category", data: days.map((d) => shortDate(d.trade_date)), axisLabel: { color: c.ink3, fontSize: 10 }, axisLine: { lineStyle: { color: c.line } } },
      yAxis: [
        { type: "value", minInterval: 1, axisLabel: { color: c.ink3, fontSize: 10 }, splitLine: { lineStyle: { color: c.line } } },
        { type: "value", max: 100, axisLabel: { color: c.ink3, fontSize: 10, formatter: "{value}%" }, splitLine: { show: false } },
      ],
      series: [
        { name: "Picks", type: "bar", barGap: "-100%", barWidth: "55%", itemStyle: { color: c.panel2, borderColor: c.line, borderRadius: 4 }, data: days.map((d) => d.picks) },
        { name: "Hit +1%", type: "bar", barWidth: "55%", itemStyle: { color: c.up, borderRadius: 4 }, data: days.map((d) => d.pick_hits) },
        { name: "Pick hit rate, rolling 20 days", type: "line", yAxisIndex: 1, smooth: true, symbol: "none", lineStyle: { width: 2.5, color: c.accent }, itemStyle: { color: c.accent }, data: days.map((d) => d.rolling_20d_pick_hit_rate) },
        { name: "Other candidates", type: "line", yAxisIndex: 1, smooth: true, symbol: "none", lineStyle: { width: 1.5, type: "dashed", color: c.ink3 }, itemStyle: { color: c.ink3 }, data: days.map((d) => d.other_hit_rate) },
      ],
    }),
    [c, days],
  );
  return (
    <Card title="Daily picks and hits" icon={<Target className="h-4 w-4" />} className={className} delay={0.15}>
      <EChart option={option} className="h-72" ariaLabel="Daily picks, hits and rolling hit rate" />
    </Card>
  );
}

function CalendarChart({ days, className }: { days: TrackRecordDay[]; className?: string }) {
  const c = useChartColors();
  const option = useMemo(() => {
    const last = days[days.length - 1]?.trade_date ?? new Date().toISOString().slice(0, 10);
    const start = new Date(last);
    start.setMonth(start.getMonth() - 3);
    return {
      tooltip: {
        backgroundColor: c.panel,
        borderColor: c.line,
        textStyle: { color: c.ink },
        formatter: (p: { value: [string, number, number, number] }) => `${shortDate(p.value[0])}: ${p.value[2]}/${p.value[3]} picks hit`,
      },
      visualMap: { show: false, min: 0, max: 100, inRange: { color: [c.down, c.accent, c.up] } },
      calendar: {
        range: [start.toISOString().slice(0, 10), last],
        cellSize: ["auto", 16],
        left: 30,
        right: 8,
        top: 24,
        itemStyle: { color: c.panel2, borderColor: c.panel, borderWidth: 3 },
        splitLine: { show: false },
        dayLabel: { color: c.ink3, fontSize: 9, firstDay: 1, nameMap: ["S", "M", "T", "W", "T", "F", "S"] },
        monthLabel: { color: c.ink2, fontSize: 10 },
        yearLabel: { show: false },
      },
      series: [{ type: "heatmap", coordinateSystem: "calendar", data: days.filter((d) => d.picks).map((d) => [d.trade_date, d.pick_hit_rate, d.pick_hits, d.picks]) }],
    };
  }, [c, days]);
  return (
    <Card title="Hit-rate calendar" icon={<CalendarDays className="h-4 w-4" />} className={className} delay={0.2}>
      <EChart option={option} className="h-72" ariaLabel="Calendar of daily pick hit rates" />
    </Card>
  );
}

function RateBars({ labels, rates, trades, color }: { labels: string[]; rates: (number | null)[]; trades: number[]; color: string }) {
  const c = useChartColors();
  const option = useMemo(
    () => ({
      tooltip: {
        backgroundColor: c.panel,
        borderColor: c.line,
        textStyle: { color: c.ink },
        formatter: (p: { name: string; value: number; dataIndex: number }) => `${p.name}: ${p.value ?? "–"}% of ${trades[p.dataIndex]} trades hit`,
      },
      grid: { left: 8, right: 30, top: 8, bottom: 8, containLabel: true },
      xAxis: { type: "value", max: 100, show: false },
      yAxis: { type: "category", data: labels, inverse: true, axisLabel: { color: c.ink2, fontSize: 11 }, axisLine: { show: false }, axisTick: { show: false } },
      series: [
        {
          type: "bar",
          barWidth: 14,
          showBackground: true,
          backgroundStyle: { color: c.panel2, borderRadius: 7 },
          itemStyle: { color, borderRadius: 7 },
          label: { show: true, position: "right", color: c.ink2, fontSize: 11, formatter: "{c}%" },
          data: rates,
        },
      ],
    }),
    [c, labels, rates, trades, color],
  );
  return <EChart option={option} className="h-56" />;
}

function AnalyticsCharts({ a }: { a: Analytics }) {
  const c = useChartColors();
  const cats = a.by_catalyst.filter((r) => r.is_pick).slice(0, 7);
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <Card title="Does a higher score hit more?" icon={<Gauge className="h-4 w-4" />} delay={0.2}>
        <RateBars labels={a.by_score_band.map((r) => `Score ${r.score_band}`)} rates={a.by_score_band.map((r) => r.hit_rate)} trades={a.by_score_band.map((r) => r.trades)} color={c.brand} />
      </Card>
      <Card title="Which news source works" icon={<Layers className="h-4 w-4" />} delay={0.25}>
        <RateBars labels={a.by_source.map((r) => SOURCE_LABEL[r.source] ?? r.source)} rates={a.by_source.map((r) => r.hit_rate)} trades={a.by_source.map((r) => r.trades)} color={c.accent} />
      </Card>
      <Card title="Which catalyst works (picks)" icon={<Target className="h-4 w-4" />} delay={0.3}>
        {cats.length ? (
          <RateBars labels={cats.map((r) => catalystLabel(r.catalyst))} rates={cats.map((r) => r.hit_rate)} trades={cats.map((r) => r.trades)} color={c.up} />
        ) : (
          <p className="py-16 text-center text-sm text-ink-3">No graded picks yet.</p>
        )}
      </Card>
    </div>
  );
}

function HistoryGrid({ rows }: { rows: PickPerformance[] }) {
  const navigate = useNavigate();
  const columns = useMemo<ColDef<PickPerformance>[]>(
    () => [
      { field: "trade_date", headerName: "Date", width: 105, valueFormatter: (p) => shortDate(p.value) },
      {
        field: "symbol",
        headerName: "Stock",
        minWidth: 170,
        flex: 1,
        cellRenderer: (p: { data?: PickPerformance }) =>
          p.data && (
            <div className="flex flex-col justify-center leading-tight">
              <span className="font-mono font-bold">{p.data.symbol}</span>
              <span className="truncate text-[11px] text-ink-3">{p.data.name}</span>
            </div>
          ),
      },
      {
        field: "is_pick",
        headerName: "Role",
        width: 95,
        cellRenderer: (p: { value: boolean }) => (p.value ? <Chip tone="accent">Pick</Chip> : <Chip>Other</Chip>),
      },
      { field: "score", headerName: "Score", width: 85, type: "rightAligned", valueFormatter: (p) => (p.value == null ? "–" : p.value.toFixed(0)) },
      { field: "price", headerName: "2 PM price", width: 110, type: "rightAligned", valueFormatter: (p) => rupees(p.value) },
      { field: "next_high", headerName: "Next high", width: 110, type: "rightAligned", valueFormatter: (p) => rupees(p.value) },
      { field: "max_gain_pct", headerName: "Best move", width: 100, type: "rightAligned", valueFormatter: (p) => pct(p.value) },
      { field: "close_return_pct", headerName: "Close", width: 90, type: "rightAligned", valueFormatter: (p) => pct(p.value) },
      {
        headerName: "Result",
        width: 120,
        valueGetter: (p) => (!p.data?.graded ? "Waiting" : p.data.hit ? "Hit" : "Missed"),
        cellRenderer: (p: { value: string }) =>
          p.value === "Hit" ? (
            <span className="inline-flex items-center gap-1 font-semibold text-up"><CheckCircle2 className="h-4 w-4" /> Hit</span>
          ) : p.value === "Missed" ? (
            <span className="inline-flex items-center gap-1 font-semibold text-down"><XCircle className="h-4 w-4" /> Missed</span>
          ) : (
            <span className="inline-flex items-center gap-1 text-ink-3"><CircleDashed className="h-4 w-4" /> Waiting</span>
          ),
      },
      { field: "catalysts", headerName: "Catalysts", minWidth: 170, flex: 1, valueFormatter: (p) => (p.value ?? []).map(catalystLabel).join(", ") },
    ],
    [],
  );
  return (
    <Card title="Every graded stock" icon={<CalendarDays className="h-4 w-4" />} padded={false} delay={0.3}>
      <div className="h-[480px]">
        <AgGridReact<PickPerformance>
          theme={gridTheme}
          rowData={rows}
          columnDefs={columns}
          rowHeight={48}
          defaultColDef={{ sortable: true, resizable: true }}
          onRowClicked={(e) => e.data && navigate(`/stock/${encodeURIComponent(e.data.symbol)}`)}
          rowClass="cursor-pointer"
          overlayNoRowsTemplate="<span style='color:var(--ink-3)'>Nothing graded yet</span>"
        />
      </div>
    </Card>
  );
}
