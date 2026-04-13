import React from "react";
import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthProvider, useAuth } from "@/providers/auth-provider";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock("@/lib/api", () => ({
  BASE_URL: "http://localhost",
  TOKEN_KEY: "access_token",
  REFRESH_KEY: "refresh_token",
  tryRefreshTokens: jest.fn().mockResolvedValue(null),
}));

// ── Helpers ──────────────────────────────────────────────────────────────────

const mockUser = {
  id: "u1",
  email: "admin@example.com",
  full_name: "Admin User",
  role: "admin" as const,
};

function TestConsumer() {
  const { user, isLoading, login, logout } = useAuth();
  if (isLoading) return <p>loading</p>;
  return (
    <div>
      {user ? <p data-testid="user">{user.email}</p> : <p data-testid="no-user">no user</p>}
      <button onClick={() => login("admin@example.com", "password")}>login</button>
      <button onClick={logout}>logout</button>
    </div>
  );
}

function Wrapper({ children }: { children: React.ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

// ── Setup ────────────────────────────────────────────────────────────────────

beforeEach(() => {
  sessionStorage.clear();
  jest.clearAllMocks();
  mockPush.mockReset();
});

// ── Tests ────────────────────────────────────────────────────────────────────

describe("AuthProvider", () => {
  it("starts in loading state then shows no-user when session is empty", async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: false });
    render(<TestConsumer />, { wrapper: Wrapper });

    expect(screen.getByText("loading")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId("no-user")).toBeInTheDocument());
  });

  it("login success sets user and redirects to /dashboard", async () => {
    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ access_token: "tok1", refresh_token: "ref1" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser,
      });

    render(<TestConsumer />, { wrapper: Wrapper });
    await waitFor(() => screen.getByText("login"));

    await act(async () => {
      await userEvent.click(screen.getByText("login"));
    });

    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("admin@example.com"));
    expect(mockPush).toHaveBeenCalledWith("/dashboard");
  });

  it("login failure throws a sanitized error (no server detail leaked)", async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: "No active account found with the given credentials" }),
    });

    let caughtMessage = "";
    function LoginTester() {
      const { login, isLoading } = useAuth();
      if (isLoading) return <p>loading</p>;
      return (
        <button
          onClick={async () => {
            try {
              await login("bad@example.com", "wrong");
            } catch (e) {
              caughtMessage = e instanceof Error ? e.message : String(e);
            }
          }}
        >
          try-login
        </button>
      );
    }

    render(<LoginTester />, { wrapper: Wrapper });
    await waitFor(() => screen.getByText("try-login"));

    await act(async () => {
      await userEvent.click(screen.getByText("try-login"));
    });

    expect(caughtMessage).toBe("Invalid email or password");
    expect(caughtMessage).not.toContain("No active account");
  });

  it("logout clears user state", async () => {
    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ access_token: "tok2", refresh_token: "ref2" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser,
      })
      // logout server call (best-effort)
      .mockResolvedValue({ ok: true });

    render(<TestConsumer />, { wrapper: Wrapper });
    await waitFor(() => screen.getByText("login"));

    await act(async () => {
      await userEvent.click(screen.getByText("login"));
    });
    await waitFor(() => screen.getByTestId("user"));

    await act(async () => {
      await userEvent.click(screen.getByText("logout"));
    });

    await waitFor(() => expect(screen.getByTestId("no-user")).toBeInTheDocument());
  });
});
