import React from "react";
import { render, screen } from "@testing-library/react";
import { StatCard } from "@/components/ui/stat-card";

describe("StatCard", () => {
  it("renders the value and label in default mode", () => {
    render(<StatCard value={42} label="Total Borrows" />);
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("Total Borrows")).toBeInTheDocument();
  });

  it("uses large font class in default (non-compact) mode", () => {
    const { container } = render(<StatCard value={10} label="Readers" />);
    expect(container.querySelector(".text-3xl")).toBeInTheDocument();
  });

  it("renders the value and label in compact mode", () => {
    render(<StatCard value={7} label="Active Borrows" compact />);
    expect(screen.getByText("7")).toBeInTheDocument();
    expect(screen.getByText("Active Borrows")).toBeInTheDocument();
  });

  it("uses smaller font class in compact mode", () => {
    const { container } = render(<StatCard value={7} label="x" compact />);
    expect(container.querySelector(".text-2xl")).toBeInTheDocument();
    expect(container.querySelector(".text-3xl")).not.toBeInTheDocument();
  });

  it("renders ReactNode value (e.g. a string with special characters)", () => {
    render(<StatCard value="—" label="Most Borrowed" />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});
