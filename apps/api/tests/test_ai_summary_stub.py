from datetime import date

import pytest

from app.models.evidence import EvidencePacket
from app.services.ai_summary.stub_provider import StubAISummaryProvider
from app.services.confidence import compute_confidence

pytestmark = pytest.mark.asyncio


def _packet(**overrides) -> EvidencePacket:
    defaults = dict(
        ticker="NVDA",
        as_of_date=date.today(),
        sector="Technology",
        close_price=401.79,
        sma_50=380.0,
        sma_200=350.0,
        rsi_14=61.0,
        macd_histogram=1.2,
        pct_above_sma_200=0.15,
        revenue_growth_yoy=0.40,
        pe_ratio=23.5,
        institutional_ownership_pct=0.79,
        market_cap=1.2e12,
        avg_news_sentiment=0.5,
        catalyst_count=5,
        news_headlines=["NVDA reports quarterly revenue above analyst estimates"],
        risk_score=20,
        risk_factors=[],
    )
    defaults.update(overrides)
    return EvidencePacket(**defaults)


async def test_stub_summary_headline_reflects_recommendation_and_score():
    packet = _packet()
    confidence = compute_confidence(packet)
    provider = StubAISummaryProvider()

    summary = await provider.generate_summary(packet, confidence)

    assert confidence.recommendation in summary.headline
    assert packet.ticker in summary.headline
    assert f"{confidence.total_score:.1f}" in summary.headline


async def test_stub_summary_reuses_confidence_strengths_and_risks():
    packet = _packet()
    confidence = compute_confidence(packet)
    provider = StubAISummaryProvider()

    summary = await provider.generate_summary(packet, confidence)

    assert summary.why_it_ranked == confidence.strengths
    assert summary.primary_risks == confidence.risks


async def test_catalyst_strength_scales_with_catalyst_count():
    provider = StubAISummaryProvider()

    high = _packet(catalyst_count=4)
    low = _packet(catalyst_count=0)

    high_summary = await provider.generate_summary(high, compute_confidence(high))
    low_summary = await provider.generate_summary(low, compute_confidence(low))

    assert high_summary.catalyst_strength == "High"
    assert low_summary.catalyst_strength == "Low"


async def test_suggested_hold_period_reflects_recommendation():
    provider = StubAISummaryProvider()

    strong = _packet(
        revenue_growth_yoy=0.44, rsi_14=59, macd_histogram=2.8, pct_above_sma_200=0.24,
        pe_ratio=10, institutional_ownership_pct=0.90, avg_news_sentiment=0.9,
        catalyst_count=5, risk_score=5,
    )
    weak = _packet(
        revenue_growth_yoy=-0.08, rsi_14=35, macd_histogram=-2.5, pct_above_sma_200=-0.12,
        pe_ratio=58, institutional_ownership_pct=0.38, avg_news_sentiment=-0.6,
        catalyst_count=0, risk_score=90,
    )

    strong_summary = await provider.generate_summary(strong, compute_confidence(strong))
    weak_summary = await provider.generate_summary(weak, compute_confidence(weak))

    assert strong_summary.suggested_hold_period == "12-24 Months"
    assert weak_summary.suggested_hold_period == "Not Recommended"


async def test_thesis_breakers_are_non_empty():
    packet = _packet()
    confidence = compute_confidence(packet)
    provider = StubAISummaryProvider()

    summary = await provider.generate_summary(packet, confidence)
    assert len(summary.thesis_breakers) > 0
