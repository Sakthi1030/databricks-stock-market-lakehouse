import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ThemeProvider, useTheme } from "./useTheme";

function mockMatchMedia(prefersDark: boolean) {
  vi.stubGlobal(
    "matchMedia",
    vi.fn().mockImplementation((query: string) => ({
      matches: query === "(prefers-color-scheme: dark)" && prefersDark,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  );
}

describe("useTheme", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.classList.remove("dark");
  });

  it("defaults to the system preference when nothing is stored", () => {
    mockMatchMedia(true);
    const { result } = renderHook(() => useTheme(), { wrapper: ThemeProvider });

    expect(result.current.theme).toBe("dark");
  });

  it("defaults to light when the system has no dark preference and nothing is stored", () => {
    mockMatchMedia(false);
    const { result } = renderHook(() => useTheme(), { wrapper: ThemeProvider });

    expect(result.current.theme).toBe("light");
  });

  it("prefers a stored value over the system preference", () => {
    mockMatchMedia(true); // system says dark...
    window.localStorage.setItem("theme", "light"); // ...but the user already chose light

    const { result } = renderHook(() => useTheme(), { wrapper: ThemeProvider });

    expect(result.current.theme).toBe("light");
  });

  it("toggleTheme flips the theme and persists it to localStorage", () => {
    mockMatchMedia(false);
    const { result } = renderHook(() => useTheme(), { wrapper: ThemeProvider });

    act(() => result.current.toggleTheme());

    expect(result.current.theme).toBe("dark");
    expect(window.localStorage.getItem("theme")).toBe("dark");
  });

  it("applies the 'dark' class to the document root when theme is dark", () => {
    mockMatchMedia(false);
    const { result } = renderHook(() => useTheme(), { wrapper: ThemeProvider });

    act(() => result.current.toggleTheme());

    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("throws when used outside a ThemeProvider", () => {
    // Deliberately not wrapping in ThemeProvider — this is the guard rail that catches a
    // consumer forgetting to add the provider, at dev time instead of a silent undefined bug.
    expect(() => renderHook(() => useTheme())).toThrow("useTheme must be used within a ThemeProvider");
  });
});
