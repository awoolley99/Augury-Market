# Augury Market

Evidence-first investment research. It doesn't guess — it interprets
measurable market signals and explains the evidence behind every
recommendation.

## Status: Milestone 1 (of 5)

| Milestone | Contents | Status |
|---|---|---|
| 1 | Monorepo, Docker, FastAPI + Postgres + auth, Next.js shell, Watchlist CRUD | **Done** |
| 2 | Market data ingestion + Stock Scanner Engine (Module 6) | Not started |
| 3 | Confidence Score Engine (Module 7) | Not started |
| 4 | AI Summary Engine (Module 8) | Not started |
| 5 | Full Dashboard Data Layer + morning briefing (Module 9/10) | Not started |

See `docs/adr/` for the reasoning behind the core architectural choices.

## Repo layout

```
augury-market/
├── apps/
│   ├── api/          FastAPI backend
│   │   ├── app/
│   │   │   ├── core/        config, security, logging
│   │   │   ├── db/          SQLAlchemy engine/session, cross-dialect UUID type
│   │   │   ├── models/      SQLAlchemy models
│   │   │   ├── schemas/     Pydantic request/response schemas
│   │   │   ├── repositories/  data-access layer
│   │   │   ├── services/    business logic
│   │   │   ├── api/v1/      route handlers
│   │   │   └── workers/     background jobs (Milestone 2+)
│   │   ├── alembic/         migrations
│   │   └── tests/
│   └── web/           Next.js frontend
│       ├── app/              routes (login, register, dashboard)
│       ├── components/
│       └── lib/               API client, auth context
└── docs/adr/           Architecture Decision Records
```

## Running locally

### Option A: Docker Compose (recommended)

```bash
docker compose up --build
```

- API: http://localhost:8000 (docs at `/docs`)
- Web: http://localhost:3000

### Option B: Run services individually

**Backend**
```bash
cd apps/api
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then set a real SECRET_KEY
# requires a running Postgres matching DATABASE_URL in .env
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd apps/web
npm install
npm run dev
```

## Running tests

```bash
cd apps/api
source venv/bin/activate
pytest -v
```

Tests run against an in-memory SQLite database (no Postgres needed) — see
`tests/conftest.py`.

## What's real vs. stubbed in Milestone 1

**Real and tested:** registration, login, JWT access/refresh tokens, `/auth/me`,
full watchlist CRUD (create/list/delete watchlists, add/remove tickers),
ownership checks (users can't touch each other's watchlists).

**Deliberately stubbed:** the dashboard shows a static explanatory note instead
of live market data, scores, or AI reports — those are Modules 6–10, built in
Milestones 2–5.
