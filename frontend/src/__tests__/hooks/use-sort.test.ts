import { renderHook, act } from "@testing-library/react";
import { useSort } from "@/hooks/use-sort";

const items = [
  { id: 1, name: "Charlie", score: 30 },
  { id: 2, name: "alice", score: 10 },
  { id: 3, name: "Bob", score: 20 },
];

describe("useSort", () => {
  it("sorts by the default key ascending on mount", () => {
    const { result } = renderHook(() => useSort(items, "name"));
    const names = result.current.sorted.map((i) => i.name);
    expect(names).toEqual(["alice", "Bob", "Charlie"]);
  });

  it("sorts descending by default when specified", () => {
    const { result } = renderHook(() => useSort(items, "name", "desc"));
    const names = result.current.sorted.map((i) => i.name);
    expect(names).toEqual(["Charlie", "Bob", "alice"]);
  });

  it("toggleSort switches to the new key ascending", () => {
    const { result } = renderHook(() => useSort(items, "name"));
    act(() => { result.current.toggleSort("score"); });
    const scores = result.current.sorted.map((i) => i.score);
    expect(scores).toEqual([10, 20, 30]);
    expect(result.current.sort).toEqual({ key: "score", direction: "asc" });
  });

  it("toggleSort on the active key flips direction", () => {
    const { result } = renderHook(() => useSort(items, "score"));
    expect(result.current.sort.direction).toBe("asc");
    act(() => { result.current.toggleSort("score"); });
    expect(result.current.sort.direction).toBe("desc");
    const scores = result.current.sorted.map((i) => i.score);
    expect(scores).toEqual([30, 20, 10]);
  });

  it("toggleSort on the active key again flips back", () => {
    const { result } = renderHook(() => useSort(items, "score"));
    act(() => { result.current.toggleSort("score"); });
    act(() => { result.current.toggleSort("score"); });
    expect(result.current.sort.direction).toBe("asc");
  });

  it("puts null values last when sorting ascending", () => {
    const data = [
      { name: "a", val: null },
      { name: "b", val: 1 },
      { name: "c", val: null },
    ];
    const { result } = renderHook(() => useSort(data, "val"));
    const vals = result.current.sorted.map((i) => i.val);
    expect(vals[0]).toBe(1);
    expect(vals[1]).toBeNull();
    expect(vals[2]).toBeNull();
  });

  it("sorts numerically for number fields", () => {
    const numbers = [{ v: 100 }, { v: 9 }, { v: 50 }];
    const { result } = renderHook(() => useSort(numbers, "v"));
    const vals = result.current.sorted.map((i) => i.v);
    expect(vals).toEqual([9, 50, 100]);
  });

  it("does not mutate the original items array", () => {
    const snap = [...items];
    const { result } = renderHook(() => useSort(items, "name"));
    act(() => { result.current.toggleSort("score"); });
    expect(items).toEqual(snap);
  });

  it("returns an empty array when given an empty input", () => {
    const { result } = renderHook(() => useSort([], "name"));
    expect(result.current.sorted).toEqual([]);
  });
});
