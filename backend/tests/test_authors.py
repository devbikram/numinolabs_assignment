"""
Integration tests for author CRUD endpoints, focusing on the
case-insensitive duplicate-name constraint.
"""
import pytest

from tests.conftest import MANAGER_EMAIL, MANAGER_PASSWORD, auth_headers, login


@pytest.fixture()
def tok(client, seed_manager):
    return login(client, MANAGER_EMAIL, MANAGER_PASSWORD)


def _create(client, tok, name="Jane Austen", bio=None):
    payload = {"name": name}
    if bio is not None:
        payload["bio"] = bio
    return client.post("/api/v1/authors/", json=payload, headers=auth_headers(tok))


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class TestCreateAuthor:
    def test_success_returns_201(self, client, tok):
        resp = _create(client, tok)
        assert resp.status_code == 201
        assert resp.json()["name"] == "Jane Austen"

    def test_exact_duplicate_returns_409(self, client, tok):
        _create(client, tok, "Jane Austen")
        resp = _create(client, tok, "Jane Austen")
        assert resp.status_code == 409

    def test_case_insensitive_duplicate_returns_409(self, client, tok):
        _create(client, tok, "Jane Austen")
        resp = _create(client, tok, "jane austen")
        assert resp.status_code == 409

    def test_leading_trailing_whitespace_is_treated_as_duplicate(self, client, tok):
        _create(client, tok, "Jane Austen")
        # Same name with surrounding spaces should still be caught
        resp = _create(client, tok, "  jane austen  ")
        assert resp.status_code == 409

    def test_different_name_succeeds(self, client, tok):
        _create(client, tok, "Jane Austen")
        resp = _create(client, tok, "Charlotte Bronte")
        assert resp.status_code == 201

    def test_unauthenticated_rejected(self, client):
        resp = client.post("/api/v1/authors/", json={"name": "Anon"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


class TestUpdateAuthor:
    def test_rename_to_existing_author_returns_409(self, client, tok):
        _create(client, tok, "Jane Austen")
        resp_b = _create(client, tok, "Charlotte Bronte")
        author_b_id = resp_b.json()["id"]
        resp = client.patch(
            f"/api/v1/authors/{author_b_id}",
            json={"name": "jane austen"},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 409

    def test_update_same_name_is_allowed(self, client, tok):
        """Renaming an author to their own current name must not raise 409."""
        resp = _create(client, tok, "Jane Austen")
        author_id = resp.json()["id"]
        resp2 = client.patch(
            f"/api/v1/authors/{author_id}",
            json={"name": "Jane Austen"},
            headers=auth_headers(tok),
        )
        assert resp2.status_code == 200
        assert resp2.json()["name"] == "Jane Austen"

    def test_update_bio_without_name_change_is_allowed(self, client, tok):
        resp = _create(client, tok, "Jane Austen")
        author_id = resp.json()["id"]
        resp2 = client.patch(
            f"/api/v1/authors/{author_id}",
            json={"bio": "English novelist"},
            headers=auth_headers(tok),
        )
        assert resp2.status_code == 200
        assert resp2.json()["bio"] == "English novelist"

    def test_update_nonexistent_author_returns_404(self, client, tok):
        import uuid
        resp = client.patch(
            f"/api/v1/authors/{uuid.uuid4()}",
            json={"name": "Ghost"},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 404

    def test_update_name_with_whitespace_case_variant_returns_409(self, client, tok):
        _create(client, tok, "Jane Austen")
        resp_b = _create(client, tok, "Charlotte Bronte")
        author_b_id = resp_b.json()["id"]
        resp = client.patch(
            f"/api/v1/authors/{author_b_id}",
            json={"name": "  jane austen  "},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# book_count correctness (Issue #1)
# ---------------------------------------------------------------------------


class TestAuthorBookCount:
    def test_book_count_zero_for_new_author(self, client, tok):
        resp = _create(client, tok, "Solo Author")
        author_id = resp.json()["id"]
        get_resp = client.get(f"/api/v1/authors/{author_id}", headers=auth_headers(tok))
        assert get_resp.status_code == 200
        assert get_resp.json()["book_count"] == 0

    def test_book_count_increments_with_book(self, client, tok):
        author_resp = _create(client, tok, "Counted Author")
        author_id = author_resp.json()["id"]

        client.post(
            "/api/v1/books/",
            json={
                "title": "Some Book",
                "isbn": "9780000099991",
                "total_copies": 1,
                "author_ids": [author_id],
            },
            headers=auth_headers(tok),
        )

        get_resp = client.get(f"/api/v1/authors/{author_id}", headers=auth_headers(tok))
        assert get_resp.status_code == 200
        assert get_resp.json()["book_count"] == 1


# ---------------------------------------------------------------------------
# Search (Issue #27)
# ---------------------------------------------------------------------------


class TestAuthorSearch:
    def test_search_by_name_substring(self, client, tok):
        _create(client, tok, "Jane Austen")
        _create(client, tok, "Charlotte Bronte")
        resp = client.get("/api/v1/authors/?search=austen", headers=auth_headers(tok))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "Jane Austen"

    def test_search_case_insensitive(self, client, tok):
        _create(client, tok, "Leo Tolstoy")
        resp = client.get("/api/v1/authors/?search=TOLSTOY", headers=auth_headers(tok))
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_search_no_match_returns_empty(self, client, tok):
        _create(client, tok, "Jane Austen")
        resp = client.get("/api/v1/authors/?search=zzznomatch", headers=auth_headers(tok))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []

    def test_search_partial_match(self, client, tok):
        _create(client, tok, "Gabriel Garcia Marquez")
        _create(client, tok, "Gabriel Oak")
        resp = client.get("/api/v1/authors/?search=gabriel", headers=auth_headers(tok))
        assert resp.status_code == 200
        assert resp.json()["total"] == 2


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


class TestDeleteAuthor:
    def test_delete_returns_success_message(self, client, tok):
        resp = _create(client, tok, "To Be Deleted")
        author_id = resp.json()["id"]
        del_resp = client.delete(f"/api/v1/authors/{author_id}", headers=auth_headers(tok))
        assert del_resp.status_code == 200
        assert "deleted" in del_resp.json()["message"].lower()

    def test_deleted_author_not_retrievable(self, client, tok):
        resp = _create(client, tok, "Also Deleted")
        author_id = resp.json()["id"]
        client.delete(f"/api/v1/authors/{author_id}", headers=auth_headers(tok))
        get_resp = client.get(f"/api/v1/authors/{author_id}", headers=auth_headers(tok))
        assert get_resp.status_code == 404

    def test_delete_nonexistent_author_returns_404(self, client, tok):
        import uuid
        resp = client.delete(f"/api/v1/authors/{uuid.uuid4()}", headers=auth_headers(tok))
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Author stats
# ---------------------------------------------------------------------------


class TestAuthorStats:
    def test_stats_zero_for_author_with_no_books(self, client, tok):
        resp = _create(client, tok, "No Books Author")
        author_id = resp.json()["id"]
        stats_resp = client.get(f"/api/v1/authors/{author_id}/stats", headers=auth_headers(tok))
        assert stats_resp.status_code == 200
        body = stats_resp.json()
        assert body["total_borrows"] == 0
        assert body["active_borrows"] == 0
        assert body["unique_readers"] == 0
        assert body["most_borrowed"] is None

    def test_stats_nonexistent_author_returns_404(self, client, tok):
        import uuid
        resp = client.get(f"/api/v1/authors/{uuid.uuid4()}/stats", headers=auth_headers(tok))
        assert resp.status_code == 404

    def test_stats_reflect_borrowings(self, client, tok, db, a_book, a_member):
        from datetime import datetime, timedelta, timezone
        from models import Borrowing
        from models.borrow import BorrowStatus
        from models.book import book_authors

        author_resp = _create(client, tok, "Stat Author")
        author_id = author_resp.json()["id"]

        import uuid as _uuid
        db.execute(book_authors.insert().values(book_id=a_book.id, author_id=_uuid.UUID(author_id)))
        db.add(Borrowing(
            book_id=a_book.id,
            member_id=a_member.id,
            borrowed_at=datetime.now(timezone.utc),
            due_date=datetime.now(timezone.utc) + timedelta(days=14),
            status=BorrowStatus.borrowed,
        ))
        db.commit()

        resp = client.get(f"/api/v1/authors/{author_id}/stats", headers=auth_headers(tok))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_borrows"] == 1
        assert body["active_borrows"] == 1
        assert body["unique_readers"] == 1
        assert body["most_borrowed"] is not None
        assert body["most_borrowed"]["borrow_count"] == 1
