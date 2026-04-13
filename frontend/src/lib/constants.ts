export const borrowStatusColors: Record<string, string> = {
  borrowed: "bg-amber-100 text-amber-800 border border-amber-300",
  returned: "bg-emerald-100 text-emerald-800 border border-emerald-300",
  overdue: "bg-red-100 text-red-800 border border-red-300",
};

export const STATUS_ORDER: Record<string, number> = {
  overdue: 0,
  borrowed: 1,
  returned: 2,
};
