import { borrowStatusColors, STATUS_ORDER } from "@/lib/constants";

describe("borrowStatusColors", () => {
  it("has entries for all three borrow statuses", () => {
    expect(borrowStatusColors).toHaveProperty("borrowed");
    expect(borrowStatusColors).toHaveProperty("returned");
    expect(borrowStatusColors).toHaveProperty("overdue");
  });

  it("borrowed status is amber-themed", () => {
    expect(borrowStatusColors.borrowed).toMatch(/amber/);
  });

  it("returned status is emerald-themed", () => {
    expect(borrowStatusColors.returned).toMatch(/emerald/);
  });

  it("overdue status is red-themed", () => {
    expect(borrowStatusColors.overdue).toMatch(/red/);
  });

  it("all values are non-empty strings", () => {
    Object.values(borrowStatusColors).forEach((v) => {
      expect(typeof v).toBe("string");
      expect(v.length).toBeGreaterThan(0);
    });
  });
});

describe("STATUS_ORDER", () => {
  it("has entries for all three borrow statuses", () => {
    expect(STATUS_ORDER).toHaveProperty("borrowed");
    expect(STATUS_ORDER).toHaveProperty("returned");
    expect(STATUS_ORDER).toHaveProperty("overdue");
  });

  it("overdue sorts first (lowest value)", () => {
    expect(STATUS_ORDER.overdue).toBeLessThan(STATUS_ORDER.borrowed);
    expect(STATUS_ORDER.overdue).toBeLessThan(STATUS_ORDER.returned);
  });

  it("borrowed sorts before returned", () => {
    expect(STATUS_ORDER.borrowed).toBeLessThan(STATUS_ORDER.returned);
  });
});
