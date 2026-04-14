"""
Shared test fixtures.

Uses an in-memory SQLite database so tests run without a live PostgreSQL instance.
pg_advisory_xact_lock and PostgreSQL-specific member-ID logic are not exercised here;
those are covered by manual / integration tests against a real DB.
"""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Provide required settings before importing app modules that read settings at import time.
# DATABASE_URL must satisfy PostgresDsn validation; the actual DB used in tests is
# overridden via dependency injection (SQLite in-memory), so this URL is never connected to.
os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost/testdb")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-xx")  # 38 chars, satisfies min_length=32

from api.deps import get_db  # noqa: E402
from config.database import Base  # noqa: E402
from core.security import hash_password  # noqa: E402
from main import app  # noqa: E402
from models import Author, Book, Borrowing, Category, Member, User, UserRole  # noqa: E402
from models.book import book_authors  # noqa: E402

_TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(_TEST_ENGINE, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_TEST_ENGINE)


def _override_get_db():
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    """Create all tables once for the entire test session."""
    Base.metadata.create_all(bind=_TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=_TEST_ENGINE)


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Clear in-memory rate-limit counters so tests never hit the limit."""
    from core.limiter import limiter
    limiter._storage.reset()
    yield


@pytest.fixture(autouse=True)
def _reset_token_blocklist():
    """Clear the in-process token revocation set between tests."""
    from core.security import reset_blocklist
    reset_blocklist()
    yield
    reset_blocklist()


@pytest.fixture(autouse=True)
def _clean_tables(_create_tables):
    """Wipe all data tables before each test for isolation."""
    db = _TestingSessionLocal()
    try:
        db.execute(book_authors.delete())
        db.query(Borrowing).delete()
        db.query(Book).delete()
        db.query(Author).delete()
        db.query(Member).delete()
        db.query(User).delete()
        db.query(Category).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture()
def db():
    session = _TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

ADMIN_EMAIL = "admin@library.com"
ADMIN_PASSWORD = "admin123"
MANAGER_EMAIL = "manager@library.com"
MANAGER_PASSWORD = "manager123"


@pytest.fixture()
def seed_admin(db):
    user = User(
        email=ADMIN_EMAIL,
        full_name="Admin User",
        hashed_password=hash_password(ADMIN_PASSWORD),
        role=UserRole.admin,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def seed_manager(db):
    user = User(
        email=MANAGER_EMAIL,
        full_name="Manager User",
        hashed_password=hash_password(MANAGER_PASSWORD),
        role=UserRole.manager,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(client, email: str, password: str) -> str:
    """Helper: log in and return the Bearer token."""
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def manager_token(client, seed_manager):
    return login(client, MANAGER_EMAIL, MANAGER_PASSWORD)


@pytest.fixture()
def a_book(db) -> Book:
    """A book with 2 copies created directly, bypassing PostgreSQL-only CRUD logic."""
    book = Book(
        title="Test Book",
        isbn="9780000000001",
        total_copies=2,
        available_copies=2,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


@pytest.fixture()
def a_member(db) -> Member:
    """A library member created directly, bypassing pg_advisory_xact_lock."""
    member = Member(
        library_id="LIBU0001",
        full_name="Test Member",
        email="testmember@library.com",
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member
