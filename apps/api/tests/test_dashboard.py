import pytest

from app.services.dashboard import DashboardService
from app.services.scanner import ScannerService
from app.services.watchlist_service import WatchlistService

pytestmark = pytest.mark.asyncio


async def test_briefing_before_any_scan_returns_neutral_defaults(db_session):
    service = DashboardService(db_session)
    briefing = await service.get_briefing(user_id="00000000-0000-0000-0000-000000000000")

    assert briefing.market_overview.tickers_scanned == 0
    assert briefing.market_overview.market_health_label == "Neutral"
    assert briefing.top_opportunities == []
    assert briefing.recent_reports == []


async def test_market_overview_reflects_scanned_universe(db_session):
    scanner = ScannerService(db_session)
    await scanner.scan_universe()

    service = DashboardService(db_session)
    briefing = await service.get_briefing(user_id="00000000-0000-0000-0000-000000000000")

    assert briefing.market_overview.tickers_scanned > 0
    assert 0 <= briefing.market_overview.market_health_score <= 100
    assert 0 <= briefing.market_overview.fear_greed_score <= 100
    assert briefing.market_overview.top_sector is not None


async def test_top_opportunities_are_sorted_descending_by_score(db_session):
    scanner = ScannerService(db_session)
    await scanner.scan_universe()

    service = DashboardService(db_session)
    briefing = await service.get_briefing(user_id="00000000-0000-0000-0000-000000000000")

    scores = [o.confidence_score for o in briefing.top_opportunities]
    assert scores == sorted(scores, reverse=True)
    assert len(briefing.top_opportunities) <= 5


async def test_watchlist_summary_includes_users_tickers(db_session):
    from app.repositories.user_repository import UserRepository
    from app.core.security import hash_password

    user_repo = UserRepository(db_session)
    user = await user_repo.create(
        email="briefing@example.com", hashed_password=hash_password("pw"), full_name=None
    )
    await db_session.commit()

    scanner = ScannerService(db_session)
    await scanner.scan_ticker("NVDA")
    await db_session.commit()

    watchlist_service = WatchlistService(db_session)
    watchlist = await watchlist_service.create_watchlist(user.id, "AI Leaders")
    await watchlist_service.add_ticker(watchlist.id, user.id, "NVDA")

    service = DashboardService(db_session)
    briefing = await service.get_briefing(user_id=user.id)

    tickers = {item.ticker for item in briefing.watchlist_summary}
    assert "NVDA" in tickers
    nvda_item = next(item for item in briefing.watchlist_summary if item.ticker == "NVDA")
    assert nvda_item.confidence_score is not None
    assert nvda_item.score_change is None  # no prior day's data yet


async def test_watchlist_summary_ticker_without_scan_has_null_score(db_session):
    from app.repositories.user_repository import UserRepository
    from app.core.security import hash_password

    user_repo = UserRepository(db_session)
    user = await user_repo.create(
        email="briefing2@example.com", hashed_password=hash_password("pw"), full_name=None
    )
    await db_session.commit()

    watchlist_service = WatchlistService(db_session)
    watchlist = await watchlist_service.create_watchlist(user.id, "Unscanned")
    await watchlist_service.add_ticker(watchlist.id, user.id, "ZZZZ")

    service = DashboardService(db_session)
    briefing = await service.get_briefing(user_id=user.id)

    item = next(i for i in briefing.watchlist_summary if i.ticker == "ZZZZ")
    assert item.confidence_score is None
    assert item.recommendation is None


async def test_recent_reports_reflects_generated_summaries(db_session):
    from app.services.ai_summary_service import AISummaryService

    scanner = ScannerService(db_session)
    packet = await scanner.scan_ticker("NVDA")
    await db_session.commit()

    summary_service = AISummaryService(db_session)
    await summary_service.get_or_generate(packet)

    service = DashboardService(db_session)
    briefing = await service.get_briefing(user_id="00000000-0000-0000-0000-000000000000")

    assert len(briefing.recent_reports) == 1
    assert briefing.recent_reports[0].ticker == "NVDA"


async def test_score_change_computed_when_prior_day_exists(db_session):
    from datetime import date, timedelta
    from app.repositories.user_repository import UserRepository
    from app.core.security import hash_password

    user_repo = UserRepository(db_session)
    user = await user_repo.create(
        email="briefing3@example.com", hashed_password=hash_password("pw"), full_name=None
    )
    await db_session.commit()

    scanner = ScannerService(db_session)
    yesterday = date.today() - timedelta(days=1)
    await scanner.scan_ticker("NVDA", as_of=yesterday)
    await scanner.scan_ticker("NVDA", as_of=date.today())
    await db_session.commit()

    watchlist_service = WatchlistService(db_session)
    watchlist = await watchlist_service.create_watchlist(user.id, "AI Leaders")
    await watchlist_service.add_ticker(watchlist.id, user.id, "NVDA")

    service = DashboardService(db_session)
    briefing = await service.get_briefing(user_id=user.id)

    nvda_item = next(item for item in briefing.watchlist_summary if item.ticker == "NVDA")
    assert nvda_item.score_change is not None
    assert nvda_item.score_change == 0.0  # same synthetic evidence both days -> same score
