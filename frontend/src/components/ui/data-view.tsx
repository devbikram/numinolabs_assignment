import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { Pagination } from "@/components/ui/pagination";

interface DataViewProps {
  isLoading: boolean;
  isError: boolean;
  errorMessage: string;
  total: number;
  skip: number;
  limit: number;
  onPageChange: (skip: number) => void;
  children: React.ReactNode;
}

export function DataView({
  isLoading,
  isError,
  errorMessage,
  total,
  skip,
  limit,
  onPageChange,
  children,
}: DataViewProps) {
  if (isLoading) return <LoadingSpinner />;
  if (isError)
    return <p className="text-destructive">{errorMessage}</p>;

  return (
    <>
      {children}
      <Pagination
        total={total}
        skip={skip}
        limit={limit}
        onPageChange={onPageChange}
      />
    </>
  );
}
