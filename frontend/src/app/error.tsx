"use client";

import { ErrorPage } from "@/components/ui/error-page";

export default function Error(props: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <ErrorPage {...props} />;
}
