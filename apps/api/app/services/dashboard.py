"""
Dashboard Data Layer (Module 10).

Aggregates the outputs of Modules 6-8 (scanner evidence, confidence scores,
AI summaries) into the morning-briefing shape from the product brief:
market overview, top opportunities across the whole scanned universe, a
per-user watchlist summary with day-over-day score deltas, and the most
recent AI reports generated.

Top Opportunities is personalized by the user's risk tolerance quiz result
(app/services/risk_quiz.py) when one exists: a Conservative investor's
ranking penalizes each ticker's own risk_score more heavily than an
Aggressive investor's does. The underlying confidence_score shown is always
the same official Module 7 number for everyone -- only the ranking order
changes, never the score itself.

Nothing here does its own data fetching from a market data provider --
it only reads what the scanner (Module 6) has already persisted. If
nothing has been scanned yet, everything degrades to empty/neutral
defaults rather than erroring.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_summary import AISummary
from app.models.evidence import EvidencePacket
from app.repositories.ai_summary_repository import AISummaryRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.risk_profile_repository import RiskProfileRepository
from app.repositories.watchlist_repository import WatchlistRepository
from app.services.confidence import ConfidenceResult, compute_confidence
from app.services.scanner import ScannerService


@dataclass(frozen=True)
class MarketOverview:
    market_health_score: int  # 0-100
    market_health_label: str  # Bullish | Neutral | Bearish
    fear_greed_score: int  # 0-100
    fear_greed_label: str  # Fear | Neutral | Greed
    top_sector: str | None
    top_sector_avg_score: float | None
    tickers_scanned: int
    catalyst_count_today: int


@dataclass(frozen=True)
class TopOpportunity:
    ticker: str
    sector: str
    confidence_score: float  # the official, unmodified Module 7 score
    recommendation: str
    top_reason: str
    personalized_rank_score: float  # confidence_score adjusted for the user's risk tolerance -- ranking uses this, display should still show confidence_score as the "real" number


# How strongly each risk tolerance level penalizes a ticker's own risk_score
# (0-100) when ranking Top Opportunities. Conservative investors get picks
# that are good AND low-risk; Aggressive investors get picks ranked almost
# entirely on raw confidence, since high risk_score often correlates with
# the higher-momentum/higher-growth names that an aggressive investor
# actually wants to see surfaced, not filtered out.
RISK_AVERSION_WEIGHTS: dict[str, float] = {
    "Conservative": 1.6,
    "Moderately Conservative": 1.1,
    "Moderate": 0.6,
    "Moderately Aggressive": 0.25,
    "Aggressive": 0.0,
}
DEFAULT_RISK_LEVEL = "Moderate"  # used until a user takes the quiz


@dataclass(frozen=True)
class WatchlistSummaryItem:
    ticker: str
    confidence_score: float | None
    recommendation: str | None
    score_change: float | None  # vs previous scan date, None if no prior data
    top_reason: str | None


@dataclass(frozen=True)
class RecentReport:
    ticker: str
    headline: str
    recommendation: str
    created_at: str


@dataclass(frozen=True)
class DashboardBriefing:
    market_overview: MarketOverview
    top_opportunities: list[TopOpportunity] = field(default_factory=list)
    watchlist_summary: list[WatchlistSummaryItem] = field(default_factory=list)
    recent_reports: list[RecentReport] = field(default_factory=list)


def _health_label(score: int) -> str:
    if score >= 65:
        return "Bullish"
    if score >= 40:
        return "Neutral"
    return "Bearish"


def _fear_greed_label(score: int) -> str:
    if score >= 65:
        return "Greed"
    if score >= 35:
        return "Neutral"
    return "Fear"


class DashboardService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.evidence_repo = EvidenceRepository(session)
        self.summary_repo = AISummaryRepository(session)
        self.watchlist_repo = WatchlistRepository(session)
        self.risk_profile_repo = RiskProfileRepository(session)
        self.scanner = ScannerService(session)

    async def _scored_universe(self) -> list[tuple[EvidencePacket, ConfidenceResult]]:
        packets = await self.evidence_repo.list_all_latest()
        return [(p, compute_confidence(p)) for p in packets]

    def _market_overview(
        self, scored: list[tuple[EvidencePacket, ConfidenceResult]]
    ) -> MarketOverview:
        if not scored:
            return MarketOverview(
                market_health_score=50,
                market_health_label="Neutral",
                fear_greed_score=50,
                fear_greed_label="Neutral",
                top_sector=None,
                top_sector_avg_score=None,
                tickers_scanned=0,
                catalyst_count_today=0,
            )

        scores = [c.total_score for _, c in scored]
        market_health_score = round((sum(scores) / len(scores)) * 10)

        sentiments = [p.avg_news_sentiment for p, _ in scored]
        avg_sentiment = sum(sentiments) / len(sentiments)
        fear_greed_score = round((avg_sentiment + 1) / 2 * 100)  # -1..1 -> 0..100

        sector_scores: dict[str, list[float]] = {}
        for p, c in scored:
            sector_scores.setdefault(p.sector, []).append(c.total_score)
        top_sector, top_sector_scores = max(
            sector_scores.items(), key=lambda kv: sum(kv[1]) / len(kv[1])
        )
        top_sector_avg = round(sum(top_sector_scores) / len(top_sector_scores), 2)

        catalyst_count_today = sum(1 for p, _ in scored if p.catalyst_count > 0)

        return MarketOverview(
            market_health_score=market_health_score,
            market_health_label=_health_label(market_health_score),
            fear_greed_score=fear_greed_score,
            fear_greed_label=_fear_greed_label(fear_greed_score),
            top_sector=top_sector,
            top_sector_avg_score=top_sector_avg,
            tickers_scanned=len(scored),
            catalyst_count_today=catalyst_count_today,
        )

    def _top_opportunities(
        self,
        scored: list[tuple[EvidencePacket, ConfidenceResult]],
        risk_level: str = DEFAULT_RISK_LEVEL,
        limit: int = 5,
    ) -> list[TopOpportunity]:
        aversion = RISK_AVERSION_WEIGHTS.get(risk_level, RISK_AVERSION_WEIGHTS[DEFAULT_RISK_LEVEL])

        def personalized_score(pc: tuple[EvidencePacket, ConfidenceResult]) -> float:
            packet, confidence = pc
            risk_penalty = aversion * (packet.risk_score / 100) * 3
            return confidence.total_score - risk_penalty

        ranked = sorted(scored, key=personalized_score, reverse=True)[:limit]
        return [
            TopOpportunity(
                ticker=p.ticker,
                sector=p.sector,
                confidence_score=c.total_score,
                recommendation=c.recommendation,
                top_reason=c.strengths[0] if c.strengths else "No standout factor.",
                personalized_rank_score=round(personalized_score((p, c)), 2),
            )
            for p, c in ranked
        ]

    async def _watchlist_summary(self, user_id) -> list[WatchlistSummaryItem]:
        watchlists = await self.watchlist_repo.list_for_user(user_id)
        tickers = sorted({item.ticker for w in watchlists for item in w.items})

        summary = []
        for ticker in tickers:
            try:
                packet = await self.scanner.ensure_scanned(ticker)
            except ValueError:
                summary.append(
                    WatchlistSummaryItem(
                        ticker=ticker, confidence_score=None, recommendation=None,
                        score_change=None, top_reason=None,
                    )
                )
                continue

            confidence = compute_confidence(packet)
            previous = await self.evidence_repo.get_previous(ticker, packet.as_of_date)
            score_change = None
            if previous:
                previous_confidence = compute_confidence(previous)
                score_change = round(confidence.total_score - previous_confidence.total_score, 2)

            summary.append(
                WatchlistSummaryItem(
                    ticker=ticker,
                    confidence_score=confidence.total_score,
                    recommendation=confidence.recommendation,
                    score_change=score_change,
                    top_reason=confidence.strengths[0] if confidence.strengths else None,
                )
            )
        return summary

    async def _recent_reports(self, limit: int = 3) -> list[RecentReport]:
        summaries: list[AISummary] = await self.summary_repo.list_recent(limit)
        return [
            RecentReport(
                ticker=s.ticker,
                headline=s.headline,
                recommendation=s.recommendation_at_generation,
                created_at=s.created_at.isoformat(),
            )
            for s in summaries
        ]

    async def get_briefing(self, user_id) -> DashboardBriefing:
        scored = await self._scored_universe()
        risk_profile = await self.risk_profile_repo.get_for_user(user_id)
        risk_level = risk_profile.risk_level if risk_profile else DEFAULT_RISK_LEVEL

        return DashboardBriefing(
            market_overview=self._market_overview(scored),
            top_opportunities=self._top_opportunities(scored, risk_level=risk_level),
            watchlist_summary=await self._watchlist_summary(user_id),
            recent_reports=await self._recent_reports(),
        )
