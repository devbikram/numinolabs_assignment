"""initial schema — complete library management system

All tables, constraints, indexes, enums, triggers, and functional indexes.

Revision ID: 0001
Revises:
Create Date: 2026-04-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Users ────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "manager", name="userrole", native_enum=False),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("users_pkey")),
    )
    op.create_index(op.f("users_email_idx"), "users", ["email"], unique=True)

    # ── Authors ──────────────────────────────────────────────────────────
    op.create_table(
        "author",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("author_pkey")),
    )
    op.create_index(op.f("author_name_idx"), "author", ["name"], unique=False)

    # Normalized unique index: case-insensitive, trimmed
    op.execute(
        "CREATE UNIQUE INDEX author_name_normalized_key ON author (LOWER(BTRIM(name)))"
    )

    # ── Categories ───────────────────────────────────────────────────────
    op.create_table(
        "category",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("category_pkey")),
    )
    op.create_index(op.f("category_name_idx"), "category", ["name"], unique=True)

    # ── Members ──────────────────────────────────────────────────────────
    op.create_table(
        "member",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("library_id", sa.String(length=20), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("member_pkey")),
        sa.UniqueConstraint("email", name=op.f("member_email_key")),
    )
    op.create_index(op.f("member_library_id_idx"), "member", ["library_id"], unique=True)
    op.create_index(op.f("member_full_name_idx"), "member", ["full_name"], unique=False)

    # ── Books ────────────────────────────────────────────────────────────
    op.create_table(
        "book",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("isbn", sa.String(length=13), nullable=False),
        sa.Column(
            "category_id",
            sa.Uuid(),
            sa.ForeignKey("category.id", ondelete="SET NULL", name=op.f("book_category_id_fkey")),
            nullable=True,
        ),
        sa.Column("published_year", sa.Integer(), nullable=True),
        sa.Column("total_copies", sa.Integer(), nullable=False),
        sa.Column("available_copies", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("book_pkey")),
        sa.UniqueConstraint("isbn", name=op.f("book_isbn_key")),
        sa.CheckConstraint("total_copies >= 0", name=op.f("book_total_copies_non_negative_check")),
        sa.CheckConstraint("available_copies >= 0", name=op.f("book_available_copies_non_negative_check")),
        sa.CheckConstraint("available_copies <= total_copies", name=op.f("book_available_lte_total_check")),
    )
    op.create_index(op.f("book_title_idx"), "book", ["title"], unique=False)
    op.create_index(op.f("book_category_id_idx"), "book", ["category_id"], unique=False)

    # ── Book ↔ Author (many-to-many) ────────────────────────────────────
    op.create_table(
        "book_authors",
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["book_id"], ["book.id"],
            name=op.f("book_authors_book_id_fkey"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["author_id"], ["author.id"],
            name=op.f("book_authors_author_id_fkey"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("book_id", "author_id", name=op.f("book_authors_pkey")),
    )

    # ── Borrowings ───────────────────────────────────────────────────────
    op.create_table(
        "borrowing",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("book_id", sa.Uuid(), nullable=True),
        sa.Column("member_id", sa.Uuid(), nullable=True),
        sa.Column("borrowed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("borrowed", "returned", "overdue", name="borrow_status"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["book_id"], ["book.id"],
            name=op.f("borrowing_book_id_fkey"), ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["member_id"], ["member.id"],
            name=op.f("borrowing_member_id_fkey"), ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("borrowing_pkey")),
    )

    # ── Trigger: sync available_copies on borrow/return ──────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION sync_available_copies()
        RETURNS TRIGGER AS $$
        DECLARE
            target_book_id UUID;
        BEGIN
            target_book_id := COALESCE(NEW.book_id, OLD.book_id);

            UPDATE book
            SET available_copies = total_copies - (
                SELECT COUNT(*)
                FROM borrowing
                WHERE book_id = target_book_id
                  AND status IN ('borrowed', 'overdue')
            )
            WHERE id = target_book_id;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_sync_available_copies
        AFTER INSERT OR UPDATE OR DELETE ON borrowing
        FOR EACH ROW
        EXECUTE FUNCTION sync_available_copies();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_sync_available_copies ON borrowing")
    op.execute("DROP FUNCTION IF EXISTS sync_available_copies()")
    op.drop_table("borrowing")
    op.drop_table("book_authors")
    op.drop_index(op.f("book_category_id_idx"), table_name="book")
    op.drop_index(op.f("book_title_idx"), table_name="book")
    op.drop_table("book")
    op.drop_index(op.f("member_full_name_idx"), table_name="member")
    op.drop_index(op.f("member_library_id_idx"), table_name="member")
    op.drop_table("member")
    op.drop_index(op.f("category_name_idx"), table_name="category")
    op.drop_table("category")
    op.execute("DROP INDEX IF EXISTS author_name_normalized_key")
    op.drop_index(op.f("author_name_idx"), table_name="author")
    op.drop_table("author")
    op.drop_index(op.f("users_email_idx"), table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS borrow_status")
