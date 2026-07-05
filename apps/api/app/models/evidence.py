"""
Evidence packet — the structured output of the Stock Scanner Engine
(Module 6), and the input to the Confidence Score Engine (Module 7,
Milestone 3). One row per (ticker, as_of_date); rescanning the same day
overwrites that day's packet rather than duplicating it.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.session import Base
from app.db.types import GUID


class EvidencePacket(Base):
    __tablename__ = "evidence_packets"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)

    ticker: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    as_of_date: Mapped[date] = mapped_column(nullable=False, index=True)
    sector: Mapped[str] = mapped_column(String(64), nullable=False)

    # Raw indicators (Module 6 output)
    close_price: Mapped[float] = mapped_column(Float, nullable=False)
    sma_50: Mapped[float | None] = mapped_column(Float, nullable=True)
    sma_200: Mapped[float | None] = mapped_column(Float, nullable=True)
    rsi_14: Mapped[float | None] = mapped_column(Float, nullable=True)
    macd_histogram: Mapped[float | None] = mapped_column(Float, nullable=True)
    pct_above_sma_200: Mapped[float | None] = mapped_column(Float, nullable=True)

    revenue_growth_yoy: Mapped[float] = mapped_column(Float, nullable=False)
    pe_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    institutional_ownership_pct: Mapped[float] = mapped_column(Float, nullable=False)
    market_cap: Mapped[float] = mapped_column(Float, nullable=False)

    avg_news_sentiment: Mapped[float] = mapped_column(Float, nullable=False)
    catalyst_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    news_headlines: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_factors: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("ticker", "as_of_date", name="uq_evidence_ticker_date"),
    )
