import { motion } from "framer-motion";
import type { ReactNode } from "react";
import type { ScoreParts } from "../api/types";
import { useCountUp } from "../hooks/useCountUp";

/** Lightweight SVG sparkline with a soft area fill; colored by direction over the window. */
export function Sparkline({ values, className = "h-10 w-28", strokeWidth = 1.8 }: { values: number[]; className?: string; strokeWidth?: number }) {
  if (values.length < 2) return <div className={className} />;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const w = 100;
  const h = 32;
  const pts = values.map((v, i) => [(i / (values.length - 1)) * w, h - 2 - ((v - min) / span) * (h - 4)]);
  const d = pts.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)}`).join(" ");
  const up = values[values.length - 1] >= values[0];
  const color = up ? "var(--up)" : "var(--down)";
  const id = `spark-${up ? "u" : "d"}`;
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className={className} aria-hidden>
      <defs>
        <linearGradient id={id} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.28" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={`${d} L${w},${h} L0,${h} Z`} fill={`url(#${id})`} />
      <path d={d} fill="none" stroke={color} strokeWidth={strokeWidth} vectorEffect="non-scaling-stroke" strokeLinejoin="round" />
    </svg>
  );
}

/** Radial 0-100 score, drawn in on mount. */
export function ScoreRing({ score, size = 64, delay = 0 }: { score: number; size?: number; delay?: number }) {
  const r = 26;
  const c = 2 * Math.PI * r;
  const shown = useCountUp(score, delay) ?? 0;
  const color = score >= 60 ? "var(--up)" : score >= 45 ? "var(--accent)" : "var(--ink-3)";
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg viewBox="0 0 64 64" className="h-full w-full -rotate-90">
        <circle cx="32" cy="32" r={r} fill="none" stroke="var(--line)" strokeWidth="6" />
        <motion.circle
          cx="32"
          cy="32"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: c * (1 - score / 100) }}
          transition={{ duration: 1.1, delay, ease: [0.16, 1, 0.3, 1] }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="num text-lg font-bold leading-none text-ink">{Math.round(shown)}</span>
        <span className="text-[9px] font-medium uppercase tracking-wider text-ink-3">score</span>
      </div>
    </div>
  );
}

const PARTS: { key: keyof ScoreParts; label: string; hint: string }[] = [
  { key: "news", label: "News", hint: "Sentiment × impact × source trust, fading with age" },
  { key: "reach", label: "Reach", hint: "How often the next-day high reached +1% (last 120 days)" },
  { key: "momentum", label: "Momentum", hint: "Today's move so far: rising, but not stretched" },
  { key: "volume", label: "Volume", hint: "Today's volume vs its 20-day average" },
];

export function ScoreBars({ scores, delay = 0 }: { scores: ScoreParts; delay?: number }) {
  return (
    <div className="space-y-1.5">
      {PARTS.map((p, i) => (
        <div key={p.key} className="flex items-center gap-2 text-[11px]" title={p.hint}>
          <span className="w-16 shrink-0 text-ink-3">{p.label}</span>
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-panel-2">
            <motion.div
              className="h-full rounded-full bg-brand"
              initial={{ width: 0 }}
              animate={{ width: `${Math.max(2, scores[p.key])}%` }}
              transition={{ duration: 0.9, delay: delay + i * 0.06, ease: [0.16, 1, 0.3, 1] }}
            />
          </div>
          <span className="num w-7 text-right font-medium text-ink-2">{Math.round(scores[p.key])}</span>
        </div>
      ))}
    </div>
  );
}

export function KpiCard({
  label,
  value,
  format = (v) => String(Math.round(v)),
  sub,
  icon,
  index = 0,
  accent = "brand",
}: {
  label: string;
  value: number | null | undefined;
  format?: (v: number) => string;
  sub?: ReactNode;
  icon: ReactNode;
  index?: number;
  accent?: "brand" | "accent" | "up" | "down";
}) {
  const shown = useCountUp(value, 0.1 + index * 0.06);
  const ring = { brand: "bg-brand/10 text-brand", accent: "bg-accent/10 text-accent", up: "bg-up/10 text-up", down: "bg-down/10 text-down" };
  return (
    <motion.div
      initial={{ opacity: 0, y: 14, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.45, delay: index * 0.06, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -3 }}
      className="rounded-2xl border border-line bg-panel p-4 shadow-card"
    >
      <div className="flex items-start justify-between gap-2">
        <span className="text-xs font-medium text-ink-2">{label}</span>
        <span className={`rounded-lg p-1.5 ${ring[accent]}`}>{icon}</span>
      </div>
      <div className="num mt-2 text-2xl font-bold tracking-tight text-ink sm:text-[28px]">
        {shown == null ? "–" : format(shown)}
      </div>
      {sub && <div className="mt-1 text-xs text-ink-3">{sub}</div>}
    </motion.div>
  );
}
