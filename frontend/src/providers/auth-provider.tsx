"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { BASE_URL, TOKEN_KEY, REFRESH_KEY, tryRefreshTokens } from "@/lib/api";
import { ROUTES } from "@/lib/routes";

const AUTH_COOKIE = "library_authed";

function setAuthCookie() {
  document.cookie = `${AUTH_COOKIE}=1; path=/; SameSite=Lax`;
}

function clearAuthCookie() {
  document.cookie = `${AUTH_COOKIE}=; path=/; max-age=0`;
}

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "manager";
}

interface AuthCtx {
  user: AuthUser | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  // Fetch /auth/me to validate token and get user
  const fetchMe = useCallback(async (t: string, signal?: AbortSignal) => {
    try {
      const res = await fetch(`${BASE_URL}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${t}` },
        signal,
      });
      if (!res.ok) throw new Error();
      return (await res.json()) as AuthUser;
    } catch {
      return null;
    }
  }, []);

  // On mount, check for stored token
  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;

    async function init() {
      const stored = sessionStorage.getItem(TOKEN_KEY);
      if (!stored) {
        // No access token — try a silent refresh before giving up
        const newToken = await tryRefreshTokens(controller.signal);
        if (!cancelled && newToken) {
          const u = await fetchMe(newToken, controller.signal);
          if (!cancelled && u) {
            setToken(newToken);
            setUser(u);
            setAuthCookie();
          }
        }
      } else {
        const u = await fetchMe(stored, controller.signal);
        if (cancelled) return;
        if (u) {
          setToken(stored);
          setUser(u);
          setAuthCookie();
        } else {
          // Token may have expired — try refresh before clearing
          const newToken = await tryRefreshTokens(controller.signal);
          if (!cancelled && newToken) {
            const refreshedUser = await fetchMe(newToken, controller.signal);
            if (!cancelled && refreshedUser) {
              setToken(newToken);
              setUser(refreshedUser);
              setAuthCookie();
              setIsLoading(false);
              return;
            }
          }
          if (!cancelled) sessionStorage.removeItem(TOKEN_KEY);
          if (!cancelled) clearAuthCookie();
        }
      }
      if (!cancelled) setIsLoading(false);
    }

    init().catch(() => {
      if (!cancelled) setIsLoading(false);
    });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [fetchMe]);

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await fetch(`${BASE_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        // Do not propagate server detail to avoid leaking information (email enumeration)
        throw new Error("Invalid email or password");
      }
      const { access_token, refresh_token } = await res.json();
      sessionStorage.setItem(TOKEN_KEY, access_token);
      if (refresh_token) sessionStorage.setItem(REFRESH_KEY, refresh_token);
      setToken(access_token);
      const u = await fetchMe(access_token);
      if (!u) throw new Error("Failed to load user profile");
      setUser(u);
      setAuthCookie();
      router.push(ROUTES.DASHBOARD);
    },
    [fetchMe, router]
  );

  const logout = useCallback(() => {
    const accessToken = sessionStorage.getItem(TOKEN_KEY);
    const refreshToken = sessionStorage.getItem(REFRESH_KEY);
    // Clear local state immediately so the UI reflects logout without waiting on network
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(REFRESH_KEY);
    clearAuthCookie();
    setToken(null);
    setUser(null);
    router.push(ROUTES.LOGIN);
    // Best-effort server-side token revocation (non-blocking, with AbortController timeout)
    if (accessToken) {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      fetch(`${BASE_URL}/api/v1/auth/logout`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(refreshToken ? { refresh_token: refreshToken } : {}),
        signal: controller.signal,
      })
        .catch(() => {})
        .finally(() => clearTimeout(timeoutId));
    }
  }, [router]);

  const value = useMemo(
    () => ({ user, token, isLoading, login, logout }),
    [user, token, isLoading, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
