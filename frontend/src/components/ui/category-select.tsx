"use client";

import { useState, useRef, useCallback } from "react";
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
import { Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { useCategories } from "@/lib/queries/categories";

interface CategorySelectProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  emptyLabel?: string;
  id?: string;
}

export function CategorySelect({
  value,
  onChange,
  placeholder = "All categories",
  emptyLabel = "All categories",
  id,
}: CategorySelectProps) {
  const { data: categoriesData } = useCategories();
  const categories = categoriesData?.items ?? [];

  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const handleClose = useCallback(() => setOpen(false), []);
  useClickOutside(ref, handleClose, open);

  const selected = categories.find((c) => c.id === value);
  const displayLabel = selected ? selected.name : placeholder;

  return (
    <div
      className="relative"
      ref={ref}
      onKeyDown={(e) => { if (e.key === "Escape") setOpen(false); }}
    >
      <Button
        id={id}
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
          <Command>
            <CommandInput placeholder="Search categories..." />
            <CommandList>
              <CommandEmpty>No categories found.</CommandEmpty>
              <CommandGroup>
                <CommandItem
                  value="__all_categories__"
                  onSelect={() => {
                    onChange("");
                    setOpen(false);
                  }}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      !value ? "opacity-100" : "opacity-0"
                    )}
                  />
                  {emptyLabel}
                </CommandItem>

                {categories.map((cat) => (
                  <CommandItem
                    key={cat.id}
                    value={cat.name}
                    onSelect={() => {
                      onChange(cat.id);
                      setOpen(false);
                    }}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        value === cat.id ? "opacity-100" : "opacity-0"
                      )}
                    />
                    {cat.name}
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </div>
      )}
    </div>
  );
}
