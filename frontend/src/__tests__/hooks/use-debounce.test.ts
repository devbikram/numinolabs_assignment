import { renderHook, act } from "@testing-library/react";
import { useDebounce } from "@/hooks/use-debounce";

beforeEach(() => jest.useFakeTimers());
afterEach(() => jest.useRealTimers());

describe("useDebounce", () => {
  it("returns the initial value immediately", () => {
    const { result } = renderHook(() => useDebounce("hello", 300));
    expect(result.current).toBe("hello");
  });

  it("does not update before the delay elapses", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: "a" } }
    );
    rerender({ value: "b" });
    act(() => { jest.advanceTimersByTime(100); });
    expect(result.current).toBe("a");
  });

  it("updates after the delay", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: "a" } }
    );
    rerender({ value: "b" });
    act(() => { jest.advanceTimersByTime(300); });
    expect(result.current).toBe("b");
  });

  it("cancels pending update when value changes again", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: "a" } }
    );
    rerender({ value: "b" });
    act(() => { jest.advanceTimersByTime(200); });
    rerender({ value: "c" });
    act(() => { jest.advanceTimersByTime(200); });
    // Only 200ms past "c" — still should not have fired
    expect(result.current).toBe("a");
    act(() => { jest.advanceTimersByTime(100); });
    expect(result.current).toBe("c");
  });

  it("uses 300ms default delay when none is provided", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value),
      { initialProps: { value: "x" } }
    );
    rerender({ value: "y" });
    act(() => { jest.advanceTimersByTime(299); });
    expect(result.current).toBe("x");
    act(() => { jest.advanceTimersByTime(1); });
    expect(result.current).toBe("y");
  });

  it("works with non-string types (numbers)", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 100),
      { initialProps: { value: 1 } }
    );
    rerender({ value: 42 });
    act(() => { jest.advanceTimersByTime(100); });
    expect(result.current).toBe(42);
  });
});
