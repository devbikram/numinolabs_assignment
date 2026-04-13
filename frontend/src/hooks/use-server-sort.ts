import { useState, useCallback } from "react";

export type SortDirection = "asc" | "desc";

export interface SortState {
  key: string;
  direction: SortDirection;
}

export function useServerSort(defaultKey: string, defaultDirection: SortDirection = "asc") {
  const [sort, setSort] = useState<SortState>({ key: defaultKey, direction: defaultDirection });

  const toggleSort = useCallback((key: string) => {
    setSort((prev) =>
      prev.key === key
        ? { key, direction: prev.direction === "asc" ? "desc" : "asc" }
        : { key, direction: "asc" }
    );
  }, []);

  return { sort, toggleSort } as const;
}
