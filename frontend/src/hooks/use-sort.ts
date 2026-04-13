import { useMemo, useState } from "react";

export type SortDirection = "asc" | "desc";

export interface SortConfig<K extends string> {
  key: K;
  direction: SortDirection;
}

export function useSort<T, K extends string>(
  items: T[],
  defaultKey: K,
  defaultDirection: SortDirection = "asc"
) {
  const [sort, setSort] = useState<SortConfig<K>>({
    key: defaultKey,
    direction: defaultDirection,
  });

  function toggleSort(key: K) {
    setSort((prev) =>
      prev.key === key
        ? { key, direction: prev.direction === "asc" ? "desc" : "asc" }
        : { key, direction: "asc" }
    );
  }

  const sorted = useMemo(() => {
    const copy = [...items];
    copy.sort((a, b) => {
      const aVal = (a as Record<string, unknown>)[sort.key];
      const bVal = (b as Record<string, unknown>)[sort.key];

      // nulls always go last
      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return 1;
      if (bVal == null) return -1;

      let cmp = 0;
      if (typeof aVal === "string" && typeof bVal === "string") {
        cmp = aVal.localeCompare(bVal, undefined, { sensitivity: "base" });
      } else if (typeof aVal === "number" && typeof bVal === "number") {
        cmp = aVal - bVal;
      } else {
        cmp = String(aVal).localeCompare(String(bVal));
      }

      return sort.direction === "asc" ? cmp : -cmp;
    });
    return copy;
  }, [items, sort]);

  return { sorted, sort, toggleSort } as const;
}
