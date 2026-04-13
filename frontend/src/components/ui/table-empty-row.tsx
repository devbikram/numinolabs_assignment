import { TableCell, TableRow } from "@/components/ui/table";

interface TableEmptyRowProps {
  colSpan: number;
  label: string;
}

export function TableEmptyRow({ colSpan, label }: TableEmptyRowProps) {
  return (
    <TableRow>
      <TableCell colSpan={colSpan} className="text-center text-muted-foreground">
        {label}
      </TableCell>
    </TableRow>
  );
}
