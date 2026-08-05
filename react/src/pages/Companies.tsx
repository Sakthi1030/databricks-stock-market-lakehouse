import { useMemo } from "react";
import { useCompanies, useLatestQuotes } from "../api/queries";
import { CompanyGrid, type CompanyGridRow } from "../components/CompanyGrid";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ErrorState } from "../components/ErrorState";

export function Companies() {
  const companies = useCompanies();
  const quotes = useLatestQuotes();

  const rows = useMemo<CompanyGridRow[]>(() => {
    if (!companies.data) return [];
    const quoteBySymbol = new Map((quotes.data ?? []).map((q) => [q.symbol, q]));
    return companies.data.map((c) => ({
      symbol: c.symbol,
      name: c.name,
      industry: c.industry,
      market_cap_musd: c.market_cap_musd,
      current_price: quoteBySymbol.get(c.symbol)?.current_price ?? null,
      pct_change: quoteBySymbol.get(c.symbol)?.pct_change ?? null,
    }));
  }, [companies.data, quotes.data]);

  if (companies.isPending) return <LoadingSpinner label="Loading companies..." />;
  if (companies.isError)
    return <ErrorState message="Couldn't load companies." onRetry={() => companies.refetch()} />;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Companies</h1>
      <CompanyGrid data={rows} />
    </div>
  );
}
