import pytest

from app.services.scanner import ScannerService

pytestmark = pytest.mark.asyncio


async def test_scan_single_ticker_creates_evidence_packet(db_session):
    scanner = ScannerService(db_session)
    packet = await scanner.scan_ticker("NVDA")
    await db_session.commit()

    assert packet.ticker == "NVDA"
    assert packet.close_price > 0
    assert 0 <= packet.risk_score <= 100
    assert isinstance(packet.news_headlines, list)


async def test_rescanning_same_day_overwrites_not_duplicates(db_session):
    scanner = ScannerService(db_session)
    first = await scanner.scan_ticker("AAPL")
    await db_session.commit()
    second = await scanner.scan_ticker("AAPL")
    await db_session.commit()

    assert first.id == second.id  # same row, updated in place


async def test_scan_universe_processes_all_tickers(db_session):
    scanner = ScannerService(db_session)
    result = await scanner.scan_universe()

    assert len(result.processed) > 0
    assert len(result.failed) == 0
