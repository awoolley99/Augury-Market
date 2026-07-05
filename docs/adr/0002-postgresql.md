# ADR 0002: PostgreSQL as the primary datastore

## Status
Accepted

## Context
Augury Market needs to store relational data (users, watchlists) alongside
semi-structured evidence packets (Module 6/7) and, eventually, time-series-ish
price/indicator history.

## Decision
PostgreSQL, accessed asynchronously via SQLAlchemy 2.0 + asyncpg.

## Rationale
- JSONB columns give us flexibility for evidence packets without a second
  database, while keeping strong relational guarantees for users/watchlists/
  billing.
- Mature ecosystem for migrations (Alembic), extensions (pg_trgm for ticker
  search, TimescaleDB later if price history volume demands it).
- Every target deployment platform (Fly.io, Render, RDS, Supabase) supports it
  natively — no vendor lock-in required for Milestone 1.

## Consequences
- Market data time-series at scale (Module 6+) may eventually warrant a
  columnar/time-series store; Postgres is the right default until that's
  measured, not assumed.
