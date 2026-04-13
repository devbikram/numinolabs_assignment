import type { FieldError } from "react-hook-form";

interface FieldErrorMsgProps {
  error?: FieldError;
  /** "sm" matches member-form style, "xs" (default) matches book-form style */
  size?: "xs" | "sm";
}

export function FieldErrorMsg({ error, size = "xs" }: FieldErrorMsgProps) {
  if (!error?.message) return null;
  const className =
    size === "sm" ? "text-sm text-destructive" : "text-xs text-destructive";
  return <p className={className}>{error.message}</p>;
}
