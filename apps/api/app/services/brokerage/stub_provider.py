"""
Deterministic, offline brokerage provider.

Generates a synthetic portfolio seeded from the user's external_user_id, so
the whole "connect a brokerage account" feature -- UI, API, dashboard
integration -- can be built, demoed, and tested without a real SnapTrade
account. This is NOT real portfolio data. Nothing here should be presented
to an end user as their actual holdings.
"""
from __future__ import annotations

import hashlib
import random
import uuid

from app.services.brokerage.base import BrokerageHolding, BrokeragePortfolio

_SAMPLE_HOLDINGS_POOL = ["AAPL", "NVDA", "VOO", "TSLA", "AMD", "MSFT", "COIN", "PLTR"]


def _seed_for(external_user_id: str) -> int:
    digest = hashlib.sha256(f"stub-brokerage::{external_user_id}".encode()).hexdigest()
    return int(digest[:16], 16)


class StubBrokerageProvider:
    async def register_user(self, external_user_id: str) -> str:
        # A believable-looking secret, deterministic per user so repeated
        # calls in tests/demos behave consistently.
        rng = random.Random(_seed_for(external_user_id))
        return str(uuid.UUID(int=rng.getrandbits(128)))

    async def get_connection_portal_url(self, external_user_id: str, user_secret: str) -> str:
        # In the real provider this redirects to SnapTrade's hosted portal.
        # Here it's just a clearly-labeled placeholder page.
        return f"https://example.com/stub-brokerage-connect?user={external_user_id}"

    async def get_portfolio(self, external_user_id: str, user_secret: str) -> BrokeragePortfolio:
        rng = random.Random(_seed_for(external_user_id))
        num_holdings = rng.randint(2, 5)
        symbols = rng.sample(_SAMPLE_HOLDINGS_POOL, k=num_holdings)

        holdings = []
        total_value = 0.0
        for symbol in symbols:
            quantity = round(rng.uniform(1, 50), 2)
            price = round(rng.uniform(20, 450), 2)
            market_value = round(quantity * price, 2)
            total_value += market_value
            holdings.append(
                BrokerageHolding(
                    symbol=symbol,
                    quantity=quantity,
                    market_value=market_value,
                    account_name="Robinhood Individual (stub)",
                )
            )

        cash = round(rng.uniform(50, 2000), 2)
        total_value = round(total_value + cash, 2)

        return BrokeragePortfolio(
            total_value=total_value,
            cash=cash,
            holdings=holdings,
            connected_accounts=["Robinhood Individual (stub)"],
        )

    async def disconnect_user(self, external_user_id: str, user_secret: str) -> None:
        return None
