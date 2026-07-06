from pydantic import BaseModel


class DimensionScoreRead(BaseModel):
    name: str
    raw_value: float | None
    score: float
    weight: int
    contribution: float


class ConfidenceRead(BaseModel):
    ticker: str
    total_score: float
    recommendation: str
    dimensions: list[DimensionScoreRead]
    risk_adjustment_points: float
    strengths: list[str]
    risks: list[str]
