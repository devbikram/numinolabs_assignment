"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PaginationProps {
  total: number;
  skip: number;
  limit: number;
  onPageChange: (skip: number) => void;
}

export function Pagination({ total, skip, limit, onPageChange }: PaginationProps) {
  const currentPage = Math.floor(skip / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  function goTo(page: number) {
    onPageChange((page - 1) * limit);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // Build visible page numbers with ellipsis
  function getPages(): (number | "ellipsis")[] {
    const pages: (number | "ellipsis")[] = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
      return pages;
    }

    pages.push(1);
    if (currentPage > 3) pages.push("ellipsis");

    const start = Math.max(2, currentPage - 1);
    const end = Math.min(totalPages - 1, currentPage + 1);
    for (let i = start; i <= end; i++) pages.push(i);

    if (currentPage < totalPages - 2) pages.push("ellipsis");
    pages.push(totalPages);

    return pages;
  }

  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between">
      <p className="text-sm text-muted-foreground">
        Showing {skip + 1}–{Math.min(skip + limit, total)} of {total}
      </p>
      <nav aria-label="Pagination" className="flex items-center gap-1">
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          aria-label="Previous page"
          disabled={currentPage <= 1}
          onClick={() => goTo(currentPage - 1)}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>

        {getPages().map((p, i) =>
          p === "ellipsis" ? (
            <span key={`e${i}`} className="px-2 text-muted-foreground">
              …
            </span>
          ) : (
            <Button
              key={p}
              variant={p === currentPage ? "default" : "outline"}
              size="icon"
              className="h-8 w-8"
              aria-label={`Page ${p}`}
              aria-current={p === currentPage ? "page" : undefined}
              onClick={() => goTo(p)}>
              {p}
            </Button>
          )
        )}

        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          aria-label="Next page"
          disabled={currentPage >= totalPages}
          onClick={() => goTo(currentPage + 1)}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </nav>
    </div>
  );
}
