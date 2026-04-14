"""
Integration tests for book CRUD endpoints.
"""
import uuid

import pytest

from models import Author, Category
from tests.conftest import MANAGER_EMAIL, MANAGER_PASSWORD, auth_headers, login

ISBN_A = "9780000000001"
ISBN_B = "9780000000018"


@pytest.fixture()
def tok(client, seed_manager):
    return login(client, MANAGER_EMAIL, MANAGER_PASSWORD)


def _book_payload(**overrides):
    base = {"title": "A Test Book", "isbn": ISBN_A, "total_copies": 3}
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class TestCreateBook:
    def test_success_returns_201(self, client, tok):
        resp = client.post("/api/v1/books/", json=_book_payload(), headers=auth_headers(tok))
        assert resp.status_code == 201
        body = resp.json()
        assert body["title"] == "A Test Book"
        assert body["isbn"] == ISBN_A

    def test_available_copies_equals_total_copies_on_create(self, client, tok):
        """Regression: create_book sets available_copies = total_copies, not 0."""
        resp = client.post("/api/v1/books/", json=_book_payload(total_copies=5), headers=auth_headers(tok))
        assert resp.status_code == 201
        body = resp.json()
        assert body["available_copies"] == 5
        assert body["total_copies"] == 5

    def test_duplicate_isbn_returns_409(self, client, tok):
        client.post("/api/v1/books/", json=_book_payload(), headers=auth_headers(tok))
        resp = client.post("/api/v1/books/", json=_book_payload(), headers=auth_headers(tok))
        assert resp.status_code == 409

    def test_unauthenticated_rejected(self, client):
        resp = client.post("/api/v1/books/", json=_book_payload())
        assert resp.status_code == 401

    def test_invalid_isbn_rejected(self, client, tok):
        resp = client.post(
            "/api/v1/books/",
            json=_book_payload(isbn="not-an-isbn"),
            headers=auth_headers(tok),
        )
        assert resp.status_code == 422

    def test_zero_copies_rejected(self, client, tok):
        resp = client.post(
            "/api/v1/books/",
            json=_book_payload(total_copies=0),
            headers=auth_headers(tok),
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# List / Get
# ---------------------------------------------------------------------------


class TestGetBook:
    def test_list_books_returns_paginated(self, client, tok):
        client.post("/api/v1/books/", json=_book_payload(), headers=auth_headers(tok))
        resp = client.get("/api/v1/books/", headers=auth_headers(tok))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert isinstance(body["items"], list)

    def test_get_book_by_id(self, client, tok):
        create_resp = client.post("/api/v1/books/", json=_book_payload(), headers=auth_headers(tok))
        book_id = create_resp.json()["id"]
        resp = client.get(f"/api/v1/books/{book_id}", headers=auth_headers(tok))
        assert resp.status_code == 200
        assert resp.json()["id"] == book_id

    def test_get_nonexistent_book_returns_404(self, client, tok):
        resp = client.get(f"/api/v1/books/{uuid.uuid4()}", headers=auth_headers(tok))
        assert resp.status_code == 404

    def test_list_books_invalid_author_filter_returns_404(self, client, tok):
        resp = client.get(
            f"/api/v1/books/?author_id={uuid.uuid4()}",
            headers=auth_headers(tok),
        )
        assert resp.status_code == 404

    def test_list_books_invalid_category_filter_returns_404(self, client, tok):
        resp = client.get(
            f"/api/v1/books/?category_id={uuid.uuid4()}",
            headers=auth_headers(tok),
        )
        assert resp.status_code == 404

    def test_list_books_invalid_sort_by_returns_422(self, client, tok):
        resp = client.get("/api/v1/books/?sort_by=not_a_column", headers=auth_headers(tok))
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


class TestUpdateBook:
    def test_update_title(self, client, tok):
        create_resp = client.post("/api/v1/books/", json=_book_payload(), headers=auth_headers(tok))
        book_id = create_resp.json()["id"]
        resp = client.patch(
            f"/api/v1/books/{book_id}",
            json={"title": "Updated Title"},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"

    def test_update_isbn_to_duplicate_returns_409(self, client, tok):
        client.post("/api/v1/books/", json=_book_payload(isbn=ISBN_A), headers=auth_headers(tok))
        resp_b = client.post("/api/v1/books/", json=_book_payload(isbn=ISBN_B), headers=auth_headers(tok))
        book_b_id = resp_b.json()["id"]
        resp = client.patch(
            f"/api/v1/books/{book_b_id}",
            json={"isbn": ISBN_A},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 409

    def test_update_nonexistent_book_returns_404(self, client, tok):
        resp = client.patch(
            f"/api/v1/books/{uuid.uuid4()}",
            json={"title": "Ghost"},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 404

    def test_update_does_not_change_available_copies(self, client, tok):
        """Regression: delta is applied, not a blind reset to total_copies."""
        create_resp = client.post("/api/v1/books/", json=_book_payload(total_copies=3), headers=auth_headers(tok))
        book_id = create_resp.json()["id"]
        # available_copies = 3 after creation; delta = +2 so available should also rise by 2
        resp = client.patch(
            f"/api/v1/books/{book_id}",
            json={"total_copies": 5},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_copies"] == 5
        assert body["available_copies"] == 5  # 3 + delta(2)

    def test_total_copies_increase_applies_delta_not_reset(self, client, tok, db):
        """When copies are outstanding, only the delta is added — not a reset to total."""
        from models import Book
        book = Book(title="Delta Book", isbn="9780000000099", total_copies=3, available_copies=1)
        db.add(book)
        db.commit()
        db.refresh(book)
        resp = client.patch(
            f"/api/v1/books/{book.id}",
            json={"total_copies": 5},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_copies"] == 5
        assert body["available_copies"] == 3  # 1 available + delta(2) new copies


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


class TestDeleteBook:
    def test_delete_book(self, client, tok):
        create_resp = client.post("/api/v1/books/", json=_book_payload(), headers=auth_headers(tok))
        book_id = create_resp.json()["id"]
        del_resp = client.delete(f"/api/v1/books/{book_id}", headers=auth_headers(tok))
        assert del_resp.status_code == 200
        get_resp = client.get(f"/api/v1/books/{book_id}", headers=auth_headers(tok))
        assert get_resp.status_code == 404

    def test_delete_nonexistent_book_returns_404(self, client, tok):
        resp = client.delete(f"/api/v1/books/{uuid.uuid4()}", headers=auth_headers(tok))
        assert resp.status_code == 404

    def test_delete_blocked_when_active_borrowing_exists(self, client, tok, db, a_book, a_member):
        """Cannot delete a book that has active (borrowed/overdue) borrowings."""
        from datetime import datetime, timedelta, timezone
        from models import Borrowing
        from models.borrow import BorrowStatus

        b = Borrowing(
            book_id=a_book.id,
            member_id=a_member.id,
            borrowed_at=datetime.now(timezone.utc),
            due_date=datetime.now(timezone.utc) + timedelta(days=14),
            status=BorrowStatus.borrowed,
        )
        db.add(b)
        db.commit()

        resp = client.delete(f"/api/v1/books/{a_book.id}", headers=auth_headers(tok))
        assert resp.status_code == 400
        assert "active borrowing" in resp.json()["detail"].lower()

    def test_delete_allowed_after_all_borrowings_returned(self, client, tok, db, a_book, a_member):
        """Deleting a book succeeds once all borrowings are returned, and borrowing records survive."""
        from datetime import datetime, timedelta, timezone
        from models import Borrowing
        from models.borrow import BorrowStatus

        b = Borrowing(
            book_id=a_book.id,
            member_id=a_member.id,
            borrowed_at=datetime.now(timezone.utc),
            due_date=datetime.now(timezone.utc) + timedelta(days=14),
            returned_at=datetime.now(timezone.utc),
            status=BorrowStatus.returned,
        )
        db.add(b)
        db.commit()
        borrowing_id = b.id

        resp = client.delete(f"/api/v1/books/{a_book.id}", headers=auth_headers(tok))
        assert resp.status_code == 200

        # Borrowing record survives with book_id set to NULL
        db.expire_all()
        surviving = db.get(Borrowing, borrowing_id)
        assert surviving is not None
        assert surviving.book_id is None


# ---------------------------------------------------------------------------
# borrow_count correctness (Issue #2)
# ---------------------------------------------------------------------------


class TestBorrowCount:
    def test_borrow_count_zero_for_new_book(self, client, tok):
        resp = client.post("/api/v1/books/", json=_book_payload(), headers=auth_headers(tok))
        book_id = resp.json()["id"]
        get_resp = client.get(f"/api/v1/books/{book_id}", headers=auth_headers(tok))
        assert get_resp.status_code == 200
        assert get_resp.json()["borrow_count"] == 0

    def test_borrow_count_increments_after_borrow(self, client, tok, db, a_book, a_member):
        """borrow_count is a correlated subquery — must reflect actual borrowing rows."""
        from datetime import datetime, timedelta, timezone
        from models import Borrowing
        from models.borrow import BorrowStatus

        # Insert a borrowing record directly to bypass the PostgreSQL trigger
        b = Borrowing(
            book_id=a_book.id,
            member_id=a_member.id,
            borrowed_at=datetime.now(timezone.utc),
            due_date=datetime.now(timezone.utc) + timedelta(days=14),
            status=BorrowStatus.borrowed,
        )
        db.add(b)
        db.commit()

        resp = client.get(f"/api/v1/books/{a_book.id}", headers=auth_headers(tok))
        assert resp.status_code == 200
        assert resp.json()["borrow_count"] == 1


# ---------------------------------------------------------------------------
# author_ids validation (Issue #5)
# ---------------------------------------------------------------------------


class TestAuthorIds:
    def test_nonexistent_author_id_returns_400(self, client, tok):
        resp = client.post(
            "/api/v1/books/",
            json=_book_payload(author_ids=[str(uuid.uuid4())]),
            headers=auth_headers(tok),
        )
        assert resp.status_code == 400

    def test_partial_nonexistent_author_ids_returns_400(self, client, tok, db):
        author = Author(name="Valid Author")
        db.add(author)
        db.commit()
        db.refresh(author)
        resp = client.post(
            "/api/v1/books/",
            json=_book_payload(author_ids=[str(author.id), str(uuid.uuid4())]),
            headers=auth_headers(tok),
        )
        assert resp.status_code == 400

    def test_valid_author_id_is_linked(self, client, tok, db):
        author = Author(name="Real Author")
        db.add(author)
        db.commit()
        db.refresh(author)
        resp = client.post(
            "/api/v1/books/",
            json=_book_payload(isbn="9780000000025", author_ids=[str(author.id)]),
            headers=auth_headers(tok),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert len(body["authors"]) == 1
        assert body["authors"][0]["id"] == str(author.id)

    def test_update_with_nonexistent_author_id_returns_400(self, client, tok, db):
        create_resp = client.post("/api/v1/books/", json=_book_payload(), headers=auth_headers(tok))
        book_id = create_resp.json()["id"]
        resp = client.patch(
            f"/api/v1/books/{book_id}",
            json={"author_ids": [str(uuid.uuid4())]},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Update: zero copies rejected (Issue #3)
# ---------------------------------------------------------------------------


class TestUpdateZeroCopies:
    def test_update_zero_copies_rejected(self, client, tok):
        create_resp = client.post("/api/v1/books/", json=_book_payload(), headers=auth_headers(tok))
        book_id = create_resp.json()["id"]
        resp = client.patch(
            f"/api/v1/books/{book_id}",
            json={"total_copies": 0},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Search (Issues #26 & #28)
# ---------------------------------------------------------------------------


class TestBookSearch:
    def test_search_by_title_substring(self, client, tok):
        client.post("/api/v1/books/", json=_book_payload(title="Rust Programming Guide"), headers=auth_headers(tok))
        client.post("/api/v1/books/", json=_book_payload(title="Python Cookbook", isbn=ISBN_B), headers=auth_headers(tok))
        resp = client.get("/api/v1/books/?search=rust", headers=auth_headers(tok))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["title"] == "Rust Programming Guide"

    def test_search_by_title_case_insensitive(self, client, tok):
        client.post("/api/v1/books/", json=_book_payload(title="Django Unleashed"), headers=auth_headers(tok))
        resp = client.get("/api/v1/books/?search=DJANGO", headers=auth_headers(tok))
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_search_by_isbn_substring(self, client, tok):
        client.post("/api/v1/books/", json=_book_payload(isbn="9780000000001"), headers=auth_headers(tok))
        client.post("/api/v1/books/", json=_book_payload(title="Other Book", isbn="9780000000018"), headers=auth_headers(tok))
        resp = client.get("/api/v1/books/?search=9780000000001", headers=auth_headers(tok))
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_search_no_match_returns_empty(self, client, tok):
        client.post("/api/v1/books/", json=_book_payload(), headers=auth_headers(tok))
        resp = client.get("/api/v1/books/?search=zzznomatch", headers=auth_headers(tok))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []

    def test_search_combined_with_category_filter(self, client, tok, db):
        """search and category_id filters should be ANDed together."""
        category = Category(name="Reference")
        db.add(category)
        db.commit()
        db.refresh(category)

        resp = client.get(
            f"/api/v1/books/?search=test&category_id={category.id}",
            headers=auth_headers(tok),
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


# ---------------------------------------------------------------------------
# Book borrowing stats (GET /books/{id}/stats)
# ---------------------------------------------------------------------------


class TestBookStats:
    def test_stats_zero_for_new_book(self, client, tok):
        resp = client.post("/api/v1/books/", json=_book_payload(), headers=auth_headers(tok))
        book_id = resp.json()["id"]
        stats = client.get(f"/api/v1/books/{book_id}/stats", headers=auth_headers(tok))
        assert stats.status_code == 200
        body = stats.json()
        assert body["total_borrows"] == 0
        assert body["active_borrows"] == 0
        assert body["unique_readers"] == 0

    def test_stats_reflect_borrowings(self, client, tok, db, a_book, a_member):
        from datetime import datetime, timedelta, timezone
        from models import Borrowing
        from models.borrow import BorrowStatus

        borrow = Borrowing(
            book_id=a_book.id,
            member_id=a_member.id,
            borrowed_at=datetime.now(timezone.utc),
            due_date=datetime.now(timezone.utc) + timedelta(days=14),
            status=BorrowStatus.borrowed,
        )
        db.add(borrow)
        db.commit()

        stats = client.get(f"/api/v1/books/{a_book.id}/stats", headers=auth_headers(tok))
        assert stats.status_code == 200
        body = stats.json()
        assert body["total_borrows"] == 1
        assert body["active_borrows"] == 1
        assert body["unique_readers"] == 1

    def test_stats_nonexistent_book_returns_404(self, client, tok):
        resp = client.get(f"/api/v1/books/{uuid.uuid4()}/stats", headers=auth_headers(tok))
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Reduce total_copies (#1 fix)
# ---------------------------------------------------------------------------


class TestReduceTotalCopies:
    def test_reduce_total_copies_succeeds(self, client, tok):
        """Reducing total_copies when all copies are available should succeed."""
        resp = client.post("/api/v1/books/", json=_book_payload(total_copies=5), headers=auth_headers(tok))
        book_id = resp.json()["id"]
        patch = client.patch(
            f"/api/v1/books/{book_id}",
            json={"total_copies": 3},
            headers=auth_headers(tok),
        )
        assert patch.status_code == 200
        body = patch.json()
        assert body["total_copies"] == 3
        assert body["available_copies"] == 3

    def test_reduce_below_on_loan_returns_400(self, client, tok, db, a_book, a_member):
        """Reducing total_copies below the count of copies on loan raises 400."""
        from datetime import datetime, timedelta, timezone
        from models import Borrowing
        from models.borrow import BorrowStatus

        # Borrow all copies (a_book has total_copies=1 by default in conftest)
        borrow = Borrowing(
            book_id=a_book.id,
            member_id=a_member.id,
            borrowed_at=datetime.now(timezone.utc),
            due_date=datetime.now(timezone.utc) + timedelta(days=7),
            status=BorrowStatus.borrowed,
        )
        db.add(borrow)
        a_book.available_copies = 0
        db.commit()

        resp = client.patch(
            f"/api/v1/books/{a_book.id}",
            json={"total_copies": 0},
            headers=auth_headers(tok),
        )
        assert resp.status_code in (400, 422)


# ---------------------------------------------------------------------------
# Update with empty author_ids (#12 fix)
# ---------------------------------------------------------------------------


class TestUpdateEmptyAuthorIds:
    def test_update_with_empty_author_ids_returns_422(self, client, tok, db):
        """Passing an empty author_ids list to a book update should be rejected."""
        resp = client.post("/api/v1/books/", json=_book_payload(), headers=auth_headers(tok))
        book_id = resp.json()["id"]
        patch = client.patch(
            f"/api/v1/books/{book_id}",
            json={"author_ids": []},
            headers=auth_headers(tok),
        )
        assert patch.status_code == 422


# ---------------------------------------------------------------------------
# Search max_length (#10 fix)
# ---------------------------------------------------------------------------


class TestSearchMaxLength:
    def test_search_over_200_chars_returns_422(self, client, tok):
        long_query = "a" * 201
        resp = client.get(f"/api/v1/books/?search={long_query}", headers=auth_headers(tok))
        assert resp.status_code == 422
