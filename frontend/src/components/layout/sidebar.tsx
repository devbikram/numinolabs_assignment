"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpen, Users, ArrowRightLeft, Library, LogOut, X, LayoutDashboard } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/providers/auth-provider";
import { Badge } from "@/components/ui/badge";
import { ROUTES } from "@/lib/routes";

export const NAV_ITEMS = [
  { href: ROUTES.DASHBOARD, label: "Dashboard", icon: LayoutDashboard },
  { href: ROUTES.BOOKS, label: "Books", icon: BookOpen },
  { href: ROUTES.MEMBERS, label: "Members", icon: Users },
  { href: ROUTES.BORROWINGS, label: "Borrowings", icon: ArrowRightLeft },
] as const;

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-50 flex w-72 flex-col bg-sidebar text-sidebar-foreground transition-transform duration-200 lg:static lg:translate-x-0",
        open ? "translate-x-0" : "-translate-x-full"
      )}
    >
      {/* Brand */}
      <div className="flex h-16 items-center justify-between border-b border-sidebar-border px-5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/15">
            <Library className="h-4.5 w-4.5" />
          </div>
          <span className="text-lg font-bold tracking-tight">Library Manager</span>
        </div>
        <button
          onClick={onClose}
          aria-label="Close navigation"
          className="rounded-md p-1 hover:bg-white/10 lg:hidden"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-widest text-white/40">
          Navigation
        </p>
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            onClick={onClose}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold transition-colors",
              pathname.startsWith(href)
                ? "bg-white/15 text-white shadow-sm"
                : "text-white/60 hover:bg-white/10 hover:text-white"
            )}
          >
            <Icon className="h-4.5 w-4.5" />
            {label}
          </Link>
        ))}
      </nav>

      {/* User section */}
      {user && (
        <div className="border-t border-sidebar-border p-4 space-y-3">
          <div className="flex items-center gap-3 px-1">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/15 text-sm font-bold">
              {user.full_name.charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold">{user.full_name}</p>
              <p className="truncate text-xs text-white/50">{user.email}</p>
            </div>
            <Badge className="bg-white/15 text-white border-0 text-[10px] font-semibold shrink-0 uppercase tracking-wide">
              {user.role}
            </Badge>
          </div>
          <button
            type="button"
            onClick={logout}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-white/60 transition-colors hover:bg-white/10 hover:text-white"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      )}
    </aside>
  );
}
