import { ArrowLeft, CandlestickChart, CheckCircle2, CircleDashed, Newspaper, Radar, XCircle } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useStock } from "../api/queries";
import type { StockDetail } from "../api/types";
import { EChart } from "../components/charts/EChart";
import { NewsRow } from "../components/NewsRow";
import { Card, Chip, EmptyState, ErrorState, PageSkeleton, Segmented, WatchStar } from "../components/ui";
import { KpiCard } from "../components/visuals";
import { useChartColors } from "../hooks/useChartColors";
import { catalystLabel, pct, rupees, shortDate, tone } from "../utils/format";

type Range = "1mo" | "3mo" | "6mo" | "1y";

export function StockPage() {
  const { symbol = "" } = useParams();
  const [range, setRange] = useState<Range>("6mo");
  const stock = useStock(symbol.toUpperCase(), range);

  if (stock.isPending) return <PageSkeleton label={`Loading ${symbol}…`} />;
  if (stock.isError) return <ErrorState message={`No price data found for ${symbol}.`} onRetry={() => stock.refetch()} />;
  const s = stock.data.data;
  const bars = s.bars;
  const last = bars[bars.length - 1];
  const prev = bars[bars.length - 2];
  const change = last && prev ? (last.close / prev.close - 1) * 100 : null;
  const graded = s.appearances.filter((a) => a.graded);
  const hits = graded.filter((a) => a.hit).length;

  return (
    <div className="space-y-5">
      <Link to="/" className="inline-flex items-center gap-1 text-sm text-ink-2 hover:text-ink">
        <ArrowLeft className="h-4 w-4" /> Back to radar
      </Link>

      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-mono text-3xl font-extrabold tracking-tight text-ink">{s.symbol}</h1>
            <WatchStar symbol={s.symbol} />
          </div>
          <p className="text-sm text-ink-2">{s.name} · NSE</p>
        </div>
        <div className="text-right">
          <div className="num text-3xl font-bold text-ink">{rupees(s.price ?? last?.close)}</div>
          <div className={`num text-sm font-semibold ${tone(change)}`}>{pct(change)} on the day</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <KpiCard index={0} label="Days on the radar" value={s.appearances.length} icon={<Radar className="h-4 w-4" />} sub={`${s.appearances.filter((a) => a.is_pick).length} as a top pick`} />
        <KpiCard index={1} label="Hit +1% next day" value={graded.length ? (100 * hits) / graded.length : null} format={(v) => `${v.toFixed(0)}%`} icon={<CheckCircle2 className="h-4 w-4" />} accent="up" sub={`${hits} of ${graded.length} graded`} />
        <KpiCard index={2} label={`${range} high`} value={bars.length ? Math.max(...bars.map((b) => b.high)) : null} format={(v) => rupees(v)} icon={<CandlestickChart className="h-4 w-4" />} accent="accent" />
        <KpiCard index={3} label="Headlines tracked" value={s.news.length} icon={<Newspaper className="h-4 w-4" />} sub="last 30 days" />
      </div>

      <Card
        title="Price"
        icon={<CandlestickChart className="h-4 w-4" />}
        action={
          <Segmented<Range>
            value={range}
            onChange={setRange}
            options={[
              { value: "1mo", label: "1M" },
              { value: "3mo", label: "3M" },
              { value: "6mo", label: "6M" },
              { value: "1y", label: "1Y" },
            ]}
          />
        }
      >
        <CandleChart s={s} />
        <p className="mt-2 flex flex-wrap items-center gap-3 text-[11px] text-ink-3">
          <span className="inline-flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-accent" /> on the radar that day</span>
          <span className="inline-flex items-center gap-1"><span className="h-0.5 w-4 bg-up" /> +1% target from the latest 2 PM price</span>
        </p>
      </Card>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card title="Radar history" icon={<Radar className="h-4 w-4" />} padded={false} className="lg:col-span-2">
          {s.appearances.length ? (
            <ul className="divide-y divide-line">
              {s.appearances.map((a) => (
                <li key={a.trade_date} className="flex items-center justify-between gap-3 px-4 py-3 sm:px-5">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 text-sm font-medium text-ink">
                      {shortDate(a.trade_date)}
                      {a.is_pick ? <Chip tone="accent">Pick #{a.rank}</Chip> : <Chip>Candidate</Chip>}
                    </div>
                    <div className="mt-0.5 truncate text-xs text-ink-3">{a.catalysts.map(catalystLabel).join(", ") || a.headline}</div>
                  </div>
                  <div className="shrink-0 text-right text-xs">
                    <div className="num text-ink-2">{rupees(a.price)} → {rupees(a.next_high)}</div>
                    {!a.graded ? (
                      <span className="inline-flex items-center gap-1 text-ink-3"><CircleDashed className="h-3.5 w-3.5" /> waiting</span>
                    ) : a.hit ? (
                      <span className="inline-flex items-center gap-1 font-semibold text-up"><CheckCircle2 className="h-3.5 w-3.5" /> {pct(a.max_gain_pct)}</span>
                    ) : (
                      <span className="inline-flex items-center gap-1 font-semibold text-down"><XCircle className="h-3.5 w-3.5" /> {pct(a.max_gain_pct)}</span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState icon={<Radar className="h-6 w-6" />} title="Not on the radar yet" />
          )}
        </Card>
        <Card title="News" icon={<Newspaper className="h-4 w-4" />} padded={false} className="lg:col-span-3">
          {s.news.length ? (
            <ul className="max-h-[520px] divide-y divide-line overflow-y-auto">
              {s.news.map((n, i) => (
                <NewsRow key={n.id} n={n} index={i} />
              ))}
            </ul>
          ) : (
            <EmptyState icon={<Newspaper className="h-6 w-6" />} title="No tracked headlines for this stock" />
          )}
        </Card>
      </div>
    </div>
  );
}

function CandleChart({ s }: { s: StockDetail }) {
  const c = useChartColors();
  const option = useMemo(() => {
    const dates = s.bars.map((b) => b.date);
    const onRadar = new Set(s.appearances.map((a) => a.trade_date));
    const latest = s.appearances[0];
    return {
      animation: true,
      tooltip: { trigger: "axis", axisPointer: { type: "cross" }, backgroundColor: c.panel, borderColor: c.line, textStyle: { color: c.ink } },
      axisPointer: { link: [{ xAxisIndex: "all" }], label: { backgroundColor: c.ink2 } },
      grid: [
        { left: 8, right: 56, top: 12, height: "64%", containLabel: false },
        { left: 8, right: 56, top: "80%", height: "14%" },
      ],
      xAxis: [
        { type: "category", data: dates, boundaryGap: true, axisLine: { lineStyle: { color: c.line } }, axisLabel: { color: c.ink3, fontSize: 10, formatter: (v: string) => shortDate(v) } },
        { type: "category", gridIndex: 1, data: dates, axisLabel: { show: false }, axisTick: { show: false }, axisLine: { lineStyle: { color: c.line } } },
      ],
      yAxis: [
        { scale: true, position: "right", axisLabel: { color: c.ink3, fontSize: 10 }, splitLine: { lineStyle: { color: c.line } } },
        { gridIndex: 1, scale: true, position: "right", axisLabel: { show: false }, splitLine: { show: false } },
      ],
      dataZoom: [{ type: "inside", xAxisIndex: [0, 1], start: 0, end: 100 }],
      series: [
        {
          name: s.symbol,
          type: "candlestick",
          data: s.bars.map((b) => [b.open, b.close, b.low, b.high]),
          itemStyle: { color: c.up, color0: c.down, borderColor: c.up, borderColor0: c.down },
          markPoint: {
            symbol: "pin",
            symbolSize: 26,
            itemStyle: { color: c.accent },
            label: { show: false },
            data: s.bars.filter((b) => onRadar.has(b.date)).map((b) => ({ coord: [b.date, b.high], value: "R" })),
          },
          markLine: latest?.target_price
            ? {
                symbol: "none",
                lineStyle: { color: c.up, type: "dashed", width: 1.5 },
                label: { color: c.up, formatter: `+1% ${rupees(latest.target_price)}`, position: "insideEndTop", fontSize: 10 },
                data: [{ yAxis: latest.target_price }],
              }
            : undefined,
        },
        {
          name: "Volume",
          type: "bar",
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: s.bars.map((b, i) => ({
            value: b.volume,
            itemStyle: { color: (i && b.close < s.bars[i - 1].close ? c.down : c.up) + "66" },
          })),
        },
      ],
    };
  }, [c, s]);
  return <EChart option={option} className="h-[380px]" ariaLabel={`${s.symbol} daily price and volume`} />;
}
