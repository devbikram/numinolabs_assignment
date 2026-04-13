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
