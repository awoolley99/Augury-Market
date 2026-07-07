from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_summary import AISummary


class AISummaryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_for_date(self, ticker: str, as_of_date: date) -> AISummary | None:
        result = await self.session.execute(
            select(AISummary).where(
                AISummary.ticker == ticker.upper(),
                AISummary.as_of_date == as_of_date,
            )
        )
        return result.scalar_one_or_none()

    async def upsert(self, data: dict) -> AISummary:
        bind = self.session.get_bind()
        if bind.dialect.name == "postgresql":
            stmt = pg_insert(AISummary).values(**data)
            update_cols = {
                k: getattr(stmt.excluded, k)
                for k in data
                if k not in ("id", "ticker", "as_of_date")
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=["ticker", "as_of_date"], set_=update_cols
            ).returning(AISummary)
            result = await self.session.execute(stmt)
            return result.scalar_one()

        existing = await self.get_for_date(data["ticker"], data["as_of_date"])
        if existing:
            for k, v in data.items():
                if k not in ("id", "ticker", "as_of_date"):
                    setattr(existing, k, v)
            await self.session.flush()
            return existing

        summary = AISummary(**data)
        self.session.add(summary)
        await self.session.flush()
        return summary
