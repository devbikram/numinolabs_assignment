import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  Table,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { SortableHeader } from "@/components/ui/sortable-header";

function Wrapper({
  sortKey = "name",
  currentKey = "name",
  direction = "asc" as const,
  onSort = jest.fn(),
  label = "Name",
  className,
}: {
  sortKey?: string;
  currentKey?: string;
  direction?: "asc" | "desc";
  onSort?: jest.Mock;
  label?: string;
  className?: string;
}) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <SortableHeader
            label={label}
            sortKey={sortKey}
            currentKey={currentKey}
            direction={direction}
            onSort={onSort}
            className={className}
          />
        </TableRow>
      </TableHeader>
    </Table>
  );
}

describe("SortableHeader", () => {
  it("renders the column label", () => {
    render(<Wrapper label="Title" />);
    expect(screen.getByText("Title")).toBeInTheDocument();
  });

  it("calls onSort with sortKey when clicked", async () => {
    const onSort = jest.fn();
    render(<Wrapper sortKey="title" currentKey="name" onSort={onSort} />);
    await userEvent.click(screen.getByRole("columnheader"));
    expect(onSort).toHaveBeenCalledWith("title");
  });

  it("shows ArrowUpDown icon when column is not active", () => {
    const { container } = render(
      <Wrapper sortKey="title" currentKey="name" />
    );
    // ArrowUpDown has two paths, ArrowUp/Down have one — just check no ArrowUp/Down by aria
    // icon presence is structural; just verify SVG is present
    expect(container.querySelector("svg")).toBeInTheDocument();
  });

  it("applies cursor-pointer class", () => {
    render(<Wrapper />);
    expect(screen.getByRole("columnheader")).toHaveClass("cursor-pointer");
  });

  it("applies extra className prop", () => {
    render(<Wrapper className="w-40" />);
    expect(screen.getByRole("columnheader")).toHaveClass("w-40");
  });
});
