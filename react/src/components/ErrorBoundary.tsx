import { Component, type ErrorInfo, type ReactNode } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

// A React error boundary must be a class component — there is no hook equivalent for
// componentDidCatch/getDerivedStateFromError. This catches render-time crashes anywhere in
// the tree below it; it's distinct from the per-query ErrorState (that handles failed API
// calls, which never throw during render).
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Unhandled error in component tree:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-50 p-6 text-center dark:bg-slate-950">
          <span className="text-5xl">⚠️</span>
          <h1 className="text-xl font-bold">Something broke.</h1>
          <p className="max-w-md text-sm text-slate-500 dark:text-slate-400">
            {this.state.error.message}
          </p>
          <button
            onClick={() => window.location.assign("/")}
            className="rounded-md bg-brand-blue px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Reload app
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
