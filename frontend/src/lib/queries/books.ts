import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { API } from "@/lib/api-endpoints";
import type {
  Book,
  BookBorrowingStats,
  BookCreate,
  BookUpdate,
  MessageResponse,
  PaginatedResponse,
} from "@/types";

export interface BookFilters {
  author_id?: string;
  category_id?: string;
  search?: string;
}

export function useBooks(
  skip = 0,
  limit = 100,
  filters?: BookFilters,
  options?: { enabled?: boolean },
  sort?: { key: string; direction: string },
) {
  const safeSearch = filters?.search && filters.search.length <= 200 ? filters.search : undefined;
  const safeFilters = filters ? { ...filters, search: safeSearch } : undefined;
  return useQuery({
    queryKey: ["books", skip, limit, safeFilters, sort],
    queryFn: () => {
      const params = new URLSearchParams({
        skip: String(skip),
        limit: String(limit),
      });
      if (safeFilters?.author_id) params.set("author_id", safeFilters.author_id);
      if (safeFilters?.category_id)
        params.set("category_id", safeFilters.category_id);
      if (safeSearch) params.set("search", safeSearch);
      if (sort) {
        params.set("sort_by", sort.key);
        params.set("order", sort.direction);
      }
      return apiFetch<PaginatedResponse<Book>>(
        `${API.BOOKS.LIST}?${params.toString()}`
      );
    },
    ...options,
  });
}

export function useBook(id: string) {
  return useQuery({
    queryKey: ["books", id],
    queryFn: () => apiFetch<Book>(API.BOOKS.DETAIL(id)),
    enabled: !!id,
  });
}

export function useBookStats(id: string) {
  return useQuery({
    queryKey: ["books", id, "stats"],
    queryFn: () => apiFetch<BookBorrowingStats>(API.BOOKS.STATS(id)),
    enabled: !!id,
  });
}

export function useCreateBook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: BookCreate) =>
      apiFetch<Book>(API.BOOKS.LIST, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["books"] }),
  });
}

export function useUpdateBook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: BookUpdate }) =>
      apiFetch<Book>(API.BOOKS.DETAIL(id), {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["books"] }),
  });
}

export function useDeleteBook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<MessageResponse>(API.BOOKS.DETAIL(id), { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["books"] }),
  });
}
