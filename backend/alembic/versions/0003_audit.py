"""audit_event table with append-only enforcement trigger

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-30

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_event",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("actor", sa.String(128), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_audit_event_entity", "audit_event", ["entity_type", "entity_id"])
    op.create_index("ix_audit_event_occurred_at", "audit_event", ["occurred_at"])

    # Append-only enforcement: deny UPDATE and DELETE on audit_event.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit_event_no_modify() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit_event is append-only; % not allowed', TG_OP;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_event_block_update
        BEFORE UPDATE ON audit_event
        FOR EACH ROW EXECUTE FUNCTION audit_event_no_modify();
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_event_block_delete
        BEFORE DELETE ON audit_event
        FOR EACH ROW EXECUTE FUNCTION audit_event_no_modify();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_event_block_update ON audit_event")
    op.execute("DROP TRIGGER IF EXISTS audit_event_block_delete ON audit_event")
    op.execute("DROP FUNCTION IF EXISTS audit_event_no_modify()")
    op.drop_index("ix_audit_event_occurred_at", table_name="audit_event")
    op.drop_index("ix_audit_event_entity", table_name="audit_event")
    op.drop_table("audit_event")
