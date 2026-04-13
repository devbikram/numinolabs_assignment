import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import { format, parseISO, isValid } from "date-fns"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function safeFormat(dateStr: string | undefined | null, fmt: string): string {
  if (!dateStr) return "—";
  const d = parseISO(dateStr);
  return isValid(d) ? format(d, fmt) : "—";
}
