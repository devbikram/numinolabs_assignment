import { renderHook, act } from "@testing-library/react";
import { useFormDialog } from "@/hooks/use-form-dialog";

interface Item {
  id: number;
  name: string;
}

describe("useFormDialog", () => {
  it("starts closed with no editing item", () => {
    const { result } = renderHook(() => useFormDialog<Item>());
    expect(result.current.formOpen).toBe(false);
    expect(result.current.editing).toBeUndefined();
  });

  it("openCreate sets formOpen=true and clears editing", () => {
    const { result } = renderHook(() => useFormDialog<Item>());

    // First set an item so we can verify it gets cleared
    act(() => { result.current.openEdit({ id: 1, name: "Alice" }); });
    expect(result.current.editing).toEqual({ id: 1, name: "Alice" });

    act(() => { result.current.openCreate(); });
    expect(result.current.formOpen).toBe(true);
    expect(result.current.editing).toBeUndefined();
  });

  it("openEdit sets formOpen=true and stores the item", () => {
    const { result } = renderHook(() => useFormDialog<Item>());
    const item = { id: 5, name: "Bob" };

    act(() => { result.current.openEdit(item); });
    expect(result.current.formOpen).toBe(true);
    expect(result.current.editing).toEqual(item);
  });

  it("setFormOpen(false) closes the dialog", () => {
    const { result } = renderHook(() => useFormDialog<Item>());

    act(() => { result.current.openCreate(); });
    expect(result.current.formOpen).toBe(true);

    act(() => { result.current.setFormOpen(false); });
    expect(result.current.formOpen).toBe(false);
  });

  it("editing persists after setFormOpen(false)", () => {
    const { result } = renderHook(() => useFormDialog<Item>());
    const item = { id: 3, name: "Carol" };

    act(() => { result.current.openEdit(item); });
    act(() => { result.current.setFormOpen(false); });

    // editing is not reset when dialog is simply closed
    expect(result.current.editing).toEqual(item);
  });
});
