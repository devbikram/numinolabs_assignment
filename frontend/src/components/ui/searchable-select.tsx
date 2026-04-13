"use client";

import { useRef, useCallback } from "react";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandList,
} from "@/components/ui/command";
import { Button } from "@/components/ui/button";
import { ChevronsUpDown } from "lucide-react";
import { useClickOutside } from "@/hooks/use-click-outside";

export interface SearchableSelectProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  searchPlaceholder: string;
  emptyText: string;
  onSearchChange?: (val: string) => void;
  children: (props: { value: string; onChange: (v: string) => void }) => React.ReactNode;
  id?: string;
}

export function SearchableSelect({
  open,
  onOpenChange,
  value,
  onChange,
  placeholder,
  searchPlaceholder,
  emptyText,
  onSearchChange,
  children,
  id,
}: SearchableSelectProps) {
  const ref = useRef<HTMLDivElement>(null);
  const handleClose = useCallback(() => onOpenChange(false), [onOpenChange]);
  useClickOutside(ref, handleClose, open);

  return (
    <div
      className="relative"
      ref={ref}
      onKeyDown={(e) => {
        if (e.key === "Escape") onOpenChange(false);
      }}
    >
      <Button
        type="button"
        id={id}
        variant="outline"
        role="combobox"
        aria-expanded={open}
        aria-haspopup="listbox"
        onClick={() => onOpenChange(!open)}
        className="w-full justify-between font-normal"
      >
        <span className="truncate">{placeholder}</span>
        <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
      </Button>
      {open && (
        <div className="absolute top-full left-0 z-50 mt-1 w-full rounded-lg border bg-popover shadow-md">
          <Command>
            <CommandInput placeholder={searchPlaceholder} onValueChange={onSearchChange} />
            <CommandList>
              <CommandEmpty>{emptyText}</CommandEmpty>
              <CommandGroup>{children({ value, onChange })}</CommandGroup>
            </CommandList>
          </Command>
        </div>
      )}
    </div>
  );
}
