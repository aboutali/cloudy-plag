"""init schema: person, document, document_span + pgvector

Revision ID: 0001
Revises:
Create Date: 2026-04-30

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "person",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("display_name", sa.String(256), nullable=False),
        sa.Column("roles", sa.JSON(), nullable=True),
        sa.Column("legal_sensitivity_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("right_of_reply_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "document",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("person.id"), nullable=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("institution", sa.String(256), nullable=True),
        sa.Column("degree", sa.String(128), nullable=True),
        sa.Column("pdf_object_key", sa.String(512), nullable=False),
        sa.Column("canonical_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("provenance", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "document_span",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("document.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("bbox_x0", sa.Float(), nullable=False),
        sa.Column("bbox_y0", sa.Float(), nullable=False),
        sa.Column("bbox_x1", sa.Float(), nullable=False),
        sa.Column("bbox_y1", sa.Float(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("section_path", sa.JSON(), nullable=True),
    )
    op.create_index("ix_document_span_doc_page", "document_span", ["document_id", "page"])


def downgrade() -> None:
    op.drop_index("ix_document_span_doc_page", table_name="document_span")
    op.drop_table("document_span")
    op.drop_table("document")
    op.drop_table("person")
