import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Category, PaginatedResponse } from "@/types";

export function useCategories() {
  return useQuery({
    queryKey: ["categories"],
    queryFn: () =>
      apiFetch<PaginatedResponse<Category>>("/categories/?skip=0&limit=50"),
  });
}
