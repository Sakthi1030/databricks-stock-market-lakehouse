import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ColumnDef } from "@tanstack/react-table";
import { describe, expect, it } from "vitest";
import { DataTable } from "./DataTable";

interface Row {
  symbol: string;
  pctChange: number;
}

const columns: ColumnDef<Row, any>[] = [
  { accessorKey: "symbol", header: "Symbol" },
  { accessorKey: "pctChange", header: "% Change" },
];

const data: Row[] = [
  { symbol: "AAPL", pctChange: 3.5 },
  { symbol: "MSFT", pctChange: 1.2 },
  { symbol: "GOOGL", pctChange: -0.8 },
];

describe("DataTable", () => {
  it("renders one row per data item", () => {
    render(<DataTable data={data} columns={columns} />);
    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("MSFT")).toBeInTheDocument();
    expect(screen.getByText("GOOGL")).toBeInTheDocument();
  });

  it("shows a 'no results' row when data is empty", () => {
    render(<DataTable data={[]} columns={columns} />);
    expect(screen.getByText("No results found.")).toBeInTheDocument();
  });

  it("filters rows via the search box across all columns", async () => {
    const user = userEvent.setup();
    render(<DataTable data={data} columns={columns} searchPlaceholder="Search..." />);

    await user.type(screen.getByPlaceholderText("Search..."), "AAPL");

    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(screen.queryByText("MSFT")).not.toBeInTheDocument();
    expect(screen.queryByText("GOOGL")).not.toBeInTheDocument();
  });

  it("sorts rows when a column header is clicked", async () => {
    const user = userEvent.setup();
    render(<DataTable data={data} columns={columns} />);

    await user.click(screen.getByText("Symbol")); // ascending

    const rows = screen.getAllByRole("row").slice(1); // skip header row
    const firstDataRow = within(rows[0]).getByText(/AAPL|GOOGL|MSFT/);
    expect(firstDataRow.textContent).toBe("AAPL"); // alphabetically first
  });

  it("paginates when data exceeds the page size", () => {
    const manyRows: Row[] = Array.from({ length: 15 }, (_, i) => ({
      symbol: `SYM${i}`,
      pctChange: i,
    }));
    render(<DataTable data={manyRows} columns={columns} pageSize={10} />);

    expect(screen.getByText(/Page 1 of 2/)).toBeInTheDocument();
    expect(screen.getByText("SYM0")).toBeInTheDocument();
    expect(screen.queryByText("SYM10")).not.toBeInTheDocument(); // on page 2, not visible yet
  });
});
