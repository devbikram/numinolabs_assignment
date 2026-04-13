import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type {
  Borrowing,
  BorrowingCreate,
  BorrowStatus,
  PaginatedResponse,
} from "@/types";

export function useBorrowings(
  skip = 0,
  limit = 100,
  status?: BorrowStatus,
  search?: string,
  dateFrom?: string,
  dateTo?: string,
  sort?: { key: string; direction: string },
) {
  const safeSearch = search && search.length <= 200 ? search : undefined;
  return useQuery({
    queryKey: ["borrowings", skip, limit, status, safeSearch, dateFrom, dateTo, sort],
    queryFn: () => {
      const params = new URLSearchParams({
        skip: String(skip),
        limit: String(limit),
      });
      if (status) params.set("status", status);
      if (safeSearch) params.set("search", safeSearch);
      if (dateFrom) params.set("date_from", dateFrom);
      if (dateTo) params.set("date_to", dateTo);
      if (sort) {
        params.set("sort_by", sort.key);
        params.set("order", sort.direction);
      }
      return apiFetch<PaginatedResponse<Borrowing>>(
        `/borrows/?${params.toString()}`
      );
    },
  });
}

export function useMemberBorrowings(memberId: string, skip = 0, limit = 20) {
  return useQuery({
    queryKey: ["borrowings", "member", memberId, skip, limit],
    queryFn: () => {
      const params = new URLSearchParams({
        member_id: memberId,
        skip: String(skip),
        limit: String(limit),
      });
      return apiFetch<PaginatedResponse<Borrowing>>(
        `/borrows/?${params.toString()}`
      );
    },
    enabled: !!memberId,
  });
}

export function useBookBorrowings(bookId: string, skip = 0, limit = 20) {
  return useQuery({
    queryKey: ["borrowings", "book", bookId, skip, limit],
    queryFn: () => {
      const params = new URLSearchParams({
        book_id: bookId,
        skip: String(skip),
        limit: String(limit),
      });
      return apiFetch<PaginatedResponse<Borrowing>>(
        `/borrows/?${params.toString()}`
      );
    },
    enabled: !!bookId,
  });
}

export function useCreateBorrowing() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: BorrowingCreate) =>
      apiFetch<Borrowing>("/borrows/", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["borrowings"] });
      queryClient.invalidateQueries({ queryKey: ["books"] });
    },
  });
}

export function useReturnBook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (borrowingId: string) =>
      apiFetch<Borrowing>(`/borrows/${borrowingId}/return`, {
        method: "PATCH",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["borrowings"] });
      queryClient.invalidateQueries({ queryKey: ["books"] });
    },
  });
}
