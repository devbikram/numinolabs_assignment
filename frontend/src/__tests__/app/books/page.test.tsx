import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import BooksPage from "@/app/books/page";

jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));

jest.mock("next/link", () => {
  const MockLink = ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  );
  MockLink.displayName = "Link";
  return MockLink;
});

jest.mock("@/lib/queries/books", () => ({
  useBooks: () => ({ data: { items: [], total: 0 }, isLoading: false }),
  useDeleteBook: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useCreateBook: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useUpdateBook: () => ({ mutateAsync: jest.fn(), isPending: false }),
}));

jest.mock("@/components/ui/author-select", () => ({
  AuthorSelect: ({ onChange }: { value: string; onChange: (v: string) => void }) => (
    <input aria-label="AuthorSelect" onChange={(e) => onChange(e.target.value)} />
  ),
}));

jest.mock("@/components/ui/category-select", () => ({
  CategorySelect: ({ onChange }: { value: string; onChange: (v: string) => void }) => (
    <input aria-label="CategorySelect" onChange={(e) => onChange(e.target.value)} />
  ),
}));

describe("BooksPage", () => {
  it("renders Books page header", () => {
    render(<BooksPage />);
    expect(screen.getByText("Books")).toBeInTheDocument();
  });

  it("renders Add Book button", () => {
    render(<BooksPage />);
    expect(screen.getByRole("button", { name: /add book/i })).toBeInTheDocument();
  });

  it("renders empty table state", () => {
    render(<BooksPage />);
    expect(screen.getByText("No books yet. Add your first book!")).toBeInTheDocument();
  });

  it("opens BookForm dialog when Add Book is clicked", async () => {
    render(<BooksPage />);
    await userEvent.click(screen.getByRole("button", { name: /add book/i }));
    // Multiple "Add Book" texts are expected (header + dialog title)
    expect(screen.getAllByText("Add Book").length).toBeGreaterThanOrEqual(2);
  });
});
