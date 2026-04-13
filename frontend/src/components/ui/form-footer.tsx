import { Button } from "@/components/ui/button";

interface FormFooterProps {
  isSubmitting: boolean;
  isEdit: boolean;
  onCancel: () => void;
}

export function FormFooter({ isSubmitting, isEdit, onCancel }: FormFooterProps) {
  return (
    <div className="flex justify-end gap-2">
      <Button type="button" variant="outline" onClick={onCancel}>
        Cancel
      </Button>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Saving..." : isEdit ? "Update" : "Create"}
      </Button>
    </div>
  );
}
