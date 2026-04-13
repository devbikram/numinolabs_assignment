export interface Category {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface CategoryBrief {
  id: string;
  name: string;
}

export interface Author {
  id: string;
  name: string;
  bio: string | null;
  book_count: number;
  created_at: string;
  updated_at: string;
}

export interface AuthorBrief {
  id: string;
  name: string;
  book_count: number;
}

export interface MostBorrowedBook {
  id: string;
  title: string;
  borrow_count: number;
}

export interface AuthorStats {
  total_borrows: number;
  active_borrows: number;
  unique_readers: number;
  most_borrowed: MostBorrowedBook | null;
}

export interface Book {
  id: string;
  title: string;
  authors: AuthorBrief[];
  isbn: string;
  category_id: string | null;
  category: CategoryBrief | null;
  published_year: number | null;
  total_copies: number;
  available_copies: number;
  borrow_count: number;
  created_at: string;
  updated_at: string;
}

export interface BookCreate {
  title: string;
  author_ids: string[];
  isbn: string;
  category_id?: string | null;
  published_year?: number | null;
  total_copies: number;
  available_copies: number;
}

export interface BookBorrowingStats {
  total_borrows: number;
  active_borrows: number;
  unique_readers: number;
}

export interface BookUpdate {
  title?: string;
  author_ids?: string[];
  isbn?: string;
  category_id?: string | null;
  published_year?: number | null;
  total_copies?: number;
  available_copies?: number;
}

export interface Member {
  id: string;
  library_id: string;
  full_name: string;
  email: string;
  phone: string | null;
  address: string | null;
  created_at: string;
  updated_at: string;
}

export interface MemberCreate {
  full_name: string;
  email: string;
  phone?: string | null;
  address?: string | null;
}

export interface MemberUpdate {
  full_name?: string;
  email?: string;
  phone?: string | null;
  address?: string | null;
}

export interface MemberBorrowingStats {
  total: number;
  borrowed: number;
  returned: number;
  overdue: number;
}

export type BorrowStatus = "borrowed" | "returned" | "overdue";

export interface BookBrief {
  id: string;
  title: string;
  isbn: string;
}

export interface MemberBrief {
  id: string;
  library_id: string;
  full_name: string;
  email: string;
  phone: string | null;
}

export interface Borrowing {
  id: string;
  book_id: string;
  member_id: string;
  borrowed_at: string;
  due_date: string;
  returned_at: string | null;
  status: BorrowStatus;
  book: BookBrief;
  member: MemberBrief;
  created_at: string;
  updated_at: string;
}

export interface BorrowingCreate {
  book_id: string;
  member_id: string;
  due_date: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface MessageResponse {
  message: string;
}

// Dashboard
export interface CategoryCount {
  name: string;
  count: number;
}

export interface BookBorrowCount {
  title: string;
  borrow_count: number;
}

export interface ActiveMember {
  name: string;
  library_id: string;
  borrow_count: number;
}

export interface RecentBorrowing {
  id: string;
  book_title: string;
  member_name: string;
  borrowed_at: string;
  status: BorrowStatus;
}

export interface DashboardStats {
  total_books: number;
  total_members: number;
  total_authors: number;
  total_categories: number;
  total_copies: number;
  available_copies: number;
  total_borrowings: number;
  borrowed_count: number;
  returned_count: number;
  overdue_count: number;
  books_per_category: CategoryCount[];
  most_borrowed_books: BookBorrowCount[];
  most_active_members: ActiveMember[];
  recent_borrowings: RecentBorrowing[];
}
