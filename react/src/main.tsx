import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "./index.css";
import { App } from "./App.tsx";
import { ThemeProvider } from "./hooks/useTheme.tsx";
import { WatchlistProvider } from "./hooks/useWatchlist.tsx";
import { ErrorBoundary } from "./components/ErrorBoundary.tsx";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000, // Gold refreshes once daily via the scheduled Job — no need to refetch every few seconds.
      retry: 1,
    },
  },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <WatchlistProvider>
            <App />
          </WatchlistProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  </StrictMode>,
);
