from datetime import datetime

from pydantic import BaseModel, field_validator


class QuizOptionRead(BaseModel):
    letter: str
    label: str


class QuizQuestionRead(BaseModel):
    id: str
    prompt: str
    options: list[QuizOptionRead]


class QuizSubmission(BaseModel):
    answers: dict[str, str]  # {"experience": "C", "loss_reaction": "B", ...}

    @field_validator("answers")
    @classmethod
    def non_empty(cls, v: dict[str, str]) -> dict[str, str]:
        if not v:
            raise ValueError("answers cannot be empty")
        return v


class RiskProfileRead(BaseModel):
    risk_score: float
    risk_level: str
    answers: dict
    updated_at: datetime

    model_config = {"from_attributes": True}
