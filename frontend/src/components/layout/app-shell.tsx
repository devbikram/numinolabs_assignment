"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import { type ReactNode } from "react";
import { AuthProvider } from "@/providers/auth-provider";
import { AuthGuard } from "@/components/layout/auth-guard";
import { Sidebar } from "@/components/layout/sidebar";
import { Menu, Library } from "lucide-react";
import { PUBLIC_PATHS } from "@/lib/routes";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <AuthGuard>
        <AppLayout>{children}</AppLayout>
      </AuthGuard>
    </AuthProvider>
  );
}

function AppLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isPublic = (PUBLIC_PATHS as readonly string[]).includes(pathname);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  if (isPublic) {
    return <>{children}</>;
  }

  return (
    <>
      {/* Mobile header */}
      <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b bg-card px-4 shadow-sm lg:hidden">
        <button
          onClick={() => setSidebarOpen(true)}
          aria-label="Open navigation"
          aria-expanded={sidebarOpen}
          className="rounded-md p-1.5 hover:bg-muted"
        >
          <Menu className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-2 font-bold tracking-tight">
          <Library className="h-5 w-5 text-primary" />
          <span>Library Manager</span>
        </div>
      </header>

      {/* Sidebar overlay (mobile) */}
      {sidebarOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          className="fixed inset-0 z-40 w-full bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div className="flex min-h-screen w-full">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <main className="min-w-0 flex-1 overflow-y-auto px-6 py-8 lg:px-10 lg:py-8">{children}</main>
      </div>
    </>
  );
}
