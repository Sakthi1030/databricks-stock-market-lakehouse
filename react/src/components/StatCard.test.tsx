import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatCard } from "./StatCard";

describe("StatCard", () => {
  it("renders the label and value", () => {
    render(<StatCard label="Gainers" value="7" color="green" />);

    expect(screen.getByText("Gainers")).toBeInTheDocument();
    expect(screen.getByText("7")).toBeInTheDocument();
  });

  it("applies the background color class matching the color prop", () => {
    const { container } = render(<StatCard label="Losers" value="3" color="red" />);
    expect(container.firstChild).toHaveClass("bg-brand-red");
  });

  it("renders an icon when provided", () => {
    render(<StatCard label="Companies" value="10" color="blue" icon={<span data-testid="icon">*</span>} />);
    expect(screen.getByTestId("icon")).toBeInTheDocument();
  });
});
