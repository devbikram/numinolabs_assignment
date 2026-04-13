import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemberTable } from "@/components/members/member-table";
import type { Member } from "@/types";

jest.mock("next/link", () => {
  const MockLink = ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  );
  MockLink.displayName = "Link";
  return MockLink;
});

jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));

const mockDeleteMutateAsync = jest.fn();
jest.mock("@/lib/queries/members", () => ({
  useDeleteMember: () => ({ mutateAsync: mockDeleteMutateAsync, isPending: false }),
}));

const makeMember = (overrides: Partial<Member> = {}): Member => ({
  id: "1",
  library_id: "LIB-001",
  full_name: "Alice Smith",
  email: "alice@example.com",
  phone: "555-0100",
  address: "123 Main St",
  created_at: "2024-01-01T00:00:00Z",
  ...overrides,
});

describe("MemberTable", () => {
  it("renders member data", () => {
    render(<MemberTable members={[makeMember()]} onEdit={jest.fn()} />);
    expect(screen.getByText("Alice Smith")).toBeInTheDocument();
    expect(screen.getByText("alice@example.com")).toBeInTheDocument();
    expect(screen.getByText("LIB-001")).toBeInTheDocument();
  });

  it("renders empty state when no members", () => {
    render(<MemberTable members={[]} onEdit={jest.fn()} />);
    expect(screen.getByText("No members found.")).toBeInTheDocument();
  });

  it("renders member name as link to detail page", () => {
    render(<MemberTable members={[makeMember({ id: "99" })]} onEdit={jest.fn()} />);
    expect(screen.getByRole("link", { name: "Alice Smith" })).toHaveAttribute("href", "/members/99");
  });

  it("calls onEdit with the member when edit button is clicked", async () => {
    const onEdit = jest.fn();
    render(<MemberTable members={[makeMember()]} onEdit={onEdit} />);
    const buttons = screen.getAllByRole("button");
    await userEvent.click(buttons[0]); // first button is Edit
    expect(onEdit).toHaveBeenCalledWith(expect.objectContaining({ full_name: "Alice Smith" }));
  });

  it("opens a confirmation dialog and deletes on confirm", async () => {
    mockDeleteMutateAsync.mockResolvedValue(undefined);
    render(<MemberTable members={[makeMember()]} onEdit={jest.fn()} />);
    // Click the delete row action button (opens Dialog)
    await userEvent.click(screen.getByRole("button", { name: "Delete" }));
    // Wait for confirmation dialog
    await screen.findByRole("dialog");
    // Click the confirm Delete button in the dialog footer
    const deleteButtons = screen.getAllByRole("button", { name: "Delete" });
    await userEvent.click(deleteButtons[deleteButtons.length - 1]);
    expect(mockDeleteMutateAsync).toHaveBeenCalledWith("1");
  });

  it("renders multiple members", () => {
    const members = [
      makeMember({ id: "1", full_name: "Alice" }),
      makeMember({ id: "2", full_name: "Bob" }),
    ];
    render(<MemberTable members={members} onEdit={jest.fn()} />);
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
  });
});
