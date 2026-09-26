import { motion } from "framer-motion";
import { AlertTriangle, Database, FileJson, RefreshCw, Star } from "lucide-react";
import type { ReactNode } from "react";
import type { DataSource } from "../api/types";
import { useWatchlist } from "../hooks/useWatchlist";

export function Card({
  title,
  icon,
  action,
  children,
  className = "",
  delay = 0,
  padded = true,
}: {
  title?: ReactNode;
  icon?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  delay?: number;
  padded?: boolean;
}) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: [0.22, 1, 0.36, 1] }}
      className={`rounded-2xl border border-line bg-panel shadow-card ${className}`}
    >
      {title && (
        <header className="flex items-center justify-between gap-3 border-b border-line px-4 py-3 sm:px-5">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-ink">
            {icon && <span className="text-ink-3">{icon}</span>}
            {title}
          </h2>
          {action}
        </header>
      )}
      <div className={padded ? "p-4 sm:p-5" : ""}>{children}</div>
    </motion.section>
  );
}

export function Skeleton({ className = "h-4 w-full" }: { className?: string }) {
  return <div className={`animate-pulse rounded-lg bg-panel-2 ${className}`} />;
}

export function PageSkeleton({ label }: { label: string }) {
  return (
    <div className="space-y-5" aria-busy="true" aria-label={label}>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} className="h-28" />
        ))}
      </div>
      <Skeleton className="h-24" />
      <div className="grid gap-4 lg:grid-cols-3">
        {Array.from({ length: 3 }, (_, i) => (
          <Skeleton key={i} className="h-72" />
        ))}
      </div>
      <p className="text-center text-sm text-ink-3">
        {label} The first visit after a quiet spell can take up to a minute while the server wakes up.
      </p>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-down/30 bg-down/5 px-6 py-14 text-center">
      <AlertTriangle className="h-9 w-9 text-down" />
      <p className="max-w-md text-sm font-medium text-ink">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 rounded-lg bg-down px-4 py-1.5 text-sm font-medium text-white hover:opacity-90"
        >
          <RefreshCw className="h-4 w-4" /> Try again
        </button>
      )}
    </div>
  );
}

export function EmptyState({ icon, title, children }: { icon: ReactNode; title: string; children?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-2 px-6 py-12 text-center">
      <div className="mb-1 rounded-2xl bg-panel-2 p-3 text-ink-3">{icon}</div>
      <p className="font-semibold text-ink">{title}</p>
      {children && <div className="max-w-md text-sm text-ink-2">{children}</div>}
    </div>
  );
}

/** Tells the viewer whether numbers came from the Databricks Gold marts or the raw-zone fallback. */
export function SourceBadge({ source }: { source?: DataSource }) {
  if (!source) return null;
  const gold = source === "databricks";
  return (
    <span
      title={gold ? "Served from the Databricks Gold tables" : "Served from the raw zone while the warehouse wakes up"}
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${
        gold ? "border-brand/30 bg-brand/10 text-brand" : "border-line bg-panel-2 text-ink-2"
      }`}
    >
      {gold ? <Database className="h-3 w-3" /> : <FileJson className="h-3 w-3" />}
      {gold ? "Databricks Gold" : "Raw zone"}
    </span>
  );
}

export function Chip({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "up" | "down" | "accent" | "brand" }) {
  const tones = {
    neutral: "bg-panel-2 text-ink-2 border-line",
    up: "bg-up/10 text-up border-up/25",
    down: "bg-down/10 text-down border-down/25",
    accent: "bg-accent/10 text-accent border-accent/25",
    brand: "bg-brand/10 text-brand border-brand/25",
  };
  return (
    <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2 py-0.5 text-[11px] font-medium ${tones[tone]}`}>
      {children}
    </span>
  );
}

export function WatchStar({ symbol }: { symbol: string }) {
  const { isWatched, toggle } = useWatchlist();
  const on = isWatched(symbol);
  return (
    <button
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        toggle(symbol);
      }}
      aria-label={on ? `Remove ${symbol} from watchlist` : `Add ${symbol} to watchlist`}
      aria-pressed={on}
      className="rounded-md p-1 text-ink-3 transition hover:bg-panel-2 hover:text-accent"
    >
      <Star className={`h-4 w-4 ${on ? "fill-accent text-accent" : ""}`} />
    </button>
  );
}

export function Segmented<T extends string>({
  value,
  options,
  onChange,
}: {
  value: T;
  options: { value: T; label: string }[];
  onChange: (v: T) => void;
}) {
  return (
    <div className="inline-flex rounded-lg border border-line bg-panel-2 p-0.5">
      {options.map((o) => (
        <button
          key={o.value}
          onClick={() => onChange(o.value)}
          className={`rounded-md px-2.5 py-1 text-xs font-medium transition ${
            value === o.value ? "bg-panel text-ink shadow-card" : "text-ink-2 hover:text-ink"
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
