import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BookForm } from "@/components/books/book-form";

jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));

const mockCreateMutateAsync = jest.fn();
const mockUpdateMutateAsync = jest.fn();

jest.mock("@/lib/queries/books", () => ({
  useCreateBook: () => ({ mutateAsync: mockCreateMutateAsync, isPending: false }),
  useUpdateBook: () => ({ mutateAsync: mockUpdateMutateAsync, isPending: false }),
}));

// Mock select components to avoid network calls
jest.mock("@/components/ui/author-select", () => ({
  AuthorSelect: ({ onChange }: { value: string[]; onChange: (v: string[]) => void }) => (
    <button type="button" onClick={() => onChange(["a1"])}>
      AuthorSelect
    </button>
  ),
}));

jest.mock("@/components/ui/category-select", () => ({
  CategorySelect: ({ onChange }: { value: string | null; onChange: (v: string | null) => void }) => (
    <button type="button" onClick={() => onChange(null)}>
      CategorySelect
    </button>
  ),
}));

describe("BookForm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders Add Book title when no book prop", () => {
    render(<BookForm open={true} onOpenChange={jest.fn()} />);
    expect(screen.getByText("Add Book")).toBeInTheDocument();
  });

  it("renders Edit Book title when book is provided", () => {
    const book = {
      id: "1",
      title: "Clean Code",
      authors: [{ id: "a1", name: "Bob", book_count: 1 }],
      isbn: "9780132350884",
      category_id: null,
      category: null,
      published_year: 2008,
      total_copies: 3,
      available_copies: 2,
      borrow_count: 0,
      created_at: "",
      updated_at: "",
    };
    render(<BookForm open={true} onOpenChange={jest.fn()} book={book} />);
    expect(screen.getByText("Edit Book")).toBeInTheDocument();
  });

  it("does not render dialog content when open=false", () => {
    render(<BookForm open={false} onOpenChange={jest.fn()} />);
    expect(screen.queryByText("Add Book")).not.toBeInTheDocument();
  });

  it("renders Title and ISBN fields", () => {
    render(<BookForm open={true} onOpenChange={jest.fn()} />);
    expect(screen.getByLabelText("Title")).toBeInTheDocument();
    expect(screen.getByLabelText(/isbn/i)).toBeInTheDocument();
  });

  it("shows validation error for empty title on submit", async () => {
    render(<BookForm open={true} onOpenChange={jest.fn()} />);
    await userEvent.click(screen.getByRole("button", { name: "Create" }));
    expect(await screen.findByText("Title is required")).toBeInTheDocument();
  });

  it("calls onOpenChange(false) when Cancel is clicked", async () => {
    const onOpenChange = jest.fn();
    render(<BookForm open={true} onOpenChange={onOpenChange} />);
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("calls createBook on valid submit", async () => {
    mockCreateMutateAsync.mockResolvedValue({ id: "new" });
    const onOpenChange = jest.fn();
    render(<BookForm open={true} onOpenChange={onOpenChange} />);
    await userEvent.type(screen.getByLabelText("Title"), "My New Book");
    await userEvent.click(screen.getByRole("button", { name: "AuthorSelect" }));
    await userEvent.type(screen.getByLabelText(/isbn/i), "9780132350884");
    await userEvent.click(screen.getByRole("button", { name: "Create" }));
    expect(mockCreateMutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({ title: "My New Book" })
    );
  });
});
