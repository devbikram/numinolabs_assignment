import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Author, AuthorStats, PaginatedResponse } from "@/types";

export function useAuthors(search?: string) {
  const safeSearch = search && search.length <= 200 ? search : undefined;
  return useQuery({
    queryKey: ["authors", { search: safeSearch }],
    queryFn: () =>
      apiFetch<PaginatedResponse<Author>>(
        `/authors/?skip=0&limit=50${safeSearch ? `&search=${encodeURIComponent(safeSearch)}` : ""}`
      ),
  });
}

export function useAuthor(id: string) {
  return useQuery({
    queryKey: ["authors", id],
    queryFn: () => apiFetch<Author>(`/authors/${id}`),
    enabled: !!id,
  });
}

export function useAuthorStats(id: string) {
  return useQuery({
    queryKey: ["authors", id, "stats"],
    queryFn: () => apiFetch<AuthorStats>(`/authors/${id}/stats`),
    enabled: !!id,
  });
}

export function useCreateAuthor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string }) =>
      apiFetch<Author>("/authors/", { method: "POST", body: JSON.stringify(data) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["authors"] });
    },
  });
}
