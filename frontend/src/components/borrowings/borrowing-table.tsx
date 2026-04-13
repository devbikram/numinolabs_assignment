"use client";

import type { Borrowing, BorrowStatus } from "@/types";
import { memo, useState } from "react";
import { useReturnBook } from "@/lib/queries/borrowings";
import type { SortDirection } from "@/hooks/use-server-sort";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { SortableHeader } from "@/components/ui/sortable-header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { TableCard } from "@/components/ui/table-card";
import { TableEmptyRow } from "@/components/ui/table-empty-row";
import { toastError } from "@/lib/errors";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { borrowStatusColors } from "@/lib/constants";
import { safeFormat } from "@/lib/utils";
import Link from "next/link";

interface BorrowingTableProps {
  borrowings: Borrowing[];
  showBook?: boolean;
  showMember?: boolean;
  showReturned?: boolean;
  emptyLabel?: string;
  sortKey?: string;
  sortDirection?: SortDirection;
  onSort?: (key: string) => void;
}

export const BorrowingTable = memo(function BorrowingTable({
  borrowings,
  showBook = true,
  showMember = true,
  showReturned = false,
  emptyLabel = "No borrowing records found.",
  sortKey = "",
  sortDirection = "asc",
  onSort,
}: BorrowingTableProps) {
  const returnBook = useReturnBook();
  const [confirmBorrowing, setConfirmBorrowing] = useState<Borrowing | null>(null);

  async function handleReturn(b: Borrowing) {
    try {
      await returnBook.mutateAsync(b.id);
      setConfirmBorrowing(null);
      toast.success("Book returned");
    } catch (e) {
      toastError(e, "Failed to return");
    }
  }

  const colCount =
    (showBook ? 1 : 0) +
    (showMember ? 2 : 0) +
    (showReturned ? 1 : 0) +
    4; // Borrowed + Due + Status + Actions

  return (
    <TableCard>
      <Table className="min-w-[600px]">
        <TableHeader>
          <TableRow>
            {showBook && (
              <TableHead className="w-[25%]">Book</TableHead>
            )}
            {showMember && (
              <TableHead>Member ID</TableHead>
            )}
            {showMember && (
              <TableHead className="w-[20%]">Member</TableHead>
            )}
            <SortableHeader label="Borrowed" sortKey="borrowed_at" currentKey={sortKey} direction={sortDirection} onSort={onSort ?? (() => {})} />
            <SortableHeader label="Due" sortKey="due_date" currentKey={sortKey} direction={sortDirection} onSort={onSort ?? (() => {})} />
            {showReturned && (
              <SortableHeader label="Returned" sortKey="returned_at" currentKey={sortKey} direction={sortDirection} onSort={onSort ?? (() => {})} />
            )}
            <SortableHeader label="Status" sortKey="status" currentKey={sortKey} direction={sortDirection} onSort={onSort ?? (() => {})} />
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {borrowings.length === 0 ? (
            <TableEmptyRow colSpan={colCount} label={emptyLabel} />
          ) : (
            borrowings.map((b) => (
              <TableRow key={b.id}>
                {showBook && (
                  <TableCell className="font-medium">
                    <Link href={`/books/${b.book.id}`} className="hover:underline">
                      {b.book.title}
                    </Link>
                  </TableCell>
                )}
                {showMember && (
                  <TableCell className="font-mono text-sm">
                    {b.member.library_id}
                  </TableCell>
                )}
                {showMember && (
                  <TableCell>
                    <Link href={`/members/${b.member.id}`} className="hover:underline font-medium">
                      {b.member.full_name}
                    </Link>
                    <div className="text-xs text-muted-foreground mt-0.5">
                      {b.member.email}
                    </div>
                    {b.member.phone && (
                      <div className="text-xs text-muted-foreground">
                        {b.member.phone}
                      </div>
                    )}
                  </TableCell>
                )}
                <TableCell>
                  {safeFormat(b.borrowed_at, "MMM d, yyyy")}
                </TableCell>
                <TableCell>
                  {safeFormat(b.due_date, "MMM d, yyyy")}
                </TableCell>
                {showReturned && (
                  <TableCell>
                    {b.returned_at
                      ? safeFormat(b.returned_at, "MMM d, yyyy")
                      : "—"}
                  </TableCell>
                )}
                <TableCell>
                  <Badge className={borrowStatusColors[b.status] ?? "bg-muted text-foreground"}>
                    {b.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  {b.status === "borrowed" || b.status === "overdue" ? (
                    <Button
                      size="sm"
                      onClick={() => setConfirmBorrowing(b)}
                      className="bg-emerald-600 text-white hover:bg-emerald-700 font-bold shadow-sm rounded-lg"
                    >
                      Return
                    </Button>
                  ) : !showReturned ? (
                    <span className="text-sm text-muted-foreground">
                      {b.returned_at
                        ? safeFormat(b.returned_at, "MMM d, yyyy")
                        : "—"}
                    </span>
                  ) : null}
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>

      <Dialog
        open={!!confirmBorrowing}
        onOpenChange={(open) => {
          if (!open) setConfirmBorrowing(null);
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold">
              Confirm Return
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to mark this book as returned?
            </DialogDescription>
          </DialogHeader>

          {confirmBorrowing && (
            <div className="grid gap-3 rounded-lg border bg-muted/40 p-4 text-sm">
              <div className="grid grid-cols-[100px_1fr] gap-1">
                <span className="font-semibold text-muted-foreground">Book</span>
                <span className="font-medium">{confirmBorrowing.book.title}</span>
              </div>
              <div className="grid grid-cols-[100px_1fr] gap-1">
                <span className="font-semibold text-muted-foreground">Member</span>
                <div>
                  <span className="font-medium">{confirmBorrowing.member.full_name}</span>
                  <div className="text-xs text-muted-foreground">{confirmBorrowing.member.email}</div>
                  {confirmBorrowing.member.phone && (
                    <div className="text-xs text-muted-foreground">{confirmBorrowing.member.phone}</div>
                  )}
                </div>
              </div>
              <div className="grid grid-cols-[100px_1fr] gap-1">
                <span className="font-semibold text-muted-foreground">Borrowed</span>
                <span>{safeFormat(confirmBorrowing.borrowed_at, "MMM d, yyyy")}</span>
              </div>
              <div className="grid grid-cols-[100px_1fr] gap-1">
                <span className="font-semibold text-muted-foreground">Due Date</span>
                <span>{safeFormat(confirmBorrowing.due_date, "MMM d, yyyy")}</span>
              </div>
              <div className="grid grid-cols-[100px_1fr] gap-1">
                <span className="font-semibold text-muted-foreground">Status</span>
                <Badge className={`w-fit ${borrowStatusColors[confirmBorrowing.status] ?? "bg-muted text-foreground"}`}>
                  {confirmBorrowing.status}
                </Badge>
              </div>
            </div>
          )}

          <DialogFooter>
            <DialogClose render={<Button variant="outline" />}>
              Cancel
            </DialogClose>
            <Button
              onClick={() => confirmBorrowing && handleReturn(confirmBorrowing)}
              disabled={returnBook.isPending}
              className="bg-emerald-600 text-white hover:bg-emerald-700 font-bold"
            >
              {returnBook.isPending ? "Returning…" : "Confirm Return"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </TableCard>
  );
});
