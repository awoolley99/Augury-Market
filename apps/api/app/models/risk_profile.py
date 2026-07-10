import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.session import Base
from app.db.types import GUID


class RiskProfile(Base):
    """
    One per user. Retaking the quiz overwrites the existing row rather than
    keeping history -- only the current risk tolerance matters for ranking
    Top Opportunities.
    """

    __tablename__ = "risk_profiles"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    answers: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"experience": "C", ...}
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0-1.0
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
