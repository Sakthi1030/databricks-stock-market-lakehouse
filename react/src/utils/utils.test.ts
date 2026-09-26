import { describe, expect, it } from "vitest";
import { catalystLabel, pct, rupees, share, tone } from "./format";
import { formatCountdown, marketPhase, msUntilNextAlert } from "./market";

// Instants given in UTC; IST is UTC+5:30.
const at = (iso: string) => new Date(iso);

describe("market clock (IST)", () => {
  it("knows the session", () => {
    expect(marketPhase(at("2026-09-28T04:00:00Z"))).toBe("open"); // Mon 09:30 IST
    expect(marketPhase(at("2026-09-28T03:35:00Z"))).toBe("pre-open"); // Mon 09:05 IST
    expect(marketPhase(at("2026-09-28T10:05:00Z"))).toBe("closed"); // Mon 15:35 IST
    expect(marketPhase(at("2026-09-26T05:00:00Z"))).toBe("closed"); // Saturday
  });

  it("counts down to the next weekday 2 PM", () => {
    expect(msUntilNextAlert(at("2026-09-28T08:00:00Z"))).toBe(30 * 60_000); // Mon 13:30 -> 14:00
    expect(msUntilNextAlert(at("2026-09-25T09:00:00Z"))).toBe(71.5 * 3600_000); // Fri 14:30 -> Mon 14:00
    expect(msUntilNextAlert(at("2026-09-26T08:30:00Z"))).toBe(48 * 3600_000); // Sat 14:00 -> Mon 14:00
  });

  it("formats countdowns", () => {
    expect(formatCountdown(90_061_000)).toBe("1d 1h 1m");
    expect(formatCountdown(3_720_000)).toBe("1h 2m");
    expect(formatCountdown(65_000)).toBe("1m 05s");
  });
});

describe("formatting", () => {
  it("formats rupees and percentages", () => {
    expect(rupees(123456.5)).toBe("₹1,23,456.50");
    expect(rupees(null)).toBe("–");
    expect(pct(1.234)).toBe("+1.23%");
    expect(pct(-0.5, 1)).toBe("-0.5%");
    expect(share(0.791)).toBe("79%");
  });

  it("picks tones and labels", () => {
    expect(tone(2)).toBe("text-up");
    expect(tone(-1)).toBe("text-down");
    expect(tone(0)).toBe("text-ink-2");
    expect(catalystLabel("order_win")).toBe("Order win");
    expect(catalystLabel("new_thing")).toBe("new thing");
  });
});
