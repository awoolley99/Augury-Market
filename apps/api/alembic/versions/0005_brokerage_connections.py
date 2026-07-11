"""add brokerage_connections table

Revision ID: 0005_brokerage_connections
Revises: 0004_risk_profiles
Create Date: 2026-07-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_brokerage_connections"
down_revision: Union[str, None] = "0004_risk_profiles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "brokerage_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("external_user_id", sa.String(length=255), nullable=False),
        sa.Column("encrypted_user_secret", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_brokerage_connection_user_id"),
    )
    op.create_index("ix_brokerage_connections_user_id", "brokerage_connections", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_brokerage_connections_user_id", table_name="brokerage_connections")
    op.drop_table("brokerage_connections")
