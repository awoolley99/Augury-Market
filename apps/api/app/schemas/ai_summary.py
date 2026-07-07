from datetime import date, datetime

from pydantic import BaseModel


class AISummaryRead(BaseModel):
    ticker: str
    as_of_date: date
    provider: str

    headline: str
    why_it_ranked: list[str]
    primary_risks: list[str]
    suggested_hold_period: str
    catalyst_strength: str
    thesis_breakers: list[str]

    confidence_score_at_generation: float
    recommendation_at_generation: str

    created_at: datetime

    model_config = {"from_attributes": True}
