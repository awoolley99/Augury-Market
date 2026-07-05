import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.watchlist import Watchlist, WatchlistItem


class WatchlistRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_user(self, user_id: uuid.UUID) -> list[Watchlist]:
        result = await self.session.execute(
            select(Watchlist)
            .where(Watchlist.user_id == user_id)
            .options(selectinload(Watchlist.items))
            .order_by(Watchlist.created_at)
        )
        return list(result.scalars().all())

    async def get_owned(self, watchlist_id: uuid.UUID, user_id: uuid.UUID) -> Watchlist | None:
        result = await self.session.execute(
            select(Watchlist)
            .where(Watchlist.id == watchlist_id, Watchlist.user_id == user_id)
            .options(selectinload(Watchlist.items))
        )
        return result.scalar_one_or_none()

    async def create(self, *, user_id: uuid.UUID, name: str) -> Watchlist:
        watchlist = Watchlist(user_id=user_id, name=name)
        self.session.add(watchlist)
        await self.session.flush()
        return watchlist

    async def delete(self, watchlist: Watchlist) -> None:
        await self.session.delete(watchlist)

    async def add_item(self, watchlist: Watchlist, ticker: str) -> WatchlistItem:
        item = WatchlistItem(watchlist_id=watchlist.id, ticker=ticker)
        self.session.add(item)
        await self.session.flush()
        return item

    async def remove_item(self, item: WatchlistItem) -> None:
        await self.session.delete(item)

    async def get_item(self, item_id: uuid.UUID, watchlist_id: uuid.UUID) -> WatchlistItem | None:
        result = await self.session.execute(
            select(WatchlistItem).where(
                WatchlistItem.id == item_id, WatchlistItem.watchlist_id == watchlist_id
            )
        )
        return result.scalar_one_or_none()
