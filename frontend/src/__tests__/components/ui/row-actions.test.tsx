import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RowActions } from "@/components/ui/row-actions";

describe("RowActions", () => {
  it("renders the delete button", () => {
    render(<RowActions onDelete={jest.fn()} />);
    expect(screen.getAllByRole("button")).toHaveLength(1);
  });

  it("renders both edit and delete buttons when onEdit is provided", () => {
    render(<RowActions onEdit={jest.fn()} onDelete={jest.fn()} />);
    expect(screen.getAllByRole("button")).toHaveLength(2);
  });

  it("calls onDelete when delete button is clicked", async () => {
    const onDelete = jest.fn();
    render(<RowActions onDelete={onDelete} />);
    await userEvent.click(screen.getAllByRole("button")[0]);
    expect(onDelete).toHaveBeenCalledTimes(1);
  });

  it("calls onEdit when edit button is clicked", async () => {
    const onEdit = jest.fn();
    render(<RowActions onEdit={onEdit} onDelete={jest.fn()} />);
    const [editBtn] = screen.getAllByRole("button");
    await userEvent.click(editBtn);
    expect(onEdit).toHaveBeenCalledTimes(1);
  });

  it("does not render edit button when onEdit is omitted", () => {
    render(<RowActions onDelete={jest.fn()} />);
    expect(screen.getAllByRole("button")).toHaveLength(1);
  });
});
