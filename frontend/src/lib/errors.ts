import { toast } from "sonner";
import { ApiError } from "@/lib/api";

/** Map sensitive HTTP statuses to generic user-facing messages (OWASP: avoid information leakage). */
const GENERIC_MESSAGES: Partial<Record<number, string>> = {
  401: "Session expired. Please sign in again.",
  403: "You do not have permission to perform this action.",
  404: "The requested item was not found.",
  409: "This action conflicts with existing data.",
  500: "A server error occurred. Please try again later.",
};

export function toastError(e: unknown, fallback = "Something went wrong"): void {
  if (e instanceof ApiError) {
    const safe = GENERIC_MESSAGES[e.status];
    toast.error(safe ?? e.message ?? fallback);
  } else {
    toast.error(fallback);
  }
}
