import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BorrowForm } from "@/components/borrowings/borrow-form";

jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));

const mockCreateMutateAsync = jest.fn();
jest.mock("@/lib/queries/borrowings", () => ({
  useCreateBorrowing: () => ({ mutateAsync: mockCreateMutateAsync, isPending: false }),
}));

jest.mock("@/lib/queries/books", () => ({
  useBooks: () => ({
    data: {
      items: [
        {
          id: "bk1",
          title: "Clean Code",
          isbn: "9780132350884",
          available_copies: 2,
          authors: [{ id: "a1", name: "Robert Martin", book_count: 1 }],
          category_id: null,
          category: null,
          published_year: null,
          total_copies: 3,
          borrow_count: 0,
          created_at: "",
          updated_at: "",
        },
      ],
      total: 1,
    },
    isLoading: false,
  }),
}));

jest.mock("@/lib/queries/members", () => ({
  useMembers: () => ({
    data: {
      items: [
        {
          id: "m1",
          library_id: "LIB-001",
          full_name: "Alice Smith",
          email: "alice@example.com",
          phone: null,
          address: null,
          created_at: "",
          updated_at: "",
        },
      ],
      total: 1,
    },
    isLoading: false,
  }),
}));

describe("BorrowForm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders Borrow a Book title when open", () => {
    render(<BorrowForm open={true} onOpenChange={jest.fn()} />);
    expect(screen.getByText("Borrow a Book")).toBeInTheDocument();
  });

  it("does not render dialog content when open=false", () => {
    render(<BorrowForm open={false} onOpenChange={jest.fn()} />);
    expect(screen.queryByText("Borrow a Book")).not.toBeInTheDocument();
  });

  it("renders book search input", async () => {
    render(<BorrowForm open={true} onOpenChange={jest.fn()} />);
    // Open the book combobox to reveal the search input
    const [bookCombobox] = screen.getAllByRole("combobox");
    await userEvent.click(bookCombobox);
    expect(screen.getByPlaceholderText(/search books/i)).toBeInTheDocument();
  });

  it("renders member search input", async () => {
    render(<BorrowForm open={true} onOpenChange={jest.fn()} />);
    // Open the member combobox to reveal the search input
    const comboboxes = screen.getAllByRole("combobox");
    await userEvent.click(comboboxes[1]);
    const inputs = screen.getAllByPlaceholderText(/search by name, email, or library id/i);
    expect(inputs.length).toBeGreaterThanOrEqual(1);
  });

  it("renders due date field", () => {
    render(<BorrowForm open={true} onOpenChange={jest.fn()} />);
    expect(screen.getByLabelText(/due date/i)).toBeInTheDocument();
  });

  it("renders Borrow submit button", () => {
    render(<BorrowForm open={true} onOpenChange={jest.fn()} />);
    expect(screen.getByRole("button", { name: /borrow/i })).toBeInTheDocument();
  });

  it("calls onOpenChange(false) when Cancel is clicked", async () => {
    const onOpenChange = jest.fn();
    render(<BorrowForm open={true} onOpenChange={onOpenChange} />);
    await userEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("shows validation errors when submitting without selecting book or member", async () => {
    render(<BorrowForm open={true} onOpenChange={jest.fn()} />);
    await userEvent.click(screen.getByRole("button", { name: /^borrow$/i }));
    await screen.findByText("Select a book");
    expect(screen.getByText("Select a member")).toBeInTheDocument();
  });
});
