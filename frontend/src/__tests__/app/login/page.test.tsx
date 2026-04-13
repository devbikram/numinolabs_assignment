import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import LoginPage from "@/app/login/page";

const mockLogin = jest.fn();
jest.mock("@/providers/auth-provider", () => ({
  useAuth: () => ({ login: mockLogin }),
}));

describe("LoginPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the Library Manager heading", () => {
    render(<LoginPage />);
    expect(screen.getByText("Library Manager")).toBeInTheDocument();
  });

  it("renders email and password inputs", () => {
    render(<LoginPage />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it("renders Sign in button", () => {
    render(<LoginPage />);
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });

  it("calls login with email and password on valid submit", async () => {
    mockLogin.mockResolvedValue(undefined);
    render(<LoginPage />);
    await userEvent.type(screen.getByLabelText(/email/i), "admin@library.com");
    await userEvent.type(screen.getByLabelText(/password/i), "secret");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
    expect(mockLogin).toHaveBeenCalledWith("admin@library.com", "secret");
  });

  it("displays error message when login fails", async () => {
    mockLogin.mockRejectedValue(new Error("Invalid credentials"));
    render(<LoginPage />);
    await userEvent.type(screen.getByLabelText(/email/i), "bad@example.com");
    await userEvent.type(screen.getByLabelText(/password/i), "wrong");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
    expect(await screen.findByText("Invalid credentials")).toBeInTheDocument();
  });

  it("shows Signing in... and disables button while submitting", async () => {
    let resolveLogin: () => void;
    mockLogin.mockReturnValue(
      new Promise<void>((res) => {
        resolveLogin = res;
      })
    );
    render(<LoginPage />);
    await userEvent.type(screen.getByLabelText(/email/i), "admin@library.com");
    await userEvent.type(screen.getByLabelText(/password/i), "secret");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
    expect(await screen.findByRole("button", { name: /signing in/i })).toBeDisabled();
    resolveLogin!();
  });
});
