export const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export const TOKEN_KEY = "library_token";
export const REFRESH_KEY = "library_refresh_token";

import { API } from "@/lib/api-endpoints";

let refreshPromise: Promise<string | null> | null = null;

const DEFAULT_TIMEOUT_MS = 15_000;

export async function tryRefreshTokens(signal?: AbortSignal): Promise<string | null> {
  if (typeof window === "undefined") return null;
  if (refreshPromise) return refreshPromise;
  refreshPromise = (async () => {
    const refreshToken = sessionStorage.getItem(REFRESH_KEY);
    if (!refreshToken) return null;
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
      // If a parent signal is provided, abort when it fires
      signal?.addEventListener("abort", () => controller.abort(), { once: true });
      const res = await fetch(`${BASE_URL}/api/v1${API.AUTH.REFRESH}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      if (!res.ok) {
        sessionStorage.removeItem(TOKEN_KEY);
        sessionStorage.removeItem(REFRESH_KEY);
        return null;
      }
      const { access_token, refresh_token: newRefresh } = await res.json();
      sessionStorage.setItem(TOKEN_KEY, access_token);
      if (newRefresh) sessionStorage.setItem(REFRESH_KEY, newRefresh);
      return access_token;
    } catch {
      return null;
    }
  })();
  try {
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}

export async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit & { _skipRefresh?: boolean }
): Promise<T> {
  const url = `${BASE_URL}/api/v1${endpoint}`;
  const token = typeof window !== "undefined" ? sessionStorage.getItem(TOKEN_KEY) : null;
  const { _skipRefresh, ...fetchOptions } = options ?? {};
  const headers: Record<string, string> = {
    ...(fetchOptions.body !== undefined ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(fetchOptions.headers as Record<string, string> | undefined),
  };

  // Apply a timeout if the caller didn't provide their own signal
  let timeoutId: ReturnType<typeof setTimeout> | undefined;
  let signal = fetchOptions.signal;
  if (!signal) {
    const controller = new AbortController();
    timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
    signal = controller.signal;
  }

  const res = await fetch(url, { ...fetchOptions, headers, signal }).finally(() => {
    if (timeoutId) clearTimeout(timeoutId);
  });

  if (res.status === 401 && !_skipRefresh) {
    const newToken = await tryRefreshTokens();
    if (newToken) {
      return apiFetch<T>(endpoint, { ...(options ?? {}), _skipRefresh: true });
    }
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(body.detail || "Something went wrong", res.status);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}
