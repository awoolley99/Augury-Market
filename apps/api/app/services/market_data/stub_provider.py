"""
Deterministic, offline market data provider.

Every value is derived from a seed built from the ticker string, so the same
ticker always produces the same price history / fundamentals / news within a
given day — useful for tests, demos, and developing the scanner pipeline
before a real vendor (Polygon/Alpaca/IEX) is wired up.

This is NOT real market data. Nothing here should be presented to an end
user as an actual price or news event.
"""
from __future__ import annotations

import hashlib
import random
from datetime import date, timedelta

from app.services.market_data.base import Fundamentals, MarketDataProvider, NewsItem, PriceBar

_SECTORS = ["Technology", "Healthcare", "Financials", "Consumer", "Industrials", "Energy"]

_HEADLINE_TEMPLATES = [
    ("{ticker} reports quarterly revenue above analyst estimates", 0.6, True),
    ("{ticker} announces expanded partnership in core market", 0.4, True),
    ("Analyst raises price target on {ticker} citing demand strength", 0.5, False),
    ("{ticker} guidance for next quarter comes in below consensus", -0.5, True),
    ("Regulatory inquiry opened into {ticker} business practices", -0.6, True),
    ("{ticker} trades in a narrow range amid low sector volume", 0.0, False),
    ("Institutional holders increase position in {ticker}", 0.3, False),
    ("{ticker} announces executive leadership transition", -0.1, True),
]


def _seed_for(ticker: str, salt: str = "") -> int:
    digest = hashlib.sha256(f"{ticker.upper()}::{salt}".encode()).hexdigest()
    return int(digest[:16], 16)


class StubMarketDataProvider(MarketDataProvider):
    def get_price_history(self, ticker: str, days: int = 200) -> list[PriceBar]:
        rng = random.Random(_seed_for(ticker, "prices"))

        # Start price varies by ticker but stays in a plausible equity range.
        price = 20 + (rng.random() * 480)
        # Mild upward or downward drift, consistent for a given ticker.
        drift = rng.uniform(-0.0015, 0.0025)

        bars: list[PriceBar] = []
        today = date.today()
        for i in range(days, 0, -1):
            trade_date = today - timedelta(days=i)
            if trade_date.weekday() >= 5:  # skip weekends
                continue
            daily_return = drift + rng.gauss(0, 0.018)
            open_price = price
            close_price = max(0.5, price * (1 + daily_return))
            high = max(open_price, close_price) * (1 + abs(rng.gauss(0, 0.006)))
            low = min(open_price, close_price) * (1 - abs(rng.gauss(0, 0.006)))
            volume = int(rng.uniform(1_000_000, 40_000_000))

            bars.append(
                PriceBar(
                    trade_date=trade_date,
                    open=round(open_price, 2),
                    high=round(high, 2),
                    low=round(low, 2),
                    close=round(close_price, 2),
                    volume=volume,
                )
            )
            price = close_price

        return bars

    def get_fundamentals(self, ticker: str) -> Fundamentals:
        rng = random.Random(_seed_for(ticker, "fundamentals"))
        return Fundamentals(
            revenue_growth_yoy=round(rng.uniform(-0.10, 0.45), 3),
            pe_ratio=round(rng.uniform(8, 60), 1) if rng.random() > 0.05 else None,
            institutional_ownership_pct=round(rng.uniform(0.35, 0.92), 3),
            market_cap=round(rng.uniform(2e9, 3.2e12), 0),
            sector=_SECTORS[rng.randrange(len(_SECTORS))],
        )

    def get_recent_news(self, ticker: str, limit: int = 5) -> list[NewsItem]:
        rng = random.Random(_seed_for(ticker, "news"))
        today = date.today()
        count = min(limit, len(_HEADLINE_TEMPLATES))
        chosen = rng.sample(_HEADLINE_TEMPLATES, k=count)

        items = []
        for i, (template, base_sentiment, is_catalyst) in enumerate(chosen):
            jitter = rng.uniform(-0.15, 0.15)
            sentiment = max(-1.0, min(1.0, base_sentiment + jitter))
            items.append(
                NewsItem(
                    headline=template.format(ticker=ticker.upper()),
                    sentiment=round(sentiment, 2),
                    is_catalyst=is_catalyst,
                    published=today - timedelta(days=rng.randint(0, 13)),
                )
            )
        return sorted(items, key=lambda n: n.published, reverse=True)
