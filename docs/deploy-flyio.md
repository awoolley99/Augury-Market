# Deploying to Fly.io

Two separate Fly apps: `augury-market-api` (FastAPI + Postgres) and
`augury-market-web` (Next.js). Run these from your own machine — I can't
reach Fly's API from my sandbox, so this part is on you, but every command
below is copy-paste-ready.

## 0. Prerequisites

```bash
curl -L https://fly.io/install.sh | sh
fly auth login
```

## 1. Create a Postgres cluster

```bash
fly postgres create --name augury-market-db --region iad --initial-cluster-size 1 --vm-size shared-cpu-1x --volume-size 3
```
Note the connection string it prints — you'll attach it to the API app next.

## 2. Deploy the API

```bash
cd apps/api
fly launch --no-deploy --name augury-market-api --region iad --copy-config
fly postgres attach augury-market-db -a augury-market-api
```
`postgres attach` sets a `DATABASE_URL` secret automatically, but it's the
sync/psycopg2-style URL — set the async one explicitly too:

```bash
fly secrets set \
  SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')" \
  CORS_ORIGINS_RAW="https://augury-market-web.fly.dev" \
  -a augury-market-api

# Fly's attach sets DATABASE_URL like postgres://... — convert it to the
# asyncpg-style URL our app expects:
fly ssh console -a augury-market-api -C "printenv DATABASE_URL"
# Take that value, replace postgres:// with postgresql+asyncpg://, then:
fly secrets set DATABASE_URL="postgresql+asyncpg://...(converted)..." -a augury-market-api
fly secrets set DATABASE_URL_SYNC="postgresql+psycopg2://...(original)..." -a augury-market-api
```

```bash
fly deploy -a augury-market-api
```

Migrations run automatically on boot (see the `command:` in
`docker-compose.yml` — for Fly, add a release command instead so it runs
once per deploy, not per machine start):

```bash
fly deploy -a augury-market-api --release-command "alembic upgrade head"
```

Verify:
```bash
curl https://augury-market-api.fly.dev/health
```

## 3. Deploy the web frontend

```bash
cd ../web
fly launch --no-deploy --name augury-market-web --region iad --copy-config
fly deploy -a augury-market-web
```

The `fly.toml` in `apps/web` already points `NEXT_PUBLIC_API_URL` at
`https://augury-market-api.fly.dev/api/v1` as a build arg — update that
value first if you named the API app something else.

Verify:
```bash
open https://augury-market-web.fly.dev/login
```

## 4. Day-two operations

```bash
fly logs -a augury-market-api      # tail API logs
fly logs -a augury-market-web      # tail web logs
fly ssh console -a augury-market-api   # shell into the API machine
fly postgres connect -a augury-market-db  # psql into the DB
```
