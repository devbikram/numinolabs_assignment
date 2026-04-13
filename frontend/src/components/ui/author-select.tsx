"use client";

import { useState, useRef, useCallback, useMemo } from "react";
import { useClickOutside } from "@/hooks/use-click-outside";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { Button } from "@/components/ui/button";
import { Check, ChevronsUpDown, Plus, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthors, useCreateAuthor } from "@/lib/queries/authors";
import { toast } from "sonner";

interface AuthorOption {
  id: string;
  name: string;
  book_count: number;
}

function formatAuthor(a: AuthorOption) {
  return `${a.name} (${a.book_count})`;
}

/* -------------------------------------------------- */
/*  Single-select variant                             */
/* -------------------------------------------------- */
interface SingleProps {
  mode?: "single";
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  id?: string;
}

/* -------------------------------------------------- */
/*  Multi-select variant                              */
/* -------------------------------------------------- */
interface MultiProps {
  mode: "multi";
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
  id?: string;
}

type AuthorSelectProps = SingleProps | MultiProps;

export function AuthorSelect(props: AuthorSelectProps) {
  const { data: authorsData } = useAuthors();
  const createAuthor = useCreateAuthor();
  const authors: AuthorOption[] = authorsData?.items ?? [];

  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);
  const handleClose = useCallback(() => setOpen(false), []);
  useClickOutside(ref, handleClose, open);

  const isMulti = props.mode === "multi";

  /* ── Display label (memoised to avoid recalculation on every render) ─── */
  const displayLabel = useMemo(() => {
    if (isMulti) {
      const selected = authors.filter((a) => (props as MultiProps).value.includes(a.id));
      return selected.length > 0 ? selected.map((a) => a.name).join(", ") : (props.placeholder ?? "Select authors...");
    } else {
      const selected = authors.find((a) => a.id === (props as SingleProps).value);
      return selected ? formatAuthor(selected) : (props.placeholder ?? "All authors");
    }
  }, [isMulti, authors, props]);

  /* ── Check if search matches any existing author ─ */
  const trimmedSearch = search.trim();
  const exactMatch = trimmedSearch.length > 0 && authors.some(
    (a) => a.name.toLowerCase() === trimmedSearch.toLowerCase()
  );

  /* ── Create new author ────────────────────────── */
  async function handleCreateAuthor() {
    if (!trimmedSearch) return;
    if (trimmedSearch.length > 255) {
      toast.error("Author name must be 255 characters or fewer");
      return;
    }
    try {
      const newAuthor = await createAuthor.mutateAsync({ name: trimmedSearch });
      if (isMulti) {
        props.onChange([...props.value, newAuthor.id]);
      } else {
        props.onChange(newAuthor.id);
      }
      setSearch("");
      toast.success(`Author "${newAuthor.name}" created`);
    } catch {
      toast.error("Failed to create author");
    }
  }

  /* ── Handlers ─────────────────────────────────── */
  function handleSingleSelect(authorId: string) {
    if (!isMulti) {
      props.onChange(authorId);
      setOpen(false);
    }
  }

  function handleMultiToggle(authorId: string) {
    if (isMulti) {
      const current = props.value;
      if (current.includes(authorId)) {
        props.onChange(current.filter((id) => id !== authorId));
      } else {
        props.onChange([...current, authorId]);
      }
    }
  }

  return (
    <div
      className="relative"
      ref={ref}
      onKeyDown={(e) => { if (e.key === "Escape") setOpen(false); }}
    >
      <Button
        id={props.id}
        type="button"
        variant="outline"
        role="combobox"
        aria-expanded={open}
        aria-haspopup="listbox"
        onClick={() => setOpen(!open)}
        className="w-full justify-between font-normal"
      >
        <span className="truncate">{displayLabel}</span>
        <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
      </Button>

      {open && (
        <div className="absolute top-full left-0 z-50 mt-1 w-full rounded-lg border bg-popover shadow-md">
          <Command shouldFilter={true}>
            <CommandInput
              placeholder="Search or add author..."
              value={search}
              onValueChange={setSearch}
            />
            <CommandList>
              <CommandEmpty>
                {trimmedSearch.length > 0 ? (
                  <button
                    type="button"
                    onClick={handleCreateAuthor}
                    disabled={createAuthor.isPending}
                    className="flex w-full items-center gap-2 px-2 py-1.5 text-sm hover:bg-accent rounded cursor-pointer disabled:opacity-50"
                  >
                    {createAuthor.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Plus className="h-4 w-4" />
                    )}
                    Create &quot;{trimmedSearch}&quot;
                  </button>
                ) : (
                  "No authors found."
                )}
              </CommandEmpty>
              <CommandGroup>
                {/* "All authors" option for single-select */}
                {!isMulti && (
                  <CommandItem
                    value="__all_authors__"
                    onSelect={() => handleSingleSelect("")}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        !props.value ? "opacity-100" : "opacity-0"
                      )}
                    />
                    All authors
                  </CommandItem>
                )}

                {authors.map((a) => {
                  const checked = isMulti
                    ? props.value.includes(a.id)
                    : props.value === a.id;

                  return (
                    <CommandItem
                      key={a.id}
                      value={a.name}
                      onSelect={() =>
                        isMulti
                          ? handleMultiToggle(a.id)
                          : handleSingleSelect(a.id)
                      }
                    >
                      <Check
                        className={cn(
                          "mr-2 h-4 w-4",
                          checked ? "opacity-100" : "opacity-0"
                        )}
                      />
                      {formatAuthor(a)}
                    </CommandItem>
                  );
                })}
              </CommandGroup>

            </CommandList>
          </Command>
        </div>
      )}
    </div>
  );
}
