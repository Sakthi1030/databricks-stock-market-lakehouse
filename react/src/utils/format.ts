import type { NewsSource } from "../api/types";

const inr = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2, minimumFractionDigits: 2 });
const int = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });

export const rupees = (v: number | null | undefined) => (v == null ? "–" : `₹${inr.format(v)}`);
export const number = (v: number | null | undefined, digits = 0) =>
  v == null ? "–" : digits ? v.toFixed(digits) : int.format(v);
export const pct = (v: number | null | undefined, digits = 2, signed = true) =>
  v == null ? "–" : `${signed && v > 0 ? "+" : ""}${v.toFixed(digits)}%`;
export const share = (v: number | null | undefined) => (v == null ? "–" : `${Math.round(v * 100)}%`);

export const tone = (v: number | null | undefined) =>
  v == null || v === 0 ? "text-ink-2" : v > 0 ? "text-up" : "text-down";

const IST = "Asia/Kolkata";
export const istDate = (iso: string, opts: Intl.DateTimeFormatOptions = { weekday: "long", day: "numeric", month: "long" }) =>
  new Date(iso.length === 10 ? `${iso}T12:00:00+05:30` : iso).toLocaleDateString("en-IN", { timeZone: IST, ...opts });
export const istTime = (iso: string) =>
  new Date(iso).toLocaleTimeString("en-IN", { timeZone: IST, hour: "numeric", minute: "2-digit" });
export const shortDate = (iso: string) => istDate(iso, { day: "numeric", month: "short" });

export function timeAgo(iso: string, now = Date.now()) {
  const s = Math.max(0, (now - new Date(iso).getTime()) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

export const SOURCE_LABEL: Record<NewsSource, string> = {
  nse: "NSE filings",
  rss: "News sites",
  google_news: "Google News",
  reddit: "Reddit",
};

const CATALYST_LABEL: Record<string, string> = {
  order_win: "Order win",
  results: "Results",
  upgrade: "Upgrade",
  downgrade: "Downgrade",
  acquisition: "Acquisition",
  fund_raise: "Fund raise",
  buyback_dividend: "Buyback / dividend",
  approval: "Approval",
  expansion: "Expansion",
  partnership: "Partnership",
  management: "Management",
  legal_regulatory: "Legal / regulatory",
  block_deal: "Block deal",
  buzz: "Reddit buzz",
  macro: "Macro",
  other: "Other",
  none: "No catalyst",
};
export const catalystLabel = (c: string) => CATALYST_LABEL[c] ?? c.replace(/_/g, " ");
