import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { API } from "@/lib/api-endpoints";
import type { Author, AuthorStats, PaginatedResponse } from "@/types";

export function useAuthors(search?: string) {
  const safeSearch = search && search.length <= 200 ? search : undefined;
  return useQuery({
    queryKey: ["authors", { search: safeSearch }],
    queryFn: () =>
      apiFetch<PaginatedResponse<Author>>(
        `${API.AUTHORS.LIST}?skip=0&limit=50${safeSearch ? `&search=${encodeURIComponent(safeSearch)}` : ""}`
      ),
  });
}

export function useAuthor(id: string) {
  return useQuery({
    queryKey: ["authors", id],
    queryFn: () => apiFetch<Author>(API.AUTHORS.DETAIL(id)),
    enabled: !!id,
  });
}

export function useAuthorStats(id: string) {
  return useQuery({
    queryKey: ["authors", id, "stats"],
    queryFn: () => apiFetch<AuthorStats>(API.AUTHORS.STATS(id)),
    enabled: !!id,
  });
}

export function useCreateAuthor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string }) =>
      apiFetch<Author>(API.AUTHORS.LIST, { method: "POST", body: JSON.stringify(data) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["authors"] });
    },
  });
}
