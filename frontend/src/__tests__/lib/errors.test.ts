import { toastError } from "@/lib/errors";
import { ApiError } from "@/lib/api";
import { toast } from "sonner";

jest.mock("sonner", () => ({ toast: { error: jest.fn() } }));

const mockToastError = toast.error as jest.Mock;

beforeEach(() => {
  mockToastError.mockClear();
});

describe("toastError", () => {
  it("shows generic message for 404 ApiError (no info leak)", () => {
    const err = new ApiError("Resource not found", 404);
    toastError(err);
    expect(mockToastError).toHaveBeenCalledWith("The requested item was not found.");
  });

  it("shows default fallback for unknown errors", () => {
    toastError(new Error("Generic error"));
    expect(mockToastError).toHaveBeenCalledWith("Something went wrong");
  });

  it("shows custom fallback when provided for non-ApiError", () => {
    toastError(new Error("oops"), "Failed to delete");
    expect(mockToastError).toHaveBeenCalledWith("Failed to delete");
  });

  it("handles non-Error values", () => {
    toastError("string error");
    expect(mockToastError).toHaveBeenCalledWith("Something went wrong");
  });

  it("handles null / undefined", () => {
    toastError(null);
    expect(mockToastError).toHaveBeenCalledWith("Something went wrong");
  });

  it("uses generic message for 409 conflict ApiError (security: no detail leak)", () => {
    const err = new ApiError("Email already exists", 409);
    toastError(err, "Custom fallback");
    expect(mockToastError).toHaveBeenCalledWith("This action conflicts with existing data.");
  });

  it("shows ApiError message for unmapped status codes (e.g. 422)", () => {
    const err = new ApiError("Unprocessable entity", 422);
    toastError(err, "Custom fallback");
    // 422 is not in GENERIC_MESSAGES, so falls back to the ApiError message
    expect(mockToastError).toHaveBeenCalledWith("Unprocessable entity");
  });
});
