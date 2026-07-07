"""add ai_summaries table

Revision ID: 0003_ai_summaries
Revises: 0002_evidence_packets
Create Date: 2026-07-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_ai_summaries"
down_revision: Union[str, None] = "0002_evidence_packets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticker", sa.String(length=12), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("why_it_ranked", sa.JSON(), nullable=False),
        sa.Column("primary_risks", sa.JSON(), nullable=False),
        sa.Column("suggested_hold_period", sa.String(length=64), nullable=False),
        sa.Column("catalyst_strength", sa.String(length=16), nullable=False),
        sa.Column("thesis_breakers", sa.JSON(), nullable=False),
        sa.Column("confidence_score_at_generation", sa.Float(), nullable=False),
        sa.Column("recommendation_at_generation", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("ticker", "as_of_date", name="uq_ai_summary_ticker_date"),
    )
    op.create_index("ix_ai_summaries_ticker", "ai_summaries", ["ticker"])
    op.create_index("ix_ai_summaries_as_of_date", "ai_summaries", ["as_of_date"])


def downgrade() -> None:
    op.drop_index("ix_ai_summaries_as_of_date", table_name="ai_summaries")
    op.drop_index("ix_ai_summaries_ticker", table_name="ai_summaries")
    op.drop_table("ai_summaries")
