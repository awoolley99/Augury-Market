from datetime import datetime

from pydantic import BaseModel


class BrokerageStatusRead(BaseModel):
    connected: bool
    provider: str | None = None
    status: str | None = None
    updated_at: datetime | None = None


class BrokerageConnectRead(BaseModel):
    connect_url: str


class BrokerageHoldingRead(BaseModel):
    symbol: str
    quantity: float
    market_value: float
    account_name: str


class BrokeragePortfolioRead(BaseModel):
    total_value: float
    cash: float
    holdings: list[BrokerageHoldingRead]
    connected_accounts: list[str]

    model_config = {"from_attributes": True}
