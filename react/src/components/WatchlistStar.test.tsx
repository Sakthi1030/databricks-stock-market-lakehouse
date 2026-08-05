import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { WatchlistProvider } from "../hooks/useWatchlist";
import { WatchlistStar } from "./WatchlistStar";

function renderStar(symbol = "AAPL") {
  return render(
    <WatchlistProvider>
      <WatchlistStar symbol={symbol} />
    </WatchlistProvider>,
  );
}

describe("WatchlistStar", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("shows an unfilled star and aria-pressed=false when not watched", () => {
    renderStar();
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("aria-pressed", "false");
    expect(button).toHaveTextContent("☆");
  });

  it("toggles to a filled star and aria-pressed=true when clicked", async () => {
    const user = userEvent.setup();
    renderStar();

    await user.click(screen.getByRole("button"));

    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("aria-pressed", "true");
    expect(button).toHaveTextContent("★");
  });

  it("toggles back when clicked twice", async () => {
    const user = userEvent.setup();
    renderStar();
    const button = screen.getByRole("button");

    await user.click(button);
    await user.click(button);

    expect(button).toHaveAttribute("aria-pressed", "false");
  });
});
