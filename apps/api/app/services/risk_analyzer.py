"""
Risk analyzer (Module 6).

Produces a 0-100 risk score (higher = riskier) from realized volatility and
drawdown in the price history, plus news-derived signals (litigation,
guidance cuts). This feeds the "Risk" evidence field and the Confidence
Score Engine's risk adjustment (Milestone 3 / Module 7).
"""
from __future__ import annotations

import statistics

from app.services.market_data.base import NewsItem, PriceBar


def _daily_returns(bars: list[PriceBar]) -> list[float]:
    returns = []
    for prev, curr in zip(bars, bars[1:]):
        if prev.close > 0:
            returns.append((curr.close - prev.close) / prev.close)
    return returns


def realized_volatility(bars: list[PriceBar], annualize: bool = True) -> float | None:
    """Standard deviation of daily returns, optionally annualized (×√252)."""
    returns = _daily_returns(bars)
    if len(returns) < 2:
        return None
    vol = statistics.pstdev(returns)
    return round(vol * (252 ** 0.5 if annualize else 1), 4)


def max_drawdown(bars: list[PriceBar]) -> float | None:
    """Largest peak-to-trough decline over the window, as a positive fraction."""
    if not bars:
        return None
    peak = bars[0].close
    worst = 0.0
    for bar in bars:
        peak = max(peak, bar.close)
        if peak > 0:
            drawdown = (peak - bar.close) / peak
            worst = max(worst, drawdown)
    return round(worst, 4)


def news_risk_flags(news: list[NewsItem]) -> list[str]:
    flags = []
    for item in news:
        if item.is_catalyst and item.sentiment < -0.2:
            flags.append(item.headline)
    return flags


def compute_risk_score(bars: list[PriceBar], news: list[NewsItem]) -> tuple[int, list[str]]:
    """
    Returns (risk_score 0-100, list of human-readable risk factors).
    Higher score = more risk. This is a heuristic starting point for
    Milestone 2 — Milestone 3's Confidence Score Engine (ADR 0004) is where
    the weighting against other evidence dimensions actually happens.
    """
    vol = realized_volatility(bars) or 0.0
    drawdown = max_drawdown(bars) or 0.0
    flags = news_risk_flags(news)

    # Typical large-cap annualized volatility (15-30%) and a normal
    # peak-to-trough drawdown (10-20% over ~10 months) shouldn't read as
    # "elevated risk" on their own -- only genuinely high volatility/
    # drawdown or bad news should push the score up meaningfully.
    vol_score = min(40, vol * 80)
    drawdown_score = min(25, drawdown * 60)
    news_score = min(20, len(flags) * 10)

    total = round(vol_score + drawdown_score + news_score)
    factors = []
    if vol > 0.35:
        factors.append(f"Elevated volatility ({vol:.0%} annualized)")
    if drawdown > 0.20:
        factors.append(f"Significant drawdown from recent highs ({drawdown:.0%})")
    factors.extend(f"Negative catalyst: {f}" for f in flags)

    return min(100, total), factors
