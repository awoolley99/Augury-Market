import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.watchlist import Watchlist, WatchlistItem
from app.repositories.watchlist_repository import WatchlistRepository


class WatchlistError(Exception):
    pass


class WatchlistNotFoundError(WatchlistError):
    pass


class WatchlistService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = WatchlistRepository(session)

    async def list_watchlists(self, user_id: uuid.UUID) -> list[Watchlist]:
        return await self.repo.list_for_user(user_id)

    async def create_watchlist(self, user_id: uuid.UUID, name: str) -> Watchlist:
        try:
            watchlist = await self.repo.create(user_id=user_id, name=name)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise WatchlistError(f"A watchlist named '{name}' already exists") from exc
        # Re-fetch with items eagerly loaded so the response model can
        # serialize `.items` without triggering an async lazy-load.
        return await self.repo.get_owned(watchlist.id, user_id)

    async def delete_watchlist(self, watchlist_id: uuid.UUID, user_id: uuid.UUID) -> None:
        watchlist = await self.repo.get_owned(watchlist_id, user_id)
        if not watchlist:
            raise WatchlistNotFoundError("Watchlist not found")
        await self.repo.delete(watchlist)
        await self.session.commit()

    async def add_ticker(
        self, watchlist_id: uuid.UUID, user_id: uuid.UUID, ticker: str
    ) -> WatchlistItem:
        watchlist = await self.repo.get_owned(watchlist_id, user_id)
        if not watchlist:
            raise WatchlistNotFoundError("Watchlist not found")
        try:
            item = await self.repo.add_item(watchlist, ticker)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise WatchlistError(f"{ticker} is already on this watchlist") from exc
        return item

    async def remove_ticker(
        self, watchlist_id: uuid.UUID, user_id: uuid.UUID, item_id: uuid.UUID
    ) -> None:
        watchlist = await self.repo.get_owned(watchlist_id, user_id)
        if not watchlist:
            raise WatchlistNotFoundError("Watchlist not found")
        item = await self.repo.get_item(item_id, watchlist_id)
        if not item:
            raise WatchlistNotFoundError("Ticker not found on this watchlist")
        await self.repo.remove_item(item)
        await self.session.commit()
