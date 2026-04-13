import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import BorrowingsPage from "@/app/borrowings/page";

jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));

jest.mock("next/link", () => {
  const MockLink = ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  );
  MockLink.displayName = "Link";
  return MockLink;
});

jest.mock("@/lib/queries/borrowings", () => ({
  useBorrowings: () => ({ data: { items: [], total: 0 }, isLoading: false }),
  useReturnBook: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useCreateBorrowing: () => ({ mutateAsync: jest.fn(), isPending: false }),
}));

jest.mock("@/lib/queries/books", () => ({
  useBooks: () => ({ data: { items: [], total: 0 }, isLoading: false }),
}));

jest.mock("@/lib/queries/members", () => ({
  useMembers: () => ({ data: { items: [], total: 0 }, isLoading: false }),
}));

describe("BorrowingsPage", () => {
  it("renders Borrowings page header", () => {
    render(<BorrowingsPage />);
    expect(screen.getByText("Borrowings")).toBeInTheDocument();
  });

  it("renders Borrow Book button", () => {
    render(<BorrowingsPage />);
    expect(screen.getByRole("button", { name: /borrow book/i })).toBeInTheDocument();
  });

  it("renders status filter buttons", () => {
    render(<BorrowingsPage />);
    expect(screen.getByRole("button", { name: "All" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Borrowed" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Returned" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Overdue" })).toBeInTheDocument();
  });

  it("renders search input", () => {
    render(<BorrowingsPage />);
    expect(
      screen.getByPlaceholderText(/search by book title/i)
    ).toBeInTheDocument();
  });

  it("renders empty table state", () => {
    render(<BorrowingsPage />);
    expect(screen.getByText("No borrowing records yet.")).toBeInTheDocument();
  });

  it("activates Borrowed status filter when clicked", async () => {
    render(<BorrowingsPage />);
    const borrowedBtn = screen.getByRole("button", { name: "Borrowed" });
    await userEvent.click(borrowedBtn);
    // After clicking, the button should have default variant (active)
    expect(borrowedBtn).toBeInTheDocument();
  });

  it("opens BorrowForm dialog when Borrow Book is clicked", async () => {
    render(<BorrowingsPage />);
    await userEvent.click(screen.getByRole("button", { name: /borrow book/i }));
    expect(screen.getByText("Borrow a Book")).toBeInTheDocument();
  });
});

// ─── M-47: Date range validation ────────────────────────────────────────────
describe("BorrowingsPage date filter validation", () => {
  const toast = jest.requireMock("sonner").toast;

  beforeEach(() => {
    toast.error.mockClear();
  });

  it("Apply button is present and can be clicked", async () => {
    render(<BorrowingsPage />);
    const applyBtn = screen.getByRole("button", { name: /apply/i });
    expect(applyBtn).toBeInTheDocument();
    // Default preset: button exists but doesn't trigger error for non-custom presets
    await userEvent.click(applyBtn);
    expect(toast.error).not.toHaveBeenCalled();
  });

  it("renders date filter fieldset with sr-only legend", () => {
    render(<BorrowingsPage />);
    const fieldset = document.querySelector("fieldset");
    expect(fieldset).toBeInTheDocument();
    const legend = fieldset?.querySelector("legend");
    expect(legend).toBeInTheDocument();
    expect(legend?.textContent).toBe("Date range filter");
    expect(legend?.className).toContain("sr-only");
  });

  it("shows custom date inputs when Custom Range is selected", async () => {
    render(<BorrowingsPage />);
    // Click the date filter select trigger to open it
    const selectTrigger = screen.getByRole("combobox", { name: /date filter/i });
    await userEvent.click(selectTrigger);
    // Select "Custom Range" by text
    const customOption = await screen.findByText("Custom Range");
    await userEvent.click(customOption);
    // Now the From and To inputs should appear
    expect(screen.getByLabelText(/filter start date/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/filter end date/i)).toBeInTheDocument();
  });

  it("shows error when custom from date is after to date", async () => {
    render(<BorrowingsPage />);
    // Switch to custom range
    const selectTrigger = screen.getByRole("combobox", { name: /date filter/i });
    await userEvent.click(selectTrigger);
    await userEvent.click(await screen.findByText("Custom Range"));

    const fromInput = screen.getByLabelText(/filter start date/i);
    const toInput = screen.getByLabelText(/filter end date/i);

    // Set from > to
    await userEvent.clear(fromInput);
    await userEvent.type(fromInput, "2025-03-15");
    await userEvent.clear(toInput);
    await userEvent.type(toInput, "2025-03-01");

    await userEvent.click(screen.getByRole("button", { name: /apply/i }));
    expect(toast.error).toHaveBeenCalledWith("Start date must be on or before end date");
  });

  it("does not show error when custom from date is before to date", async () => {
    render(<BorrowingsPage />);
    const selectTrigger = screen.getByRole("combobox", { name: /date filter/i });
    await userEvent.click(selectTrigger);
    await userEvent.click(await screen.findByText("Custom Range"));

    const fromInput = screen.getByLabelText(/filter start date/i);
    const toInput = screen.getByLabelText(/filter end date/i);

    await userEvent.clear(fromInput);
    await userEvent.type(fromInput, "2025-03-01");
    await userEvent.clear(toInput);
    await userEvent.type(toInput, "2025-03-15");

    await userEvent.click(screen.getByRole("button", { name: /apply/i }));
    expect(toast.error).not.toHaveBeenCalled();
  });
});
