import React from "react";
import { render, screen } from "@testing-library/react";
import { FieldErrorMsg } from "@/components/ui/field-error";
import type { FieldError } from "react-hook-form";

function makeError(message: string): FieldError {
  return { message, type: "required" };
}

describe("FieldErrorMsg", () => {
  it("renders the error message", () => {
    render(<FieldErrorMsg error={makeError("This field is required")} />);
    expect(screen.getByText("This field is required")).toBeInTheDocument();
  });

  it("returns null when error is undefined", () => {
    const { container } = render(<FieldErrorMsg />);
    expect(container.firstChild).toBeNull();
  });

  it("returns null when error has no message", () => {
    const { container } = render(<FieldErrorMsg error={{ type: "required" } as FieldError} />);
    expect(container.firstChild).toBeNull();
  });

  it("uses text-xs by default", () => {
    render(<FieldErrorMsg error={makeError("Error")} />);
    expect(screen.getByText("Error")).toHaveClass("text-xs");
  });

  it("uses text-sm when size is sm", () => {
    render(<FieldErrorMsg error={makeError("Error")} size="sm" />);
    expect(screen.getByText("Error")).toHaveClass("text-sm");
    expect(screen.getByText("Error")).not.toHaveClass("text-xs");
  });

  it("always applies text-destructive", () => {
    render(<FieldErrorMsg error={makeError("Error")} />);
    expect(screen.getByText("Error")).toHaveClass("text-destructive");
  });
});
