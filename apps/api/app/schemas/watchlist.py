import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class WatchlistItemRead(BaseModel):
    id: uuid.UUID
    ticker: str
    added_at: datetime

    model_config = {"from_attributes": True}


class WatchlistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class WatchlistRead(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    items: list[WatchlistItemRead] = []

    model_config = {"from_attributes": True}


class WatchlistItemCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=12)

    @field_validator("ticker")
    @classmethod
    def uppercase_ticker(cls, v: str) -> str:
        return v.strip().upper()
