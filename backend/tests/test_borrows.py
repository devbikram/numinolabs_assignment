"""
Integration tests for borrowing and return endpoints.
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from models import Book, Borrowing, Member
from models.borrow import BorrowStatus
from tests.conftest import MANAGER_EMAIL, MANAGER_PASSWORD, auth_headers, login

_DUE = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()


@pytest.fixture()
def tok(client, seed_manager):
    return login(client, MANAGER_EMAIL, MANAGER_PASSWORD)


def _borrow_payload(book_id, member_id):
    return {"book_id": str(book_id), "member_id": str(member_id), "due_date": _DUE}


# ---------------------------------------------------------------------------
# Borrow — success path
# ---------------------------------------------------------------------------


class TestBorrowSuccess:
    def test_borrow_returns_201_with_nested_book_and_member(
        self, client, tok, a_book, a_member
    ):
        resp = client.post(
            "/api/v1/borrows/",
            json=_borrow_payload(a_book.id, a_member.id),
            headers=auth_headers(tok),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "borrowed"
        assert body["book"]["id"] == str(a_book.id)
        assert body["member"]["id"] == str(a_member.id)
        assert body["returned_at"] is None

    def test_borrow_decrements_available_copies(self, client, tok, db, a_book, a_member):
        assert a_book.available_copies == 2

        client.post(
            "/api/v1/borrows/",
            json=_borrow_payload(a_book.id, a_member.id),
            headers=auth_headers(tok),
        )
        db.refresh(a_book)
        assert a_book.available_copies == 1

    def test_borrow_creates_retrievable_record(self, client, tok, a_book, a_member):
        create_resp = client.post(
            "/api/v1/borrows/",
            json=_borrow_payload(a_book.id, a_member.id),
            headers=auth_headers(tok),
        )
        borrow_id = create_resp.json()["id"]
        get_resp = client.get(f"/api/v1/borrows/{borrow_id}", headers=auth_headers(tok))
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == borrow_id


# ---------------------------------------------------------------------------
# Return — success and rejection paths
# ---------------------------------------------------------------------------


class TestReturn:
    def test_return_sets_status_and_returned_at(self, client, tok, a_book, a_member):
        borrow_resp = client.post(
            "/api/v1/borrows/",
            json=_borrow_payload(a_book.id, a_member.id),
            headers=auth_headers(tok),
        )
        borrow_id = borrow_resp.json()["id"]
        return_resp = client.patch(
            f"/api/v1/borrows/{borrow_id}/return",
            headers=auth_headers(tok),
        )
        assert return_resp.status_code == 200
        body = return_resp.json()
        assert body["status"] == "returned"
        assert body["returned_at"] is not None

    def test_return_increments_available_copies(self, client, tok, db, a_book, a_member):
        borrow_resp = client.post(
            "/api/v1/borrows/",
            json=_borrow_payload(a_book.id, a_member.id),
            headers=auth_headers(tok),
        )
        db.refresh(a_book)
        assert a_book.available_copies == 1

        borrow_id = borrow_resp.json()["id"]
        client.patch(f"/api/v1/borrows/{borrow_id}/return", headers=auth_headers(tok))
        db.refresh(a_book)
        assert a_book.available_copies == 2

    def test_double_return_rejected_with_400(self, client, tok, a_book, a_member):
        borrow_resp = client.post(
            "/api/v1/borrows/",
            json=_borrow_payload(a_book.id, a_member.id),
            headers=auth_headers(tok),
        )
        borrow_id = borrow_resp.json()["id"]
        client.patch(f"/api/v1/borrows/{borrow_id}/return", headers=auth_headers(tok))
        resp = client.patch(f"/api/v1/borrows/{borrow_id}/return", headers=auth_headers(tok))
        assert resp.status_code == 400

    def test_return_nonexistent_borrowing_returns_404(self, client, tok):
        resp = client.patch(
            f"/api/v1/borrows/{uuid.uuid4()}/return",
            headers=auth_headers(tok),
        )
        assert resp.status_code == 404

    def test_return_succeeds_when_book_was_deleted(self, client, tok, db, a_book, a_member):
        """Returning a borrowing whose book was deleted marks it returned without crashing."""
        b = Borrowing(
            book_id=a_book.id,
            member_id=a_member.id,
            borrowed_at=datetime.now(timezone.utc),
            due_date=datetime.now(timezone.utc) + timedelta(days=14),
            status=BorrowStatus.borrowed,
        )
        db.add(b)
        # Manually adjust available_copies to reflect the borrow
        a_book.available_copies -= 1
        db.commit()
        borrowing_id = b.id

        # Delete the book (no active borrows guard fires because we bypass service)
        db.delete(a_book)
        db.commit()

        # Now return the borrowing — should succeed gracefully
        resp = client.patch(
            f"/api/v1/borrows/{borrowing_id}/return",
            headers=auth_headers(tok),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "returned"
        assert body["returned_at"] is not None
        assert body["book_id"] is None


# ---------------------------------------------------------------------------
# 404 paths for borrow
# ---------------------------------------------------------------------------


class TestBorrowNotFound:
    def test_borrow_nonexistent_book_returns_404(self, client, tok, a_member):
        resp = client.post(
            "/api/v1/borrows/",
            json=_borrow_payload(uuid.uuid4(), a_member.id),
            headers=auth_headers(tok),
        )
        assert resp.status_code == 404

    def test_borrow_nonexistent_member_returns_404(self, client, tok, a_book):
        resp = client.post(
            "/api/v1/borrows/",
            json=_borrow_payload(a_book.id, uuid.uuid4()),
            headers=auth_headers(tok),
        )
        assert resp.status_code == 404

    @pytest.mark.parametrize("query_key", ["book_id", "member_id", "category_id", "author_id"])
    def test_list_borrowings_invalid_filter_returns_404(self, client, tok, query_key):
        resp = client.get(
            f"/api/v1/borrows/?{query_key}={uuid.uuid4()}",
            headers=auth_headers(tok),
        )
        assert resp.status_code == 404

    def test_list_borrowings_invalid_sort_by_returns_422(self, client, tok):
        resp = client.get("/api/v1/borrows/?sort_by=not_a_column", headers=auth_headers(tok))
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Unavailable book — fast-fail guard
# ---------------------------------------------------------------------------


class TestUnavailableBook:
    def test_borrow_zero_copy_book_returns_400(self, client, tok, db, a_member):
        """Book with available_copies=0 is rejected by the endpoint fast-fail guard."""
        exhausted = Book(
            title="No Copies",
            isbn="0000000001",
            total_copies=1,
            available_copies=0,
        )
        db.add(exhausted)
        db.commit()
        db.refresh(exhausted)

        resp = client.post(
            "/api/v1/borrows/",
            json=_borrow_payload(exhausted.id, a_member.id),
            headers=auth_headers(tok),
        )
        assert resp.status_code == 400
        assert "no available copies" in resp.json()["detail"].lower()

    def test_all_copies_exhausted_returns_400(self, client, tok, db, a_member):
        """Once all copies are borrowed, the next borrow attempt returns 400."""
        single_copy = Book(
            title="Single Copy Book",
            isbn="0000000099",
            total_copies=1,
            available_copies=1,
        )
        db.add(single_copy)
        db.commit()
        db.refresh(single_copy)

        # First borrow succeeds
        resp1 = client.post(
            "/api/v1/borrows/",
            json=_borrow_payload(single_copy.id, a_member.id),
            headers=auth_headers(tok),
        )
        assert resp1.status_code == 201
        db.refresh(single_copy)
        assert single_copy.available_copies == 0

        # Create a second member to try borrowing the same book
        second_member = Member(
            library_id="LIBU9999",
            full_name="Second Member",
            email="second@library.com",
        )
        db.add(second_member)
        db.commit()
        db.refresh(second_member)

        resp2 = client.post(
            "/api/v1/borrows/",
            json=_borrow_payload(single_copy.id, second_member.id),
            headers=auth_headers(tok),
        )
        assert resp2.status_code == 400


# ---------------------------------------------------------------------------
# Duplicate active borrowing prevention
# ---------------------------------------------------------------------------


class TestDuplicateBorrowing:
    def test_same_member_cannot_borrow_same_book_twice(
        self, client, tok, a_book, a_member
    ):
        """A member with an active borrowing for a book cannot borrow it again."""
        resp1 = client.post(
            "/api/v1/borrows/",
            json=_borrow_payload(a_book.id, a_member.id),
            headers=auth_headers(tok),
        )
        assert resp1.status_code == 201

        resp2 = client.post(
            "/api/v1/borrows/",
            json=_borrow_payload(a_book.id, a_member.id),
            headers=auth_headers(tok),
        )
        assert resp2.status_code == 400
        assert "already has an active borrowing" in resp2.json()["detail"].lower()

    def test_member_can_reborrow_after_return(self, client, tok, a_book, a_member):
        """Once returned, the same member can borrow the same book again."""
        borrow_resp = client.post(
            "/api/v1/borrows/",
            json=_borrow_payload(a_book.id, a_member.id),
            headers=auth_headers(tok),
        )
        borrow_id = borrow_resp.json()["id"]
        client.patch(f"/api/v1/borrows/{borrow_id}/return", headers=auth_headers(tok))

        resp = client.post(
            "/api/v1/borrows/",
            json=_borrow_payload(a_book.id, a_member.id),
            headers=auth_headers(tok),
        )
        assert resp.status_code == 201

    def test_different_members_can_borrow_same_book(
        self, client, tok, db, a_book, a_member
    ):
        """Different members can borrow different copies of the same book."""
        resp1 = client.post(
            "/api/v1/borrows/",
            json=_borrow_payload(a_book.id, a_member.id),
            headers=auth_headers(tok),
        )
        assert resp1.status_code == 201

        second_member = Member(
            library_id="LIBU0002",
            full_name="Another Member",
            email="another@library.com",
        )
        db.add(second_member)
        db.commit()
        db.refresh(second_member)

        resp2 = client.post(
            "/api/v1/borrows/",
            json=_borrow_payload(a_book.id, second_member.id),
            headers=auth_headers(tok),
        )
        assert resp2.status_code == 201


# ---------------------------------------------------------------------------
# Borrow list
# ---------------------------------------------------------------------------


class TestBorrowList:
    def test_list_borrowings_returns_paginated(self, client, tok, a_book, a_member):
        client.post(
            "/api/v1/borrows/",
            json=_borrow_payload(a_book.id, a_member.id),
            headers=auth_headers(tok),
        )
        resp = client.get("/api/v1/borrows/", headers=auth_headers(tok))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert len(body["items"]) >= 1

    def test_unauthenticated_cannot_list_borrowings(self, client):
        resp = client.get("/api/v1/borrows/")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Overdue marking (Issue #4)
# ---------------------------------------------------------------------------


class TestOverdue:
    def test_mark_overdue_transitions_borrowed_to_overdue(self, db, a_book, a_member):
        """mark_overdue_borrowings flips borrowed records with a past due_date."""
        from crud.borrow import mark_overdue_borrowings

        borrowing = Borrowing(
            book_id=a_book.id,
            member_id=a_member.id,
            borrowed_at=datetime.now(timezone.utc) - timedelta(days=20),
            due_date=datetime.now(timezone.utc) - timedelta(days=1),
            status=BorrowStatus.borrowed,
        )
        db.add(borrowing)
        db.commit()
        db.refresh(borrowing)

        count = mark_overdue_borrowings(db)
        db.refresh(borrowing)

        assert count == 1
        assert borrowing.status == BorrowStatus.overdue

    def test_mark_overdue_ignores_returned_borrowings(self, db, a_book, a_member):
        """Already-returned records with a past due_date must not be changed."""
        from crud.borrow import mark_overdue_borrowings

        borrowing = Borrowing(
            book_id=a_book.id,
            member_id=a_member.id,
            borrowed_at=datetime.now(timezone.utc) - timedelta(days=20),
            due_date=datetime.now(timezone.utc) - timedelta(days=1),
            returned_at=datetime.now(timezone.utc) - timedelta(days=5),
            status=BorrowStatus.returned,
        )
        db.add(borrowing)
        db.commit()
        db.refresh(borrowing)

        mark_overdue_borrowings(db)
        db.refresh(borrowing)

        assert borrowing.status == BorrowStatus.returned

    def test_mark_overdue_ignores_future_due_dates(self, db, a_book, a_member):
        """Active borrowings with a future due_date must not be marked overdue."""
        from crud.borrow import mark_overdue_borrowings

        borrowing = Borrowing(
            book_id=a_book.id,
            member_id=a_member.id,
            borrowed_at=datetime.now(timezone.utc),
            due_date=datetime.now(timezone.utc) + timedelta(days=7),
            status=BorrowStatus.borrowed,
        )
        db.add(borrowing)
        db.commit()
        db.refresh(borrowing)

        count = mark_overdue_borrowings(db)
        db.refresh(borrowing)

        assert count == 0
        assert borrowing.status == BorrowStatus.borrowed


# ---------------------------------------------------------------------------
# Due-date validation (Issue #11)
# ---------------------------------------------------------------------------


class TestDueDateValidation:
    def test_past_due_date_rejected(self, client, tok, a_book, a_member):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        resp = client.post(
            "/api/v1/borrows/",
            json={"book_id": str(a_book.id), "member_id": str(a_member.id), "due_date": past},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 422

    def test_present_due_date_rejected(self, client, tok, a_book, a_member):
        # datetime.now is not in the future — the validator should reject it
        right_now = datetime.now(timezone.utc).isoformat()
        resp = client.post(
            "/api/v1/borrows/",
            json={"book_id": str(a_book.id), "member_id": str(a_member.id), "due_date": right_now},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 422

    def test_future_due_date_passes_validation(self, client, tok, a_book, a_member):
        future = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
        resp = client.post(
            "/api/v1/borrows/",
            json={"book_id": str(a_book.id), "member_id": str(a_member.id), "due_date": future},
            headers=auth_headers(tok),
        )
        # 422 would mean schema rejected it — any other status means validation passed
        assert resp.status_code != 422

    def test_far_future_due_date_rejected(self, client, tok, a_book, a_member):
        far_future = (datetime.now(timezone.utc) + timedelta(days=5 * 365 + 1)).isoformat()
        resp = client.post(
            "/api/v1/borrows/",
            json={"book_id": str(a_book.id), "member_id": str(a_member.id), "due_date": far_future},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 422

    def test_naive_due_date_rejected(self, client, tok, a_book, a_member):
        # Naive datetime (no timezone info) must be rejected with 422
        naive = "2099-01-01T12:00:00"
        resp = client.post(
            "/api/v1/borrows/",
            json={"book_id": str(a_book.id), "member_id": str(a_member.id), "due_date": naive},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /borrows/{id} — not-found path
# ---------------------------------------------------------------------------


class TestGetBorrowingById:
    def test_get_nonexistent_borrowing_returns_404(self, client, tok):
        resp = client.get(f"/api/v1/borrows/{uuid.uuid4()}", headers=auth_headers(tok))
        assert resp.status_code == 404
