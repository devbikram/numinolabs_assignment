import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { API } from "@/lib/api-endpoints";
import type {
  Member,
  MemberBorrowingStats,
  MemberCreate,
  MemberUpdate,
  MessageResponse,
  PaginatedResponse,
} from "@/types";

export function useMembers(
  skip = 0,
  limit = 100,
  search?: string,
  options?: { enabled?: boolean },
  sort?: { key: string; direction: string },
) {
  const safeSearch = search && search.length <= 200 ? search : undefined;
  return useQuery({
    queryKey: ["members", skip, limit, safeSearch, sort],
    queryFn: () => {
      const params = new URLSearchParams({
        skip: String(skip),
        limit: String(limit),
      });
      if (safeSearch) params.set("search", safeSearch);
      if (sort) {
        params.set("sort_by", sort.key);
        params.set("order", sort.direction);
      }
      return apiFetch<PaginatedResponse<Member>>(
        `${API.MEMBERS.LIST}?${params.toString()}`
      );
    },
    ...options,
  });
}

export function useMember(id: string) {
  return useQuery({
    queryKey: ["members", id],
    queryFn: () => apiFetch<Member>(API.MEMBERS.DETAIL(id)),
    enabled: !!id,
  });
}

export function useMemberStats(id: string) {
  return useQuery({
    queryKey: ["members", id, "stats"],
    queryFn: () => apiFetch<MemberBorrowingStats>(API.MEMBERS.STATS(id)),
    enabled: !!id,
  });
}

export function useCreateMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: MemberCreate) =>
      apiFetch<Member>(API.MEMBERS.LIST, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["members"] }),
  });
}

export function useUpdateMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: MemberUpdate }) =>
      apiFetch<Member>(API.MEMBERS.DETAIL(id), {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["members"] }),
  });
}

export function useDeleteMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<MessageResponse>(API.MEMBERS.DETAIL(id), { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["members"] }),
  });
}
