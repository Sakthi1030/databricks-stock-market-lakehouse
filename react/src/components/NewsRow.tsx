import { motion } from "framer-motion";
import { ExternalLink, FileText, Globe, MessageCircle, Newspaper } from "lucide-react";
import { Link } from "react-router-dom";
import type { NewsItem, NewsSource } from "../api/types";
import { catalystLabel, timeAgo } from "../utils/format";
import { Chip } from "./ui";

const SOURCE_ICON: Record<NewsSource, typeof Newspaper> = {
  nse: FileText,
  rss: Newspaper,
  google_news: Globe,
  reddit: MessageCircle,
};

export function sentimentTone(s: number) {
  return s >= 0.25 ? "up" : s <= -0.25 ? "down" : "neutral";
}

function ImpactDots({ impact }: { impact: number }) {
  return (
    <span className="inline-flex items-center gap-0.5" title={`Likely next-day impact: ${impact}/3`}>
      {[1, 2, 3].map((i) => (
        <span key={i} className={`h-1.5 w-1.5 rounded-full ${i <= impact ? "bg-accent" : "bg-line"}`} />
      ))}
    </span>
  );
}

export function NewsRow({ n, index = 0 }: { n: NewsItem; index?: number }) {
  const Icon = SOURCE_ICON[n.source] ?? Newspaper;
  const t = sentimentTone(n.sentiment);
  return (
    <motion.li
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: Math.min(index, 12) * 0.025 }}
      className="flex gap-3 px-4 py-3.5 transition hover:bg-panel-2/60 sm:px-5"
    >
      <div className="mt-0.5 rounded-lg bg-panel-2 p-2 text-ink-3">
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-ink-3">
          <span className="font-medium text-ink-2">{n.outlet}</span>
          <span>·</span>
          <time dateTime={n.published}>{timeAgo(n.published)}</time>
          {n.category && n.source === "nse" && (
            <>
              <span>·</span>
              <span>{n.category}</span>
            </>
          )}
        </div>
        <a
          href={n.url}
          target="_blank"
          rel="noreferrer"
          className="group mt-0.5 flex items-start gap-1 text-sm font-medium leading-snug text-ink hover:text-brand"
        >
          <span>{n.title}</span>
          <ExternalLink className="mt-0.5 h-3 w-3 shrink-0 opacity-0 transition group-hover:opacity-100" />
        </a>
        {n.reason && <p className="mt-1 text-xs text-ink-2">{n.reason}</p>}
        <div className="mt-2 flex flex-wrap items-center gap-1.5">
          <Chip tone={t}>{t === "up" ? "Bullish" : t === "down" ? "Bearish" : "Neutral"}</Chip>
          {n.catalyst && n.catalyst !== "other" && <Chip tone="brand">{catalystLabel(n.catalyst)}</Chip>}
          <ImpactDots impact={n.impact} />
          {n.symbols.map((s) => (
            <Link
              key={s}
              to={`/stock/${encodeURIComponent(s)}`}
              className="rounded-md border border-line px-1.5 py-0.5 font-mono text-[11px] font-bold text-ink-2 hover:border-brand/40 hover:text-brand"
            >
              {s}
            </Link>
          ))}
        </div>
      </div>
    </motion.li>
  );
}
