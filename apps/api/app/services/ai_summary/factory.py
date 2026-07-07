from app.core.config import settings
from app.services.ai_summary.base import AISummaryProvider
from app.services.ai_summary.stub_provider import StubAISummaryProvider


def get_ai_summary_provider() -> AISummaryProvider:
    provider = settings.AI_SUMMARY_PROVIDER
    if provider == "stub":
        return StubAISummaryProvider()

    if provider == "anthropic":
        from app.services.ai_summary.anthropic_provider import AnthropicAISummaryProvider

        return AnthropicAISummaryProvider()

    raise NotImplementedError(
        f"AI summary provider '{provider}' is not implemented. "
        "Set AI_SUMMARY_PROVIDER=stub or AI_SUMMARY_PROVIDER=anthropic (with ANTHROPIC_API_KEY set)."
    )
