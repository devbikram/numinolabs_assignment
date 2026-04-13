"use client";

import { useState, useMemo, useCallback } from "react";
import { format, subDays } from "date-fns";
import { useBorrowings } from "@/lib/queries/borrowings";
import { useDebounce } from "@/hooks/use-debounce";
import { BorrowingTable } from "@/components/borrowings/borrowing-table";
import { BorrowForm } from "@/components/borrowings/borrow-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search } from "lucide-react";
import { PageHeader } from "@/components/ui/page-header";
import { DataView } from "@/components/ui/data-view";
import { useServerSort } from "@/hooks/use-server-sort";
import { toast } from "sonner";
import type { BorrowStatus } from "@/types";
import { DEFAULT_PAGE_SIZE } from "@/lib/routes";

const STATUS_OPTIONS: { label: string; value: BorrowStatus | "all" }[] = [
  { label: "All", value: "all" },
  { label: "Borrowed", value: "borrowed" },
  { label: "Returned", value: "returned" },
  { label: "Overdue", value: "overdue" },
];

type DatePreset = "7d" | "30d" | "90d" | "custom";

const DATE_PRESETS: { label: string; value: DatePreset }[] = [
  { label: "Last 7 Days", value: "7d" },
  { label: "Last 30 Days", value: "30d" },
  { label: "Last 90 Days", value: "90d" },
  { label: "Custom Range", value: "custom" },
];

export default function BorrowingsPage() {
  const [statusFilter, setStatusFilter] = useState<BorrowStatus | "all">("all");
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);
  const [datePreset, setDatePreset] = useState<DatePreset>("7d");
  const [customFrom, setCustomFrom] = useState("");
  const [customTo, setCustomTo] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [skip, setSkip] = useState(0);
  const { sort, toggleSort } = useServerSort("borrowed_at", "desc");

  // Applied filter state — only updated on "Apply" click
  const [appliedPreset, setAppliedPreset] = useState<DatePreset>("7d");
  const [appliedCustomFrom, setAppliedCustomFrom] = useState("");
  const [appliedCustomTo, setAppliedCustomTo] = useState("");

  const { dateFrom, dateTo } = useMemo(() => {
    const today = format(new Date(), "yyyy-MM-dd");
    switch (appliedPreset) {
      case "7d":
        return { dateFrom: format(subDays(new Date(), 7), "yyyy-MM-dd"), dateTo: today };
      case "30d":
        return { dateFrom: format(subDays(new Date(), 30), "yyyy-MM-dd"), dateTo: today };
      case "90d":
        return { dateFrom: format(subDays(new Date(), 90), "yyyy-MM-dd"), dateTo: today };
      case "custom":
        return { dateFrom: appliedCustomFrom || undefined, dateTo: appliedCustomTo || undefined };
    }
  }, [appliedPreset, appliedCustomFrom, appliedCustomTo]);

  const applyDateFilter = useCallback(() => {
    if (datePreset === "custom" && customFrom && customTo && customFrom > customTo) {
      toast.error("Start date must be on or before end date");
      return;
    }
    setAppliedPreset(datePreset);
    setAppliedCustomFrom(customFrom);
    setAppliedCustomTo(customTo);
    setSkip(0);
  }, [datePreset, customFrom, customTo]);

  const isDirty = datePreset !== appliedPreset || customFrom !== appliedCustomFrom || customTo !== appliedCustomTo;

  const { data, isLoading, isError } = useBorrowings(
    skip,
    DEFAULT_PAGE_SIZE,
    statusFilter === "all" ? undefined : statusFilter,
    debouncedSearch || undefined,
    dateFrom,
    dateTo,
    sort
  );

  return (
    <div className="space-y-8">
      <PageHeader title="Borrowings" addLabel="Borrow Book" onAdd={() => setFormOpen(true)} />

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative w-full sm:max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            aria-label="Search borrowings"
            placeholder="Search by book title, member name, or library ID..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setSkip(0); }}
            className="pl-9"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {STATUS_OPTIONS.map((opt) => (
            <Button
              key={opt.value}
              size="sm"
              variant={statusFilter === opt.value ? "default" : "outline"}
              onClick={() => { setStatusFilter(opt.value); setSkip(0); }}
            >
              {opt.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Date filter */}
      <fieldset className="flex flex-wrap items-end gap-4">
        <legend className="sr-only">Date range filter</legend>
        <div className="space-y-1.5">
          <Label htmlFor="date-range-select" className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Date Filter</Label>
          <Select value={datePreset} onValueChange={(v) => setDatePreset(v as DatePreset)}>
            <SelectTrigger id="date-range-select" className="h-10 w-48 font-semibold">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {DATE_PRESETS.map((p) => (
                <SelectItem key={p.value} value={p.value}>
                  {p.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        {datePreset === "custom" && (
          <>
            <div className="space-y-1.5">
              <Label htmlFor="date-from" className="text-xs font-bold uppercase tracking-wide text-muted-foreground">From</Label>
              <Input
                id="date-from"
                type="date"
                aria-label="Filter start date"
                value={customFrom}
                onChange={(e) => setCustomFrom(e.target.value)}
                className="h-10 w-auto font-semibold"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="date-to" className="text-xs font-bold uppercase tracking-wide text-muted-foreground">To</Label>
              <Input
                id="date-to"
                type="date"
                aria-label="Filter end date"
                value={customTo}
                onChange={(e) => setCustomTo(e.target.value)}
                className="h-10 w-auto font-semibold"
              />
            </div>
          </>
        )}
        <Button size="lg" onClick={applyDateFilter} disabled={!isDirty} className="font-bold px-6 shadow-sm">
          Apply
        </Button>
      </fieldset>

      <DataView
        isLoading={isLoading}
        isError={isError}
        errorMessage="Failed to load borrowings. Please try again."
        total={data?.total ?? 0}
        skip={skip}
        limit={DEFAULT_PAGE_SIZE}
        onPageChange={setSkip}
      >
        <BorrowingTable
          borrowings={data?.items ?? []}
          sortKey={sort.key}
          sortDirection={sort.direction}
          onSort={toggleSort}
          emptyLabel={
            statusFilter !== "all" || debouncedSearch
              ? "No borrowings match your current filters."
              : "No borrowing records yet."
          }
        />
      </DataView>

      <BorrowForm open={formOpen} onOpenChange={setFormOpen} />
    </div>
  );
}
