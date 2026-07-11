import pytest

from app.services.brokerage.stub_provider import StubBrokerageProvider

pytestmark = pytest.mark.asyncio


async def test_register_user_is_deterministic():
    provider = StubBrokerageProvider()
    first = await provider.register_user("user-123")
    second = await provider.register_user("user-123")
    assert first == second


async def test_different_users_get_different_secrets():
    provider = StubBrokerageProvider()
    a = await provider.register_user("user-a")
    b = await provider.register_user("user-b")
    assert a != b


async def test_portfolio_is_deterministic_and_has_holdings():
    provider = StubBrokerageProvider()
    secret = await provider.register_user("user-123")
    first = await provider.get_portfolio("user-123", secret)
    second = await provider.get_portfolio("user-123", secret)

    assert first.total_value == second.total_value
    assert len(first.holdings) >= 2
    assert first.total_value == round(
        sum(h.market_value for h in first.holdings) + first.cash, 2
    )
    assert first.connected_accounts


async def test_connection_portal_url_includes_user_id():
    provider = StubBrokerageProvider()
    url = await provider.get_connection_portal_url("user-123", "secret")
    assert "user-123" in url


async def test_disconnect_does_not_raise():
    provider = StubBrokerageProvider()
    await provider.disconnect_user("user-123", "secret")  # should complete silently
