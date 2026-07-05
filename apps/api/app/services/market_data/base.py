"""
Provider-agnostic market data interface (ADR 0005). Every vendor adapter
(Polygon, Alpaca, IEX, ...) implements `MarketDataProvider`; the scanner
pipeline only ever talks to this interface.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True)
class PriceBar:
    """A single day's OHLCV bar."""

    trade_date: date
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass(frozen=True)
class Fundamentals:
    revenue_growth_yoy: float  # e.g. 0.32 == 32%
    pe_ratio: float | None
    institutional_ownership_pct: float  # 0-1
    market_cap: float
    sector: str


@dataclass(frozen=True)
class NewsItem:
    headline: str
    sentiment: float  # -1.0 (very negative) .. 1.0 (very positive)
    is_catalyst: bool  # earnings, guidance, litigation, M&A, etc.
    published: date


class MarketDataProvider(Protocol):
    """Anything that can answer these three questions for a ticker is a
    valid market data provider for the scanner pipeline."""

    def get_price_history(self, ticker: str, days: int = 200) -> list[PriceBar]:
        ...

    def get_fundamentals(self, ticker: str) -> Fundamentals:
        ...

    def get_recent_news(self, ticker: str, limit: int = 5) -> list[NewsItem]:
        ...
