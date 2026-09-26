/** NSE session clock in IST, independent of the viewer's own time zone. */

const IST_OFFSET_MIN = 330;

/** Wall-clock parts of `now` in IST. */
export function istParts(now: Date) {
  const ist = new Date(now.getTime() + (IST_OFFSET_MIN + now.getTimezoneOffset()) * 60_000);
  return { day: ist.getDay(), minutes: ist.getHours() * 60 + ist.getMinutes(), ist };
}

export type MarketPhase = "pre-open" | "open" | "closed";

export function marketPhase(now: Date): MarketPhase {
  const { day, minutes } = istParts(now);
  if (day === 0 || day === 6) return "closed";
  if (minutes >= 9 * 60 + 15 && minutes < 15 * 60 + 30) return "open";
  if (minutes >= 9 * 60 && minutes < 9 * 60 + 15) return "pre-open";
  return "closed";
}

/** Milliseconds until the next weekday 14:00 IST alert (holidays aren't known client-side). */
export function msUntilNextAlert(now: Date): number {
  const { ist } = istParts(now);
  const target = new Date(ist);
  target.setHours(14, 0, 0, 0);
  if (ist >= target) target.setDate(target.getDate() + 1);
  while (target.getDay() === 0 || target.getDay() === 6) target.setDate(target.getDate() + 1);
  return target.getTime() - ist.getTime();
}

export function formatCountdown(ms: number): string {
  const total = Math.floor(ms / 1000);
  const d = Math.floor(total / 86400);
  const h = Math.floor((total % 86400) / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  if (d > 0) return `${d}d ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m ${String(s).padStart(2, "0")}s`;
}
