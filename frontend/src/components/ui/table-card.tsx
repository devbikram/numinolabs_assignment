import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface TableCardProps {
  children: ReactNode;
  className?: string;
}

export function TableCard({ children, className }: TableCardProps) {
  return (
    <div className={cn("rounded-xl border bg-card shadow-sm overflow-hidden", className)}>
      {children}
    </div>
  );
}
