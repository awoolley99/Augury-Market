"""
Universe loader (Module 6).

Loads the set of tickers the scanner should process. For now this is a
curated sample spanning sectors and market caps — large enough to exercise
the full pipeline meaningfully, small enough to run in seconds without a paid
data feed. Swapping this for real S&P 500 / Nasdaq 100 / Russell 1000 / ETF
membership lists is a follow-up once a market data vendor (ADR 0005) is
under contract; the interface below doesn't need to change when that happens.
"""
from __future__ import annotations

_SAMPLE_UNIVERSE = [
    # Mega-cap tech
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO",
    # AI / semis
    "AMD", "SMCI", "MU", "TSM",
    # Cloud / SaaS
    "CRM", "NOW", "SNOW", "PLTR",
    # Healthcare
    "UNH", "LLY", "JNJ", "PFE",
    # Financials
    "JPM", "BAC", "GS", "V",
    # Consumer
    "COST", "WMT", "MCD", "NKE",
    # Industrials / Energy
    "CAT", "BA", "XOM", "CVX",
    # ETFs
    "SPY", "QQQ", "VTI",
]


class UniverseLoader:
    def load(self) -> list[str]:
        return list(_SAMPLE_UNIVERSE)
