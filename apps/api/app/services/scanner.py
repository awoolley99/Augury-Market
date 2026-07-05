"""
Stock Scanner Engine (Module 6) orchestrator.

Pipeline: Universe Loader -> Market Data Fetcher -> Indicator Engine ->
News Collector -> Risk Analyzer -> Evidence Packet Storage.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evidence import EvidencePacket
from app.repositories.evidence_repository import EvidenceRepository
from app.services import indicators
from app.services.market_data.base import MarketDataProvider
from app.services.market_data.factory import get_market_data_provider
from app.services.risk_analyzer import compute_risk_score
from app.services.universe import UniverseLoader


class ScanResult:
    def __init__(self):
        self.processed: list[str] = []
        self.failed: list[tuple[str, str]] = []  # (ticker, reason)


class ScannerService:
    def __init__(self, session: AsyncSession, provider: MarketDataProvider | None = None):
        self.session = session
        self.repo = EvidenceRepository(session)
        self.provider = provider or get_market_data_provider()
        self.universe = UniverseLoader()

    def build_packet_data(self, ticker: str, as_of: date) -> dict:
        """Runs the pipeline for a single ticker and returns the row data
        (no DB I/O) — split out from `scan_ticker` so it's independently
        testable without a session."""
        bars = self.provider.get_price_history(ticker, days=290)
        if len(bars) < 30:
            raise ValueError(f"Not enough price history for {ticker}")

        closes = [b.close for b in bars]
        fundamentals = self.provider.get_fundamentals(ticker)
        news = self.provider.get_recent_news(ticker, limit=8)

        sma_50 = indicators.sma(closes, 50)
        sma_200 = indicators.sma(closes, 200)
        rsi_14 = indicators.rsi(closes, 14)
        macd_result = indicators.macd(closes)
        macd_histogram = macd_result[2] if macd_result else None
        pct_above_200 = indicators.pct_above_moving_average(closes[-1], sma_200)

        risk_score, risk_factors = compute_risk_score(bars, news)

        avg_sentiment = round(sum(n.sentiment for n in news) / len(news), 3) if news else 0.0
        catalyst_count = sum(1 for n in news if n.is_catalyst)

        return dict(
            ticker=ticker.upper(),
            as_of_date=as_of,
            sector=fundamentals.sector,
            close_price=closes[-1],
            sma_50=sma_50,
            sma_200=sma_200,
            rsi_14=rsi_14,
            macd_histogram=macd_histogram,
            pct_above_sma_200=pct_above_200,
            revenue_growth_yoy=fundamentals.revenue_growth_yoy,
            pe_ratio=fundamentals.pe_ratio,
            institutional_ownership_pct=fundamentals.institutional_ownership_pct,
            market_cap=fundamentals.market_cap,
            avg_news_sentiment=avg_sentiment,
            catalyst_count=catalyst_count,
            news_headlines=[n.headline for n in news[:5]],
            risk_score=risk_score,
            risk_factors=risk_factors,
        )

    async def scan_ticker(self, ticker: str, as_of: date | None = None) -> EvidencePacket:
        as_of = as_of or date.today()
        packet_data = self.build_packet_data(ticker, as_of)
        return await self.repo.upsert(packet_data)

    async def scan_universe(self, as_of: date | None = None) -> ScanResult:
        as_of = as_of or date.today()
        result = ScanResult()

        for ticker in self.universe.load():
            try:
                await self.scan_ticker(ticker, as_of)
                result.processed.append(ticker)
            except Exception as exc:  # noqa: BLE001 — one bad ticker shouldn't kill the run
                result.failed.append((ticker, str(exc)))

        await self.session.commit()
        return result
