import { BellRing, Code2, Info, Moon, Newspaper, Radar, Sun, Target } from "lucide-react";
import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { useNow } from "../hooks/useNow";
import { useTheme } from "../hooks/useTheme";
import { formatCountdown, marketPhase, msUntilNextAlert } from "../utils/market";

const NAV = [
  { to: "/", label: "Radar", icon: Radar, end: true },
  { to: "/news", label: "News", icon: Newspaper },
  { to: "/track-record", label: "Track record", icon: Target },
  { to: "/how-it-works", label: "How it works", icon: Info },
];

function Logo() {
  return (
    <div className="flex items-center gap-2.5">
      <div className="relative h-9 w-9 overflow-hidden rounded-xl bg-[#0b1224] ring-1 ring-white/10">
        <div className="radar-sweep absolute inset-0 rounded-full" />
        <div className="absolute inset-[7px] rounded-full border border-sky-900" />
        <div className="absolute left-[23px] top-[10px] h-1.5 w-1.5 rounded-full bg-emerald-400" />
        <div className="absolute left-1/2 top-1/2 h-1 w-1 -translate-x-1/2 -translate-y-1/2 rounded-full bg-white" />
      </div>
      <div className="leading-tight">
        <div className="text-sm font-bold tracking-tight text-ink">NSE News Radar</div>
        <div className="text-[11px] text-ink-3">news → next-day +1%</div>
      </div>
    </div>
  );
}

function MarketStatus() {
  const now = useNow(1000);
  const phase = marketPhase(now);
  const label = { open: "Market open", "pre-open": "Pre-open", closed: "Market closed" }[phase];
  return (
    <div className="flex items-center gap-2 text-xs sm:gap-3">
      <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-panel px-2.5 py-1 font-medium text-ink-2">
        <span className={`live-dot relative h-2 w-2 rounded-full ${phase === "open" ? "text-up bg-up" : "text-ink-3 bg-ink-3"}`} />
        {label}
      </span>
      <span
        className="hidden items-center gap-1.5 rounded-full border border-accent/30 bg-accent/10 px-2.5 py-1 font-medium text-accent sm:inline-flex"
        title="The email goes out at 2:00 PM IST on trading days"
      >
        <BellRing className="h-3.5 w-3.5" />
        <span className="num">Next alert in {formatCountdown(msUntilNextAlert(now))}</span>
      </span>
    </div>
  );
}

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  return (
    <button
      onClick={toggleTheme}
      aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
      className="rounded-lg border border-line bg-panel p-2 text-ink-2 transition hover:text-ink"
    >
      {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </button>
  );
}

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen lg:pl-60">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-line bg-panel/80 px-4 py-5 backdrop-blur lg:flex">
        <Logo />
        <nav className="mt-8 space-y-1">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition ${
                  isActive ? "bg-brand/10 text-brand" : "text-ink-2 hover:bg-panel-2 hover:text-ink"
                }`
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto space-y-3 rounded-xl border border-line bg-panel-2 p-3 text-[11px] leading-relaxed text-ink-3">
          <p>Signals from public news, not investment advice. Always use a stop-loss.</p>
          <a
            href="https://github.com/Sakthi1030/databricks-stock-market-lakehouse"
            className="inline-flex items-center gap-1.5 font-medium text-ink-2 hover:text-ink"
          >
            <Code2 className="h-3.5 w-3.5" /> Source on GitHub
          </a>
        </div>
      </aside>

      {/* Top bar */}
      <header className="sticky top-0 z-20 flex items-center justify-between gap-3 border-b border-line bg-bg/80 px-4 py-3 backdrop-blur sm:px-6">
        <div className="lg:hidden">
          <Logo />
        </div>
        <div className="hidden lg:block" />
        <div className="flex items-center gap-2 sm:gap-3">
          <MarketStatus />
          <ThemeToggle />
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 pb-28 pt-5 sm:px-6 lg:pb-12">{children}</main>

      {/* Mobile tab bar */}
      <nav className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-4 border-t border-line bg-panel/95 pb-[env(safe-area-inset-bottom)] backdrop-blur lg:hidden">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex flex-col items-center gap-1 py-2.5 text-[11px] font-medium ${isActive ? "text-brand" : "text-ink-3"}`
            }
          >
            <Icon className="h-5 w-5" />
            {label.split(" ")[0]}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
