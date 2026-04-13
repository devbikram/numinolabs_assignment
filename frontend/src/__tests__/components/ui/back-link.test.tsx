import React from "react";
import { render, screen } from "@testing-library/react";
import { BackLink } from "@/components/ui/back-link";

// next/link renders an anchor tag in test environment
jest.mock("next/link", () => {
  const MockLink = ({
    href,
    children,
    className,
  }: {
    href: string;
    children: React.ReactNode;
    className?: string;
  }) => (
    <a href={href} className={className}>
      {children}
    </a>
  );
  MockLink.displayName = "MockLink";
  return MockLink;
});

describe("BackLink", () => {
  it("renders a link with the correct href", () => {
    render(<BackLink href="/books" label="Back to Books" />);
    expect(screen.getByRole("link")).toHaveAttribute("href", "/books");
  });

  it("renders the label text", () => {
    render(<BackLink href="/members" label="Back to Members" />);
    expect(screen.getByText("Back to Members")).toBeInTheDocument();
  });

  it("applies font-medium class in default mode", () => {
    render(<BackLink href="/books" label="Back" />);
    expect(screen.getByRole("link")).toHaveClass("font-medium");
  });

  it("does not apply font-medium in compact mode", () => {
    render(<BackLink href="/books" label="Back" compact />);
    expect(screen.getByRole("link")).not.toHaveClass("font-medium");
  });

  it("renders the ArrowLeft icon", () => {
    const { container } = render(<BackLink href="/books" label="Back" />);
    // Lucide renders an SVG
    expect(container.querySelector("svg")).toBeInTheDocument();
  });
});
