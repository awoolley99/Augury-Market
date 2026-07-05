import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evidence import EvidencePacket


class EvidenceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, packet_data: dict) -> EvidencePacket:
        """Insert a new evidence packet, or overwrite the existing one for
        this (ticker, as_of_date). Uses ON CONFLICT on Postgres; falls back
        to a manual get-then-update for other dialects (e.g. SQLite tests)."""
        bind = self.session.get_bind()
        if bind.dialect.name == "postgresql":
            stmt = pg_insert(EvidencePacket).values(**packet_data)
            update_cols = {
                k: getattr(stmt.excluded, k)
                for k in packet_data
                if k not in ("id", "ticker", "as_of_date")
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=["ticker", "as_of_date"], set_=update_cols
            ).returning(EvidencePacket)
            result = await self.session.execute(stmt)
            return result.scalar_one()

        existing = await self.get_for_date(packet_data["ticker"], packet_data["as_of_date"])
        if existing:
            for k, v in packet_data.items():
                if k not in ("id", "ticker", "as_of_date"):
                    setattr(existing, k, v)
            await self.session.flush()
            return existing

        packet = EvidencePacket(**packet_data)
        self.session.add(packet)
        await self.session.flush()
        return packet

    async def get_latest(self, ticker: str) -> EvidencePacket | None:
        result = await self.session.execute(
            select(EvidencePacket)
            .where(EvidencePacket.ticker == ticker.upper())
            .order_by(EvidencePacket.as_of_date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_for_date(self, ticker: str, as_of_date: date) -> EvidencePacket | None:
        result = await self.session.execute(
            select(EvidencePacket).where(
                EvidencePacket.ticker == ticker.upper(),
                EvidencePacket.as_of_date == as_of_date,
            )
        )
        return result.scalar_one_or_none()

    async def list_latest_for_tickers(self, tickers: list[str]) -> list[EvidencePacket]:
        if not tickers:
            return []
        upper_tickers = [t.upper() for t in tickers]
        # One latest row per ticker: simplest portable approach is per-ticker
        # queries. Universe sizes here (dozens, not thousands) make this fine;
        # a windowed query would be the move once the universe is large.
        packets = []
        for ticker in upper_tickers:
            packet = await self.get_latest(ticker)
            if packet:
                packets.append(packet)
        return packets

    async def list_all_latest(self) -> list[EvidencePacket]:
        result = await self.session.execute(
            select(EvidencePacket).order_by(EvidencePacket.as_of_date.desc())
        )
        seen: set[str] = set()
        latest: list[EvidencePacket] = []
        for packet in result.scalars().all():
            if packet.ticker not in seen:
                seen.add(packet.ticker)
                latest.append(packet)
        return latest
