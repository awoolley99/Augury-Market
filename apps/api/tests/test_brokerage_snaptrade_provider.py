from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.brokerage.snaptrade_provider import SnapTradeBrokerageProvider


def _response(body):
    resp = MagicMock()
    resp.body = body
    return resp


def test_missing_credentials_raises_immediately():
    with pytest.raises(RuntimeError, match="SNAPTRADE_CLIENT_ID"):
        SnapTradeBrokerageProvider(client_id=None, consumer_key=None)


@pytest.mark.asyncio
async def test_register_user_returns_secret():
    provider = SnapTradeBrokerageProvider(client_id="cid", consumer_key="ckey")
    provider.client.authentication.aregister_snap_trade_user = AsyncMock(
        return_value=_response({"userSecret": "abc-123"})
    )

    secret = await provider.register_user("app-user-1")

    assert secret == "abc-123"
    provider.client.authentication.aregister_snap_trade_user.assert_awaited_once_with(
        user_id="app-user-1"
    )


async def test_register_user_raises_on_missing_secret():
    provider = SnapTradeBrokerageProvider(client_id="cid", consumer_key="ckey")
    provider.client.authentication.aregister_snap_trade_user = AsyncMock(
        return_value=_response({"somethingElse": "no secret here"})
    )
    with pytest.raises(ValueError, match="missing userSecret"):
        await provider.register_user("app-user-1")


async def test_get_connection_portal_url_passes_robinhood_broker_slug():
    provider = SnapTradeBrokerageProvider(client_id="cid", consumer_key="ckey")
    provider.client.authentication.alogin_snap_trade_user = AsyncMock(
        return_value=_response({"redirectURI": "https://connect.snaptrade.com/xyz"})
    )

    url = await provider.get_connection_portal_url("app-user-1", "secret-1")

    assert url == "https://connect.snaptrade.com/xyz"
    call_kwargs = provider.client.authentication.alogin_snap_trade_user.call_args.kwargs
    assert call_kwargs["user_id"] == "app-user-1"
    assert call_kwargs["user_secret"] == "secret-1"
    assert call_kwargs["broker"] == "ROBINHOOD"


async def test_get_portfolio_aggregates_across_accounts():
    provider = SnapTradeBrokerageProvider(client_id="cid", consumer_key="ckey")

    provider.client.account_information.alist_user_accounts = AsyncMock(
        return_value=_response([
            {"id": "acct-1", "name": "Robinhood Individual"},
        ])
    )
    provider.client.account_information.aget_user_account_balance = AsyncMock(
        return_value=_response({"cash": 150.50})
    )
    provider.client.account_information.aget_user_account_positions = AsyncMock(
        return_value=_response([
            {"symbol": {"symbol": {"symbol": "NVDA"}}, "units": 3, "market_value": 1200.0},
            {"symbol": {"symbol": {"symbol": "AAPL"}}, "units": 5, "market_value": 1000.0},
        ])
    )

    portfolio = await provider.get_portfolio("app-user-1", "secret-1")

    assert portfolio.cash == 150.50
    assert len(portfolio.holdings) == 2
    symbols = {h.symbol for h in portfolio.holdings}
    assert symbols == {"NVDA", "AAPL"}
    assert portfolio.total_value == round(1200.0 + 1000.0 + 150.50, 2)
    assert portfolio.connected_accounts == ["Robinhood Individual"]


async def test_get_portfolio_handles_empty_accounts_gracefully():
    provider = SnapTradeBrokerageProvider(client_id="cid", consumer_key="ckey")
    provider.client.account_information.alist_user_accounts = AsyncMock(
        return_value=_response([])
    )

    portfolio = await provider.get_portfolio("app-user-1", "secret-1")

    assert portfolio.total_value == 0.0
    assert portfolio.holdings == []
    assert portfolio.connected_accounts == []


async def test_disconnect_user_calls_delete():
    provider = SnapTradeBrokerageProvider(client_id="cid", consumer_key="ckey")
    provider.client.authentication.adelete_snap_trade_user = AsyncMock(return_value=_response({}))

    await provider.disconnect_user("app-user-1", "secret-1")

    provider.client.authentication.adelete_snap_trade_user.assert_awaited_once_with(
        user_id="app-user-1"
    )
