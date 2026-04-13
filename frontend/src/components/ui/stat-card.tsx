import type { ReactNode } from "react";

interface StatCardProps {
  value: ReactNode;
  label: string;
  /** Compact variant: smaller card, used in author detail page */
  compact?: boolean;
}

export function StatCard({ value, label, compact = false }: StatCardProps) {
  if (compact) {
    return (
      <div className="rounded-lg border p-4 text-center">
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-xs text-muted-foreground">{label}</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-card p-5 text-center shadow-sm">
      <p className="text-3xl font-extrabold">{value}</p>
      <p className="text-sm font-medium text-muted-foreground mt-1">{label}</p>
    </div>
  );
}
