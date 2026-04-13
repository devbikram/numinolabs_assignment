"use client";

import { Button } from "@/components/ui/button";

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
  message?: string;
}

export function ErrorPage({
  error,
  reset,
  message = "Something went wrong.",
}: ErrorPageProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 gap-4">
      <p className="text-destructive font-medium">{message}</p>
      {error.digest && (
        <p className="text-xs text-muted-foreground font-mono">
          {error.digest}
        </p>
      )}
      <Button onClick={reset}>Try again</Button>
    </div>
  );
}
