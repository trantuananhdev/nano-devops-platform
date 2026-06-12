"""011: Add api_keys table (T-33 — API Key Management)

Revision ID: 011_add_api_keys
Revises: 010_audit_log_harness
Create Date: 2026-06-09

Migration idempotency — T-66 FINAL FIX (attempt 3):

  The problem: SQLAlchemy 2.0.36 with asyncpg 0.30.0.
  When op.create_table() contains an sa.Enum column, SQLAlchemy registers an
  _on_table_create event listener on the Enum type object. Even with
  create_type=False, the listener is still invoked via the table's "before_create"
  dispatch, and it emits "CREATE TYPE apikeytype AS ENUM (...)" a second time.
  asyncpg raises DuplicateObjectError.

  Root cause (confirmed from traceback):
    named_types.py:98  _on_table_create → self.create(bind=bind, checkfirst=checkfirst)
  The `create_type=False` check in SQLAlchemy's named_types._on_table_create
  does NOT suppress the call when the alembic migration connection context
  differs from the table-level event dispatch binding in SA 2.0.36.

  DEFINITIVE FIX: Bypass op.create_table() entirely for this migration.
  Use raw SQL DDL via op.execute() to create the table.
  Raw DDL does NOT trigger SQLAlchemy type event listeners at all.

  Pattern for all three steps:
    1. pg_type catalog check → CREATE TYPE (if missing)
    2. information_schema check → raw SQL CREATE TABLE (if missing)
    3. pg_indexes check → CREATE INDEX (if missing)
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "011_add_api_keys"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # ── Step 1: Create ENUM type idempotently ─────────────────────────────────
    # PostgreSQL has no "CREATE TYPE IF NOT EXISTS" syntax.
    # Check pg_type catalog first; CREATE TYPE only when absent.
    type_exists = bind.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'apikeytype'")
    ).scalar()
    if not type_exists:
        # Use op.execute() for DDL — routes through Alembic's DDL executor,
        # not the prepared-statement path.
        op.execute(sa.text(
            "CREATE TYPE apikeytype AS ENUM ('gemini', 'mcp', 'minio', 'internal')"
        ))

    # ── Step 2: Create table via raw SQL DDL ──────────────────────────────────
    # IMPORTANT: We do NOT use op.create_table() with sa.Enum here.
    # op.create_table() + sa.Enum triggers SQLAlchemy's _on_table_create event
    # which emits a second "CREATE TYPE" even when create_type=False — this is a
    # confirmed bug/limitation in SQLAlchemy 2.0.36 + asyncpg 0.30.0 under
    # Alembic's async migration context.
    #
    # Raw SQL DDL bypasses ALL SQLAlchemy type event listeners entirely.
    table_exists = bind.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_name = 'api_keys' AND table_schema = 'public'"
        )
    ).scalar()

    if not table_exists:
        op.execute(sa.text("""
            CREATE TABLE api_keys (
                id          SERIAL PRIMARY KEY,
                name        VARCHAR(128) NOT NULL,
                key_type    apikeytype NOT NULL,
                key_prefix  VARCHAR(16) NOT NULL,
                hashed_key  VARCHAR(255) NOT NULL,
                is_active   BOOLEAN NOT NULL DEFAULT true,
                created_by  INTEGER REFERENCES users(id) ON DELETE SET NULL,
                last_used_at TIMESTAMPTZ,
                created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

    # ── Step 3: Create indexes idempotently ───────────────────────────────────
    def _idx_exists(name: str) -> bool:
        return bool(
            bind.execute(
                sa.text(
                    "SELECT 1 FROM pg_indexes "
                    "WHERE indexname = :name AND tablename = 'api_keys'"
                ),
                {"name": name},
            ).scalar()
        )

    if not _idx_exists("ix_api_keys_key_type"):
        op.execute(sa.text(
            "CREATE INDEX ix_api_keys_key_type ON api_keys (key_type)"
        ))
    if not _idx_exists("ix_api_keys_is_active"):
        op.execute(sa.text(
            "CREATE INDEX ix_api_keys_is_active ON api_keys (is_active)"
        ))


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_api_keys_is_active"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_api_keys_key_type"))
    op.execute(sa.text("DROP TABLE IF EXISTS api_keys"))
    op.execute(sa.text("DROP TYPE IF EXISTS apikeytype"))
