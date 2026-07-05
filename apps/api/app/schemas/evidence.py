from datetime import date, datetime

from pydantic import BaseModel


class EvidencePacketRead(BaseModel):
    ticker: str
    as_of_date: date
    sector: str

    close_price: float
    sma_50: float | None
    sma_200: float | None
    rsi_14: float | None
    macd_histogram: float | None
    pct_above_sma_200: float | None

    revenue_growth_yoy: float
    pe_ratio: float | None
    institutional_ownership_pct: float
    market_cap: float

    avg_news_sentiment: float
    catalyst_count: int
    news_headlines: list[str]

    risk_score: int
    risk_factors: list[str]

    created_at: datetime

    model_config = {"from_attributes": True}


class ScanRunResult(BaseModel):
    as_of_date: date
    processed_count: int
    failed_count: int
    processed: list[str]
    failed: list[str]
