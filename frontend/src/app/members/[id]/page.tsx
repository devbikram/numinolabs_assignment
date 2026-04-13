"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useMember, useMemberStats } from "@/lib/queries/members";
import { safeFormat } from "@/lib/utils";
import { useMemberBorrowings } from "@/lib/queries/borrowings";
import { BorrowingTable } from "@/components/borrowings/borrowing-table";
import { Badge } from "@/components/ui/badge";
import { Pagination } from "@/components/ui/pagination";
import { BackLink } from "@/components/ui/back-link";
import { MetaField } from "@/components/ui/meta-field";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { DEFAULT_PAGE_SIZE } from "@/lib/routes";

export default function MemberDetailsPage() {
  const { id } = useParams<{ id: string }>();
  const { data: member, isLoading: memberLoading, isError: memberError } = useMember(id);
  const { data: stats } = useMemberStats(id);
  const [skip, setSkip] = useState(0);
  const { data: borrowingsData, isLoading: borrowingsLoading } =
    useMemberBorrowings(id, skip, DEFAULT_PAGE_SIZE);

  if (memberLoading) {
    return <LoadingSpinner />;
  }

  if (memberError) {
    return <p className="text-destructive p-6">Failed to load member. Please try again.</p>;
  }

  if (!member) {
    return <p className="text-destructive p-6">Member not found.</p>;
  }

  const borrowings = borrowingsData?.items ?? [];
  const total = borrowingsData?.total ?? 0;

  return (
    <div className="space-y-8">
      {/* Back link */}
      <BackLink href="/members" label="Back to Members" />

      {/* Member info card */}
      <div className="rounded-lg border bg-card p-8 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">{member.full_name}</h1>
            <p className="text-sm text-muted-foreground font-mono mt-1">
              {member.library_id}
            </p>
          </div>
          <div className="flex gap-2 flex-wrap">
            <Badge variant="secondary" className="text-sm">
              {stats?.total ?? 0} total
            </Badge>
            <Badge variant="default" className="text-sm">
              {stats?.borrowed ?? 0} borrowed
            </Badge>
            <Badge variant="secondary" className="text-sm">
              {stats?.returned ?? 0} returned
            </Badge>
            {(stats?.overdue ?? 0) > 0 && (
              <Badge variant="destructive" className="text-sm">
                {stats?.overdue} overdue
              </Badge>
            )}
          </div>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <MetaField label="Email" value={member.email} />
          <MetaField label="Phone" value={member.phone ?? "—"} />
          <MetaField label="Address" value={member.address ?? "—"} />
          <MetaField label="Member Since" value={safeFormat(member.created_at, "MMM d, yyyy")} />
        </div>
      </div>

      {/* Transaction history */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold tracking-tight">Borrowings</h2>

        {borrowingsLoading ? (
          <p className="text-muted-foreground">Loading transactions...</p>
        ) : (
          <>
            <BorrowingTable
              borrowings={borrowings}
              showMember={false}
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
