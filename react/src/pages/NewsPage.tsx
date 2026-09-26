import { Filter, Newspaper, Search } from "lucide-react";
import { useDeferredValue, useMemo, useState } from "react";
import { useNews } from "../api/queries";
import type { NewsSource } from "../api/types";
import { NewsRow, sentimentTone } from "../components/NewsRow";
import { Card, EmptyState, ErrorState, PageSkeleton, Segmented } from "../components/ui";
import { SOURCE_LABEL } from "../utils/format";

type Mood = "all" | "up" | "down";
const SOURCES: (NewsSource | "all")[] = ["all", "nse", "rss", "google_news", "reddit"];

export function NewsPage() {
  const [days, setDays] = useState<"1" | "2" | "5">("2");
  const [source, setSource] = useState<NewsSource | "all">("all");
  const [mood, setMood] = useState<Mood>("all");
  const [minImpact, setMinImpact] = useState(0);
  const [onlyStocks, setOnlyStocks] = useState(true);
  const [query, setQuery] = useState("");
  const q = useDeferredValue(query.trim().toLowerCase());
  const news = useNews(Number(days));

  const counts = useMemo(() => {
    const out: Record<string, number> = { all: 0 };
    (news.data?.data ?? []).forEach((n) => {
      out.all += 1;
      out[n.source] = (out[n.source] ?? 0) + 1;
    });
    return out;
  }, [news.data]);

  const rows = useMemo(
    () =>
      (news.data?.data ?? []).filter(
        (n) =>
          (source === "all" || n.source === source) &&
          (mood === "all" || sentimentTone(n.sentiment) === mood) &&
          n.impact >= minImpact &&
          (!onlyStocks || n.symbols.length > 0) &&
          (!q || n.title.toLowerCase().includes(q) || n.symbols.some((s) => s.toLowerCase().includes(q))),
      ),
    [news.data, source, mood, minImpact, onlyStocks, q],
  );

  if (news.isPending) return <PageSkeleton label="Loading the news feed…" />;
  if (news.isError) return <ErrorState message="Couldn't load the news feed." onRetry={() => news.refetch()} />;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-ink">News feed</h1>
          <p className="mt-1 text-sm text-ink-2">
            Every headline the radar read, tagged with the stocks it's about, its likely next-day impact and the catalyst.
          </p>
        </div>
        <Segmented
          value={days}
          onChange={setDays}
          options={[
            { value: "1", label: "Latest run" },
            { value: "2", label: "2 days" },
            { value: "5", label: "5 days" },
          ]}
        />
      </div>

      <div className="flex flex-wrap gap-2">
        {SOURCES.map((s) => (
          <button
            key={s}
            onClick={() => setSource(s)}
            className={`rounded-full border px-3 py-1.5 text-xs font-medium transition ${
              source === s ? "border-brand bg-brand text-white" : "border-line bg-panel text-ink-2 hover:text-ink"
            }`}
          >
            {s === "all" ? "All sources" : SOURCE_LABEL[s]}
            <span className="num ml-1.5 opacity-70">{counts[s] ?? 0}</span>
          </button>
        ))}
      </div>

      <Card
        padded={false}
        title={`${rows.length} headlines`}
        icon={<Filter className="h-4 w-4" />}
        action={
          <div className="flex flex-wrap items-center justify-end gap-2">
            <Segmented<Mood>
              value={mood}
              onChange={setMood}
              options={[
                { value: "all", label: "All" },
                { value: "up", label: "Bullish" },
                { value: "down", label: "Bearish" },
              ]}
            />
            <Segmented
              value={String(minImpact) as "0" | "2" | "3"}
              onChange={(v) => setMinImpact(Number(v))}
              options={[
                { value: "0", label: "Any impact" },
                { value: "2", label: "Impact 2+" },
                { value: "3", label: "Big only" },
              ]}
            />
          </div>
        }
      >
        <div className="flex flex-wrap items-center gap-3 border-b border-line px-4 py-2.5 sm:px-5">
          <label className="flex flex-1 items-center gap-2 rounded-lg border border-line bg-panel-2 px-3 py-1.5 text-sm">
            <Search className="h-4 w-4 text-ink-3" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search headlines or symbols"
              className="w-full bg-transparent text-ink outline-none placeholder:text-ink-3"
            />
          </label>
          <label className="flex items-center gap-2 text-xs text-ink-2">
            <input type="checkbox" checked={onlyStocks} onChange={(e) => setOnlyStocks(e.target.checked)} className="accent-[var(--brand)]" />
            Only stock-specific
          </label>
        </div>
        {rows.length ? (
          <ul className="divide-y divide-line">
            {rows.slice(0, 200).map((n, i) => (
              <NewsRow key={n.id} n={n} index={i} />
            ))}
          </ul>
        ) : (
          <EmptyState icon={<Newspaper className="h-6 w-6" />} title="No headlines match these filters" />
        )}
      </Card>
    </div>
  );
}
