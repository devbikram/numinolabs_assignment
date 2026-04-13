"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useBook, useBookStats } from "@/lib/queries/books";
import { safeFormat } from "@/lib/utils";
import { useBookBorrowings } from "@/lib/queries/borrowings";
import { BorrowingTable } from "@/components/borrowings/borrowing-table";
import { Badge } from "@/components/ui/badge";
import { Pagination } from "@/components/ui/pagination";
import { BackLink } from "@/components/ui/back-link";
import { MetaField } from "@/components/ui/meta-field";
import { StatCard } from "@/components/ui/stat-card";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { DEFAULT_PAGE_SIZE } from "@/lib/routes";

export default function BookDetailsPage() {
  const { id } = useParams<{ id: string }>();
  const { data: book, isLoading: bookLoading, isError: bookError } = useBook(id);
  const { data: stats } = useBookStats(id);
  const [skip, setSkip] = useState(0);
  const { data: borrowingsData, isLoading: borrowingsLoading } =
    useBookBorrowings(id, skip, DEFAULT_PAGE_SIZE);

  if (bookLoading) {
    return <LoadingSpinner />;
  }

  if (bookError) {
    return <p className="text-destructive p-6">Failed to load book. Please try again.</p>;
  }

  if (!book) {
    return <p className="text-destructive p-6">Book not found.</p>;
  }

  const borrowings = borrowingsData?.items ?? [];
  const total = borrowingsData?.total ?? 0;

  return (
    <div className="space-y-8">
      <BackLink href="/books" label="Back to Books" />

      {/* Book info card */}
      <div className="rounded-lg border bg-card p-8 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">{book.title}</h1>
            {book.authors.length > 0 && (
              <p className="text-sm text-muted-foreground mt-1">
                by{" "}
                {book.authors.map((a, i) => (
                  <span key={a.id}>
                    {i > 0 && ", "}
                    <Link
                      href={`/authors/${a.id}`}
                      className="hover:underline"
                    >
                      {a.name}
                    </Link>
                  </span>
                ))}
              </p>
            )}
          </div>
          <Badge
            variant={book.available_copies > 0 ? "default" : "destructive"}
            className="text-sm"
          >
            {book.available_copies} / {book.total_copies} available
          </Badge>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <MetaField label="ISBN" value={book.isbn} mono />
          <MetaField label="Category" value={book.category?.name ?? "—"} />
          <MetaField label="Published Year" value={book.published_year ?? "—"} />
          <MetaField label="Added" value={safeFormat(book.created_at, "MMM d, yyyy")} />
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatCard value={stats.total_borrows} label="Total Borrows" />
          <StatCard value={stats.active_borrows} label="Active Borrows" />
          <StatCard value={stats.unique_readers} label="Unique Readers" />
        </div>
      )}

      {/* Borrowing history */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold tracking-tight">Borrowings</h2>

        {borrowingsLoading ? (
          <p className="text-muted-foreground">Loading borrowings...</p>
        ) : (
          <>
            <BorrowingTable
              borrowings={borrowings}
              showBook={false}
              showReturned
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
