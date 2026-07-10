from pydantic import BaseModel


class MarketOverviewRead(BaseModel):
    market_health_score: int
    market_health_label: str
    fear_greed_score: int
    fear_greed_label: str
    top_sector: str | None
    top_sector_avg_score: float | None
    tickers_scanned: int
    catalyst_count_today: int

    model_config = {"from_attributes": True}


class TopOpportunityRead(BaseModel):
    ticker: str
    sector: str
    confidence_score: float
    recommendation: str
    top_reason: str
    personalized_rank_score: float

    model_config = {"from_attributes": True}


class WatchlistSummaryItemRead(BaseModel):
    ticker: str
    confidence_score: float | None
    recommendation: str | None
    score_change: float | None
    top_reason: str | None

    model_config = {"from_attributes": True}


class RecentReportRead(BaseModel):
    ticker: str
    headline: str
    recommendation: str
    created_at: str

    model_config = {"from_attributes": True}


class DashboardBriefingRead(BaseModel):
    market_overview: MarketOverviewRead
    top_opportunities: list[TopOpportunityRead]
    watchlist_summary: list[WatchlistSummaryItemRead]
    recent_reports: list[RecentReportRead]

    model_config = {"from_attributes": True}
