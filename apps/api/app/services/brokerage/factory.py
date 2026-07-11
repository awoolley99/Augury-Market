from app.core.config import settings
from app.services.brokerage.base import BrokerageProvider
from app.services.brokerage.stub_provider import StubBrokerageProvider


def get_brokerage_provider() -> BrokerageProvider:
    provider = settings.BROKERAGE_PROVIDER
    if provider == "stub":
        return StubBrokerageProvider()

    if provider == "snaptrade":
        from app.services.brokerage.snaptrade_provider import SnapTradeBrokerageProvider

        return SnapTradeBrokerageProvider()

    raise NotImplementedError(
        f"Brokerage provider '{provider}' is not implemented. "
        "Set BROKERAGE_PROVIDER=stub or BROKERAGE_PROVIDER=snaptrade "
        "(with SNAPTRADE_CLIENT_ID and SNAPTRADE_CONSUMER_KEY set)."
    )
