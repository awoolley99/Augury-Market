import pytest

from app.services.ai_summary_service import AISummaryService
from app.services.scanner import ScannerService

pytestmark = pytest.mark.asyncio


async def test_generates_and_caches_summary(db_session):
    scanner = ScannerService(db_session)
    packet = await scanner.scan_ticker("NVDA")
    await db_session.commit()

    service = AISummaryService(db_session)
    first = await service.get_or_generate(packet)
    second = await service.get_or_generate(packet)

    assert first.id == second.id  # served from cache, not regenerated
    assert first.headline == second.headline


async def test_force_regenerates_even_if_cached(db_session):
    scanner = ScannerService(db_session)
    packet = await scanner.scan_ticker("AAPL")
    await db_session.commit()

    service = AISummaryService(db_session)
    first = await service.get_or_generate(packet)
    second = await service.get_or_generate(packet, force=True)

    assert first.id == second.id  # same row, updated in place
    assert second.provider == "StubAISummaryProvider"


async def test_summary_records_confidence_score_it_was_generated_against(db_session):
    scanner = ScannerService(db_session)
    packet = await scanner.scan_ticker("MSFT")
    await db_session.commit()

    service = AISummaryService(db_session)
    summary = await service.get_or_generate(packet)

    assert summary.confidence_score_at_generation is not None
    assert summary.recommendation_at_generation in {
        "Strong Buy Candidate", "Buy Candidate", "Watch / Hold", "Avoid",
    }
