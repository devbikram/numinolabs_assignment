"""
Integration tests for the /members endpoints.

NOTE on PostgreSQL-specific member creation:
  `_next_library_id` uses pg_advisory_xact_lock and REGEXP_REPLACE which are
  not available in SQLite. Tests that exercise POST /members/ patch that function
  with a SQLite-compatible counter. All other endpoints are tested against members
  created directly via the DB fixture (a_member / _make_member).
"""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from models.borrow import BorrowStatus, Borrowing
from tests.conftest import MANAGER_EMAIL, MANAGER_PASSWORD, auth_headers, login

_DUE = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()


@pytest.fixture()
def tok(client, seed_manager):
    return login(client, MANAGER_EMAIL, MANAGER_PASSWORD)


@pytest.fixture()
def mock_library_id():
    """Replace pg-specific _next_library_id with a SQLite-compatible counter."""
    counter = [0]

    def _next_id(db):
        counter[0] += 1
        return f"LIBU{counter[0]:04d}"

    with patch("crud.member._next_library_id", side_effect=_next_id):
        yield


def _make_member(db, *, full_name="Alice Smith", email="alice@library.com",
                 library_id=None, phone=None, address=None):
    from models.member import Member
    member = Member(
        library_id=library_id or f"LIBU{uuid.uuid4().hex[:4].upper()}",
        full_name=full_name,
        email=email,
        phone=phone,
        address=address,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class TestCreateMember:
    def test_success_returns_201_with_library_id(self, client, tok, mock_library_id):
        resp = client.post(
            "/api/v1/members/",
            json={"full_name": "Alice Smith", "email": "alice@library.com"},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["full_name"] == "Alice Smith"
        assert body["email"] == "alice@library.com"
        assert body["library_id"].startswith("LIBU")
        assert "id" in body
        assert "created_at" in body
        assert "updated_at" in body

    def test_library_ids_are_sequential(self, client, tok, mock_library_id):
        r1 = client.post(
            "/api/v1/members/",
            json={"full_name": "Alice", "email": "a@lib.com"},
            headers=auth_headers(tok),
        )
        r2 = client.post(
            "/api/v1/members/",
            json={"full_name": "Bob", "email": "b@lib.com"},
            headers=auth_headers(tok),
        )
        assert r1.json()["library_id"] == "LIBU0001"
        assert r2.json()["library_id"] == "LIBU0002"

    def test_duplicate_email_returns_409(self, client, tok, mock_library_id):
        client.post(
            "/api/v1/members/",
            json={"full_name": "Alice", "email": "dup@library.com"},
            headers=auth_headers(tok),
        )
        resp = client.post(
            "/api/v1/members/",
            json={"full_name": "Alice Copy", "email": "dup@library.com"},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 409

    def test_optional_phone_and_address(self, client, tok, mock_library_id):
        resp = client.post(
            "/api/v1/members/",
            json={"full_name": "Bob", "email": "bob@library.com",
                  "phone": "555-1234", "address": "123 Main St"},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["phone"] == "555-1234"
        assert body["address"] == "123 Main St"

    def test_invalid_email_returns_422(self, client, tok):
        resp = client.post(
            "/api/v1/members/",
            json={"full_name": "Bad Email", "email": "not-an-email"},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 422

    def test_missing_required_fields_returns_422(self, client, tok):
        resp = client.post("/api/v1/members/", json={}, headers=auth_headers(tok))
        assert resp.status_code == 422

    def test_unauthenticated_returns_401(self, client):
        resp = client.post(
            "/api/v1/members/",
            json={"full_name": "Eve", "email": "eve@library.com"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


class TestListMembers:
    def test_empty_returns_paginated_response(self, client, tok):
        resp = client.get("/api/v1/members/", headers=auth_headers(tok))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []

    def test_lists_existing_members(self, client, tok, db):
        _make_member(db, full_name="Alice", email="alice@lib.com", library_id="LIBU0001")
        _make_member(db, full_name="Bob", email="bob@lib.com", library_id="LIBU0002")
        resp = client.get("/api/v1/members/", headers=auth_headers(tok))
        body = resp.json()
        assert body["total"] == 2
        names = {m["full_name"] for m in body["items"]}
        assert names == {"Alice", "Bob"}

    def test_members_ordered_by_name(self, client, tok, db):
        _make_member(db, full_name="Zara", email="z@lib.com", library_id="LIBU0003")
        _make_member(db, full_name="Alice", email="a@lib.com", library_id="LIBU0001")
        _make_member(db, full_name="Mike", email="m@lib.com", library_id="LIBU0002")
        resp = client.get("/api/v1/members/", headers=auth_headers(tok))
        names = [m["full_name"] for m in resp.json()["items"]]
        assert names == sorted(names)

    def test_pagination_skip_and_limit(self, client, tok, db):
        for i in range(1, 5):
            _make_member(db, full_name=f"Member {i}", email=f"m{i}@lib.com",
                         library_id=f"LIBU{i:04d}")
        resp = client.get("/api/v1/members/?skip=2&limit=2", headers=auth_headers(tok))
        body = resp.json()
        assert body["total"] == 4
        assert len(body["items"]) == 2

    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/api/v1/members/")
        assert resp.status_code == 401

    def test_invalid_sort_by_returns_422(self, client, tok):
        resp = client.get("/api/v1/members/?sort_by=not_a_column", headers=auth_headers(tok))
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


class TestSearchMembers:
    def test_search_by_name(self, client, tok, db):
        _make_member(db, full_name="Alice Smith", email="alice@lib.com", library_id="LIBU0001")
        _make_member(db, full_name="Bob Jones", email="bob@lib.com", library_id="LIBU0002")
        resp = client.get("/api/v1/members/?search=alice", headers=auth_headers(tok))
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["full_name"] == "Alice Smith"

    def test_search_by_email(self, client, tok, db):
        _make_member(db, full_name="Alice", email="alice@library.com", library_id="LIBU0001")
        _make_member(db, full_name="Bob", email="bob@other.com", library_id="LIBU0002")
        resp = client.get("/api/v1/members/?search=library.com", headers=auth_headers(tok))
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["full_name"] == "Alice"

    def test_search_by_library_id(self, client, tok, db):
        _make_member(db, full_name="Alice", email="alice@lib.com", library_id="LIBU0042")
        _make_member(db, full_name="Bob", email="bob@lib.com", library_id="LIBU0099")
        resp = client.get("/api/v1/members/?search=0042", headers=auth_headers(tok))
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["library_id"] == "LIBU0042"

    def test_search_case_insensitive(self, client, tok, db):
        _make_member(db, full_name="Alice Smith", email="a@lib.com", library_id="LIBU0001")
        resp = client.get("/api/v1/members/?search=ALICE", headers=auth_headers(tok))
        assert resp.json()["total"] == 1

    def test_search_no_match_returns_empty(self, client, tok, db):
        _make_member(db, full_name="Alice", email="a@lib.com", library_id="LIBU0001")
        resp = client.get("/api/v1/members/?search=zzznomatch", headers=auth_headers(tok))
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []


# ---------------------------------------------------------------------------
# Get by ID
# ---------------------------------------------------------------------------


class TestGetMember:
    def test_returns_member(self, client, tok, a_member):
        resp = client.get(f"/api/v1/members/{a_member.id}", headers=auth_headers(tok))
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == str(a_member.id)
        assert body["full_name"] == a_member.full_name
        assert body["library_id"] == a_member.library_id

    def test_unknown_id_returns_404(self, client, tok):
        resp = client.get(f"/api/v1/members/{uuid.uuid4()}", headers=auth_headers(tok))
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"/api/v1/members/{uuid.uuid4()}")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


class TestUpdateMember:
    def test_update_name_succeeds(self, client, tok, a_member):
        resp = client.patch(
            f"/api/v1/members/{a_member.id}",
            json={"full_name": "Updated Name"},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Updated Name"

    def test_update_phone_and_address(self, client, tok, a_member):
        resp = client.patch(
            f"/api/v1/members/{a_member.id}",
            json={"phone": "999-0000", "address": "456 Oak Ave"},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["phone"] == "999-0000"
        assert body["address"] == "456 Oak Ave"

    def test_update_email_to_own_email_is_allowed(self, client, tok, a_member):
        resp = client.patch(
            f"/api/v1/members/{a_member.id}",
            json={"email": a_member.email},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == a_member.email

    def test_update_email_to_existing_email_returns_409(self, client, tok, db, a_member):
        other = _make_member(db, full_name="Other", email="other@lib.com",
                             library_id="LIBU9999")
        resp = client.patch(
            f"/api/v1/members/{a_member.id}",
            json={"email": other.email},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 409

    def test_update_nonexistent_member_returns_404(self, client, tok):
        resp = client.patch(
            f"/api/v1/members/{uuid.uuid4()}",
            json={"full_name": "Ghost"},
            headers=auth_headers(tok),
        )
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        resp = client.patch(
            f"/api/v1/members/{uuid.uuid4()}",
            json={"full_name": "X"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


class TestDeleteMember:
    def test_delete_returns_200_with_message(self, client, tok, a_member):
        resp = client.delete(f"/api/v1/members/{a_member.id}", headers=auth_headers(tok))
        assert resp.status_code == 200
        assert resp.json()["message"] == "Member deleted successfully"

    def test_deleted_member_not_retrievable(self, client, tok, a_member):
        client.delete(f"/api/v1/members/{a_member.id}", headers=auth_headers(tok))
        resp = client.get(f"/api/v1/members/{a_member.id}", headers=auth_headers(tok))
        assert resp.status_code == 404

    def test_delete_nonexistent_returns_404(self, client, tok):
        resp = client.delete(
            f"/api/v1/members/{uuid.uuid4()}", headers=auth_headers(tok)
        )
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        resp = client.delete(f"/api/v1/members/{uuid.uuid4()}")
        assert resp.status_code == 401

    def test_delete_blocked_when_active_borrowing_exists(self, client, tok, db, a_member):
        """Cannot delete a member that has active (borrowed/overdue) borrowings."""
        from models import Book

        book = Book(title="Borrow Book", isbn="9780000099001", total_copies=2, available_copies=2)
        db.add(book)
        db.commit()
        db.refresh(book)

        b = Borrowing(
            book_id=book.id,
            member_id=a_member.id,
            borrowed_at=datetime.now(timezone.utc),
            due_date=datetime.now(timezone.utc) + timedelta(days=14),
            status=BorrowStatus.borrowed,
        )
        db.add(b)
        db.commit()

        resp = client.delete(f"/api/v1/members/{a_member.id}", headers=auth_headers(tok))
        assert resp.status_code == 400
        assert "active borrowing" in resp.json()["detail"].lower()

    def test_delete_allowed_after_all_borrowings_returned(self, client, tok, db, a_member):
        """Deleting a member succeeds once all borrowings are returned; records survive."""
        from models import Book

        book = Book(title="Borrow Book", isbn="9780000099002", total_copies=2, available_copies=2)
        db.add(book)
        db.commit()
        db.refresh(book)

        b = Borrowing(
            book_id=book.id,
            member_id=a_member.id,
            borrowed_at=datetime.now(timezone.utc),
            due_date=datetime.now(timezone.utc) + timedelta(days=14),
            returned_at=datetime.now(timezone.utc),
            status=BorrowStatus.returned,
        )
        db.add(b)
        db.commit()
        borrowing_id = b.id

        resp = client.delete(f"/api/v1/members/{a_member.id}", headers=auth_headers(tok))
        assert resp.status_code == 200

        # Borrowing record survives with member_id set to NULL
        db.expire_all()
        surviving = db.get(Borrowing, borrowing_id)
        assert surviving is not None
        assert surviving.member_id is None


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


class TestMemberStats:
    def test_stats_zero_for_new_member(self, client, tok, a_member):
        resp = client.get(
            f"/api/v1/members/{a_member.id}/stats", headers=auth_headers(tok)
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body == {"total": 0, "borrowed": 0, "returned": 0, "overdue": 0}

    def test_stats_reflect_borrowing_status_counts(self, client, tok, db, a_member):
        from models import Book
        book1 = Book(title="Book A", isbn="9780000000011", total_copies=3, available_copies=3)
        book2 = Book(title="Book B", isbn="9780000000022", total_copies=3, available_copies=3)
        book3 = Book(title="Book C", isbn="9780000000033", total_copies=3, available_copies=3)
        db.add_all([book1, book2, book3])
        db.commit()

        now = datetime.now(timezone.utc)
        due = now + timedelta(days=14)

        borrowings = [
            Borrowing(book_id=book1.id, member_id=a_member.id,
                      borrowed_at=now, due_date=due, status=BorrowStatus.borrowed),
            Borrowing(book_id=book2.id, member_id=a_member.id,
                      borrowed_at=now, due_date=due, status=BorrowStatus.returned,
                      returned_at=now),
            Borrowing(book_id=book3.id, member_id=a_member.id,
                      borrowed_at=now, due_date=now - timedelta(days=1),
                      status=BorrowStatus.overdue),
        ]
        db.add_all(borrowings)
        db.commit()

        resp = client.get(
            f"/api/v1/members/{a_member.id}/stats", headers=auth_headers(tok)
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 3
        assert body["borrowed"] == 1
        assert body["returned"] == 1
        assert body["overdue"] == 1

    def test_stats_unknown_member_returns_404(self, client, tok):
        resp = client.get(
            f"/api/v1/members/{uuid.uuid4()}/stats", headers=auth_headers(tok)
        )
        assert resp.status_code == 404

    def test_stats_unauthenticated_returns_401(self, client):
        resp = client.get(f"/api/v1/members/{uuid.uuid4()}/stats")
        assert resp.status_code == 401
