import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BookTable } from "@/components/books/book-table";
import type { Book } from "@/types";

jest.mock("next/link", () => {
  const MockLink = ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  );
  MockLink.displayName = "Link";
  return MockLink;
});

jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));

const mockDeleteMutateAsync = jest.fn();
jest.mock("@/lib/queries/books", () => ({
  useDeleteBook: () => ({ mutateAsync: mockDeleteMutateAsync, isPending: false }),
}));

const makeBook = (overrides: Partial<Book> = {}): Book => ({
  id: "1",
  title: "Clean Code",
  authors: [{ id: "a1", name: "Robert Martin", book_count: 1 }],
  isbn: "9780132350884",
  category_id: "c1",
  category: { id: "c1", name: "Programming" },
  published_year: 2008,
  total_copies: 3,
  available_copies: 2,
  borrow_count: 5,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
  ...overrides,
});

describe("BookTable", () => {
  it("renders book titles", () => {
    render(<BookTable books={[makeBook()]} />);
    expect(screen.getByText("Clean Code")).toBeInTheDocument();
  });

  it("renders empty state when no books", () => {
    render(<BookTable books={[]} />);
    expect(screen.getByText("No books found.")).toBeInTheDocument();
  });

  it("renders multiple books", () => {
    const books = [makeBook({ id: "1", title: "Book A" }), makeBook({ id: "2", title: "Book B" })];
    render(<BookTable books={books} />);
    expect(screen.getByText("Book A")).toBeInTheDocument();
    expect(screen.getByText("Book B")).toBeInTheDocument();
  });

  it("renders author links when showAuthors is true (default)", () => {
    render(<BookTable books={[makeBook()]} />);
    expect(screen.getByText("Robert Martin")).toBeInTheDocument();
  });

  it("hides authors column when showAuthors=false", () => {
    render(<BookTable books={[makeBook()]} showAuthors={false} />);
    expect(screen.queryByText("Robert Martin")).not.toBeInTheDocument();
  });

  it("renders book link to correct href", () => {
    render(<BookTable books={[makeBook({ id: "42" })]} />);
    expect(screen.getByRole("link", { name: "Clean Code" })).toHaveAttribute("href", "/books/42");
  });

  it("calls onEdit when edit button clicked", async () => {
    const onEdit = jest.fn();
    render(<BookTable books={[makeBook()]} onEdit={onEdit} />);
    const editBtn = screen.getAllByRole("button")[0];
    await userEvent.click(editBtn);
    expect(onEdit).toHaveBeenCalledWith(expect.objectContaining({ title: "Clean Code" }));
  });

  it("opens a confirmation dialog and deletes on confirm", async () => {
    mockDeleteMutateAsync.mockResolvedValue(undefined);
    render(<BookTable books={[makeBook()]} />);
    // Click the delete row action button (opens Dialog)
    await userEvent.click(screen.getByRole("button", { name: "Delete" }));
    // Wait for confirmation dialog
    await screen.findByRole("dialog");
    // Click the confirm Delete button (last button named "Delete" belongs to the dialog footer)
    const deleteButtons = screen.getAllByRole("button", { name: "Delete" });
    await userEvent.click(deleteButtons[deleteButtons.length - 1]);
    expect(mockDeleteMutateAsync).toHaveBeenCalledWith("1");
  });
});
