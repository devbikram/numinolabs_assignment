/** Centralised API endpoint constants — use these instead of inline string literals. */
export const API = {
  AUTH: {
    LOGIN: "/auth/login",
    LOGOUT: "/auth/logout",
    REFRESH: "/auth/refresh",
    ME: "/auth/me",
  },
  BOOKS: {
    LIST: "/books/",
    DETAIL: (id: string) => `/books/${id}` as const,
    STATS: (id: string) => `/books/${id}/stats` as const,
  },
  AUTHORS: {
    LIST: "/authors/",
    DETAIL: (id: string) => `/authors/${id}` as const,
    STATS: (id: string) => `/authors/${id}/stats` as const,
  },
  BORROWS: {
    LIST: "/borrows/",
    RETURN: (id: string) => `/borrows/${id}/return` as const,
  },
  CATEGORIES: {
    LIST: "/categories/",
  },
  MEMBERS: {
    LIST: "/members/",
    DETAIL: (id: string) => `/members/${id}` as const,
    STATS: (id: string) => `/members/${id}/stats` as const,
  },
  DASHBOARD: {
    STATS: "/dashboard/stats",
  },
} as const;
