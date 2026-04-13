import React from "react";
import { render, screen } from "@testing-library/react";
import MemberDetailsPage from "@/app/members/[id]/page";

jest.mock("next/navigation", () => ({
  useParams: () => ({ id: "m1" }),
}));

jest.mock("next/link", () => {
  const MockLink = ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  );
  MockLink.displayName = "Link";
  return MockLink;
});

jest.mock("sonner", () => ({ toast: { success: jest.fn() } }));

const mockMember = {
  id: "m1",
  library_id: "LIB-001",
  full_name: "Alice Smith",
  email: "alice@example.com",
  phone: "555-0100",
  address: "123 Main St",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

const mockStats = { total: 5, borrowed: 2, returned: 3, overdue: 0 };

jest.mock("@/lib/queries/members", () => ({
  useMember: () => ({ data: mockMember, isLoading: false }),
  useMemberStats: () => ({ data: mockStats }),
}));

jest.mock("@/lib/queries/borrowings", () => ({
  useMemberBorrowings: () => ({ data: { items: [], total: 0 }, isLoading: false }),
  useReturnBook: () => ({ mutateAsync: jest.fn(), isPending: false }),
}));

describe("MemberDetailsPage", () => {
  it("renders member full name", () => {
    render(<MemberDetailsPage />);
    expect(screen.getByText("Alice Smith")).toBeInTheDocument();
  });

  it("renders back link to /members", () => {
    render(<MemberDetailsPage />);
    expect(screen.getByRole("link", { name: /back to members/i })).toHaveAttribute(
      "href",
      "/members"
    );
  });

  it("renders library ID", () => {
    render(<MemberDetailsPage />);
    expect(screen.getByText("LIB-001")).toBeInTheDocument();
  });

  it("renders email meta field", () => {
    render(<MemberDetailsPage />);
    expect(screen.getByText("alice@example.com")).toBeInTheDocument();
  });

  it("renders borrowings section", () => {
    render(<MemberDetailsPage />);
    expect(screen.getByText("Borrowings")).toBeInTheDocument();
  });

  it("renders empty borrowings state", () => {
    render(<MemberDetailsPage />);
    expect(screen.getByText("No borrowing records found.")).toBeInTheDocument();
  });
});
