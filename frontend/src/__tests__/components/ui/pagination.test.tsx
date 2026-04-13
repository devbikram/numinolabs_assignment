import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Pagination } from "@/components/ui/pagination";

describe("Pagination", () => {
  it("returns null when there is only one page", () => {
    const { container } = render(
      <Pagination total={10} skip={0} limit={20} onPageChange={jest.fn()} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders page buttons for each page", () => {
    render(<Pagination total={30} skip={0} limit={10} onPageChange={jest.fn()} />);
    expect(screen.getByRole("button", { name: "Page 1" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Page 2" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Page 3" })).toBeInTheDocument();
  });

  it("disables previous button on first page", () => {
    render(<Pagination total={30} skip={0} limit={10} onPageChange={jest.fn()} />);
    const buttons = screen.getAllByRole("button");
    // first button is prev
    expect(buttons[0]).toBeDisabled();
  });

  it("disables next button on last page", () => {
    render(<Pagination total={30} skip={20} limit={10} onPageChange={jest.fn()} />);
    const buttons = screen.getAllByRole("button");
    // last button is next
    expect(buttons[buttons.length - 1]).toBeDisabled();
  });

  it("calls onPageChange with correct skip when next is clicked", async () => {
    const onPageChange = jest.fn();
    render(<Pagination total={30} skip={0} limit={10} onPageChange={onPageChange} />);
    const buttons = screen.getAllByRole("button");
    await userEvent.click(buttons[buttons.length - 1]);
    expect(onPageChange).toHaveBeenCalledWith(10);
  });

  it("calls onPageChange with correct skip when prev is clicked", async () => {
    const onPageChange = jest.fn();
    render(<Pagination total={30} skip={20} limit={10} onPageChange={onPageChange} />);
    const buttons = screen.getAllByRole("button");
    await userEvent.click(buttons[0]);
    expect(onPageChange).toHaveBeenCalledWith(10);
  });

  it("calls onPageChange with correct skip when a page number is clicked", async () => {
    const onPageChange = jest.fn();
    render(<Pagination total={30} skip={0} limit={10} onPageChange={onPageChange} />);
    await userEvent.click(screen.getByRole("button", { name: "Page 2" }));
    expect(onPageChange).toHaveBeenCalledWith(10);
  });

  it("shows the showing N-M of total label", () => {
    render(<Pagination total={30} skip={0} limit={10} onPageChange={jest.fn()} />);
    expect(screen.getByText(/Showing 1–10 of 30/)).toBeInTheDocument();
  });
});
