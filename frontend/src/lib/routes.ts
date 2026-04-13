/** Centralised route constants — use these instead of inline string literals. */
export const ROUTES = {
  HOME: "/",
  LOGIN: "/login",
  DASHBOARD: "/dashboard",
  BOOKS: "/books",
  BOOK: (id: string) => `/books/${id}` as const,
  MEMBERS: "/members",
  MEMBER: (id: string) => `/members/${id}` as const,
  BORROWINGS: "/borrowings",
  AUTHOR: (id: string) => `/authors/${id}` as const,
} as const;

export const PUBLIC_PATHS = ["/login"] as const;

export const DEFAULT_PAGE_SIZE = 20;
