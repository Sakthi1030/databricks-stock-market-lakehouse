import { motion } from "framer-motion";
import { Activity, Newspaper, Radar as RadarIcon, ScanSearch, Target, Telescope } from "lucide-react";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useToday } from "../api/queries";
import type { NewsSource, TodayRun } from "../api/types";
import { EChart } from "../components/charts/EChart";
import { AiBrief, CandidatesGrid, IndexStrip, MarketLight, PickCard, TickerTape } from "../components/radar";
import { Card, EmptyState, ErrorState, PageSkeleton } from "../components/ui";
import { KpiCard, MiniStack, SlotDots, VersusBars } from "../components/visuals";
import { useChartColors } from "../hooks/useChartColors";
import { catalystLabel, istDate, istTime, SOURCE_LABEL } from "../utils/format";
import { marketMood } from "../utils/mood";

export function RadarPage() {
  const today = useToday();
  if (today.isPending) return <PageSkeleton label="Loading today's radar…" />;
  if (today.isError)
    return <ErrorState message="Couldn't load today's radar. The API may still be waking up." onRetry={() => today.refetch()} />;
  return <Radar run={today.data.data} />;
}

function Radar({ run }: { run: TodayRun }) {
  const navigate = useNavigate();
  const picks = run.candidates.filter((c) => c.is_pick);
  const tr = run.track_record;
  const mood = marketMood(run.indices["NIFTY 50"], run.indices["NIFTY Bank"]);
  const [flash, setFlash] = useState(false);
  const c = useChartColors();

  // "Picks today" jumps to the five picks and makes them pulse once so the eye lands there.
  const showPicks = () => {
    document.getElementById("picks")?.scrollIntoView({ behavior: "smooth", block: "start" });
    setFlash(false);
    requestAnimationFrame(() => setFlash(true));
    window.setTimeout(() => setFlash(false), 3000);
  };
  const showCandidates = () => document.getElementById("candidates")?.scrollIntoView({ behavior: "smooth", block: "start" });

  return (
    <div className="space-y-5">
      <TickerTape indices={run.indices} candidates={run.candidates} />

      {/* Hero */}
      <section className="relative overflow-hidden rounded-3xl border border-line bg-panel p-5 shadow-card sm:p-6">
        <div className="grid-paper pointer-events-none absolute inset-0" />
        <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 opacity-60">
          <div className="radar-sweep absolute inset-0 rounded-full" />
          <div className="absolute inset-8 rounded-full border border-line" />
          <div className="absolute inset-20 rounded-full border border-line" />
        </div>
        <div className="relative grid gap-5 lg:grid-cols-[1fr_minmax(0,440px)]">
          <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col justify-between gap-4">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">Today's radar</div>
              <h1 className="mt-1 text-3xl font-bold text-ink sm:text-4xl">{istDate(run.market_date)}</h1>
              <p className="mt-1.5 max-w-xl text-sm text-ink-2">
                Stocks with fresh positive news, scored at <b className="text-ink">{istTime(run.run_at)}</b> for a next-day
                move of <b className="text-up">+{run.target_pct}%</b>. Buy in delivery before the close, sell at the target.
              </p>
            </div>
            <IndexStrip indices={run.indices} />
          </motion.div>
          {mood && <MarketLight mood={mood} />}
        </div>
      </section>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <KpiCard
          index={0}
          label="Picks today"
          value={picks.length}
          icon={<Target className="h-4 w-4" />}
          accent="accent"
          visual={<SlotDots filled={picks.length} total={5} />}
          sub={`of ${run.candidates.length} scored stocks`}
          onClick={showPicks}
          cta="View the top picks"
        />
        <KpiCard
          index={1}
          label="Headlines scanned"
          value={run.stats.headlines}
          icon={<Newspaper className="h-4 w-4" />}
          visual={
            <MiniStack
              parts={(Object.entries(run.stats.by_source) as [NewsSource, number][]).map(([k, v], i) => ({
                label: SOURCE_LABEL[k],
                value: v,
                color: c.series[i % c.series.length],
              }))}
            />
          }
          sub={`${run.stats.classified_by_gemini} read by Gemini`}
          onClick={() => navigate("/news")}
          cta="Open the news feed"
        />
        <KpiCard
          index={2}
          label="Stocks with good news"
          value={run.stats.matched_stocks}
          icon={<ScanSearch className="h-4 w-4" />}
          visual={
            <MiniStack
              parts={[
                { label: "Picks", value: picks.length, color: c.accent },
                { label: "Watching", value: run.candidates.filter((x) => !x.is_pick && !x.skip_reason).length, color: c.brand },
                { label: "Skipped", value: run.candidates.filter((x) => x.skip_reason).length, color: c.ink3 },
              ]}
            />
          }
          sub="picks · watching · skipped"
          onClick={showCandidates}
          cta="See all candidates"
        />
        <KpiCard
          index={3}
          label="Pick hit rate"
          value={tr.pick_hit_rate}
          format={(v) => `${v.toFixed(0)}%`}
          icon={<Activity className="h-4 w-4" />}
          accent="up"
          visual={<VersusBars a={tr.pick_hit_rate} b={tr.other_hit_rate} aLabel="Picks" bLabel="Others" />}
          sub={tr.picks ? `${tr.pick_hits}/${tr.picks} over ${tr.days} days` : "builds from the first graded day"}
          onClick={() => navigate("/track-record")}
          cta="Open the track record"
        />
      </div>

      <AiBrief brief={run.brief} byGemini={run.stats.classified_by_gemini > 0} />

      {/* Picks */}
      <section id="picks" className="scroll-mt-20">
        <div className="mb-3 flex items-end justify-between">
          <h2 className="flex items-center gap-2 text-lg font-bold text-ink">
            <RadarIcon className="h-5 w-5 text-accent" /> Top picks
          </h2>
          <span className="text-xs text-ink-3">tap a card for the chart and news</span>
        </div>
        {picks.length ? (
          <div className={`grid gap-4 sm:grid-cols-2 xl:grid-cols-3 ${flash ? "flash" : ""}`}>
            {picks.map((c, i) => (
              <PickCard key={c.symbol} c={c} index={i} targetPct={run.target_pct} />
            ))}
          </div>
        ) : (
          <Card>
            <EmptyState icon={<Telescope className="h-6 w-6" />} title="No stock passed every check today">
              Nothing had strong enough news with enough liquidity and a sane move so far. Sitting out is a valid trade.
            </EmptyState>
          </Card>
        )}
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        <ScoreRadar run={run} />
        <NewsMix run={run} />
      </div>

      <div id="candidates" className="scroll-mt-20">
        <CandidatesGrid candidates={run.candidates} />
      </div>
    </div>
  );
}

function ScoreRadar({ run }: { run: TodayRun }) {
  const c = useChartColors();
  const navigate = useNavigate();
  const picks = run.candidates.filter((x) => x.is_pick).slice(0, 5);
  const option = useMemo(
    () => ({
      color: c.series,
      legend: { bottom: 0, textStyle: { color: c.ink2, fontSize: 11 }, icon: "circle", itemWidth: 8 },
      tooltip: { backgroundColor: c.panel, borderColor: c.line, textStyle: { color: c.ink } },
      radar: {
        radius: "62%",
        center: ["50%", "46%"],
        indicator: ["News", "Reach", "Momentum", "Volume"].map((name) => ({ name, max: 100 })),
        axisName: { color: c.ink2, fontSize: 11 },
        splitLine: { lineStyle: { color: c.line } },
        splitArea: { areaStyle: { color: ["transparent"] } },
        axisLine: { lineStyle: { color: c.line } },
      },
      series: [
        {
          type: "radar",
          symbolSize: 4,
          areaStyle: { opacity: 0.12 },
          lineStyle: { width: 2 },
          data: picks.map((p) => ({
            name: p.symbol,
            value: [p.scores.news, p.scores.reach, p.scores.momentum, p.scores.volume].map(Math.round),
          })),
        },
      ],
    }),
    [c, picks],
  );
  return (
    <Card title="Why the picks scored high" icon={<RadarIcon className="h-4 w-4" />} delay={0.25}>
      {picks.length ? (
        <EChart option={option} className="h-72" ariaLabel="Score components of today's picks"
          onClick={(p) => p.name && navigate(`/stock/${encodeURIComponent(p.name)}`)} />
      ) : (
        <p className="py-16 text-center text-sm text-ink-3">No picks to compare today.</p>
      )}
    </Card>
  );
}

function NewsMix({ run }: { run: TodayRun }) {
  const c = useChartColors();
  const option = useMemo(() => {
    const sources = Object.entries(run.stats.by_source) as [NewsSource, number][];
    const catalysts = new Map<string, number>();
    run.candidates.forEach((x) => x.catalysts.forEach((k) => catalysts.set(k, (catalysts.get(k) ?? 0) + 1)));
    const cats = [...catalysts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 6).reverse();
    return {
      color: c.series,
      tooltip: { backgroundColor: c.panel, borderColor: c.line, textStyle: { color: c.ink } },
      legend: {
        left: 0,
        bottom: 0,
        width: "48%",
        icon: "circle",
        itemWidth: 8,
        textStyle: { color: c.ink2, fontSize: 10 },
        formatter: (name: string) => `${name} ${sources.find(([k]) => SOURCE_LABEL[k] === name)?.[1] ?? ""}`,
      },
      title: [
        { text: "Headlines by source", left: "24%", top: 0, textAlign: "center", textStyle: { color: c.ink2, fontSize: 11, fontWeight: 500 } },
        { text: "Catalysts among candidates", left: "73%", top: 0, textAlign: "center", textStyle: { color: c.ink2, fontSize: 11, fontWeight: 500 } },
      ],
      series: [
        {
          type: "pie",
          radius: ["42%", "66%"],
          center: ["24%", "48%"],
          itemStyle: { borderColor: c.panel, borderWidth: 2, borderRadius: 4 },
          label: { show: false },
          data: sources.map(([k, v]) => ({ name: SOURCE_LABEL[k], value: v })),
        },
        {
          type: "bar",
          xAxisIndex: 0,
          yAxisIndex: 0,
          barWidth: 12,
          itemStyle: { color: c.accent, borderRadius: [0, 4, 4, 0] },
          label: { show: true, position: "right", color: c.ink2, fontSize: 10 },
          data: cats.map(([, v]) => v),
        },
      ],
      grid: { left: "56%", right: "6%", top: 28, bottom: 8, containLabel: true },
      xAxis: { type: "value", show: false },
      yAxis: {
        type: "category",
        data: cats.map(([k]) => catalystLabel(k)),
        axisLabel: { color: c.ink2, fontSize: 10 },
        axisLine: { show: false },
        axisTick: { show: false },
      },
    };
  }, [c, run]);
  return (
    <Card title="Where today's signal came from" icon={<Newspaper className="h-4 w-4" />} delay={0.3}>
      <EChart option={option} className="h-72" ariaLabel="Headlines by source and catalysts" />
    </Card>
  );
}
