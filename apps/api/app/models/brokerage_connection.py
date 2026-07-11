import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.session import Base
from app.db.types import GUID


class BrokerageConnection(Base):
    """
    One row per user. `external_user_id` and `encrypted_user_secret` are
    SnapTrade's identifiers for that user within our SnapTrade API key --
    NOT the user's brokerage login. The user's actual Robinhood (or other
    brokerage) credentials are entered directly on SnapTrade's hosted
    Connection Portal and never touch our servers.

    `encrypted_user_secret` is encrypted at rest (app/core/crypto.py) since
    it functions as a per-user API key that authorizes real account access.
    """

    __tablename__ = "brokerage_connections"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    provider: Mapped[str] = mapped_column(String(32), nullable=False)  # "stub" | "snaptrade"
    external_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_user_secret: Mapped[str] = mapped_column(Text, nullable=False)

    # "pending" until the user completes the hosted Connection Portal flow
    # and links at least one real brokerage account; "connected" after.
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
