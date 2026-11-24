"""add embedding columns to document_span and source_span

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-30

"""
from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DIM = 384


def upgrade() -> None:
    op.execute(f"ALTER TABLE document_span ADD COLUMN embedding vector({DIM})")
    op.execute(f"ALTER TABLE source_span ADD COLUMN embedding vector({DIM})")
    # IVFFlat index for cosine search; lists tuned for small corpus.
    op.execute(
        f"CREATE INDEX ix_document_span_embedding ON document_span "
        f"USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50)"
    )
    op.execute(
        f"CREATE INDEX ix_source_span_embedding ON source_span "
        f"USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_document_span_embedding")
    op.execute("DROP INDEX IF EXISTS ix_source_span_embedding")
    op.execute("ALTER TABLE source_span DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE document_span DROP COLUMN IF EXISTS embedding")
