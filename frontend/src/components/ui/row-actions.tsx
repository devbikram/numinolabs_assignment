import { Button } from "@/components/ui/button";
import { Pencil, Trash2 } from "lucide-react";

interface RowActionsProps {
  onEdit?: () => void;
  onDelete: () => void;
}

export function RowActions({ onEdit, onDelete }: RowActionsProps) {
  return (
    <div className="flex justify-end gap-1.5">
      {onEdit && (
        <Button
          variant="outline"
          size="icon"
          onClick={onEdit}
          aria-label="Edit"
          className="h-8 w-8"
        >
          <Pencil className="h-3.5 w-3.5" />
        </Button>
      )}
      <Button
        variant="outline"
        size="icon"
        onClick={onDelete}
        aria-label="Delete"
        className="h-8 w-8 border-destructive/30 text-destructive hover:bg-destructive/10 hover:text-destructive"
      >
        <Trash2 className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
}
