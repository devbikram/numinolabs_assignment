import React from "react";
import { render, screen } from "@testing-library/react";
import AuthorDetailsPage from "@/app/authors/[id]/page";

jest.mock("next/navigation", () => ({
  useParams: () => ({ id: "a1" }),
}));

jest.mock("next/link", () => {
  const MockLink = ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  );
  MockLink.displayName = "Link";
  return MockLink;
});

jest.mock("sonner", () => ({ toast: { success: jest.fn() } }));

const mockAuthor = {
  id: "a1",
  name: "Robert Martin",
  bio: "Author of Clean Code and other books.",
  book_count: 4,
  created_at: "2023-01-01T00:00:00Z",
  updated_at: "2023-01-01T00:00:00Z",
};

const mockStats = {
  total_borrows: 20,
  active_borrows: 3,
  unique_readers: 12,
  most_borrowed: { id: "bk1", title: "Clean Code", borrow_count: 10 },
};

jest.mock("@/lib/queries/authors", () => ({
  useAuthor: () => ({ data: mockAuthor, isLoading: false }),
  useAuthorStats: () => ({ data: mockStats }),
}));

jest.mock("@/lib/queries/books", () => ({
  useBooks: () => ({ data: { items: [], total: 0 }, isLoading: false }),
  useDeleteBook: () => ({ mutateAsync: jest.fn(), isPending: false }),
}));

describe("AuthorDetailsPage", () => {
  it("renders author name", () => {
    render(<AuthorDetailsPage />);
    expect(screen.getByText("Robert Martin")).toBeInTheDocument();
  });

  it("renders back link to /books", () => {
    render(<AuthorDetailsPage />);
    expect(screen.getByRole("link", { name: /back to books/i })).toHaveAttribute("href", "/books");
  });

  it("renders author bio", () => {
    render(<AuthorDetailsPage />);
    expect(screen.getByText("Author of Clean Code and other books.")).toBeInTheDocument();
  });

  it("renders stat cards", () => {
    render(<AuthorDetailsPage />);
    expect(screen.getByText("Total Borrows")).toBeInTheDocument();
    expect(screen.getByText("Active Borrows")).toBeInTheDocument();
    expect(screen.getByText("Unique Readers")).toBeInTheDocument();
  });

  it("renders most borrowed book title", () => {
    render(<AuthorDetailsPage />);
    // The most_borrowed card title
    expect(screen.getByText("Clean Code", { selector: "p" })).toBeInTheDocument();
  });

  it("renders empty books state", () => {
    render(<AuthorDetailsPage />);
    expect(screen.getByText("No books found.")).toBeInTheDocument();
  });
});
