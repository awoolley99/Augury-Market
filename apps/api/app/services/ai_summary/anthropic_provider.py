"""
Anthropic-backed AI summary provider.

Calls the Claude API to turn an already-scored evidence packet into
human-readable research prose. The prompt is deliberately restrictive: the
model is given the exact numeric score and recommendation and told to
explain *that*, not to form its own opinion. It's asked for strict JSON so
the response can be parsed without any further LLM calls.
"""
from __future__ import annotations

import json

import httpx

from app.core.config import settings
from app.models.evidence import EvidencePacket
from app.services.ai_summary.base import AISummaryResult
from app.services.confidence import ConfidenceResult

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

SYSTEM_PROMPT = """\
You are the AI Summary Engine inside Augury Market, an evidence-first \
investment research platform. You will be given a stock's evidence packet \
and an ALREADY-COMPUTED confidence score and recommendation.

Your only job is to explain that score in clear, concise investment-research \
prose. You must NOT:
- invent a different score or recommendation than the one given
- second-guess or contradict the numeric recommendation
- state facts about the company that are not present in the evidence given

Respond with ONLY a JSON object (no markdown fences, no preamble) matching \
exactly this shape:
{
  "headline": "one sentence summarizing the call",
  "why_it_ranked": ["3-5 bullets grounded in the evidence"],
  "primary_risks": ["2-4 bullets grounded in the evidence"],
  "suggested_hold_period": "e.g. '12-24 Months' or 'Not Recommended'",
  "catalyst_strength": "Low, Moderate, or High",
  "thesis_breakers": ["2-4 bullets: what evidence would change this call"]
}
"""


def _build_user_prompt(packet: EvidencePacket, confidence: ConfidenceResult) -> str:
    dimension_lines = "\n".join(
        f"- {d.name}: raw={d.raw_value}, normalized_score={d.score:.1f}/100 (weight {d.weight}%)"
        for d in confidence.dimensions
    )
    return f"""\
Ticker: {packet.ticker}
Sector: {packet.sector}
As of: {packet.as_of_date}

COMPUTED CONFIDENCE SCORE (do not change this): {confidence.total_score}/10
COMPUTED RECOMMENDATION (do not change this): {confidence.recommendation}
Risk adjustment applied: -{confidence.risk_adjustment_points} points (risk score {packet.risk_score}/100)

Dimension breakdown:
{dimension_lines}

Raw evidence:
- Close price: {packet.close_price}
- 50-day / 200-day SMA: {packet.sma_50} / {packet.sma_200}
- RSI(14): {packet.rsi_14}
- MACD histogram: {packet.macd_histogram}
- Revenue growth YoY: {packet.revenue_growth_yoy}
- P/E ratio: {packet.pe_ratio}
- Institutional ownership: {packet.institutional_ownership_pct}
- Avg news sentiment: {packet.avg_news_sentiment}
- Catalyst count: {packet.catalyst_count}
- Recent headlines: {packet.news_headlines}
- Risk factors: {packet.risk_factors}

Write the JSON report now.
"""


class AnthropicAISummaryProvider:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.AI_SUMMARY_MODEL
        if not self.api_key:
            raise RuntimeError(
                "AI_SUMMARY_PROVIDER=anthropic requires ANTHROPIC_API_KEY to be set."
            )

    async def generate_summary(
        self, packet: EvidencePacket, confidence: ConfidenceResult
    ) -> AISummaryResult:
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "system": SYSTEM_PROMPT,
            "messages": [
                {"role": "user", "content": _build_user_prompt(packet, confidence)}
            ],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(ANTHROPIC_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
        raw_text = "".join(text_blocks).strip()

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"AI summary provider returned non-JSON output: {raw_text[:200]}"
            ) from exc

        return AISummaryResult(
            headline=parsed["headline"],
            why_it_ranked=parsed["why_it_ranked"],
            primary_risks=parsed["primary_risks"],
            suggested_hold_period=parsed["suggested_hold_period"],
            catalyst_strength=parsed["catalyst_strength"],
            thesis_breakers=parsed["thesis_breakers"],
        )
