"""
Confidence Score Engine (Module 7, ADR 0004).

Deterministic — no AI, no randomness. The same evidence packet always
produces the same score. Each raw evidence field is normalized to a 0-100
sub-score, weighted, summed, then reduced by a risk adjustment. The AI
Summary Engine (Module 8, Milestone 4) explains this score in prose; it
never computes or overrides it.

Weights (must sum to 100 before the risk adjustment, which is subtractive):
  Business Quality   30%   <- revenue growth
  Momentum           20%   <- RSI, MACD histogram, price vs 200-day SMA
  Valuation          10%   <- P/E ratio (lower is better, all else equal)
  News & Catalysts   15%   <- catalyst count + how positive that news is
  Institutional      15%   <- institutional ownership %
  Sentiment          10%   <- average news sentiment
  Risk Adjustment   -15%   <- risk_score scaled down and subtracted
"""
from __future__ import annotations

from dataclasses import dataclass

from app.models.evidence import EvidencePacket

WEIGHTS = {
    "business_quality": 30,
    "momentum": 20,
    "valuation": 10,
    "news_catalysts": 15,
    "institutional_activity": 15,
    "sentiment": 10,
}
RISK_ADJUSTMENT_WEIGHT = 15  # subtracted, scaled by risk_score / 100

SCORE_BANDS = [
    (9.0, "Strong Buy Candidate"),
    (8.0, "Buy Candidate"),
    (7.0, "Watch / Hold"),
]
DEFAULT_RECOMMENDATION = "Avoid"


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _normalize(value: float, low: float, high: float) -> float:
    """Linearly map value in [low, high] to [0, 100], clamped at the ends."""
    if high == low:
        return 50.0
    return _clamp((value - low) / (high - low) * 100)


@dataclass(frozen=True)
class DimensionScore:
    name: str
    raw_value: float | None
    score: float  # 0-100, already normalized
    weight: int
    contribution: float  # score * weight / 100


@dataclass(frozen=True)
class ConfidenceResult:
    ticker: str
    total_score: float  # 0-10
    recommendation: str
    dimensions: list[DimensionScore]
    risk_adjustment_points: float  # positive number of points subtracted
    strengths: list[str]
    risks: list[str]


def _business_quality(packet: EvidencePacket) -> DimensionScore:
    score = _normalize(packet.revenue_growth_yoy, -0.10, 0.45)
    return DimensionScore(
        "business_quality", packet.revenue_growth_yoy, score,
        WEIGHTS["business_quality"], score * WEIGHTS["business_quality"] / 100,
    )


def _momentum(packet: EvidencePacket) -> DimensionScore:
    parts = []
    if packet.rsi_14 is not None:
        # RSI: 50 is neutral. Reward momentum without over-rewarding overbought extremes.
        parts.append(_clamp(100 - abs(packet.rsi_14 - 60) * 1.5))
    if packet.macd_histogram is not None:
        # Positive histogram = bullish crossover; scale generously since
        # magnitudes are small dollar amounts, not percentages.
        parts.append(_normalize(packet.macd_histogram, -3, 3))
    if packet.pct_above_sma_200 is not None:
        parts.append(_normalize(packet.pct_above_sma_200, -0.15, 0.25))

    score = sum(parts) / len(parts) if parts else 50.0
    raw = packet.pct_above_sma_200
    return DimensionScore(
        "momentum", raw, score, WEIGHTS["momentum"], score * WEIGHTS["momentum"] / 100
    )


def _valuation(packet: EvidencePacket) -> DimensionScore:
    if packet.pe_ratio is None:
        score = 50.0  # no P/E (e.g. unprofitable or an ETF) -> neutral, not penalized
    else:
        # Lower P/E scores higher. Range chosen to match the stub provider's
        # 8-60 spread; a real vendor integration would want sector-relative
        # P/E instead of an absolute band.
        score = 100 - _normalize(packet.pe_ratio, 8, 60)
    return DimensionScore(
        "valuation", packet.pe_ratio, score, WEIGHTS["valuation"],
        score * WEIGHTS["valuation"] / 100,
    )


def _news_catalysts(packet: EvidencePacket) -> DimensionScore:
    catalyst_presence = _clamp(packet.catalyst_count * 20)  # 5+ catalysts -> saturates at 100
    sentiment_component = _normalize(packet.avg_news_sentiment, -1, 1)
    score = (catalyst_presence * 0.4) + (sentiment_component * 0.6)
    return DimensionScore(
        "news_catalysts", float(packet.catalyst_count), score,
        WEIGHTS["news_catalysts"], score * WEIGHTS["news_catalysts"] / 100,
    )


def _institutional_activity(packet: EvidencePacket) -> DimensionScore:
    score = _normalize(packet.institutional_ownership_pct, 0.35, 0.92)
    return DimensionScore(
        "institutional_activity", packet.institutional_ownership_pct, score,
        WEIGHTS["institutional_activity"],
        score * WEIGHTS["institutional_activity"] / 100,
    )


def _sentiment(packet: EvidencePacket) -> DimensionScore:
    score = _normalize(packet.avg_news_sentiment, -1, 1)
    return DimensionScore(
        "sentiment", packet.avg_news_sentiment, score,
        WEIGHTS["sentiment"], score * WEIGHTS["sentiment"] / 100,
    )


def _recommendation_for(score_0_to_10: float) -> str:
    for threshold, label in SCORE_BANDS:
        if score_0_to_10 >= threshold:
            return label
    return DEFAULT_RECOMMENDATION


def _explain(dimensions: list[DimensionScore], packet: EvidencePacket) -> tuple[list[str], list[str]]:
    """
    Rule-based bullets from the dimension scores — NOT an AI summary. This is
    a placeholder for Module 8 (Milestone 4), which will generate genuine
    prose from this same evidence. Kept intentionally terse and mechanical
    so nobody mistakes it for the AI Summary Engine's output.
    """
    strengths = []
    risks = []

    by_name = {d.name: d for d in dimensions}

    if by_name["business_quality"].score >= 70:
        strengths.append(f"Revenue growth of {packet.revenue_growth_yoy:.0%} year-over-year is strong.")
    if by_name["momentum"].score >= 70:
        strengths.append("Price trend and technical momentum are firmly positive.")
    if by_name["institutional_activity"].score >= 70:
        strengths.append(f"Institutional ownership is high ({packet.institutional_ownership_pct:.0%}).")
    if by_name["news_catalysts"].score >= 70:
        strengths.append("Recent news includes multiple positive catalysts.")
    if by_name["valuation"].score >= 70 and packet.pe_ratio:
        strengths.append(f"Valuation (P/E {packet.pe_ratio:.1f}) is reasonable relative to the sample universe.")

    if by_name["valuation"].score < 30 and packet.pe_ratio:
        risks.append(f"Valuation is elevated (P/E {packet.pe_ratio:.1f}).")
    if by_name["momentum"].score < 30:
        risks.append("Technical momentum is weak or negative.")
    if packet.risk_score >= 60:
        risks.append(f"Overall risk score is elevated ({packet.risk_score}/100).")
    risks.extend(packet.risk_factors[:2])

    if not strengths:
        strengths.append("No dimension currently scores strongly above neutral.")
    if not risks:
        risks.append("No elevated risk factors detected in the current evidence.")

    return strengths, risks


def compute_confidence(packet: EvidencePacket) -> ConfidenceResult:
    dimensions = [
        _business_quality(packet),
        _momentum(packet),
        _valuation(packet),
        _news_catalysts(packet),
        _institutional_activity(packet),
        _sentiment(packet),
    ]

    raw_total = sum(d.contribution for d in dimensions)  # 0-100
    risk_adjustment_points = (packet.risk_score / 100) * RISK_ADJUSTMENT_WEIGHT
    adjusted_total = _clamp(raw_total - risk_adjustment_points, 0, 100)
    total_score = round(adjusted_total / 10, 2)  # -> 0-10 scale

    strengths, risks = _explain(dimensions, packet)

    return ConfidenceResult(
        ticker=packet.ticker,
        total_score=total_score,
        recommendation=_recommendation_for(total_score),
        dimensions=dimensions,
        risk_adjustment_points=round(risk_adjustment_points, 2),
        strengths=strengths,
        risks=risks,
    )
