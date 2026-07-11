"""
Brokerage account linking orchestration (Robinhood via SnapTrade, ADR 0006).

Three operations: connect (register + get a portal URL), get_portfolio
(read-only holdings/balance), disconnect (revoke everything).
"""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.crypto import decrypt_secret, encrypt_secret
from app.models.brokerage_connection import BrokerageConnection
from app.repositories.brokerage_connection_repository import BrokerageConnectionRepository
from app.services.brokerage.base import BrokerageProvider, BrokeragePortfolio
from app.services.brokerage.factory import get_brokerage_provider


class BrokerageError(Exception):
    pass


class BrokerageNotConnectedError(BrokerageError):
    pass


class BrokerageService:
    def __init__(self, session: AsyncSession, provider: BrokerageProvider | None = None):
        self.session = session
        self.repo = BrokerageConnectionRepository(session)
        self.provider = provider or get_brokerage_provider()

    async def get_connection(self, user_id: uuid.UUID) -> BrokerageConnection | None:
        return await self.repo.get_for_user(user_id)

    async def start_connection(self, user_id: uuid.UUID) -> str:
        """
        Ensures a provider-side user exists for this app user, then returns
        the Connection Portal URL they should visit to log into their
        actual brokerage. Idempotent: re-calling this for an already-
        registered user just returns a fresh portal URL rather than
        re-registering (SnapTrade users are meant to be one-to-one with
        app users, created once).
        """
        existing = await self.repo.get_for_user(user_id)

        if existing:
            user_secret = decrypt_secret(existing.encrypted_user_secret)
            return await self.provider.get_connection_portal_url(
                existing.external_user_id, user_secret
            )

        external_user_id = str(user_id)
        user_secret = await self.provider.register_user(external_user_id)

        await self.repo.create(
            user_id=user_id,
            provider=settings.BROKERAGE_PROVIDER,
            external_user_id=external_user_id,
            encrypted_user_secret=encrypt_secret(user_secret),
        )
        await self.session.commit()

        return await self.provider.get_connection_portal_url(external_user_id, user_secret)

    async def get_portfolio(self, user_id: uuid.UUID) -> BrokeragePortfolio:
        connection = await self.repo.get_for_user(user_id)
        if not connection:
            raise BrokerageNotConnectedError(
                "No brokerage connection started yet. Call start_connection first."
            )

        user_secret = decrypt_secret(connection.encrypted_user_secret)
        portfolio = await self.provider.get_portfolio(connection.external_user_id, user_secret)

        # Opportunistic status update: we don't get a synchronous callback
        # when the user finishes the Connection Portal flow, so "connected"
        # is inferred from actually seeing a linked account back.
        if portfolio.connected_accounts and connection.status != "connected":
            await self.repo.mark_connected(connection)
            await self.session.commit()

        return portfolio

    async def disconnect(self, user_id: uuid.UUID) -> None:
        connection = await self.repo.get_for_user(user_id)
        if not connection:
            raise BrokerageNotConnectedError("No brokerage connection to disconnect.")

        user_secret = decrypt_secret(connection.encrypted_user_secret)
        await self.provider.disconnect_user(connection.external_user_id, user_secret)
        await self.repo.delete(connection)
        await self.session.commit()
