"use client";

import Link from "next/link";
import { memo, useState } from "react";
import type { Member } from "@/types";
import { useDeleteMember } from "@/lib/queries/members";
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
import { TableCard } from "@/components/ui/table-card";
import { TableEmptyRow } from "@/components/ui/table-empty-row";
import { RowActions } from "@/components/ui/row-actions";
import { toastError } from "@/lib/errors";
import { toast } from "sonner";
import { DeleteConfirmationDialog } from "@/components/ui/delete-confirmation-dialog";

interface MemberTableProps {
  members: Member[];
  onEdit: (member: Member) => void;
  sortKey?: string;
  sortDirection?: SortDirection;
  onSort?: (key: string) => void;
}

export const MemberTable = memo(function MemberTable({ members, onEdit, sortKey = "", sortDirection = "asc", onSort }: MemberTableProps) {
  const deleteMember = useDeleteMember();
  const [deleteTarget, setDeleteTarget] = useState<Member | null>(null);

  async function handleDeleteConfirm() {
    if (!deleteTarget) return;
    try {
      await deleteMember.mutateAsync(deleteTarget.id);
      toast.success("Member deleted");
      setDeleteTarget(null);
    } catch (e) {
      toastError(e, "Failed to delete");
    }
  }

  return (
    <>
    <TableCard>
      <Table className="min-w-[600px]">
        <TableHeader>
          <TableRow>
            <SortableHeader label="Library ID" sortKey="library_id" currentKey={sortKey} direction={sortDirection} onSort={onSort ?? (() => {})} />
            <SortableHeader label="Name" sortKey="full_name" currentKey={sortKey} direction={sortDirection} onSort={onSort ?? (() => {})} className="w-[20%]" />
            <SortableHeader label="Email" sortKey="email" currentKey={sortKey} direction={sortDirection} onSort={onSort ?? (() => {})} className="w-[25%]" />
            <SortableHeader label="Phone" sortKey="phone" currentKey={sortKey} direction={sortDirection} onSort={onSort ?? (() => {})} />
            <SortableHeader label="Address" sortKey="address" currentKey={sortKey} direction={sortDirection} onSort={onSort ?? (() => {})} />
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {members.length === 0 ? (
            <TableEmptyRow colSpan={6} label="No members found." />
          ) : (
            members.map((member) => (
              <TableRow key={member.id}>
                <TableCell className="font-mono text-sm">{member.library_id}</TableCell>
                <TableCell className="font-medium">
                  <Link
                    href={`/members/${member.id}`}
                    className="hover:underline text-primary"
                  >
                    {member.full_name}
                  </Link>
                </TableCell>
                <TableCell>{member.email}</TableCell>
                <TableCell>{member.phone ?? "—"}</TableCell>
                <TableCell>{member.address ?? "—"}</TableCell>
                <TableCell className="text-right">
                    <RowActions
                      onEdit={() => onEdit(member)}
                      onDelete={() => setDeleteTarget(member)}
                    />
                  </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </TableCard>

    <DeleteConfirmationDialog
      open={!!deleteTarget}
      onOpenChange={(open) => { if (!open) setDeleteTarget(null); }}
      title="Delete Member"
      description={`Are you sure you want to delete "${deleteTarget?.full_name}"? This action cannot be undone.`}
      isPending={deleteMember.isPending}
      onConfirm={handleDeleteConfirm}
    />
    </>
  );
});
