import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.risk_profile import RiskProfile


class RiskProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_for_user(self, user_id: uuid.UUID) -> RiskProfile | None:
        result = await self.session.execute(
            select(RiskProfile).where(RiskProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, user_id: uuid.UUID, answers: dict, risk_score: float, risk_level: str) -> RiskProfile:
        data = dict(user_id=user_id, answers=answers, risk_score=risk_score, risk_level=risk_level)

        bind = self.session.get_bind()
        if bind.dialect.name == "postgresql":
            stmt = pg_insert(RiskProfile).values(**data)
            stmt = stmt.on_conflict_do_update(
                index_elements=["user_id"],
                set_={"answers": stmt.excluded.answers, "risk_score": stmt.excluded.risk_score,
                      "risk_level": stmt.excluded.risk_level},
            ).returning(RiskProfile)
            result = await self.session.execute(stmt)
            return result.scalar_one()

        existing = await self.get_for_user(user_id)
        if existing:
            existing.answers = answers
            existing.risk_score = risk_score
            existing.risk_level = risk_level
            await self.session.flush()
            await self.session.refresh(existing)
            return existing

        profile = RiskProfile(**data)
        self.session.add(profile)
        await self.session.flush()
        return profile
