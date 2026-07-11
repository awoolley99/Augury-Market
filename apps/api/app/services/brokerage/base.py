"""
Brokerage-linking provider interface (ADR 0006).

Robinhood itself has no public developer API -- there is no way for any
third-party app, including this one, to connect directly to a Robinhood
account. The only legitimate path is through a licensed aggregator
(SnapTrade, in this case) whose hosted "Connection Portal" handles the
user's real brokerage login. Their password never touches our servers;
we only ever receive a scoped, revocable identifier (userId + userSecret)
that lets us ask SnapTrade for read-only holdings/balance data.

Every provider implementation follows the same three-step flow:
  1. register_user  -- create an identity for this app-user within the
     provider, get back a secret that authorizes future calls for them.
  2. get_connection_portal_url -- a URL the user visits to actually log
     into their brokerage (Robinhood, etc.) and grant access.
  3. get_portfolio -- read-only holdings/balance, once connected.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class BrokerageHolding:
    symbol: str
    quantity: float
    market_value: float
    account_name: str


@dataclass(frozen=True)
class BrokeragePortfolio:
    total_value: float
    cash: float
    holdings: list[BrokerageHolding] = field(default_factory=list)
    connected_accounts: list[str] = field(default_factory=list)  # e.g. ["Robinhood Individual"]


class BrokerageProvider(Protocol):
    async def register_user(self, external_user_id: str) -> str:
        """Registers a new user with the provider, returns their secret."""
        ...

    async def get_connection_portal_url(self, external_user_id: str, user_secret: str) -> str:
        """A URL the user visits to log into their brokerage and grant access."""
        ...

    async def get_portfolio(self, external_user_id: str, user_secret: str) -> BrokeragePortfolio:
        ...

    async def disconnect_user(self, external_user_id: str, user_secret: str) -> None:
        """Fully removes this user from the provider, revoking all connections."""
        ...
