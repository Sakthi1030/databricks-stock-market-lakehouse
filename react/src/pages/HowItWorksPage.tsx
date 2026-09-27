import { motion } from "framer-motion";
import {
  BellRing,
  Bot,
  Clock,
  Database,
  FileText,
  GitBranch,
  Globe,
  LayoutDashboard,
  Mail,
  MessageCircle,
  Newspaper,
  Server,
  ShieldCheck,
  Workflow,
} from "lucide-react";
import type { ReactNode } from "react";
import { Card } from "../components/ui";

function Node({ icon, title, sub, tone = "brand", delay = 0 }: { icon: ReactNode; title: string; sub: string; tone?: "brand" | "accent" | "up"; delay?: number }) {
  const ring = { brand: "bg-brand/10 text-brand", accent: "bg-accent/10 text-accent", up: "bg-up/10 text-up" }[tone];
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="flex items-start gap-3 rounded-xl border border-line bg-panel-2/60 p-3"
    >
      <span className={`rounded-lg p-2 ${ring}`}>{icon}</span>
      <div>
        <div className="text-sm font-semibold text-ink">{title}</div>
        <div className="text-xs leading-relaxed text-ink-2">{sub}</div>
      </div>
    </motion.div>
  );
}

function Stage({ n, title, children }: { n: number; title: string; children: ReactNode }) {
  return (
    <div className="relative">
      <div className="mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-ink-3">
        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-accent text-[10px] text-white">{n}</span>
        {title}
      </div>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

const TIMELINE = [
  { time: "1:07 PM", title: "Read the news", text: "NSE filings, Economic Times, Business Standard, Livemint, Business Today, Moneycontrol and Times Now (via Google News), and three Indian stock subreddits." },
  { time: "1:10 PM", title: "Gemini reads every headline", text: "Which NSE companies it is about, bullish or bearish, how big the likely next-day effect is, and the catalyst type." },
  { time: "1:58 PM", title: "Price snapshot", text: "Live price, today's move, volume vs normal, liquidity, and how often this stock's next-day high has reached +1%." },
  { time: "2:00 PM", title: "Email with the picks", text: "Top five by score, each with the +1% sell target and the headlines behind it." },
  { time: "3:52 PM", title: "Grade yesterday", text: "Did yesterday's picks, and every other candidate, reach +1% today? The answer feeds the track record." },
  { time: "4:00 PM", title: "Databricks refresh", text: "Bronze, Silver and Gold Delta tables rebuild from the raw zone; the site's analytics read Gold." },
];

export function HowItWorksPage() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-ink">How it works</h1>
        <p className="mt-1 max-w-3xl text-sm text-ink-2">
          A strategy many retail investors follow: find stocks with good news, buy in delivery before the close, and sell the
          next day once they're up 1%. This project automates the news reading, scores each stock, emails the picks at 2 PM,
          and keeps an honest record of whether they worked.
        </p>
      </div>

      <Card title="Architecture" icon={<Workflow className="h-4 w-4" />}>
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          <Stage n={1} title="Sources">
            <Node icon={<FileText className="h-4 w-4" />} title="NSE filings" sub="Orders, results, acquisitions" delay={0.05} />
            <Node icon={<Newspaper className="h-4 w-4" />} title="News sites (RSS)" sub="ET, Business Standard, Mint, Business Today" delay={0.1} />
            <Node icon={<Globe className="h-4 w-4" />} title="Google News" sub="Moneycontrol, Times Now, topic searches" delay={0.15} />
            <Node icon={<MessageCircle className="h-4 w-4" />} title="Reddit" sub="IndianStreetBets and two more" delay={0.2} />
          </Stage>
          <Stage n={2} title="2 PM pipeline">
            <Node icon={<GitBranch className="h-4 w-4" />} title="GitHub Actions" sub="Scheduled on trading days; Python" tone="accent" delay={0.25} />
            <Node icon={<Bot className="h-4 w-4" />} title="Gemini" sub="Tags stocks, sentiment, impact, catalyst" tone="accent" delay={0.3} />
            <Node icon={<Mail className="h-4 w-4" />} title="Email alert" sub="Top picks with +1% targets" tone="accent" delay={0.35} />
          </Stage>
          <Stage n={3} title="Lakehouse">
            <Node icon={<FileText className="h-4 w-4" />} title="Raw zone" sub="JSON on the repo's data branch" delay={0.4} />
            <Node icon={<Database className="h-4 w-4" />} title="Databricks Bronze → Silver → Gold" sub="PySpark + Delta Lake, Unity Catalog; daily job" delay={0.45} />
          </Stage>
          <Stage n={4} title="Serving">
            <Node icon={<Server className="h-4 w-4" />} title="FastAPI on Render" sub="Gold via SQL Warehouse, raw-zone fallback" tone="up" delay={0.5} />
            <Node icon={<LayoutDashboard className="h-4 w-4" />} title="This site (Vercel)" sub="React, ECharts, AG Grid" tone="up" delay={0.55} />
          </Stage>
        </div>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="A trading day" icon={<Clock className="h-4 w-4" />}>
          <ol className="relative space-y-4 border-l border-line pl-5">
            {TIMELINE.map((t, i) => (
              <motion.li key={t.time} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.05 * i }}>
                <span className="absolute -left-[5px] mt-1.5 h-2.5 w-2.5 rounded-full border-2 border-panel bg-accent" />
                <div className="num text-xs font-bold text-accent">{t.time} IST</div>
                <div className="text-sm font-semibold text-ink">{t.title}</div>
                <p className="text-xs leading-relaxed text-ink-2">{t.text}</p>
              </motion.li>
            ))}
          </ol>
        </Card>

        <Card title="How the score is built" icon={<BellRing className="h-4 w-4" />}>
          <div className="space-y-3 text-sm text-ink-2">
            <div className="rounded-xl bg-panel-2 p-3 font-mono text-xs text-ink">
              score = 0.45·news + 0.25·reach + 0.15·momentum + 0.15·volume
            </div>
            <ul className="space-y-2 text-xs leading-relaxed">
              <li><b className="text-ink">News</b>: each headline's sentiment × impact (0 to 3) × source trust (NSE 1.0, news sites 0.8, Google News 0.7, Reddit 0.5), halving every 12 hours, plus a bonus when several outlets agree.</li>
              <li><b className="text-ink">Reach</b>: over the last 120 sessions, how often this stock's next-day high was at least 1% above the previous close.</li>
              <li><b className="text-ink">Momentum</b>: best when the stock is already up 0.5 to 3% by 2 PM; weak when falling or stretched.</li>
              <li><b className="text-ink">Volume</b>: today's volume so far against its 20-day average, adjusted for the time of day.</li>
            </ul>
            <div className="flex items-start gap-2 rounded-xl border border-line p-3 text-xs">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-up" />
              <span>
                Guards: skipped if it trades under ₹1 crore a day (hard to exit at +1%), is below ₹10, or is already up more than
                6% (chasing). Signals come from public news, not advice: a +1% high is common on many days, so the track record
                compares picks with other candidates to show whether the score adds anything.
              </span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
