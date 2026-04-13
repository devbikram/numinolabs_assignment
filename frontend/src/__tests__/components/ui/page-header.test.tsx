import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PageHeader } from "@/components/ui/page-header";

describe("PageHeader", () => {
  it("renders the title", () => {
    render(<PageHeader title="Books" addLabel="Add Book" onAdd={jest.fn()} />);
    expect(screen.getByText("Books")).toBeInTheDocument();
  });

  it("renders the add button with provided label", () => {
    render(<PageHeader title="Members" addLabel="Add Member" onAdd={jest.fn()} />);
    expect(screen.getByRole("button", { name: /Add Member/i })).toBeInTheDocument();
  });

  it("calls onAdd when the button is clicked", async () => {
    const onAdd = jest.fn();
    render(<PageHeader title="Members" addLabel="Add Member" onAdd={onAdd} />);
    await userEvent.click(screen.getByRole("button", { name: /Add Member/i }));
    expect(onAdd).toHaveBeenCalledTimes(1);
  });

  it("renders the Plus icon inside the button", () => {
    const { container } = render(
      <PageHeader title="Books" addLabel="Add Book" onAdd={jest.fn()} />
    );
    expect(container.querySelector("button svg")).toBeInTheDocument();
  });
});
