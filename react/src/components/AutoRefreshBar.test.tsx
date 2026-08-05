import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { AutoRefreshBar } from "./AutoRefreshBar";

describe("AutoRefreshBar", () => {
  it("shows 'Refreshing…' while a fetch is in flight, regardless of lastUpdated", () => {
    render(
      <AutoRefreshBar
        lastUpdated={Date.now()}
        isFetching
        onRefresh={vi.fn()}
        autoRefresh={false}
        onAutoRefreshChange={vi.fn()}
      />,
    );
    expect(screen.getByText("Refreshing…")).toBeInTheDocument();
  });

  it("shows nothing yet when there's no lastUpdated timestamp and not fetching", () => {
    render(
      <AutoRefreshBar
        lastUpdated={undefined}
        isFetching={false}
        onRefresh={vi.fn()}
        autoRefresh={false}
        onAutoRefreshChange={vi.fn()}
      />,
    );
    expect(screen.queryByText(/Updated/)).not.toBeInTheDocument();
  });

  it("shows 'Updated just now' immediately after a fresh fetch", () => {
    render(
      <AutoRefreshBar
        lastUpdated={Date.now()}
        isFetching={false}
        onRefresh={vi.fn()}
        autoRefresh={false}
        onAutoRefreshChange={vi.fn()}
      />,
    );
    expect(screen.getByText("Updated just now")).toBeInTheDocument();
  });

  it("calls onRefresh when the refresh button is clicked", async () => {
    const onRefresh = vi.fn();
    const user = userEvent.setup();
    render(
      <AutoRefreshBar
        lastUpdated={Date.now()}
        isFetching={false}
        onRefresh={onRefresh}
        autoRefresh={false}
        onAutoRefreshChange={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: /refresh now/i }));

    expect(onRefresh).toHaveBeenCalledTimes(1);
  });

  it("disables the refresh button while already fetching", () => {
    render(
      <AutoRefreshBar
        lastUpdated={Date.now()}
        isFetching
        onRefresh={vi.fn()}
        autoRefresh={false}
        onAutoRefreshChange={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: /refresh now/i })).toBeDisabled();
  });

  it("calls onAutoRefreshChange when the checkbox is toggled", async () => {
    const onAutoRefreshChange = vi.fn();
    const user = userEvent.setup();
    render(
      <AutoRefreshBar
        lastUpdated={Date.now()}
        isFetching={false}
        onRefresh={vi.fn()}
        autoRefresh={false}
        onAutoRefreshChange={onAutoRefreshChange}
      />,
    );

    await user.click(screen.getByRole("checkbox"));

    expect(onAutoRefreshChange).toHaveBeenCalledWith(true);
  });

  it("reflects the current autoRefresh state in the checkbox", () => {
    render(
      <AutoRefreshBar
        lastUpdated={Date.now()}
        isFetching={false}
        onRefresh={vi.fn()}
        autoRefresh={true}
        onAutoRefreshChange={vi.fn()}
      />,
    );
    expect(screen.getByRole("checkbox")).toBeChecked();
  });
});
