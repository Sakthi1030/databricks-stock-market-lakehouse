import { describe, expect, it } from "vitest";
import { marketMood } from "./mood";

const q = (change_pct: number, sparkline: number[]) => ({ price: sparkline[sparkline.length - 1], change_pct, sparkline });
const rising = Array.from({ length: 22 }, (_, i) => 100 + i);
const falling = Array.from({ length: 22 }, (_, i) => 130 - i);

describe("marketMood", () => {
  it("is green in a rising market on an up day", () => {
    expect(marketMood(q(0.6, rising), q(0.4, rising))?.mood).toBe("green");
  });
  it("is red in a falling market", () => {
    expect(marketMood(q(-0.4, falling), q(-0.2, falling))?.mood).toBe("red");
  });
  it("is red on a sharp drop even in an uptrend", () => {
    expect(marketMood(q(-1.3, rising))?.mood).toBe("red");
  });
  it("is amber when signals disagree", () => {
    expect(marketMood(q(-0.3, rising), q(-0.2, rising))?.mood).toBe("amber");
  });
  it("needs enough history", () => {
    expect(marketMood(q(1, [1, 2, 3]))).toBeNull();
  });
});
