import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { API } from "@/lib/api-endpoints";
import type { Category, PaginatedResponse } from "@/types";

export function useCategories() {
  return useQuery({
    queryKey: ["categories"],
    queryFn: () =>
      apiFetch<PaginatedResponse<Category>>(`${API.CATEGORIES.LIST}?skip=0&limit=50`),
  });
}
