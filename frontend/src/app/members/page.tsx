"use client";

import { useState } from "react";
import { useMembers } from "@/lib/queries/members";
import { useDebounce } from "@/hooks/use-debounce";
import { MemberTable } from "@/components/members/member-table";
import { MemberForm } from "@/components/members/member-form";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";
import { DataView } from "@/components/ui/data-view";
import { useFormDialog } from "@/hooks/use-form-dialog";
import { useServerSort } from "@/hooks/use-server-sort";
import type { Member } from "@/types";
import { DEFAULT_PAGE_SIZE } from "@/lib/routes";

export default function MembersPage() {
  const [search, setSearch] = useState("");
  const [skip, setSkip] = useState(0);
  const debouncedSearch = useDebounce(search, 300);
  const { sort, toggleSort } = useServerSort("full_name");
  const { data, isLoading, isError } = useMembers(skip, DEFAULT_PAGE_SIZE, debouncedSearch || undefined, undefined, sort);
  const { formOpen, editing: editingMember, openCreate, openEdit, setFormOpen, closeForm } = useFormDialog<Member>();

  return (
    <div className="space-y-8">
      <PageHeader title="Members" addLabel="Add Member" onAdd={openCreate} />

      <div className="flex gap-3">
        <Input
          id="member-search"
          aria-label="Search members"
          placeholder="Search by name, email, or library ID..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setSkip(0); }}  // debounced via useDebounce
          className="w-full sm:max-w-sm"
        />
      </div>

      <DataView
        isLoading={isLoading}
        isError={isError}
        errorMessage="Failed to load members. Please try again."
        total={data?.total ?? 0}
        skip={skip}
        limit={DEFAULT_PAGE_SIZE}
        onPageChange={setSkip}
      >
        <MemberTable members={data?.items ?? []} onEdit={openEdit} sortKey={sort.key} sortDirection={sort.direction} onSort={toggleSort} />
      </DataView>

      <MemberForm
        open={formOpen}
        onOpenChange={(open) => { if (!open) closeForm(); }}
        member={editingMember}
      />
    </div>
  );
}
