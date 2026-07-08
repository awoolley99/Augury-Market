# Augury Market

Evidence-first investment research. It doesn't guess — it interprets
measurable market signals and explains the evidence behind every
recommendation.

## Status: Milestone 1 (of 5)

| Milestone | Contents | Status |
|---|---|---|
| 1 | Monorepo, Docker, FastAPI + Postgres + auth, Next.js shell, Watchlist CRUD | **Done** |
| 2 | Market data ingestion + Stock Scanner Engine (Module 6) | **Done** |
| 3 | Confidence Score Engine (Module 7) | **Done** |
| 4 | AI Summary Engine (Module 8) | **Done** |
| 5 | Full Dashboard Data Layer + morning briefing (Module 9/10) | **Done** |

All 5 original milestones from the product blueprint are now built. See
"What's next" at the bottom of this README for natural follow-ups.

See `docs/adr/` for the reasoning behind the core architectural choices, and
`docs/deploy-flyio.md` for deploying to Fly.io.

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

**Real and tested (Milestone 1):** registration, login, JWT access/refresh tokens, `/auth/me`,
full watchlist CRUD (create/list/delete watchlists, add/remove tickers),
ownership checks (users can't touch each other's watchlists).

**Real and tested (Milestone 2):** the Stock Scanner Engine — universe loader
(curated ~35-ticker sample), indicator engine (SMA/EMA/RSI/MACD, unit tested
against known values), risk analyzer (volatility + drawdown + negative-news
heuristics), and evidence packet storage, all wired to a live `/scanner/run`
endpoint and rendered on the dashboard. Verified end-to-end against a real
Postgres instance (not just SQLite/mocks) during development.

**Real and tested (Milestone 3):** the Confidence Score Engine (ADR 0004) —
a deterministic weighted formula (business quality 30%, momentum 20%,
valuation 10%, news/catalysts 15%, institutional activity 15%, sentiment
10%, minus a risk adjustment) over each evidence packet, producing a 0-10
score and a Strong Buy / Buy / Watch-Hold / Avoid recommendation. Same
evidence always produces the same score — no AI involved yet (that's
Milestone 4). Verified against the full 35-ticker sample universe, not just
hand-picked test cases: this caught and fixed a real bug where the stub
market data provider drew every fundamental independently per ticker,
causing every single stock to regress to the same mediocre score and land
in "Avoid" — fixed by correlating fundamentals through a per-ticker quality
factor, the way real companies' metrics actually move together.

**Real and tested (Milestone 4):** the AI Summary Engine (Module 8) — turns
an evidence packet + its already-computed confidence score into a research
report (headline, why it ranked, primary risks, suggested hold period,
catalyst strength, what would change the thesis), cached per (ticker, date)
so a real LLM isn't called more than once a day per ticker. Two providers,
selected via `AI_SUMMARY_PROVIDER`:
- `stub` (default): free, offline, rule-based — reuses the confidence
  engine's own strengths/risks. No API key needed.
- `anthropic`: calls the real Claude API (`AI_SUMMARY_MODEL`, defaults to
  `claude-haiku-4-5-20251001`) with a system prompt that's given the
  already-computed score and explicitly told to narrate it, not invent a
  different one (ADR 0004) — needs `ANTHROPIC_API_KEY` set.
Click "View report" on any ticker on the dashboard to see one. The
Anthropic-backed provider's HTTP calls are fully mocked in tests — the test
suite never makes real (or billed) API calls.

**Real and tested (Milestone 5):** the Dashboard Data Layer (Module 10) —
`GET /dashboard/briefing` aggregates everything above into one response:
a market overview (health score, fear/greed, top sector, catalyst count —
all computed from the scanned universe's own confidence scores and
sentiment, not a separate data source), the top 5 opportunities across the
*whole* scanned universe ranked by confidence score, the current user's
watchlist summary with day-over-day score deltas (when a prior day's scan
exists), and the most recently generated AI reports. Degrades to neutral
defaults before anything's been scanned rather than erroring. The dashboard
UI now shows this as the actual morning-briefing view — stat strip, top
opportunities list, recent reports — above the existing watchlist/scanner
UI from Milestones 1-2.

Building this also surfaced a real bug in the Milestone 1 watchlist code:
`add_item`/`remove_item` were mutating the database directly without going
through the SQLAlchemy relationship, so an already-loaded `Watchlist.items`
collection in memory could go stale within a single long-lived session (the
per-request API sessions never hit this, since each request gets a fresh
session — the dashboard was the first thing to reuse one session across
multiple service calls). Fixed by going through the relationship so cascade
and in-memory consistency are handled correctly.

**Deliberately stubbed:** market data comes from `StubMarketDataProvider` —
deterministic synthetic prices/fundamentals/news, not real market data (see
ADR 0005). No real vendor (Polygon/Alpaca/IEX) is wired up yet. AI summaries
default to the free `stub` provider rather than a real Anthropic API call
(see Milestone 4 above for how to switch that on).

## What's next

Before the milestone follow-ups below: **any ticker now works, not just the
curated sample universe.** Originally, tickers outside the ~35-ticker
sample list (`UniverseLoader`) never showed up in the Market Snapshot, the
dashboard, confidence scores, or AI summaries -- those endpoints only ever
returned pre-scanned tickers. Fixed by adding `ScannerService.ensure_scanned`,
which scans a ticker on demand the first time it's needed, rather than
requiring it to be part of a batch-scanned universe. `UniverseLoader`'s
sample list still controls what gets ranked in "Top Opportunities" (a
curated, known set makes sense to rank), but it no longer gates what
tickers a user can actually track.

All 5 milestones from the original blueprint are built. Natural follow-ups,
roughly in order of likely value:

- **A real market data vendor** (Polygon, Alpaca, IEX, or similar) behind
  the existing `MarketDataProvider` interface — the biggest lever for making
  this a real product instead of a demo, since everything downstream
  (scanner, scoring, AI summaries, dashboard) already works against
  whatever the provider returns.
- **A background scheduler** so the scanner runs automatically every
  morning instead of needing a manual "Run scanner" click (the product
  brief's "morning briefing" framing implies this).
- **Real S&P 500 / Nasdaq 100 / Russell 1000 / ETF membership lists**
  instead of the curated ~35-ticker sample universe.
- **Backtesting** (mentioned in the original product brief as a future
  differentiator) — validating the confidence engine's weights against
  historical evidence rather than just today's snapshot.
- **Portfolio-aware recommendations** — the brief's "portfolio intelligence"
  concept, weighing a new pick against what a user already holds rather
  than scoring each ticker in isolation.
- Visual/UX polish on the dashboard — the current UI is functional but was
  built quickly to validate the data layer; worth a real design pass now
  that all the underlying data is real.
