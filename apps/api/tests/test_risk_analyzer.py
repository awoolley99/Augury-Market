from datetime import date, timedelta

from app.services.market_data.base import NewsItem, PriceBar
from app.services.risk_analyzer import compute_risk_score, max_drawdown, realized_volatility


def _flat_bars(days: int, price: float = 100.0) -> list[PriceBar]:
    today = date.today()
    return [
        PriceBar(
            trade_date=today - timedelta(days=days - i),
            open=price,
            high=price,
            low=price,
            close=price,
            volume=1_000_000,
        )
        for i in range(days)
    ]


def test_flat_prices_have_zero_volatility_and_drawdown():
    bars = _flat_bars(30)
    assert realized_volatility(bars) == 0.0
    assert max_drawdown(bars) == 0.0


def test_drawdown_detects_peak_to_trough_decline():
    today = date.today()
    bars = [
        PriceBar(trade_date=today - timedelta(days=2), open=100, high=100, low=100, close=100, volume=1),
        PriceBar(trade_date=today - timedelta(days=1), open=100, high=100, low=100, close=150, volume=1),
        PriceBar(trade_date=today, open=150, high=150, low=100, close=100, volume=1),
    ]
    dd = max_drawdown(bars)
    assert dd is not None
    assert abs(dd - (150 - 100) / 150) < 0.01


def test_risk_score_increases_with_negative_catalyst_news():
    bars = _flat_bars(30)
    no_news_score, _ = compute_risk_score(bars, [])
    bad_news = [
        NewsItem(headline="Litigation filed", sentiment=-0.8, is_catalyst=True, published=date.today())
    ]
    with_bad_news_score, factors = compute_risk_score(bars, bad_news)
    assert with_bad_news_score > no_news_score
    assert any("Litigation" in f for f in factors)


def test_risk_score_bounded_0_to_100():
    bars = _flat_bars(30)
    score, _ = compute_risk_score(bars, [])
    assert 0 <= score <= 100
