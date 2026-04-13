import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BorrowingTable } from "@/components/borrowings/borrowing-table";
import type { Borrowing } from "@/types";

jest.mock("next/link", () => {
  const MockLink = ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  );
  MockLink.displayName = "Link";
  return MockLink;
});

jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));

const mockReturnMutateAsync = jest.fn();
jest.mock("@/lib/queries/borrowings", () => ({
  useReturnBook: () => ({ mutateAsync: mockReturnMutateAsync, isPending: false }),
}));

const makeBorrowing = (overrides: Partial<Borrowing> = {}): Borrowing => ({
  id: "b1",
  book_id: "bk1",
  member_id: "m1",
  borrowed_at: "2024-01-10T00:00:00Z",
  due_date: "2024-01-24T00:00:00Z",
  returned_at: null,
  status: "borrowed",
  book: { id: "bk1", title: "Clean Code", isbn: "9780132350884" },
  member: {
    id: "m1",
    library_id: "LIB-001",
    full_name: "Alice Smith",
    email: "alice@example.com",
    phone: null,
  },
  created_at: "2024-01-10T00:00:00Z",
  updated_at: "2024-01-10T00:00:00Z",
  ...overrides,
});

describe("BorrowingTable", () => {
  it("renders empty state when no borrowings", () => {
    render(<BorrowingTable borrowings={[]} />);
    expect(screen.getByText("No borrowing records found.")).toBeInTheDocument();
  });

  it("renders book title and member name", () => {
    render(<BorrowingTable borrowings={[makeBorrowing()]} />);
    expect(screen.getByText("Clean Code")).toBeInTheDocument();
    expect(screen.getByText("Alice Smith")).toBeInTheDocument();
  });

  it("renders status badge", () => {
    render(<BorrowingTable borrowings={[makeBorrowing()]} />);
    expect(screen.getByText("borrowed")).toBeInTheDocument();
  });

  it("renders overdue status badge", () => {
    render(<BorrowingTable borrowings={[makeBorrowing({ status: "overdue" })]} />);
    expect(screen.getByText("overdue")).toBeInTheDocument();
  });

  it("renders returned status badge", () => {
    render(
      <BorrowingTable
        borrowings={[makeBorrowing({ status: "returned", returned_at: "2024-01-20T00:00:00Z" })]}
      />
    );
    expect(screen.getByText("returned")).toBeInTheDocument();
  });

  it("hides book column when showBook=false", () => {
    render(<BorrowingTable borrowings={[makeBorrowing()]} showBook={false} />);
    expect(screen.queryByText("Clean Code")).not.toBeInTheDocument();
  });

  it("hides member columns when showMember=false", () => {
    render(<BorrowingTable borrowings={[makeBorrowing()]} showMember={false} />);
    expect(screen.queryByText("Alice Smith")).not.toBeInTheDocument();
  });

  it("renders Return button for non-returned borrowings", () => {
    render(<BorrowingTable borrowings={[makeBorrowing()]} />);
    expect(screen.getByRole("button", { name: /return/i })).toBeInTheDocument();
  });

  it("opens confirmation dialog when Return is clicked", async () => {
    render(<BorrowingTable borrowings={[makeBorrowing()]} />);
    await userEvent.click(screen.getByRole("button", { name: /return/i }));
    // Dialog should appear with confirm button
    expect(screen.getByRole("button", { name: /confirm/i })).toBeInTheDocument();
  });
});
