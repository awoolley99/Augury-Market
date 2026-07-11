"""
Central application configuration.

All environment-derived settings live here. Nothing else in the codebase
should call os.environ directly — import `settings` from this module instead.
"""
from functools import lru_cache
from typing import List

from pydantic import AnyUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_NAME: str = "Augury Market API"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # --- Security ---
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    JWT_ALGORITHM: str = "HS256"

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://augury:augury@db:5432/augury_market"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://augury:augury@db:5432/augury_market"

    # --- CORS ---
    CORS_ORIGINS_RAW: str = "http://localhost:3000"

    @property
    def CORS_ORIGINS(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS_RAW.split(",") if origin.strip()]

    # --- Market data providers (Milestone 2, kept here so config is centralized) ---
    MARKET_DATA_PROVIDER: str = "stub"  # stub | polygon | alpaca | iex
    MARKET_DATA_API_KEY: str | None = None

    # --- AI provider (Milestone 4) ---
    AI_SUMMARY_PROVIDER: str = "stub"  # stub | anthropic
    AI_SUMMARY_MODEL: str = "claude-haiku-4-5-20251001"
    ANTHROPIC_API_KEY: str | None = None

    # --- Brokerage linking (Robinhood, etc. via SnapTrade) ---
    BROKERAGE_PROVIDER: str = "stub"  # stub | snaptrade
    SNAPTRADE_CLIENT_ID: str | None = None
    SNAPTRADE_CONSUMER_KEY: str | None = None
    # Fernet key used to encrypt each user's SnapTrade userSecret at rest.
    # Generate with: python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    BROKERAGE_TOKEN_ENCRYPTION_KEY: str | None = None

    @field_validator("MARKET_DATA_PROVIDER")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        return v.lower()


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
