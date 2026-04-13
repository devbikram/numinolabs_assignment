import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemberForm } from "@/components/members/member-form";

jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));

const mockCreateMutateAsync = jest.fn();
const mockUpdateMutateAsync = jest.fn();

jest.mock("@/lib/queries/members", () => ({
  useCreateMember: () => ({ mutateAsync: mockCreateMutateAsync, isPending: false }),
  useUpdateMember: () => ({ mutateAsync: mockUpdateMutateAsync, isPending: false }),
}));

describe("MemberForm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders Add Member title when no member prop", () => {
    render(<MemberForm open={true} onOpenChange={jest.fn()} />);
    expect(screen.getByText("Add Member")).toBeInTheDocument();
  });

  it("renders Edit Member title when member is provided", () => {
    const member = {
      id: "1",
      library_id: "LIB-001",
      full_name: "Alice",
      email: "alice@example.com",
      phone: null,
      address: null,
      created_at: "",
      updated_at: "",
    };
    render(<MemberForm open={true} onOpenChange={jest.fn()} member={member} />);
    expect(screen.getByText("Edit Member")).toBeInTheDocument();
  });

  it("does not render dialog content when open=false", () => {
    render(<MemberForm open={false} onOpenChange={jest.fn()} />);
    expect(screen.queryByText("Add Member")).not.toBeInTheDocument();
  });

  it("renders Name, Email, Phone, Address fields", () => {
    render(<MemberForm open={true} onOpenChange={jest.fn()} />);
    expect(screen.getByLabelText("Full Name")).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Phone")).toBeInTheDocument();
    expect(screen.getByLabelText("Address")).toBeInTheDocument();
  });

  it("shows validation errors for empty required fields on submit", async () => {
    render(<MemberForm open={true} onOpenChange={jest.fn()} />);
    await userEvent.click(screen.getByRole("button", { name: "Create" }));
    expect(await screen.findByText(/name is required/i)).toBeInTheDocument();
  });

  it("calls onOpenChange(false) when Cancel is clicked", async () => {
    const onOpenChange = jest.fn();
    render(<MemberForm open={true} onOpenChange={onOpenChange} />);
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("calls createMember and closes dialog on valid submit", async () => {
    mockCreateMutateAsync.mockResolvedValue({ id: "new" });
    const onOpenChange = jest.fn();
    render(<MemberForm open={true} onOpenChange={onOpenChange} />);
    await userEvent.type(screen.getByLabelText("Full Name"), "Bob Jones");
    await userEvent.type(screen.getByLabelText("Email"), "bob@example.com");
    await userEvent.click(screen.getByRole("button", { name: "Create" }));
    expect(mockCreateMutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({ full_name: "Bob Jones", email: "bob@example.com" })
    );
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
