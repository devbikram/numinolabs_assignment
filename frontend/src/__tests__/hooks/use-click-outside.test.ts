import { renderHook } from "@testing-library/react";
import { useRef } from "react";
import { useClickOutside } from "@/hooks/use-click-outside";

function makeElement(): HTMLDivElement {
  const el = document.createElement("div");
  document.body.appendChild(el);
  return el;
}

function fireMouseDown(target: EventTarget): void {
  const event = new MouseEvent("mousedown", { bubbles: true });
  Object.defineProperty(event, "target", { value: target, writable: false });
  document.dispatchEvent(event);
}

function fireTouchStart(target: EventTarget): void {
  const event = new Event("touchstart", { bubbles: true });
  Object.defineProperty(event, "target", { value: target, writable: false });
  document.dispatchEvent(event);
}

describe("useClickOutside", () => {
  it("calls callback when mousedown fires outside the ref element", () => {
    const el = makeElement();
    const outside = document.createElement("button");
    document.body.appendChild(outside);
    const callback = jest.fn();

    const { unmount } = renderHook(() => {
      const ref = useRef<HTMLElement | null>(el);
      useClickOutside(ref, callback);
    });

    fireMouseDown(outside);
    expect(callback).toHaveBeenCalledTimes(1);
    unmount();
    outside.remove();
    el.remove();
  });

  it("does not call callback when mousedown fires inside the ref element", () => {
    const el = makeElement();
    const callback = jest.fn();

    const { unmount } = renderHook(() => {
      const ref = useRef<HTMLElement | null>(el);
      useClickOutside(ref, callback);
    });

    fireMouseDown(el);
    expect(callback).not.toHaveBeenCalled();
    unmount();
    el.remove();
  });

  it("calls callback when touchstart fires outside the ref element", () => {
    const el = makeElement();
    const outside = document.createElement("button");
    document.body.appendChild(outside);
    const callback = jest.fn();

    const { unmount } = renderHook(() => {
      const ref = useRef<HTMLElement | null>(el);
      useClickOutside(ref, callback);
    });

    fireTouchStart(outside);
    expect(callback).toHaveBeenCalledTimes(1);
    unmount();
    outside.remove();
    el.remove();
  });

  it("does not call callback when enabled=false", () => {
    const el = makeElement();
    const outside = document.createElement("button");
    document.body.appendChild(outside);
    const callback = jest.fn();

    const { unmount } = renderHook(() => {
      const ref = useRef<HTMLElement | null>(el);
      useClickOutside(ref, callback, false);
    });

    fireMouseDown(outside);
    expect(callback).not.toHaveBeenCalled();
    unmount();
    outside.remove();
    el.remove();
  });

  it("removes event listeners on unmount", () => {
    const el = makeElement();
    const outside = document.createElement("button");
    document.body.appendChild(outside);
    const callback = jest.fn();

    const { unmount } = renderHook(() => {
      const ref = useRef<HTMLElement | null>(el);
      useClickOutside(ref, callback);
    });

    unmount();
    fireMouseDown(outside);
    expect(callback).not.toHaveBeenCalled();
    outside.remove();
    el.remove();
  });
});
