from datetime import date

from app.models.evidence import EvidencePacket
from app.services.confidence import compute_confidence


def _packet(**overrides) -> EvidencePacket:
    defaults = dict(
        ticker="TEST",
        as_of_date=date.today(),
        sector="Technology",
        close_price=100.0,
        sma_50=95.0,
        sma_200=90.0,
        rsi_14=55.0,
        macd_histogram=0.5,
        pct_above_sma_200=0.05,
        revenue_growth_yoy=0.15,
        pe_ratio=25.0,
        institutional_ownership_pct=0.6,
        market_cap=5e11,
        avg_news_sentiment=0.1,
        catalyst_count=1,
        news_headlines=[],
        risk_score=40,
        risk_factors=[],
    )
    defaults.update(overrides)
    return EvidencePacket(**defaults)


def test_strong_evidence_produces_strong_buy():
    packet = _packet(
        revenue_growth_yoy=0.44,
        rsi_14=59,
        macd_histogram=2.8,
        pct_above_sma_200=0.24,
        pe_ratio=10,
        institutional_ownership_pct=0.90,
        avg_news_sentiment=0.9,
        catalyst_count=5,
        risk_score=5,
    )
    result = compute_confidence(packet)
    assert result.total_score >= 9.0
    assert result.recommendation == "Strong Buy Candidate"
    assert len(result.strengths) > 0


def test_weak_evidence_produces_avoid():
    packet = _packet(
        revenue_growth_yoy=-0.08,
        rsi_14=35,
        macd_histogram=-2.5,
        pct_above_sma_200=-0.12,
        pe_ratio=58,
        institutional_ownership_pct=0.38,
        avg_news_sentiment=-0.6,
        catalyst_count=0,
        risk_score=90,
        risk_factors=["Litigation filed against the company"],
    )
    result = compute_confidence(packet)
    assert result.total_score < 7.0
    assert result.recommendation == "Avoid"
    assert len(result.risks) > 0


def test_good_but_not_great_evidence_lands_in_watch_hold_band():
    # Hand-computed to land at ~7.45/10: clearly good evidence, but not
    # good enough on every dimension to clear the 8.0 Buy Candidate bar.
    packet = _packet(
        revenue_growth_yoy=0.35,
        rsi_14=57,
        macd_histogram=1.8,
        pct_above_sma_200=0.15,
        pe_ratio=15,
        institutional_ownership_pct=0.75,
        avg_news_sentiment=0.5,
        catalyst_count=3,
        risk_score=25,
    )
    result = compute_confidence(packet)
    assert 7.0 <= result.total_score < 8.0
    assert result.recommendation == "Watch / Hold"


def test_purely_neutral_evidence_scores_low_by_design():
    """
    This isn't a bug: with every dimension sitting at its range midpoint
    (RSI 50, MACD 0, sentiment 0, etc.), the raw score lands around 45-50/100
    -> ~4.5-5.0/10, which is 'Avoid'. The confidence engine is a screener,
    not a grader on a curve -- only evidence that's genuinely good-to-great
    clears the 7.0 bar. A stock with nothing going for it and nothing wrong
    with it should not be flagged as worth watching.
    """
    packet = _packet(
        revenue_growth_yoy=0.175,  # midpoint of stub provider's range
        rsi_14=50,
        macd_histogram=0.0,
        pct_above_sma_200=0.05,
        pe_ratio=34,  # roughly midpoint of stub provider's 8-60 range
        institutional_ownership_pct=0.635,  # midpoint of stub provider's range
        avg_news_sentiment=0.0,
        catalyst_count=1,
        risk_score=50,
    )
    result = compute_confidence(packet)
    assert result.total_score < 7.0
    assert result.recommendation == "Avoid"


def test_score_is_deterministic():
    packet = _packet()
    first = compute_confidence(packet)
    second = compute_confidence(packet)
    assert first.total_score == second.total_score
    assert first.recommendation == second.recommendation


def test_score_bounded_zero_to_ten():
    extreme_bad = _packet(
        revenue_growth_yoy=-1.0, rsi_14=0, macd_histogram=-100,
        pct_above_sma_200=-1.0, pe_ratio=1000, institutional_ownership_pct=0.0,
        avg_news_sentiment=-1.0, catalyst_count=0, risk_score=100,
    )
    extreme_good = _packet(
        revenue_growth_yoy=5.0, rsi_14=60, macd_histogram=100,
        pct_above_sma_200=5.0, pe_ratio=1, institutional_ownership_pct=1.0,
        avg_news_sentiment=1.0, catalyst_count=20, risk_score=0,
    )
    assert 0 <= compute_confidence(extreme_bad).total_score <= 10
    assert 0 <= compute_confidence(extreme_good).total_score <= 10


def test_missing_pe_ratio_scores_neutral_not_penalized():
    with_pe = _packet(pe_ratio=25.0)
    without_pe = _packet(pe_ratio=None)
    result_with = compute_confidence(with_pe)
    result_without = compute_confidence(without_pe)
    valuation_without = next(d for d in result_without.dimensions if d.name == "valuation")
    assert valuation_without.score == 50.0
    # Without P/E shouldn't be catastrophically worse than a reasonable P/E
    assert abs(result_with.total_score - result_without.total_score) < 2.0


def test_dimension_weights_sum_to_100_before_risk_adjustment():
    packet = _packet()
    result = compute_confidence(packet)
    assert sum(d.weight for d in result.dimensions) == 100


def test_synthetic_universe_produces_a_spread_of_recommendations():
    """
    Regression guard: earlier versions of the stub provider drew every
    fundamental (revenue growth, institutional ownership, momentum,
    sentiment) fully independently per ticker. Real companies have
    correlated fundamentals; independent draws made every ticker regress to
    the same mediocre average, and the ENTIRE 35-ticker sample universe
    landed in 'Avoid' -- not a useful demo of a screener that's supposed to
    differentiate. This test fails loudly if that flattening regresses.
    """
    from app.services.market_data.stub_provider import StubMarketDataProvider
    from app.services.risk_analyzer import compute_risk_score
    from app.services.universe import UniverseLoader
    from app.services import indicators as ind

    provider = StubMarketDataProvider()
    recommendations = set()

    for ticker in UniverseLoader().load():
        bars = provider.get_price_history(ticker, days=290)
        closes = [b.close for b in bars]
        fundamentals = provider.get_fundamentals(ticker)
        news = provider.get_recent_news(ticker, limit=8)
        risk_score, risk_factors = compute_risk_score(bars, news)
        macd_result = ind.macd(closes)
        packet = EvidencePacket(
            ticker=ticker, as_of_date=date.today(), sector=fundamentals.sector,
            close_price=closes[-1], sma_50=ind.sma(closes, 50), sma_200=ind.sma(closes, 200),
            rsi_14=ind.rsi(closes, 14), macd_histogram=macd_result[2] if macd_result else None,
            pct_above_sma_200=ind.pct_above_moving_average(closes[-1], ind.sma(closes, 200)),
            revenue_growth_yoy=fundamentals.revenue_growth_yoy, pe_ratio=fundamentals.pe_ratio,
            institutional_ownership_pct=fundamentals.institutional_ownership_pct,
            market_cap=fundamentals.market_cap,
            avg_news_sentiment=sum(n.sentiment for n in news) / len(news) if news else 0,
            catalyst_count=sum(1 for n in news if n.is_catalyst), news_headlines=[],
            risk_score=risk_score, risk_factors=risk_factors,
        )
        recommendations.add(compute_confidence(packet).recommendation)

    # Not asserting an exact distribution (that would make this test brittle
    # against any future stub tuning) -- just that it isn't a single band.
    assert len(recommendations) >= 2, (
        f"Expected multiple recommendation bands across the sample universe, "
        f"got only: {recommendations}"
    )
