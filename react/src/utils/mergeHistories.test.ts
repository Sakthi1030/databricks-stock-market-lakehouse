import { describe, expect, it } from "vitest";
import { mergeHistoriesByDate } from "./mergeHistories";

describe("mergeHistoriesByDate", () => {
  it("pivots per-company history arrays into one row per date", () => {
    const result = mergeHistoriesByDate(
      ["AAPL", "MSFT"],
      [
        { data: [{ ingestion_date: "2026-01-01", current_price: 150 }] },
        { data: [{ ingestion_date: "2026-01-01", current_price: 300 }] },
      ],
    );

    expect(result).toEqual([{ date: "2026-01-01", AAPL: 150, MSFT: 300 }]);
  });

  it("sorts rows chronologically regardless of input order", () => {
    const result = mergeHistoriesByDate(
      ["AAPL"],
      [
        {
          data: [
            { ingestion_date: "2026-01-03", current_price: 152 },
            { ingestion_date: "2026-01-01", current_price: 150 },
            { ingestion_date: "2026-01-02", current_price: 151 },
          ],
        },
      ],
    );

    expect(result.map((r) => r.date)).toEqual(["2026-01-01", "2026-01-02", "2026-01-03"]);
  });

  it("leaves a gap (undefined) rather than dropping the row when a company has no data for a date", () => {
    const result = mergeHistoriesByDate(
      ["AAPL", "MSFT"],
      [
        { data: [{ ingestion_date: "2026-01-01", current_price: 150 }] },
        { data: [] }, // MSFT has no data at all
      ],
    );

    expect(result).toEqual([{ date: "2026-01-01", AAPL: 150 }]);
    expect(result[0].MSFT).toBeUndefined();
  });

  it("returns an empty array when no symbols are selected", () => {
    expect(mergeHistoriesByDate([], [])).toEqual([]);
  });

  it("handles a query that hasn't resolved yet (data undefined)", () => {
    const result = mergeHistoriesByDate(["AAPL"], [{ data: undefined }]);
    expect(result).toEqual([]);
  });
});
