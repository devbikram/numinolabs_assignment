import React from "react";
import { render, screen } from "@testing-library/react";
import {
  Table,
  TableBody,
  TableRow,
} from "@/components/ui/table";
import { TableEmptyRow } from "@/components/ui/table-empty-row";

function Wrapper({ colSpan, label }: { colSpan: number; label: string }) {
  return (
    <Table>
      <TableBody>
        <TableEmptyRow colSpan={colSpan} label={label} />
      </TableBody>
    </Table>
  );
}

describe("TableEmptyRow", () => {
  it("renders the label text", () => {
    render(<Wrapper colSpan={5} label="No books found." />);
    expect(screen.getByText("No books found.")).toBeInTheDocument();
  });

  it("applies the expected CSS classes", () => {
    render(<Wrapper colSpan={5} label="Empty" />);
    const cell = screen.getByRole("cell", { name: "Empty" });
    expect(cell).toHaveClass("text-center", "text-muted-foreground");
  });

  it("sets the correct colSpan attribute", () => {
    render(<Wrapper colSpan={7} label="Empty" />);
    const cell = screen.getByRole("cell", { name: "Empty" });
    expect(cell).toHaveAttribute("colspan", "7");
  });
});
