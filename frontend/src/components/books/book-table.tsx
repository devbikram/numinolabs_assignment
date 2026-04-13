"use client";

import { memo, useState } from "react";
import Link from "next/link";
import type { Book } from "@/types";
import { useDeleteBook } from "@/lib/queries/books";
import type { SortDirection } from "@/hooks/use-server-sort";
import { SortableHeader } from "@/components/ui/sortable-header";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { TableCard } from "@/components/ui/table-card";
import { TableEmptyRow } from "@/components/ui/table-empty-row";
import { RowActions } from "@/components/ui/row-actions";
import { toastError } from "@/lib/errors";
import { toast } from "sonner";
import { DeleteConfirmationDialog } from "@/components/ui/delete-confirmation-dialog";

interface BookTableProps {
  books: Book[];
  onEdit?: (book: Book) => void;
  showAuthors?: boolean;
  showBorrows?: boolean;
  showActions?: boolean;
  emptyLabel?: string;
  sortKey?: string;
  sortDirection?: SortDirection;
  onSort?: (key: string) => void;
}

export const BookTable = memo(function BookTable({
  books,
  onEdit,
  showAuthors = true,
  showBorrows = false,
  showActions = true,
  emptyLabel = "No books found.",
  sortKey = "",
  sortDirection = "asc",
  onSort,
}: BookTableProps) {
  const deleteBook = useDeleteBook();
  const [deleteTarget, setDeleteTarget] = useState<Book | null>(null);

  async function handleDeleteConfirm() {
    if (!deleteTarget) return;
    try {
      await deleteBook.mutateAsync(deleteTarget.id);
      toast.success("Book deleted");
      setDeleteTarget(null);
    } catch (e) {
      toastError(e, "Failed to delete");
    }
  }

  const colCount =
    5 + (showAuthors ? 1 : 0) + (showBorrows ? 1 : 0) + (showActions ? 1 : 0);

  return (
    <>
    <TableCard>
      <Table className="min-w-[700px]">
        <TableHeader>
          <TableRow>
            <SortableHeader label="Title" sortKey="title" currentKey={sortKey} direction={sortDirection} onSort={onSort ?? (() => {})} className="w-[25%]" />
            {showAuthors && (
              <TableHead className="w-[25%]">Author(s)</TableHead>
            )}
            <TableHead>Category</TableHead>
            <SortableHeader label="ISBN" sortKey="isbn" currentKey={sortKey} direction={sortDirection} onSort={onSort ?? (() => {})} />
            <SortableHeader label="Year" sortKey="published_year" currentKey={sortKey} direction={sortDirection} onSort={onSort ?? (() => {})} />
            {showBorrows && (
              <TableHead className="text-center">Borrows</TableHead>
            )}
            <SortableHeader label="Copies" sortKey="available_copies" currentKey={sortKey} direction={sortDirection} onSort={onSort ?? (() => {})} className="text-center" />
            {showActions && <TableHead className="text-right">Actions</TableHead>}
          </TableRow>
        </TableHeader>
        <TableBody>
          {books.length === 0 ? (
            <TableEmptyRow colSpan={colCount} label={emptyLabel} />
          ) : (
            books.map((book) => (
              <TableRow key={book.id}>
                <TableCell className="font-medium">
                  <Link href={`/books/${book.id}`} className="hover:underline">{book.title}</Link>
                </TableCell>
                {showAuthors && (
                  <TableCell>{book.authors.map((a, i) => (
                    <span key={a.id}>
                      {i > 0 && ", "}
                      <Link href={`/authors/${a.id}`} className="hover:underline">{a.name}</Link>
                    </span>
                  )) || "—"}</TableCell>
                )}
                <TableCell>{book.category?.name ?? "—"}</TableCell>
                <TableCell className="font-mono text-sm">{book.isbn}</TableCell>
                <TableCell>{book.published_year ?? "—"}</TableCell>
                {showBorrows && (
                  <TableCell className="text-center font-mono text-sm">
                    {book.borrow_count}
                  </TableCell>
                )}
                <TableCell className="text-center">
                  <Badge
                    variant={book.available_copies > 0 ? "default" : "destructive"}
                  >
                    {book.available_copies} / {book.total_copies}
                  </Badge>
                </TableCell>
                {showActions && (
                  <TableCell className="text-right">
                    <RowActions
                      onEdit={() => onEdit?.(book)}
                      onDelete={() => setDeleteTarget(book)}
                    />
                  </TableCell>
                )}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </TableCard>

    <DeleteConfirmationDialog
      open={!!deleteTarget}
      onOpenChange={(open) => { if (!open) setDeleteTarget(null); }}
      title="Delete Book"
      description={`Are you sure you want to delete "${deleteTarget?.title}"? This action cannot be undone.`}
      isPending={deleteBook.isPending}
      onConfirm={handleDeleteConfirm}
    />
    </>
  );
});
