"""
AI Summary Engine orchestration (Module 8).

Generates a summary from the latest evidence + confidence score, caching it
per (ticker, date) so a real LLM provider isn't called more than once a day
per ticker. Force-regenerate bypasses the cache (e.g. if evidence changed
intraday from a re-scan).
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_summary import AISummary
from app.models.evidence import EvidencePacket
from app.repositories.ai_summary_repository import AISummaryRepository
from app.services.ai_summary.base import AISummaryProvider
from app.services.ai_summary.factory import get_ai_summary_provider
from app.services.confidence import compute_confidence


class AISummaryService:
    def __init__(self, session: AsyncSession, provider: AISummaryProvider | None = None):
        self.session = session
        self.repo = AISummaryRepository(session)
        self.provider = provider or get_ai_summary_provider()

    async def get_or_generate(self, packet: EvidencePacket, force: bool = False) -> AISummary:
        as_of = packet.as_of_date

        if not force:
            existing = await self.repo.get_for_date(packet.ticker, as_of)
            if existing:
                return existing

        confidence = compute_confidence(packet)
        result = await self.provider.generate_summary(packet, confidence)

        data = dict(
            ticker=packet.ticker,
            as_of_date=as_of,
            provider=type(self.provider).__name__,
            headline=result.headline,
            why_it_ranked=result.why_it_ranked,
            primary_risks=result.primary_risks,
            suggested_hold_period=result.suggested_hold_period,
            catalyst_strength=result.catalyst_strength,
            thesis_breakers=result.thesis_breakers,
            confidence_score_at_generation=confidence.total_score,
            recommendation_at_generation=confidence.recommendation,
        )
        summary = await self.repo.upsert(data)
        await self.session.commit()
        return summary
