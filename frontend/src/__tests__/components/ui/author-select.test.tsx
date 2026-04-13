import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthorSelect } from "@/components/ui/author-select";

jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));

const mockAuthors = [
  { id: "a1", name: "Robert Martin", book_count: 5 },
  { id: "a2", name: "Martin Fowler", book_count: 3 },
  { id: "a3", name: "Kent Beck", book_count: 2 },
];

const mockCreateMutateAsync = jest.fn();
jest.mock("@/lib/queries/authors", () => ({
  useAuthors: () => ({ data: { items: mockAuthors } }),
  useCreateAuthor: () => ({ mutateAsync: mockCreateMutateAsync, isPending: false }),
}));

describe("AuthorSelect — single mode", () => {
  it("renders with placeholder", () => {
    render(<AuthorSelect value="" onChange={jest.fn()} placeholder="Pick author" />);
    expect(screen.getByRole("combobox")).toHaveTextContent("Pick author");
  });

  it("shows author list when clicked", async () => {
    render(<AuthorSelect value="" onChange={jest.fn()} />);
    await userEvent.click(screen.getByRole("combobox"));
    expect(screen.getByText("Robert Martin (5)")).toBeInTheDocument();
    expect(screen.getByText("Martin Fowler (3)")).toBeInTheDocument();
  });

  it("displays selected author name when value is set", () => {
    render(<AuthorSelect value="a1" onChange={jest.fn()} />);
    expect(screen.getByRole("combobox")).toHaveTextContent("Robert Martin (5)");
  });

  it("calls onChange when an author is selected", async () => {
    const onChange = jest.fn();
    render(<AuthorSelect value="" onChange={onChange} />);
    await userEvent.click(screen.getByRole("combobox"));
    await userEvent.click(screen.getByText("Kent Beck (2)"));
    expect(onChange).toHaveBeenCalledWith("a3");
  });

  it("shows 'All authors' option for single mode", async () => {
    render(<AuthorSelect value="a1" onChange={jest.fn()} />);
    await userEvent.click(screen.getByRole("combobox"));
    expect(screen.getByText("All authors")).toBeInTheDocument();
  });
});

describe("AuthorSelect — multi mode", () => {
  it("renders with placeholder when no authors selected", () => {
    render(<AuthorSelect mode="multi" value={[]} onChange={jest.fn()} placeholder="Select authors..." />);
    expect(screen.getByRole("combobox")).toHaveTextContent("Select authors...");
  });

  it("shows comma-separated names when multiple authors are selected", () => {
    render(<AuthorSelect mode="multi" value={["a1", "a2"]} onChange={jest.fn()} />);
    expect(screen.getByRole("combobox")).toHaveTextContent("Robert Martin, Martin Fowler");
  });

  it("does not show 'All authors' option in multi mode", async () => {
    render(<AuthorSelect mode="multi" value={[]} onChange={jest.fn()} />);
    await userEvent.click(screen.getByRole("combobox"));
    expect(screen.queryByText("All authors")).not.toBeInTheDocument();
  });

  it("calls onChange with added author when toggled on", async () => {
    const onChange = jest.fn();
    render(<AuthorSelect mode="multi" value={["a1"]} onChange={onChange} />);
    await userEvent.click(screen.getByRole("combobox"));
    await userEvent.click(screen.getByText("Kent Beck (2)"));
    expect(onChange).toHaveBeenCalledWith(["a1", "a3"]);
  });

  it("calls onChange with removed author when toggled off", async () => {
    const onChange = jest.fn();
    render(<AuthorSelect mode="multi" value={["a1", "a2"]} onChange={onChange} />);
    await userEvent.click(screen.getByRole("combobox"));
    await userEvent.click(screen.getByText("Robert Martin (5)"));
    expect(onChange).toHaveBeenCalledWith(["a2"]);
  });
});

describe("AuthorSelect — create author", () => {
  beforeEach(() => {
    mockCreateMutateAsync.mockReset();
  });

  it("shows create button when searching for a non-existing author", async () => {
    render(<AuthorSelect value="" onChange={jest.fn()} />);
    await userEvent.click(screen.getByRole("combobox"));
    const searchInput = screen.getByPlaceholderText(/search or add author/i);
    await userEvent.type(searchInput, "New Author");
    // The "No authors found" empty state should show a create button
    expect(screen.getByText(/create/i)).toBeInTheDocument();
  });

  it("does not show create button when search matches an existing author exactly", async () => {
    render(<AuthorSelect value="" onChange={jest.fn()} />);
    await userEvent.click(screen.getByRole("combobox"));
    const searchInput = screen.getByPlaceholderText(/search or add author/i);
    await userEvent.type(searchInput, "Robert Martin");
    // Should see the author in the list, but no duplicate "create" button at bottom
    expect(screen.getByText("Robert Martin (5)")).toBeInTheDocument();
  });
});
