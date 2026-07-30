# StromeX API

FastAPI backend for the StromeX MVP: auth, chat + multi-model routing, memory,
Qur'an tutor (SM-2 spaced repetition), book writing + PDF export, admin.

## Local development (no Docker)

Requires Python 3.11+, a running Postgres 16 instance, and Redis.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env   # edit DATABASE_URL/REDIS_URL if yours differ

alembic upgrade head
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive OpenAPI explorer.

## Running with Docker

See `../../infra/docker-compose.yml` — it wires Postgres, Redis, Qdrant, this
API, and the web app together, and runs migrations automatically on boot.

## Tests

```bash
source .venv/bin/activate
python -m pytest -q
```

Tests run against a real Postgres database (`DATABASE_URL` in
`app/tests/conftest.py` defaults to `stromex_test`) inside a transaction that
is rolled back after every test, and a real in-memory Qdrant instance per
test — nothing here is mocked at the database layer. Create the test database
once:

```bash
createdb -O stromex stromex_test
```

## Model providers

Every provider (Claude, OpenAI, DeepSeek, Perplexity) is optional. Set
whichever API keys you have in `.env`; the routing engine
(`app/services/llm/router.py`) skips unconfigured providers and fails over to
the next one in the chain automatically. With **no** keys set, in
`development`/`test` environments only, chat falls back to a clearly-labeled
`stromex-dev-echo` provider so the rest of the stack (auth, persistence,
memory, routing logic itself) is fully testable without any paid credentials.
That fallback is intentionally unavailable when `ENVIRONMENT=production`.

## What's real vs. what's deferred

- Real: JWT auth, Postgres schema + Alembic migrations, the routing engine's
  selection/failover logic, SM-2 spaced repetition, memory read/write against
  Qdrant, WeasyPrint PDF export with embedded brand fonts (verified with
  actual Arabic RTL content), rate limiting, admin endpoints, audit logging.
- Deferred (needs real credentials/infra this environment doesn't have):
  live traffic against Claude/OpenAI/DeepSeek/Perplexity, a managed Qdrant/
  Postgres/Redis deployment, and the actual Cloudflare + VPS rollout (see
  `../../infra/DEPLOYMENT.md`).
