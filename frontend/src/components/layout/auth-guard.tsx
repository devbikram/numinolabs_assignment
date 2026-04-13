"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import { useAuth } from "@/providers/auth-provider";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { PUBLIC_PATHS } from "@/lib/routes";

export function AuthGuard({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const isPublic = (PUBLIC_PATHS as readonly string[]).includes(pathname);

  useEffect(() => {
    if (isLoading) return;
    if (!user && !isPublic) {
      router.replace("/login");
    }
    if (user && isPublic) {
      router.replace("/books");
    }
  }, [user, isLoading, isPublic, router]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (!user && !isPublic) return null;
  if (user && isPublic) return null;

  return <>{children}</>;
}
