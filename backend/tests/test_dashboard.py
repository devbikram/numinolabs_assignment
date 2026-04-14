"""
Integration tests for the dashboard statistics endpoint.
"""
import pytest

from tests.conftest import ADMIN_EMAIL, ADMIN_PASSWORD, auth_headers, login


@pytest.fixture()
def tok(client, seed_admin):
    return login(client, ADMIN_EMAIL, ADMIN_PASSWORD)


class TestDashboardStats:
    def test_empty_db_returns_zero_counts(self, client, tok):
        resp = client.get("/api/v1/dashboard/stats", headers=auth_headers(tok))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_books"] == 0
        assert body["total_members"] == 0
        assert body["total_authors"] == 0
        assert body["total_categories"] == 0
        assert body["total_borrowings"] == 0
        assert body["books_per_category"] == []
        assert body["most_borrowed_books"] == []
        assert body["most_active_members"] == []
        assert body["recent_borrowings"] == []

    def test_unauthenticated_request_rejected(self, client):
        resp = client.get("/api/v1/dashboard/stats")
        assert resp.status_code == 401

    def test_counts_reflect_created_data(self, client, tok, db):
        from models import Author, Book, Member

        db.add_all([
            Author(name="Dashboard Author"),
            Book(title="Dashboard Book", isbn="9780000000099", total_copies=2, available_copies=2),
            Member(library_id="DASHU001", full_name="Dashboard Member", email="dash@test.com"),
        ])
        db.commit()

        resp = client.get("/api/v1/dashboard/stats", headers=auth_headers(tok))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_authors"] == 1
        assert body["total_books"] == 1
        assert body["total_members"] == 1
        assert body["total_copies"] == 2
        assert body["available_copies"] == 2

    def test_dashboard_handles_deleted_book_in_recent_borrowings(self, client, tok, db):
        """Dashboard shows '[Deleted]' instead of crashing when a borrowing's book was removed."""
        from datetime import datetime, timedelta, timezone
        from models import Book, Borrowing, Member
        from models.borrow import BorrowStatus

        book = Book(title="Soon Gone", isbn="9780000000077", total_copies=1, available_copies=1)
        member = Member(library_id="DASHU002", full_name="Dashboard Reader", email="dr@test.com")
        db.add_all([book, member])
        db.commit()
        db.refresh(book)
        db.refresh(member)

        b = Borrowing(
            book_id=book.id,
            member_id=member.id,
            borrowed_at=datetime.now(timezone.utc),
            due_date=datetime.now(timezone.utc) + timedelta(days=14),
            returned_at=datetime.now(timezone.utc),
            status=BorrowStatus.returned,
        )
        db.add(b)
        db.commit()

        # Delete the book — borrowing survives with book_id=NULL
        db.delete(book)
        db.commit()

        resp = client.get("/api/v1/dashboard/stats", headers=auth_headers(tok))
        assert resp.status_code == 200
        recent = resp.json()["recent_borrowings"]
        assert len(recent) == 1
        assert recent[0]["book_title"] == "[Deleted]"
        assert recent[0]["member_name"] == "Dashboard Reader"
