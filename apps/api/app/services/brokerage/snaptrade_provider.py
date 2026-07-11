"""
SnapTrade-backed brokerage provider (ADR 0006).

Uses the official `snaptrade-python-sdk` (PyPI: snaptrade-python-sdk,
import name `snaptrade_client`) rather than hand-rolling SnapTrade's
HMAC request-signing scheme -- verified against the installed SDK's real
method signatures via introspection, not guessed from memory.

IMPORTANT CAVEAT: the auth flow below (register_user, get_connection_portal_url,
disconnect_user) is verified against the SDK's confirmed signatures and
SnapTrade's documented flow. The exact nested field names used in
_extract_holdings/_extract_balance are best-effort, based on SnapTrade's
publicly documented response shapes -- this code was written without
network access to a real SnapTrade sandbox account to confirm the exact
JSON field names holdings/positions come back with. The first time this
runs against a real connected account, treat any parsing mismatch as
expected and adjust the field lookups to match whatever comes back --
this is flagged in ADR 0006 as something to smoke-test, not something
already verified end-to-end like the rest of this codebase's providers.
"""
from __future__ import annotations

from snaptrade_client import SnapTrade

from app.core.config import settings
from app.services.brokerage.base import BrokerageHolding, BrokeragePortfolio

# SnapTrade's slug for Robinhood in their brokerage reference list. This is
# the one piece of this integration most likely to need correcting once
# real credentials exist -- confirm the exact slug via SnapTrade's
# reference_data.list_all_brokerages() endpoint and update here if needed.
DEFAULT_BROKER_SLUG = "ROBINHOOD"


def _get(obj, *keys, default=None):
    """
    Best-effort nested field extraction that works whether the SDK gives us
    a dict, an attrs-style model object, or something dict-like. Tries each
    key in turn (not nested) -- callers chain this for nested lookups. See
    module docstring: exact field names are unverified against a live
    account and may need adjusting.
    """
    for key in keys:
        if obj is None:
            return default
        if isinstance(obj, dict):
            if key in obj:
                obj = obj[key]
                continue
            return default
        if hasattr(obj, key):
            obj = getattr(obj, key)
            continue
        return default
    return obj if obj is not None else default


class SnapTradeBrokerageProvider:
    def __init__(self, client_id: str | None = None, consumer_key: str | None = None):
        client_id = client_id or settings.SNAPTRADE_CLIENT_ID
        consumer_key = consumer_key or settings.SNAPTRADE_CONSUMER_KEY
        if not client_id or not consumer_key:
            raise RuntimeError(
                "BROKERAGE_PROVIDER=snaptrade requires SNAPTRADE_CLIENT_ID and "
                "SNAPTRADE_CONSUMER_KEY to be set."
            )
        self.client = SnapTrade(consumer_key=consumer_key, client_id=client_id)

    async def register_user(self, external_user_id: str) -> str:
        response = await self.client.authentication.aregister_snap_trade_user(
            user_id=external_user_id
        )
        user_secret = _get(response.body, "userSecret")
        if not user_secret:
            raise ValueError(f"SnapTrade register_user response missing userSecret: {response.body}")
        return user_secret

    async def get_connection_portal_url(self, external_user_id: str, user_secret: str) -> str:
        response = await self.client.authentication.alogin_snap_trade_user(
            user_id=external_user_id,
            user_secret=user_secret,
            broker=DEFAULT_BROKER_SLUG,
        )
        redirect_uri = _get(response.body, "redirectURI")
        if not redirect_uri:
            raise ValueError(f"SnapTrade login response missing redirectURI: {response.body}")
        return redirect_uri

    async def get_portfolio(self, external_user_id: str, user_secret: str) -> BrokeragePortfolio:
        accounts_response = await self.client.account_information.alist_user_accounts(
            user_id=external_user_id, user_secret=user_secret
        )
        accounts = accounts_response.body or []

        holdings: list[BrokerageHolding] = []
        connected_accounts: list[str] = []
        total_value = 0.0
        total_cash = 0.0

        for account in accounts:
            account_id = _get(account, "id")
            account_name = _get(account, "name") or _get(account, "institution_name") or "Connected brokerage account"
            connected_accounts.append(account_name)

            balance = await self.client.account_information.aget_user_account_balance(
                user_id=external_user_id, user_secret=user_secret, account_id=account_id
            )
            cash = float(_get(balance.body, "cash") or _get(balance.body, "total", "value") or 0)
            total_cash += cash

            positions = await self.client.account_information.aget_user_account_positions(
                user_id=external_user_id, user_secret=user_secret, account_id=account_id
            )
            for position in positions.body or []:
                symbol = (
                    _get(position, "symbol", "symbol", "symbol")  # common SnapTrade nesting: position -> symbol -> universal_symbol -> ticker
                    or _get(position, "symbol", "symbol")
                    or _get(position, "symbol")
                    or "UNKNOWN"
                )
                quantity = float(_get(position, "units") or _get(position, "fractional_units") or 0)
                market_value = float(_get(position, "market_value") or 0)
                if not market_value and quantity:
                    price = float(_get(position, "price") or 0)
                    market_value = round(quantity * price, 2)

                total_value += market_value
                holdings.append(
                    BrokerageHolding(
                        symbol=str(symbol),
                        quantity=quantity,
                        market_value=market_value,
                        account_name=account_name,
                    )
                )

        total_value = round(total_value + total_cash, 2)

        return BrokeragePortfolio(
            total_value=total_value,
            cash=round(total_cash, 2),
            holdings=holdings,
            connected_accounts=connected_accounts,
        )

    async def disconnect_user(self, external_user_id: str, user_secret: str) -> None:
        await self.client.authentication.adelete_snap_trade_user(user_id=external_user_id)
