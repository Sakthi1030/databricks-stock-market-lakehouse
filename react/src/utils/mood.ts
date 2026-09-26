import type { IndexQuote } from "../api/types";

export type Mood = "green" | "amber" | "red";

export interface MoodCheck {
  label: string;
  ok: boolean;
  detail: string;
}

export interface MarketMood {
  mood: Mood;
  headline: string;
  advice: string;
  checks: MoodCheck[];
}

const avg = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / xs.length;

/**
 * A simple traffic light for "is today a good day to buy for tomorrow?", from NIFTY 50 alone:
 * today's move, its trend vs the 20-day average, and the last 5 sessions. Each check votes ±1.
 * Buying a news pick into a falling market is how a +1% target turns into a stop-loss.
 */
export function marketMood(nifty: IndexQuote | undefined, bank?: IndexQuote): MarketMood | null {
  if (!nifty || nifty.sparkline.length < 6) return null;
  const closes = nifty.sparkline;
  const last = closes[closes.length - 1];
  const ma = avg(closes.slice(-20));
  const fiveAgo = closes[closes.length - 6];
  const week = (last / fiveAgo - 1) * 100;
  const checks: MoodCheck[] = [
    { label: "Nifty today", ok: nifty.change_pct >= 0, detail: `${nifty.change_pct >= 0 ? "+" : ""}${nifty.change_pct.toFixed(2)}%` },
    { label: "vs 20-day avg", ok: last >= ma, detail: `${last >= ma ? "+" : ""}${((last / ma - 1) * 100).toFixed(1)}%` },
    { label: "Last 5 days", ok: week >= 0, detail: `${week >= 0 ? "+" : ""}${week.toFixed(1)}%` },
  ];
  if (bank) checks.push({ label: "Bank Nifty", ok: bank.change_pct >= 0, detail: `${bank.change_pct >= 0 ? "+" : ""}${bank.change_pct.toFixed(2)}%` });

  const votes = checks.reduce((s, c) => s + (c.ok ? 1 : -1), 0);
  const sharpDrop = nifty.change_pct <= -1;
  const mood: Mood = sharpDrop || votes <= -2 ? "red" : votes >= 2 ? "green" : "amber";
  return {
    mood,
    checks,
    headline: { green: "Good day to buy", amber: "Be selective", red: "Stay cautious" }[mood],
    advice: {
      green: "The market is supporting moves. Picks with strong news have the wind behind them.",
      amber: "Mixed market. Stick to the top one or two picks and size positions smaller.",
      red: "The market is falling. Even good news often gets sold; consider sitting today out.",
    }[mood],
  };
}
