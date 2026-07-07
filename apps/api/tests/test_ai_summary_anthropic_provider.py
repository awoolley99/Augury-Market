import json
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.evidence import EvidencePacket
from app.services.ai_summary.anthropic_provider import AnthropicAISummaryProvider
from app.services.confidence import compute_confidence

def _packet() -> EvidencePacket:
    return EvidencePacket(
        ticker="NVDA", as_of_date=date.today(), sector="Technology",
        close_price=401.79, sma_50=380.0, sma_200=350.0, rsi_14=61.0,
        macd_histogram=1.2, pct_above_sma_200=0.15, revenue_growth_yoy=0.40,
        pe_ratio=23.5, institutional_ownership_pct=0.79, market_cap=1.2e12,
        avg_news_sentiment=0.5, catalyst_count=5, news_headlines=[],
        risk_score=20, risk_factors=[],
    )


def _fake_anthropic_response(parsed_json: dict) -> MagicMock:
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "content": [{"type": "text", "text": json.dumps(parsed_json)}]
    }
    return response


def test_missing_api_key_raises_immediately():
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        AnthropicAISummaryProvider(api_key=None)


async def test_generate_summary_parses_valid_json_response():
    packet = _packet()
    confidence = compute_confidence(packet)
    provider = AnthropicAISummaryProvider(api_key="test-key-123")

    fake_json = {
        "headline": "Strong Buy Candidate on continued AI infrastructure demand",
        "why_it_ranked": ["Revenue growth outpaces peers", "Institutional ownership rising"],
        "primary_risks": ["Valuation is elevated", "Earnings in three weeks"],
        "suggested_hold_period": "12-24 Months",
        "catalyst_strength": "High",
        "thesis_breakers": ["Data center demand slows", "Guidance disappoints"],
    }

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=_fake_anthropic_response(fake_json))):
        result = await provider.generate_summary(packet, confidence)

    assert result.headline == fake_json["headline"]
    assert result.why_it_ranked == fake_json["why_it_ranked"]
    assert result.catalyst_strength == "High"


async def test_generate_summary_raises_on_non_json_response():
    packet = _packet()
    confidence = compute_confidence(packet)
    provider = AnthropicAISummaryProvider(api_key="test-key-123")

    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {"content": [{"type": "text", "text": "not valid json"}]}

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=response)):
        with pytest.raises(ValueError, match="non-JSON"):
            await provider.generate_summary(packet, confidence)


async def test_request_payload_includes_computed_score_and_recommendation():
    """The prompt sent to the model must include the already-computed score
    so the model narrates it rather than inventing its own (ADR 0004)."""
    packet = _packet()
    confidence = compute_confidence(packet)
    provider = AnthropicAISummaryProvider(api_key="test-key-123", model="claude-haiku-4-5-20251001")

    fake_json = {
        "headline": "x", "why_it_ranked": ["x"], "primary_risks": ["x"],
        "suggested_hold_period": "x", "catalyst_strength": "Low", "thesis_breakers": ["x"],
    }
    mock_post = AsyncMock(return_value=_fake_anthropic_response(fake_json))

    with patch("httpx.AsyncClient.post", new=mock_post):
        await provider.generate_summary(packet, confidence)

    sent_payload = mock_post.call_args.kwargs["json"]
    user_message = sent_payload["messages"][0]["content"]
    assert str(confidence.total_score) in user_message
    assert confidence.recommendation in user_message
    assert sent_payload["model"] == "claude-haiku-4-5-20251001"
