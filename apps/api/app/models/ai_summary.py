import uuid
from datetime import date, datetime

from sqlalchemy import JSON, DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.session import Base
from app.db.types import GUID


class AISummary(Base):
    __tablename__ = "ai_summaries"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)

    ticker: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    as_of_date: Mapped[date] = mapped_column(nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)  # "stub" | "anthropic"

    headline: Mapped[str] = mapped_column(Text, nullable=False)
    why_it_ranked: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    primary_risks: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    suggested_hold_period: Mapped[str] = mapped_column(String(64), nullable=False)
    catalyst_strength: Mapped[str] = mapped_column(String(16), nullable=False)
    thesis_breakers: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # The confidence score/recommendation this summary was generated against,
    # so a UI can flag a stale summary if the score has since changed.
    confidence_score_at_generation: Mapped[float] = mapped_column(nullable=False)
    recommendation_at_generation: Mapped[str] = mapped_column(String(32), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("ticker", "as_of_date", name="uq_ai_summary_ticker_date"),
    )
