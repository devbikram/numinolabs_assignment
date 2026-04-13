import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import { TableHead } from "@/components/ui/table";
import { cn } from "@/lib/utils";
import type { SortDirection } from "@/hooks/use-server-sort";

interface SortableHeaderProps {
  label: string;
  sortKey: string;
  currentKey: string;
  direction: SortDirection;
  onSort: (key: string) => void;
  className?: string;
}

export function SortableHeader({
  label,
  sortKey,
  currentKey,
  direction,
  onSort,
  className,
}: SortableHeaderProps) {
  const isActive = currentKey === sortKey;

  return (
    <TableHead
      className={cn("cursor-pointer select-none hover:bg-muted/50 focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none rounded-sm", className)}
      tabIndex={0}
      aria-sort={isActive ? (direction === "asc" ? "ascending" : "descending") : "none"}
      onClick={() => onSort(sortKey)}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onSort(sortKey)}
    >
      <div className="flex items-center gap-1">
        {label}
        {isActive ? (
          direction === "asc" ? (
            <ArrowUp className="h-3.5 w-3.5" />
          ) : (
            <ArrowDown className="h-3.5 w-3.5" />
          )
        ) : (
          <ArrowUpDown className="h-3.5 w-3.5 text-muted-foreground/50" />
        )}
      </div>
    </TableHead>
  );
}
