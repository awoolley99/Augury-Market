import pytest

from app.services.dashboard import DashboardService
from app.services.risk_quiz import QUIZ_QUESTIONS, score_quiz
from app.services.scanner import ScannerService

pytestmark = pytest.mark.asyncio


async def _register_and_login(client, email):
    await client.post("/api/v1/auth/register", json={"email": email, "password": "supersecret1"})
    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "supersecret1"}
    )
    return {"Authorization": f"Bearer {login_resp.json()['access_token']}"}


async def test_top_opportunities_ranking_differs_between_conservative_and_aggressive(client):
    # A single shared universe scan -- both users see the same underlying data.
    headers_conservative = await _register_and_login(client, "conservative@example.com")
    await client.post("/api/v1/scanner/run", headers=headers_conservative)

    headers_aggressive = await _register_and_login(client, "aggressive@example.com")

    conservative_answers = {q.id: "A" for q in QUIZ_QUESTIONS}
    await client.post(
        "/api/v1/quiz/submit", json={"answers": conservative_answers}, headers=headers_conservative
    )

    aggressive_answers = {q.id: q.options[-1].letter for q in QUIZ_QUESTIONS}
    await client.post(
        "/api/v1/quiz/submit", json={"answers": aggressive_answers}, headers=headers_aggressive
    )

    conservative_briefing = (
        await client.get("/api/v1/dashboard/briefing", headers=headers_conservative)
    ).json()
    aggressive_briefing = (
        await client.get("/api/v1/dashboard/briefing", headers=headers_aggressive)
    ).json()

    conservative_order = [o["ticker"] for o in conservative_briefing["top_opportunities"]]
    aggressive_order = [o["ticker"] for o in aggressive_briefing["top_opportunities"]]

    # The two risk profiles must produce a different ranking order given a
    # universe with varying risk_scores per ticker -- if they're identical,
    # the personalization isn't actually doing anything.
    assert conservative_order != aggressive_order


async def test_displayed_confidence_score_is_identical_regardless_of_risk_profile(client):
    """
    Personalization must only change ORDERING, never the underlying
    confidence score shown for a given ticker -- that score is the single
    official Module 7 number (ADR 0004), the same for every user.
    """
    headers_a = await _register_and_login(client, "usera@example.com")
    await client.post("/api/v1/scanner/run", headers=headers_a)
    headers_b = await _register_and_login(client, "userb@example.com")

    await client.post(
        "/api/v1/quiz/submit",
        json={"answers": {q.id: "A" for q in QUIZ_QUESTIONS}},
        headers=headers_a,
    )
    await client.post(
        "/api/v1/quiz/submit",
        json={"answers": {q.id: q.options[-1].letter for q in QUIZ_QUESTIONS}},
        headers=headers_b,
    )

    briefing_a = (await client.get("/api/v1/dashboard/briefing", headers=headers_a)).json()
    briefing_b = (await client.get("/api/v1/dashboard/briefing", headers=headers_b)).json()

    scores_a = {o["ticker"]: o["confidence_score"] for o in briefing_a["top_opportunities"]}
    scores_b = {o["ticker"]: o["confidence_score"] for o in briefing_b["top_opportunities"]}

    shared_tickers = set(scores_a) & set(scores_b)
    assert shared_tickers, "expected at least some overlap between the two rankings"
    for ticker in shared_tickers:
        assert scores_a[ticker] == scores_b[ticker]


async def test_no_quiz_taken_uses_moderate_default(db_session):
    scanner = ScannerService(db_session)
    await scanner.scan_universe()

    service = DashboardService(db_session)
    briefing_default = await service.get_briefing(user_id="00000000-0000-0000-0000-000000000000")

    # A user with a "Moderate" profile should rank identically to no profile
    # at all, since Moderate is the documented default.
    conservative_scored = await service._scored_universe()
    moderate_ranked = service._top_opportunities(conservative_scored, risk_level="Moderate")
    default_ranked = service._top_opportunities(conservative_scored)  # no risk_level passed

    assert [o.ticker for o in moderate_ranked] == [o.ticker for o in default_ranked]
    assert [o.ticker for o in default_ranked] == [
        o.ticker for o in briefing_default.top_opportunities
    ]


async def test_conservative_ranking_penalizes_high_risk_more_than_aggressive(db_session):
    """
    Direct unit-level check of the ranking math, independent of the API
    layer: given the same scored universe, a Conservative profile's
    personalized_rank_score for a high-risk ticker should be lower relative
    to its own confidence_score than an Aggressive profile's is.
    """
    scanner = ScannerService(db_session)
    await scanner.scan_universe()

    service = DashboardService(db_session)
    scored = await service._scored_universe()

    # Find a ticker with a meaningfully high risk_score to check the math against.
    packet, confidence = max(scored, key=lambda pc: pc[0].risk_score)

    conservative_ranked = {
        o.ticker: o for o in service._top_opportunities(scored, risk_level="Conservative", limit=len(scored))
    }
    aggressive_ranked = {
        o.ticker: o for o in service._top_opportunities(scored, risk_level="Aggressive", limit=len(scored))
    }

    conservative_gap = confidence.total_score - conservative_ranked[packet.ticker].personalized_rank_score
    aggressive_gap = confidence.total_score - aggressive_ranked[packet.ticker].personalized_rank_score

    assert conservative_gap > aggressive_gap
    assert aggressive_gap == 0.0  # Aggressive has a 0.0 risk aversion weight -- no penalty at all
