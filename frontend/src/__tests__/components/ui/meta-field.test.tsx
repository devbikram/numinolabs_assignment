import React from "react";
import { render, screen } from "@testing-library/react";
import { MetaField } from "@/components/ui/meta-field";

describe("MetaField", () => {
  it("renders label and value", () => {
    render(<MetaField label="ISBN" value="9781234567890" />);
    expect(screen.getByText("ISBN")).toBeInTheDocument();
    expect(screen.getByText("9781234567890")).toBeInTheDocument();
  });

  it("applies font-mono class when mono=true", () => {
    const { container } = render(<MetaField label="ISBN" value="123" mono />);
    expect(container.querySelector(".font-mono")).toBeInTheDocument();
  });

  it("does not apply font-mono by default", () => {
    const { container } = render(<MetaField label="Category" value="Fiction" />);
    expect(container.querySelector(".font-mono")).not.toBeInTheDocument();
  });

  it("renders ReactNode value", () => {
    render(<MetaField label="Author" value={<strong>Tolkien</strong>} />);
    expect(screen.getByText("Tolkien")).toBeInTheDocument();
  });

  it("renders em-dash placeholder", () => {
    render(<MetaField label="Phone" value="—" />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});
