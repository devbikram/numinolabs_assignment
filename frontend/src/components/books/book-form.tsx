"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useCreateBook, useUpdateBook } from "@/lib/queries/books";
import type { Book } from "@/types";
import { FormDialog } from "@/components/ui/form-dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AuthorSelect } from "@/components/ui/author-select";
import { CategorySelect } from "@/components/ui/category-select";
import { FormFooter } from "@/components/ui/form-footer";
import { FieldErrorMsg } from "@/components/ui/field-error";
import { toastError } from "@/lib/errors";
import { toast } from "sonner";

const bookSchema = z.object({
  title: z.string().min(1, "Title is required").max(500),
  author_ids: z.array(z.string()).min(1, "At least one author is required"),
  isbn: z
    .string()
    .regex(/^\d{10}(\d{3})?$/, "Must be 10 or 13 digits"),
  category_id: z.string().nullable().optional(),
  published_year: z.coerce
    .number()
    .min(1000)
    .max(2100)
    .nullable()
    .optional(),
  total_copies: z.coerce.number().int().min(1),
  available_copies: z.coerce.number().int().min(0),
}).refine(
  (d) => (d.available_copies ?? 0) <= d.total_copies,
  { message: "Available copies cannot exceed total copies", path: ["available_copies"] }
);

type BookFormValues = z.infer<typeof bookSchema>;

interface BookFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  book?: Book | null;
}

export function BookForm({ open, onOpenChange, book }: BookFormProps) {
  const isEdit = !!book;
  const createBook = useCreateBook();
  const updateBook = useUpdateBook();
  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<BookFormValues>({
    resolver: zodResolver(bookSchema),
    defaultValues: {
      title: "",
      author_ids: [],
      isbn: "",
      category_id: null,
      published_year: null,
      total_copies: 1,
      available_copies: 1,
    },
  });

  const selectedAuthorIds = watch("author_ids");

  useEffect(() => {
    if (open) {
      reset(
        book
          ? {
              title: book.title,
              author_ids: book.authors.map((a) => a.id),
              isbn: book.isbn,
              category_id: book.category_id,
              published_year: book.published_year,
              total_copies: book.total_copies,
              available_copies: book.available_copies,
            }
          : {
              title: "",
              author_ids: [],
              isbn: "",
              category_id: null,
              published_year: null,
              total_copies: 1,
              available_copies: 1,
            }
      );
    }
  }, [open, book, reset]);

  async function onSubmit(data: BookFormValues) {
    try {
      const payload = {
        ...data,
        category_id: data.category_id || null,
        published_year: data.published_year ?? null,
        available_copies: isEdit ? data.available_copies : data.total_copies,
      };
      if (isEdit) {
        await updateBook.mutateAsync({ id: book.id, data: payload });
        toast.success("Book updated");
      } else {
        await createBook.mutateAsync(payload);
        toast.success("Book created");
      }
      reset();
      onOpenChange(false);
    } catch (e) {
      toastError(e);
    }
  }

  return (
    <FormDialog
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Edit Book" : "Add Book"}
      onSubmit={handleSubmit(onSubmit)}
      className="sm:max-w-md"
    >
      <div className="space-y-2">
        <Label htmlFor="title">Title</Label>
        <Input id="title" {...register("title")} />
        <FieldErrorMsg error={errors.title} />
      </div>
      <div className="space-y-2">
        <Label htmlFor="book-authors">Author(s)</Label>
        <AuthorSelect
          id="book-authors"
          mode="multi"
          value={selectedAuthorIds ?? []}
          onChange={(ids) => setValue("author_ids", ids)}
        />
      </div>
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="isbn">ISBN</Label>
          <span className="text-xs text-muted-foreground">{(watch("isbn") || "").length}/13</span>
        </div>
        <Input id="isbn" {...register("isbn")} placeholder="10 or 13 digits" />
        <FieldErrorMsg error={errors.isbn} />
      </div>
      <div className="space-y-2">
        <Label htmlFor="book-category">Category</Label>
        <CategorySelect
          id="book-category"
          value={watch("category_id") ?? ""}
          onChange={(v) => setValue("category_id", v || null)}
          placeholder="No category"
          emptyLabel="No category"
        />
      </div>
      <div className={`grid gap-3 ${isEdit ? "grid-cols-3" : "grid-cols-2"}`}>
        <div className="space-y-2">
          <Label htmlFor="published_year">Year</Label>
          <Input
            id="published_year"
            type="number"
            {...register("published_year", { valueAsNumber: true })}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="total_copies">{isEdit ? "Total" : "Copies"}</Label>
          <Input
            id="total_copies"
            type="number"
            {...register("total_copies", { valueAsNumber: true })}
          />
        </div>
        {isEdit && (
          <div className="space-y-2">
            <Label htmlFor="available_copies">Available</Label>
            <Input
              id="available_copies"
              type="number"
              {...register("available_copies", { valueAsNumber: true })}
            />
          </div>
        )}
      </div>
      <FormFooter
        isSubmitting={isSubmitting}
        isEdit={isEdit}
        onCancel={() => onOpenChange(false)}
      />
    </FormDialog>
  );
}
