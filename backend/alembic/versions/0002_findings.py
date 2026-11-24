"""source, source_span, analysis_run, reviewer, finding, review

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-30

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "source",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("authors", sa.JSON(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("identifiers", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("canonical_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("archived_copy_key", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "source_span",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("source.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("locator", sa.String(256), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
    )
    op.create_index("ix_source_span_source", "source_span", ["source_id"])

    op.create_table(
        "analysis_run",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("detector_id", sa.String(64), nullable=False),
        sa.Column("detector_version", sa.String(32), nullable=False),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("prompt_hash", sa.String(64), nullable=True),
        sa.Column("inputs", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("outputs_summary", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "reviewer",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("handle", sa.String(64), nullable=False, unique=True),
        sa.Column("verified_identity", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("role", sa.String(32), nullable=False, server_default="reviewer"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "finding",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_span_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("document_span.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_span_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("detector_id", sa.String(64), nullable=False),
        sa.Column("detector_version", sa.String(32), nullable=False),
        sa.Column(
            "confidence_category",
            sa.String(32),
            nullable=False,
            server_default="requires_review",
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="unreviewed"),
        sa.Column("similarity_score", sa.Float(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column(
            "analysis_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analysis_run.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_finding_document_span", "finding", ["document_span_id"])
    op.create_index("ix_finding_status", "finding", ["status"])

    op.create_table(
        "review",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "finding_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("finding.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reviewer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reviewer.id"),
            nullable=False,
        ),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("review")
    op.drop_index("ix_finding_status", table_name="finding")
    op.drop_index("ix_finding_document_span", table_name="finding")
    op.drop_table("finding")
    op.drop_table("reviewer")
    op.drop_table("analysis_run")
    op.drop_index("ix_source_span_source", table_name="source_span")
    op.drop_table("source_span")
    op.drop_table("source")
