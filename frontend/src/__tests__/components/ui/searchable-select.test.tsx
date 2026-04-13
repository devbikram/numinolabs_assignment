import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SearchableSelect } from "@/components/ui/searchable-select";
import { CommandItem } from "@/components/ui/command";

function renderSelect(overrides: Partial<React.ComponentProps<typeof SearchableSelect>> = {}) {
  const defaultProps: React.ComponentProps<typeof SearchableSelect> = {
    open: false,
    onOpenChange: jest.fn(),
    value: "",
    onChange: jest.fn(),
    placeholder: "Select item",
    searchPlaceholder: "Search items...",
    emptyText: "No items found.",
    children: ({ onChange }) => (
      <>
        <CommandItem value="apple" onSelect={() => onChange("apple")}>Apple</CommandItem>
        <CommandItem value="banana" onSelect={() => onChange("banana")}>Banana</CommandItem>
      </>
    ),
    ...overrides,
  };
  return render(<SearchableSelect {...defaultProps} />);
}

describe("SearchableSelect", () => {
  it("renders trigger button with placeholder", () => {
    renderSelect();
    expect(screen.getByRole("combobox")).toHaveTextContent("Select item");
  });

  it("does not show dropdown when closed", () => {
    renderSelect({ open: false });
    expect(screen.queryByPlaceholderText("Search items...")).not.toBeInTheDocument();
  });

  it("shows dropdown with search input when open", () => {
    renderSelect({ open: true });
    expect(screen.getByPlaceholderText("Search items...")).toBeInTheDocument();
  });

  it("renders children items when open", () => {
    renderSelect({ open: true });
    expect(screen.getByText("Apple")).toBeInTheDocument();
    expect(screen.getByText("Banana")).toBeInTheDocument();
  });

  it("calls onOpenChange when trigger is clicked", async () => {
    const onOpenChange = jest.fn();
    renderSelect({ onOpenChange });
    await userEvent.click(screen.getByRole("combobox"));
    expect(onOpenChange).toHaveBeenCalledWith(true);
  });

  it("calls onOpenChange(false) when Escape is pressed on the container", async () => {
    const onOpenChange = jest.fn();
    renderSelect({ open: true, onOpenChange });
    const searchInput = screen.getByPlaceholderText("Search items...");
    // Focus inside the component, then press Escape
    await userEvent.click(searchInput);
    await userEvent.keyboard("{Escape}");
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("calls onSearchChange when typing in search input", async () => {
    const onSearchChange = jest.fn();
    renderSelect({ open: true, onSearchChange });
    const searchInput = screen.getByPlaceholderText("Search items...");
    await userEvent.type(searchInput, "app");
    expect(onSearchChange).toHaveBeenCalled();
  });

  it("shows empty text when no items match filter", () => {
    renderSelect({
      open: true,
      emptyText: "Nothing here",
      children: () => null,
    });
    expect(screen.getByText("Nothing here")).toBeInTheDocument();
  });

  it("supports custom id on trigger button", () => {
    renderSelect({ id: "my-select" });
    expect(screen.getByRole("combobox")).toHaveAttribute("id", "my-select");
  });
});
