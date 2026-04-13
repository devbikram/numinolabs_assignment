import React from "react";
import { render, screen } from "@testing-library/react";
import { TableCard } from "@/components/ui/table-card";

describe("TableCard", () => {
  it("renders children", () => {
    render(<TableCard><span>content</span></TableCard>);
    expect(screen.getByText("content")).toBeInTheDocument();
  });

  it("applies the base wrapper classes", () => {
    const { container } = render(<TableCard>child</TableCard>);
    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass("rounded-xl", "border", "overflow-hidden");
  });

  it("merges additional className via prop", () => {
    const { container } = render(
      <TableCard className="my-custom">child</TableCard>
    );
    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass("my-custom");
  });
});
