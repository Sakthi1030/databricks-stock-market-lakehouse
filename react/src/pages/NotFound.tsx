import { Link } from "react-router-dom";

export function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-24 text-center">
      <span className="text-6xl font-bold text-brand-blue">404</span>
      <p className="text-slate-500 dark:text-slate-400">This page doesn't exist.</p>
      <Link to="/" className="mt-2 rounded-md bg-brand-blue px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
        Back to Dashboard
      </Link>
    </div>
  );
}
