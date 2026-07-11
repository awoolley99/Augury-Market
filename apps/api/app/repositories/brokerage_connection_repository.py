import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brokerage_connection import BrokerageConnection


class BrokerageConnectionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_for_user(self, user_id: uuid.UUID) -> BrokerageConnection | None:
        result = await self.session.execute(
            select(BrokerageConnection).where(BrokerageConnection.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self, *, user_id: uuid.UUID, provider: str, external_user_id: str, encrypted_user_secret: str
    ) -> BrokerageConnection:
        connection = BrokerageConnection(
            user_id=user_id,
            provider=provider,
            external_user_id=external_user_id,
            encrypted_user_secret=encrypted_user_secret,
            status="pending",
        )
        self.session.add(connection)
        await self.session.flush()
        return connection

    async def mark_connected(self, connection: BrokerageConnection) -> None:
        connection.status = "connected"
        await self.session.flush()

    async def delete(self, connection: BrokerageConnection) -> None:
        await self.session.delete(connection)
