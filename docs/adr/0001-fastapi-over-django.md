# ADR 0001: FastAPI over Django for the API layer

## Status
Accepted

## Context
The API is async-heavy (market data fetching, AI summary generation, concurrent
scanning of 1,000–2,000 tickers) and needs a typed, self-documenting contract
that the Next.js frontend can consume directly.

## Decision
Use FastAPI with async SQLAlchemy 2.0, rather than Django/DRF.

## Rationale
- Native async support end-to-end (routes, DB via asyncpg, HTTP calls to market
  data / AI providers) without bolting on Channels or async views.
- Pydantic models double as request/response validation and OpenAPI schema —
  the frontend gets a typed contract for free.
- Smaller surface area for a service that is fundamentally an API, not a
  server-rendered site with an admin panel.

## Consequences
- We give up Django's batteries (admin panel, ORM migrations UI). We add
  Alembic explicitly for migrations.
- Team must be comfortable with async Python patterns throughout the stack.
