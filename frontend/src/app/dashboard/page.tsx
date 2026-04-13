"use client";

import { useDashboardStats } from "@/lib/queries/dashboard";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  BookOpen,
  Users,
  PenTool,
  FolderOpen,
  Copy,
  BookCheck,
  ArrowRightLeft,
  AlertTriangle,
  Clock,
  TrendingUp,
} from "lucide-react";
import { borrowStatusColors } from "@/lib/constants";
import { safeFormat } from "@/lib/utils";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { useMemo } from "react";

export default function DashboardPage() {
  const { data: stats, isLoading, isError } = useDashboardStats();

  const summaryCards = useMemo(() => {
    if (!stats) return [];
    return [
      { label: "Total Books", value: stats.total_books, icon: BookOpen, color: "text-blue-600 bg-blue-100" },
      { label: "Total Members", value: stats.total_members, icon: Users, color: "text-violet-600 bg-violet-100" },
      { label: "Total Authors", value: stats.total_authors, icon: PenTool, color: "text-amber-600 bg-amber-100" },
      { label: "Categories", value: stats.total_categories, icon: FolderOpen, color: "text-teal-600 bg-teal-100" },
      { label: "Total Copies", value: stats.total_copies, icon: Copy, color: "text-indigo-600 bg-indigo-100" },
      { label: "Available Copies", value: stats.available_copies, icon: BookCheck, color: "text-emerald-600 bg-emerald-100" },
      { label: "Active Borrows", value: stats.borrowed_count, icon: ArrowRightLeft, color: "text-orange-600 bg-orange-100" },
      { label: "Overdue", value: stats.overdue_count, icon: AlertTriangle, color: "text-red-600 bg-red-100" },
    ];
  }, [stats]);

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (isError) {
    return <p className="text-destructive p-6">Failed to load dashboard. Please try again.</p>;
  }

  if (!stats) return null;

  // H-35: Empty state when library has no data yet
  if (
    stats.total_books === 0 &&
    stats.total_members === 0
  ) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <BookOpen className="h-12 w-12 text-muted-foreground/40" />
        <p className="text-muted-foreground text-lg font-medium">No data yet</p>
        <p className="text-sm text-muted-foreground">Add books and members to get started.</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-extrabold tracking-tight">Dashboard</h1>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        {summaryCards.map((card) => (
          <Card key={card.label}>
            <CardContent className="flex items-center gap-4 px-4 py-4">
              <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-lg ${card.color}`}>
                <card.icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">{card.label}</p>
                <p className="text-2xl font-extrabold tracking-tight">{card.value.toLocaleString()}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Borrowing Summary Bar */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg font-bold">
            <ArrowRightLeft className="h-5 w-5 text-primary" />
            Borrowing Overview
          </CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-sm font-semibold text-muted-foreground">
              Total: {stats.total_borrowings.toLocaleString()} borrowings
            </span>
          </div>
          <div
            role="img"
            aria-label={`Borrowing overview: ${stats.returned_count} returned, ${stats.borrowed_count} borrowed, ${stats.overdue_count} overdue`}
            className="flex h-4 w-full overflow-hidden rounded-full bg-muted"
          >
            {stats.total_borrowings > 0 && (
              <>
                <div
                  className="bg-emerald-500 transition-all"
                  style={{ width: `${(stats.returned_count / stats.total_borrowings) * 100}%` }}
                  title={`Returned: ${stats.returned_count}`}
                />
                <div
                  className="bg-amber-400 transition-all"
                  style={{ width: `${(stats.borrowed_count / stats.total_borrowings) * 100}%` }}
                  title={`Borrowed: ${stats.borrowed_count}`}
                />
                <div
                  className="bg-red-500 transition-all"
                  style={{ width: `${(stats.overdue_count / stats.total_borrowings) * 100}%` }}
                  title={`Overdue: ${stats.overdue_count}`}
                />
              </>
            )}
          </div>
          <div className="mt-3 flex flex-wrap gap-4 text-sm">
            <span className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-full bg-emerald-500" />
              Returned: <strong>{stats.returned_count.toLocaleString()}</strong>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-full bg-amber-400" />
              Borrowed: <strong>{stats.borrowed_count.toLocaleString()}</strong>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-full bg-red-500" />
              Overdue: <strong>{stats.overdue_count.toLocaleString()}</strong>
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Two-column layout */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Books per Category */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg font-bold">
              <FolderOpen className="h-5 w-5 text-primary" />
              Books per Category
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="space-y-3">
              {stats.books_per_category.map((cat) => (
                <div key={cat.name} className="flex items-center gap-3">
                  <span className="w-32 shrink-0 truncate text-sm font-medium">{cat.name}</span>
                  <div className="flex-1">
                    <div className="h-6 w-full overflow-hidden rounded bg-muted">
                      <div
                        className="h-full rounded bg-primary/80 transition-all"
                        style={{
                          width: `${(cat.count / Math.max(...stats.books_per_category.map((c) => c.count), 1)) * 100}%`,
                        }}
                      />
                    </div>
                  </div>
                  <span className="w-10 text-right text-sm font-bold">{cat.count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Most Borrowed Books */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg font-bold">
              <TrendingUp className="h-5 w-5 text-primary" />
              Most Borrowed Books
            </CardTitle>
          </CardHeader>
          <CardContent className="px-0 pb-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>#</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead className="text-right">Borrows</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {stats.most_borrowed_books.map((book, i) => (
                  <TableRow key={book.title}>
                    <TableCell className="font-bold text-muted-foreground">{i + 1}</TableCell>
                    <TableCell className="font-medium">{book.title}</TableCell>
                    <TableCell className="text-right font-bold">{book.borrow_count}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Most Active Members */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg font-bold">
              <Users className="h-5 w-5 text-primary" />
              Most Active Members
            </CardTitle>
          </CardHeader>
          <CardContent className="px-0 pb-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>#</TableHead>
                  <TableHead>Member</TableHead>
                  <TableHead>ID</TableHead>
                  <TableHead className="text-right">Borrows</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {stats.most_active_members.map((m, i) => (
                  <TableRow key={m.library_id}>
                    <TableCell className="font-bold text-muted-foreground">{i + 1}</TableCell>
                    <TableCell className="font-medium">{m.name}</TableCell>
                    <TableCell className="font-mono text-sm">{m.library_id}</TableCell>
                    <TableCell className="text-right font-bold">{m.borrow_count}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Recent Borrowings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg font-bold">
              <Clock className="h-5 w-5 text-primary" />
              Recent Borrowings
            </CardTitle>
          </CardHeader>
          <CardContent className="px-0 pb-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Book</TableHead>
                  <TableHead>Member</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {stats.recent_borrowings.map((b) => (
                  <TableRow key={b.id}>
                    <TableCell className="font-medium">{b.book_title}</TableCell>
                    <TableCell>{b.member_name}</TableCell>
                    <TableCell>{safeFormat(b.borrowed_at, "MMM d, yyyy")}</TableCell>
                    <TableCell>
                      <Badge className={borrowStatusColors[b.status] ?? "bg-muted text-foreground"}>
                        {b.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
