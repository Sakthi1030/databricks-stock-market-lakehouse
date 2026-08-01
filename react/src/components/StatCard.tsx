import type { ReactNode } from "react";

type StatCardColor = "blue" | "purple" | "green" | "red" | "amber" | "teal";

const COLOR_CLASSES: Record<StatCardColor, string> = {
  blue: "bg-brand-blue",
  purple: "bg-brand-purple",
  green: "bg-brand-green",
  red: "bg-brand-red",
  amber: "bg-brand-amber",
  teal: "bg-brand-teal",
};

interface StatCardProps {
  label: string;
  value: string;
  color: StatCardColor;
  icon?: ReactNode;
}

export function StatCard({ label, value, color, icon }: StatCardProps) {
  return (
    <div
      className={`flex flex-col justify-between rounded-xl p-4 text-white shadow-sm ${COLOR_CLASSES[color]}`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-white/80">{label}</span>
        {icon && <span className="text-white/90">{icon}</span>}
      </div>
      <span className="mt-2 text-2xl font-bold">{value}</span>
    </div>
  );
}
