import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface MetaFieldProps {
  label: string;
  value: ReactNode;
  /** Apply font-mono to the value */
  mono?: boolean;
}

export function MetaField({ label, value, mono = false }: MetaFieldProps) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={cn("text-sm", mono && "font-mono")}>{value}</p>
    </div>
  );
}
