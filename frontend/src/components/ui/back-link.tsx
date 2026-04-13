import Link from "next/link";
import { ArrowLeft } from "lucide-react";

interface BackLinkProps {
  href: string;
  label: string;
  /** Use compact styling (no font-medium, slightly less prominent) */
  compact?: boolean;
}

export function BackLink({ href, label, compact = false }: BackLinkProps) {
  return (
    <Link
      href={href}
      className={
        compact
          ? "inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
          : "inline-flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
      }
    >
      <ArrowLeft className="h-4 w-4" /> {label}
    </Link>
  );
}
