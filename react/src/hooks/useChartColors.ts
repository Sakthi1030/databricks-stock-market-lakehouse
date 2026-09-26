import { useMemo } from "react";
import { useTheme } from "./useTheme";

export interface ChartColors {
  ink: string;
  ink2: string;
  ink3: string;
  line: string;
  panel: string;
  panel2: string;
  brand: string;
  accent: string;
  up: string;
  down: string;
  series: string[];
}

/** The CSS theme tokens resolved to literal colors, for ECharts (which can't read CSS variables). */
export function useChartColors(): ChartColors {
  const { theme } = useTheme();
  return useMemo(() => {
    const css = getComputedStyle(document.documentElement);
    const v = (name: string) => css.getPropertyValue(name).trim();
    const dark = theme === "dark";
    return {
      ink: v("--ink"),
      ink2: v("--ink-2"),
      ink3: v("--ink-3"),
      line: v("--line"),
      panel: v("--panel"),
      panel2: v("--panel-2"),
      brand: v("--brand"),
      accent: v("--accent"),
      up: v("--up"),
      down: v("--down"),
      series: dark
        ? ["#60a5fa", "#fbbf24", "#34d399", "#a78bfa", "#f472b6", "#38bdf8"]
        : ["#2563eb", "#d97706", "#059669", "#7c3aed", "#db2777", "#0284c7"],
    };
    // theme is the trigger: the variables change when the .dark class flips.
  }, [theme]);
}
