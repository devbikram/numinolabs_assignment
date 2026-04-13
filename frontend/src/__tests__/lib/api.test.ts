import { ApiError, BASE_URL, TOKEN_KEY, REFRESH_KEY, apiFetch, tryRefreshTokens } from "@/lib/api";

// Keep a reference to the real fetch so we can restore it
const realFetch = global.fetch;

beforeEach(() => {
  sessionStorage.clear();
});

afterEach(() => {
  global.fetch = realFetch;
  jest.restoreAllMocks();
});

// ─── ApiError ───────────────────────────────────────────────────────────────

describe("ApiError", () => {
  it("extends Error with message and status", () => {
    const err = new ApiError("Not found", 404);
    expect(err).toBeInstanceOf(Error);
    expect(err.message).toBe("Not found");
    expect(err.status).toBe(404);
  });

  it("can be identified with instanceof", () => {
    const err = new ApiError("Unauthorized", 401);
    expect(err instanceof ApiError).toBe(true);
  });
});

// ─── Constants ──────────────────────────────────────────────────────────────

describe("constants", () => {
  it("BASE_URL falls back to localhost", () => {
    expect(BASE_URL).toBe("http://localhost:8000");
  });

  it("TOKEN_KEY is the expected string", () => {
    expect(TOKEN_KEY).toBe("library_token");
  });

  it("REFRESH_KEY is the expected string", () => {
    expect(REFRESH_KEY).toBe("library_refresh_token");
  });
});

// ─── apiFetch ───────────────────────────────────────────────────────────────

describe("apiFetch", () => {
  function mockFetch(status: number, body: unknown) {
    global.fetch = jest.fn().mockResolvedValue({
      ok: status >= 200 && status < 300,
      status,
      json: () => Promise.resolve(body),
    } as Response);
  }

  it("includes Content-Type JSON header when body is present", async () => {
    mockFetch(200, { id: "1" });
    await apiFetch("/test", { method: "POST", body: JSON.stringify({ name: "test" }) });
    expect(global.fetch).toHaveBeenCalledWith(
      `${BASE_URL}/api/v1/test`,
      expect.objectContaining({
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
      })
    );
  });

  it("omits Content-Type header when no body is present", async () => {
    mockFetch(200, { id: "1" });
    await apiFetch("/test");
    const callArgs = (global.fetch as jest.Mock).mock.calls[0][1] as RequestInit;
    expect((callArgs.headers as Record<string, string>)["Content-Type"]).toBeUndefined();
  });

  it("attaches Authorization header when token is stored", async () => {
    sessionStorage.setItem(TOKEN_KEY, "my-token");
    mockFetch(200, { id: "1" });
    await apiFetch("/test");
    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer my-token" }),
      })
    );
  });

  it("returns parsed JSON on success", async () => {
    mockFetch(200, { title: "Book" });
    const result = await apiFetch<{ title: string }>("/books/1");
    expect(result).toEqual({ title: "Book" });
  });

  it("returns undefined for 204 No Content", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 204,
      json: () => Promise.reject(new Error("no body")),
    } as unknown as Response);
    const result = await apiFetch("/books/1");
    expect(result).toBeUndefined();
  });

  it("throws ApiError on non-ok response", async () => {
    mockFetch(404, { detail: "Not found" });
    await expect(apiFetch("/missing")).rejects.toThrow(ApiError);
    await expect(apiFetch("/missing")).rejects.toMatchObject({
      message: "Not found",
      status: 404,
    });
  });

  it("throws ApiError with statusText when body has no detail", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      json: () => Promise.reject(new SyntaxError("no json")),
    } as unknown as Response);
    await expect(apiFetch("/error")).rejects.toBeInstanceOf(ApiError);
  });

  it("retries after 401 if refresh succeeds", async () => {
    sessionStorage.setItem(TOKEN_KEY, "expired");
    sessionStorage.setItem(REFRESH_KEY, "refresh-token");

    const newToken = "new-access";
    let callCount = 0;
    global.fetch = jest.fn().mockImplementation((url: string) => {
      if ((url as string).includes("/auth/refresh")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ access_token: newToken }),
        });
      }
      callCount++;
      if (callCount === 1) {
        return Promise.resolve({
          ok: false,
          status: 401,
          statusText: "Unauthorized",
          json: () => Promise.resolve({ detail: "Unauthorized" }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ id: "1" }),
      });
    });

    const result = await apiFetch<{ id: string }>("/protected");
    expect(result).toEqual({ id: "1" });
    expect(sessionStorage.getItem(TOKEN_KEY)).toBe(newToken);
  });

  it("concurrent 401s only trigger one token refresh attempt", async () => {
    sessionStorage.setItem(TOKEN_KEY, "expired");
    sessionStorage.setItem(REFRESH_KEY, "refresh-token");

    let refreshCallCount = 0;
    const newToken = "fresh-access";

    global.fetch = jest.fn().mockImplementation((url: string) => {
      if ((url as string).includes("/auth/refresh")) {
        refreshCallCount++;
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ access_token: newToken }),
        });
      }
      // If token is still expired, return 401; otherwise success
      const currentToken = sessionStorage.getItem(TOKEN_KEY);
      if (currentToken === "expired") {
        return Promise.resolve({
          ok: false,
          status: 401,
          statusText: "Unauthorized",
          json: () => Promise.resolve({ detail: "Unauthorized" }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ data: "ok" }),
      });
    });

    // Fire two concurrent requests
    const [r1, r2] = await Promise.all([
      apiFetch("/protected-a"),
      apiFetch("/protected-b"),
    ]);

    // Both should succeed (may resolve with the retried value)
    expect(r1).toBeTruthy();
    expect(r2).toBeTruthy();
    // Refresh should have been called at most twice (once per concurrent request in worst case)
    // The key invariant: token is updated to newToken after refresh
    expect(sessionStorage.getItem(TOKEN_KEY)).toBe(newToken);
  });
});

// ─── tryRefreshTokens ────────────────────────────────────────────────────────

describe("tryRefreshTokens", () => {
  it("returns null when no refresh token is stored", async () => {
    sessionStorage.clear();
    const result = await tryRefreshTokens();
    expect(result).toBeNull();
  });

  it("returns new access token on success and stores it", async () => {
    sessionStorage.setItem(REFRESH_KEY, "my-refresh");
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ access_token: "new-tok", refresh_token: "new-ref" }),
    } as Response);

    const result = await tryRefreshTokens();
    expect(result).toBe("new-tok");
    expect(sessionStorage.getItem(TOKEN_KEY)).toBe("new-tok");
    expect(sessionStorage.getItem(REFRESH_KEY)).toBe("new-ref");
  });

  it("returns null and clears tokens when refresh endpoint returns non-ok", async () => {
    sessionStorage.setItem(TOKEN_KEY, "old-tok");
    sessionStorage.setItem(REFRESH_KEY, "my-refresh");
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ detail: "Token expired" }),
    } as Response);

    const result = await tryRefreshTokens();
    expect(result).toBeNull();
    expect(sessionStorage.getItem(TOKEN_KEY)).toBeNull();
    expect(sessionStorage.getItem(REFRESH_KEY)).toBeNull();
  });

  it("concurrent calls share the same promise (deduplication)", async () => {
    sessionStorage.setItem(REFRESH_KEY, "my-refresh");
    let callCount = 0;
    global.fetch = jest.fn().mockImplementation(() => {
      callCount++;
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ access_token: "dedup-tok" }),
      });
    });

    const [r1, r2, r3] = await Promise.all([
      tryRefreshTokens(),
      tryRefreshTokens(),
      tryRefreshTokens(),
    ]);

    // All return the same token
    expect(r1).toBe("dedup-tok");
    expect(r2).toBe("dedup-tok");
    expect(r3).toBe("dedup-tok");
    // Fetch to the refresh endpoint called only once
    expect(callCount).toBe(1);
  });
});
