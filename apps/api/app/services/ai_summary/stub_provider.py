"""
Deterministic stub AI summary provider.

Reuses the confidence engine's own rule-based strengths/risks (Module 7)
and formats them into the Module 8 report shape, without calling any LLM.
This is NOT the AI Summary Engine's real output -- it's a free, offline
placeholder so the rest of the app (API contract, dashboard, tests) can be
built and exercised before an ANTHROPIC_API_KEY is configured.
"""
from __future__ import annotations

from app.models.evidence import EvidencePacket
from app.services.ai_summary.base import AISummaryResult
from app.services.confidence import ConfidenceResult


def _catalyst_strength(packet: EvidencePacket) -> str:
    if packet.catalyst_count >= 3:
        return "High"
    if packet.catalyst_count >= 1:
        return "Moderate"
    return "Low"


def _suggested_hold_period(confidence: ConfidenceResult) -> str:
    if confidence.recommendation in ("Strong Buy Candidate", "Buy Candidate"):
        return "12-24 Months"
    if confidence.recommendation == "Watch / Hold":
        return "3-6 Months"
    return "Not Recommended"


def _thesis_breakers(packet: EvidencePacket, confidence: ConfidenceResult) -> list[str]:
    breakers = []
    if packet.revenue_growth_yoy > 0:
        breakers.append("Meaningful slowdown in revenue growth.")
    breakers.append("Negative earnings guidance.")
    if packet.pct_above_sma_200 is not None and packet.pct_above_sma_200 > 0:
        breakers.append("Breakdown below the 200-day moving average.")
    if confidence.recommendation in ("Strong Buy Candidate", "Buy Candidate"):
        breakers.append("Institutional ownership beginning to decline.")
    return breakers[:4]


class StubAISummaryProvider:
    async def generate_summary(
        self, packet: EvidencePacket, confidence: ConfidenceResult
    ) -> AISummaryResult:
        headline = (
            f"{confidence.recommendation} on {packet.ticker} "
            f"({confidence.total_score:.1f}/10) based on current scanner evidence."
        )
        return AISummaryResult(
            headline=headline,
            why_it_ranked=list(confidence.strengths),
            primary_risks=list(confidence.risks),
            suggested_hold_period=_suggested_hold_period(confidence),
            catalyst_strength=_catalyst_strength(packet),
            thesis_breakers=_thesis_breakers(packet, confidence),
        )
