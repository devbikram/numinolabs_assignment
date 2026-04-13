import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import MembersPage from "@/app/members/page";

jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));

jest.mock("next/link", () => {
  const MockLink = ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  );
  MockLink.displayName = "Link";
  return MockLink;
});

jest.mock("@/lib/queries/members", () => ({
  useMembers: () => ({ data: { items: [], total: 0 }, isLoading: false }),
  useDeleteMember: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useCreateMember: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useUpdateMember: () => ({ mutateAsync: jest.fn(), isPending: false }),
}));

describe("MembersPage", () => {
  it("renders Members page header", () => {
    render(<MembersPage />);
    expect(screen.getByText("Members")).toBeInTheDocument();
  });

  it("renders Add Member button", () => {
    render(<MembersPage />);
    expect(screen.getByRole("button", { name: /add member/i })).toBeInTheDocument();
  });

  it("renders search input", () => {
    render(<MembersPage />);
    expect(
      screen.getByPlaceholderText(/search by name, email, or library id/i)
    ).toBeInTheDocument();
  });

  it("renders empty table state", () => {
    render(<MembersPage />);
    expect(screen.getByText("No members found.")).toBeInTheDocument();
  });

  it("opens MemberForm dialog when Add Member is clicked", async () => {
    render(<MembersPage />);
    await userEvent.click(screen.getByRole("button", { name: /add member/i }));
    // Multiple "Add Member" texts expected (header + dialog title)
    expect(screen.getAllByText("Add Member").length).toBeGreaterThanOrEqual(2);
  });
});
