from app.core.config import settings
from app.services.market_data.base import MarketDataProvider
from app.services.market_data.stub_provider import StubMarketDataProvider


def get_market_data_provider() -> MarketDataProvider:
    provider = settings.MARKET_DATA_PROVIDER
    if provider == "stub":
        return StubMarketDataProvider()

    # Real vendor adapters land here as they're built (ADR 0005):
    # if provider == "polygon": return PolygonProvider(settings.MARKET_DATA_API_KEY)
    # if provider == "alpaca": return AlpacaProvider(settings.MARKET_DATA_API_KEY)
    raise NotImplementedError(
        f"Market data provider '{provider}' is not implemented yet. "
        "Set MARKET_DATA_PROVIDER=stub or add an adapter in app/services/market_data/."
    )
