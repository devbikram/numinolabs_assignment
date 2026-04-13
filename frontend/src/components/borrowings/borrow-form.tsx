"use client";

import { useState, useMemo, useEffect } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { format, addDays } from "date-fns";

import { useBooks } from "@/lib/queries/books";
import { useMembers } from "@/lib/queries/members";
import { useCreateBorrowing } from "@/lib/queries/borrowings";
import { useDebounce } from "@/hooks/use-debounce";
import {
  CommandItem,
} from "@/components/ui/command";
import { FormDialog } from "@/components/ui/form-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { SearchableSelect } from "@/components/ui/searchable-select";
import { toast } from "sonner";
import { toastError } from "@/lib/errors";

const borrowSchema = z.object({
  book_id: z.string().min(1, "Select a book"),
  member_id: z.string().min(1, "Select a member"),
  due_date: z
    .string()
    .min(1, "Due date is required")
    .refine(
      (d) => d >= format(new Date(), "yyyy-MM-dd"),
      "Due date must be today or later"
    ),
});

type BorrowFormData = z.infer<typeof borrowSchema>;

interface BorrowFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function BorrowForm({ open, onOpenChange }: BorrowFormProps) {
  const [bookSearch, setBookSearch] = useState("");
  const [memberSearch, setMemberSearch] = useState("");
  const debouncedBookSearch = useDebounce(bookSearch, 300);
  const debouncedMemberSearch = useDebounce(memberSearch, 300);

  const { data: booksData } = useBooks(0, 30, { search: debouncedBookSearch || undefined }, { enabled: open });
  const { data: membersData } = useMembers(0, 30, debouncedMemberSearch || undefined, { enabled: open });
  const createBorrowing = useCreateBorrowing();

  const [bookOpen, setBookOpen] = useState(false);
  const [memberOpen, setMemberOpen] = useState(false);

  // Re-computed whenever the dialog opens so the default always reflects today + 14 days
  const defaultDue = useMemo(
    () => format(addDays(new Date(), 14), "yyyy-MM-dd"),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [open]
  );

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors, isSubmitting },
  } = useForm<BorrowFormData>({
    resolver: zodResolver(borrowSchema),
    defaultValues: { book_id: "", member_id: "", due_date: defaultDue },
  });

  // Reset form and search state when dialog opens/closes
  useEffect(() => {
    if (open) {
      reset({ book_id: "", member_id: "", due_date: defaultDue });
    } else {
      setBookSearch("");
      setMemberSearch("");
    }
  }, [open, defaultDue, reset]);

  async function onSubmit(data: BorrowFormData) {
    try {
      await createBorrowing.mutateAsync({
        ...data,
        due_date: `${data.due_date}T23:59:59Z`,
      });
      toast.success("Book borrowed successfully");
      onOpenChange(false);
    } catch (e) {
      toastError(e);
    }
  }

  const availableBooks = useMemo(
    () => (booksData?.items ?? []).filter((b) => b.available_copies > 0),
    [booksData]
  );
  const members = membersData?.items ?? [];

  return (
    <FormDialog
      open={open}
      onOpenChange={onOpenChange}
      title="Borrow a Book"
      onSubmit={handleSubmit(onSubmit)}
    >
      {/* Book searchable combobox */}
      <div className="space-y-1">
            <Label htmlFor="book-select">Book</Label>
            <Controller
              control={control}
              name="book_id"
              render={({ field }) => {
                const selected = availableBooks.find((b) => b.id === field.value);
                return (
                  <SearchableSelect
                    id="book-select"
                    open={bookOpen}
                    onOpenChange={setBookOpen}
                    value={field.value}
                    onChange={field.onChange}
                    onSearchChange={setBookSearch}
                    placeholder={
                      selected
                        ? `${selected.title} — ${selected.authors.map((a) => a.name).join(", ")}`
                        : "Search and select a book..."
                    }
                    searchPlaceholder="Search books..."
                    emptyText="No books found."
                  >
                    {({ value: currentValue, onChange }) =>
                      availableBooks.map((book) => (
                        <CommandItem
                          key={book.id}
                          value={`${book.title} ${book.authors.map((a) => a.name).join(" ")} ${book.isbn}`}
                          onSelect={() => {
                            onChange(book.id);
                            setBookOpen(false);
                          }}
                        >
                          <Check
                            className={cn(
                              "mr-2 h-4 w-4",
                              currentValue === book.id ? "opacity-100" : "opacity-0"
                            )}
                          />
                          <div className="flex flex-col">
                            <span>{book.title} — {book.authors.map((a) => a.name).join(", ") || ""}</span>
                            <span className="text-xs text-muted-foreground">
                              ISBN: {book.isbn} · {book.available_copies} available
                            </span>
                          </div>
                        </CommandItem>
                      ))
                    }
                  </SearchableSelect>
                );
              }}
            />
            {errors.book_id && (
              <p className="text-sm text-destructive">{errors.book_id.message}</p>
            )}
          </div>

          {/* Member searchable combobox */}
          <div className="space-y-1">
            <Label htmlFor="member-select">Member</Label>
            <Controller
              control={control}
              name="member_id"
              render={({ field }) => {
                const selected = members.find((m) => m.id === field.value);
                return (
                  <SearchableSelect
                    id="member-select"
                    open={memberOpen}
                    onOpenChange={setMemberOpen}
                    value={field.value}
                    onChange={field.onChange}
                    onSearchChange={setMemberSearch}
                    placeholder={
                      selected
                        ? `${selected.library_id} · ${selected.full_name}`
                        : "Search and select a member..."
                    }
                    searchPlaceholder="Search by name, email, or library ID..."
                    emptyText="No members found."
                  >
                    {({ value: currentValue, onChange }) =>
                      members.map((m) => (
                        <CommandItem
                          key={m.id}
                          value={`${m.library_id} ${m.full_name} ${m.email}`}
                          onSelect={() => {
                            onChange(m.id);
                            setMemberOpen(false);
                          }}
                        >
                          <Check
                            className={cn(
                              "mr-2 h-4 w-4",
                              currentValue === m.id ? "opacity-100" : "opacity-0"
                            )}
                          />
                          <div className="flex flex-col">
                            <span>{m.library_id} · {m.full_name}</span>
                            <span className="text-xs text-muted-foreground">
                              {m.email}
                            </span>
                          </div>
                        </CommandItem>
                      ))
                    }
                  </SearchableSelect>
                );
              }}
            />
            {errors.member_id && (
              <p className="text-sm text-destructive">{errors.member_id.message}</p>
            )}
          </div>

          <div className="space-y-1">
            <Label htmlFor="due_date">Due Date</Label>
            <Input id="due_date" type="date" {...register("due_date")} />
            {errors.due_date && (
              <p className="text-sm text-destructive">{errors.due_date.message}</p>
            )}
          </div>
          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              Borrow
            </Button>
          </div>
    </FormDialog>
  );
}
