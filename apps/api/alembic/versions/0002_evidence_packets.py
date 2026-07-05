"""add evidence_packets table

Revision ID: 0002_evidence_packets
Revises: 0001_initial
Create Date: 2026-07-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_evidence_packets"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evidence_packets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticker", sa.String(length=12), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("sector", sa.String(length=64), nullable=False),
        sa.Column("close_price", sa.Float(), nullable=False),
        sa.Column("sma_50", sa.Float(), nullable=True),
        sa.Column("sma_200", sa.Float(), nullable=True),
        sa.Column("rsi_14", sa.Float(), nullable=True),
        sa.Column("macd_histogram", sa.Float(), nullable=True),
        sa.Column("pct_above_sma_200", sa.Float(), nullable=True),
        sa.Column("revenue_growth_yoy", sa.Float(), nullable=False),
        sa.Column("pe_ratio", sa.Float(), nullable=True),
        sa.Column("institutional_ownership_pct", sa.Float(), nullable=False),
        sa.Column("market_cap", sa.Float(), nullable=False),
        sa.Column("avg_news_sentiment", sa.Float(), nullable=False),
        sa.Column("catalyst_count", sa.Integer(), nullable=False),
        sa.Column("news_headlines", sa.JSON(), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("risk_factors", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("ticker", "as_of_date", name="uq_evidence_ticker_date"),
    )
    op.create_index("ix_evidence_packets_ticker", "evidence_packets", ["ticker"])
    op.create_index("ix_evidence_packets_as_of_date", "evidence_packets", ["as_of_date"])


def downgrade() -> None:
    op.drop_index("ix_evidence_packets_as_of_date", table_name="evidence_packets")
    op.drop_index("ix_evidence_packets_ticker", table_name="evidence_packets")
    op.drop_table("evidence_packets")
