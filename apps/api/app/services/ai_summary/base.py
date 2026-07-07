"""
AI Summary Engine (Module 8) provider interface.

Per ADR 0004: the AI never computes or adjusts the confidence score. Every
provider implementation receives the already-computed score and evidence,
and its only job is to narrate it in prose -- strengths, risks, a suggested
holding period, catalyst strength, and what would change the thesis. If a
provider's output ever disagrees with the numeric recommendation it was
given, that's a prompting bug to fix, not a feature.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.models.evidence import EvidencePacket
from app.services.confidence import ConfidenceResult


@dataclass(frozen=True)
class AISummaryResult:
    headline: str  # one sentence, e.g. "Strong Buy Candidate on continued AI infrastructure demand"
    why_it_ranked: list[str]  # 3-5 bullets, grounded in the evidence it was given
    primary_risks: list[str]  # 2-4 bullets
    suggested_hold_period: str  # e.g. "12-24 Months"
    catalyst_strength: str  # "Low" | "Moderate" | "High"
    thesis_breakers: list[str]  # "What would change the thesis" bullets


class AISummaryProvider(Protocol):
    async def generate_summary(
        self, packet: EvidencePacket, confidence: ConfidenceResult
    ) -> AISummaryResult:
        ...
