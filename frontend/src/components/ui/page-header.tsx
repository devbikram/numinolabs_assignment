import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

interface PageHeaderProps {
  title: string;
  addLabel: string;
  onAdd: () => void;
}

export function PageHeader({ title, addLabel, onAdd }: PageHeaderProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <h1 className="text-3xl font-extrabold tracking-tight">{title}</h1>
      <Button onClick={onAdd} size="lg">
        <Plus className="mr-2 h-4 w-4" /> {addLabel}
      </Button>
    </div>
  );
}
