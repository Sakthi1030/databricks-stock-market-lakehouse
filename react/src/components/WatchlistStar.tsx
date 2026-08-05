import { useWatchlist } from "../hooks/useWatchlist";

export function WatchlistStar({ symbol }: { symbol: string }) {
  const { isWatched, toggle } = useWatchlist();
  const watched = isWatched(symbol);

  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        e.preventDefault();
        toggle(symbol);
      }}
      aria-label={watched ? `Remove ${symbol} from watchlist` : `Add ${symbol} to watchlist`}
      aria-pressed={watched}
      className="text-lg leading-none transition-colors"
      title={watched ? "Remove from watchlist" : "Add to watchlist"}
    >
      <span className={watched ? "text-brand-amber" : "text-slate-300 hover:text-slate-400 dark:text-slate-600"}>
        {watched ? "★" : "☆"}
      </span>
    </button>
  );
}
