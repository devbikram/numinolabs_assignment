"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useAuthor, useAuthorStats } from "@/lib/queries/authors";
import { safeFormat } from "@/lib/utils";
import { useBooks } from "@/lib/queries/books";
import { BookTable } from "@/components/books/book-table";
import { Badge } from "@/components/ui/badge";
import { Pagination } from "@/components/ui/pagination";
import { BackLink } from "@/components/ui/back-link";
import { StatCard } from "@/components/ui/stat-card";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { DEFAULT_PAGE_SIZE } from "@/lib/routes";

export default function AuthorDetailsPage() {
  const { id } = useParams<{ id: string }>();
  const { data: author, isLoading: authorLoading, isError: authorError } = useAuthor(id);
  const { data: stats } = useAuthorStats(id);
  const [skip, setSkip] = useState(0);
  const { data: booksData, isLoading: booksLoading } = useBooks(skip, DEFAULT_PAGE_SIZE, {
    author_id: id,
  });

  if (authorLoading) {
    return <LoadingSpinner />;
  }

  if (authorError) {
    return <p className="text-destructive p-6">Failed to load author. Please try again.</p>;
  }

  if (!author) {
    return <p className="text-destructive p-6">Author not found.</p>;
  }

  const books = booksData?.items ?? [];
  const total = booksData?.total ?? 0;

  return (
    <div className="space-y-6">
      <BackLink href="/books" label="Back to Books" compact />

      {/* Author info card */}
      <div className="rounded-lg border p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold">{author.name}</h1>
            {author.bio && (
              <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
                {author.bio}
              </p>
            )}
          </div>
          <Badge variant="secondary" className="text-sm">
            {author.book_count} book{author.book_count !== 1 ? "s" : ""}
          </Badge>
        </div>

        <div className="mt-4 text-xs text-muted-foreground">
          Added {safeFormat(author.created_at, "MMM d, yyyy")}
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard value={stats.total_borrows} label="Total Borrows" compact />
          <StatCard value={stats.active_borrows} label="Active Borrows" compact />
          <StatCard value={stats.unique_readers} label="Unique Readers" compact />
          <div className="rounded-lg border p-4 text-center">
            <p className="text-2xl font-bold truncate" title={stats.most_borrowed?.title}>
              {stats.most_borrowed?.title ?? "—"}
            </p>
            <p className="text-xs text-muted-foreground">
              Most Borrowed{stats.most_borrowed ? ` (${stats.most_borrowed.borrow_count}×)` : ""}
            </p>
          </div>
        </div>
      )}

      {/* Books list */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Books</h2>

        {booksLoading ? (
          <p className="text-muted-foreground">Loading books...</p>
        ) : (
          <>
            <BookTable
              books={books}
              showAuthors={false}
              showBorrows
              showActions={false}
            />
            <Pagination
              total={total}
              skip={skip}
              limit={DEFAULT_PAGE_SIZE}
              onPageChange={setSkip}
            />
          </>
        )}
      </div>
    </div>
  );
}
