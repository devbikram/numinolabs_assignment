"use client";

import { useState, useMemo } from "react";
import { useBooks, type BookFilters } from "@/lib/queries/books";
import { BookTable } from "@/components/books/book-table";
import { BookForm } from "@/components/books/book-form";
import { AuthorSelect } from "@/components/ui/author-select";
import { CategorySelect } from "@/components/ui/category-select";
import { PageHeader } from "@/components/ui/page-header";
import { DataView } from "@/components/ui/data-view";
import { useFormDialog } from "@/hooks/use-form-dialog";
import { useServerSort } from "@/hooks/use-server-sort";
import type { Book } from "@/types";
import { DEFAULT_PAGE_SIZE } from "@/lib/routes";

export default function BooksPage() {
  const [authorFilter, setAuthorFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [skip, setSkip] = useState(0);
  const { sort, toggleSort } = useServerSort("title");

  const filters = useMemo<BookFilters>(() => ({
    author_id: authorFilter || undefined,
    category_id: categoryFilter || undefined,
  }), [authorFilter, categoryFilter]);
  const { data, isLoading, isError } = useBooks(skip, DEFAULT_PAGE_SIZE, filters, undefined, sort);
  const { formOpen, editing: editingBook, openCreate, openEdit, setFormOpen, closeForm } = useFormDialog<Book>();

  return (
    <div className="space-y-8">
      <PageHeader title="Books" addLabel="Add Book" onAdd={openCreate} />

      <div className="flex flex-wrap gap-3">
        <div className="w-full sm:w-56">
          <AuthorSelect
            value={authorFilter}
            onChange={(v) => { setAuthorFilter(v); setSkip(0); }}
          />
        </div>
        <div className="w-full sm:w-56">
          <CategorySelect
            value={categoryFilter}
            onChange={(v) => { setCategoryFilter(v); setSkip(0); }}
          />
        </div>
      </div>

      <DataView
        isLoading={isLoading}
        isError={isError}
        errorMessage="Failed to load books. Please try again."
        total={data?.total ?? 0}
        skip={skip}
        limit={DEFAULT_PAGE_SIZE}
        onPageChange={setSkip}
      >
        <BookTable
          books={data?.items ?? []}
          onEdit={openEdit}
          sortKey={sort.key}
          sortDirection={sort.direction}
          onSort={toggleSort}
          emptyLabel={
            authorFilter || categoryFilter
              ? "No books match your current filters."
              : "No books yet. Add your first book!"
          }
        />
      </DataView>

      <BookForm
        open={formOpen}
        onOpenChange={(open) => { if (!open) closeForm(); }}
        book={editingBook}
      />
    </div>
  );
}
