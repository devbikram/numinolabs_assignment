import { useCallback, useState } from "react";

interface UseFormDialogResult<T> {
  formOpen: boolean;
  editing: T | undefined;
  openCreate: () => void;
  openEdit: (item: T) => void;
  setFormOpen: (open: boolean) => void;
  closeForm: () => void;
}

export function useFormDialog<T>(): UseFormDialogResult<T> {
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<T | undefined>();

  const openCreate = useCallback(() => {
    setEditing(undefined);
    setFormOpen(true);
  }, []);

  const openEdit = useCallback((item: T) => {
    setEditing(item);
    setFormOpen(true);
  }, []);

  const closeForm = useCallback(() => {
    setEditing(undefined);
    setFormOpen(false);
  }, []);

  return { formOpen, editing, openCreate, openEdit, setFormOpen, closeForm };
}
