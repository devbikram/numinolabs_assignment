import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FormFooter } from "@/components/ui/form-footer";

describe("FormFooter", () => {
  it("renders Cancel button", () => {
    render(<FormFooter isSubmitting={false} isEdit={false} onCancel={jest.fn()} />);
    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
  });

  it("renders Create button when not editing", () => {
    render(<FormFooter isSubmitting={false} isEdit={false} onCancel={jest.fn()} />);
    expect(screen.getByRole("button", { name: "Create" })).toBeInTheDocument();
  });

  it("renders Update button when editing", () => {
    render(<FormFooter isSubmitting={false} isEdit={true} onCancel={jest.fn()} />);
    expect(screen.getByRole("button", { name: "Update" })).toBeInTheDocument();
  });

  it("renders Saving... and disables submit while submitting", () => {
    render(<FormFooter isSubmitting={true} isEdit={false} onCancel={jest.fn()} />);
    const submitBtn = screen.getByRole("button", { name: "Saving..." });
    expect(submitBtn).toBeDisabled();
  });

  it("calls onCancel when Cancel button is clicked", async () => {
    const onCancel = jest.fn();
    render(<FormFooter isSubmitting={false} isEdit={false} onCancel={onCancel} />);
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
