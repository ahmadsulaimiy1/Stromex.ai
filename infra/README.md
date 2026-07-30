# StromeX Infra

`docker-compose.yml` runs the full MVP stack locally: Postgres, Redis,
Qdrant, the FastAPI backend, and the Next.js frontend.

```bash
cp ../apps/api/.env.example ../apps/api/.env   # first run only
cd infra
docker compose up --build
```

- Web: http://localhost:3000
- API: http://localhost:8000/docs
- Qdrant dashboard: http://localhost:6333/dashboard

The `api` container runs `alembic upgrade head` before starting, so the
schema is always current on boot. Data persists in the `postgres_data` and
`qdrant_data` named volumes between runs.

For the production topology (Cloudflare + VPS), see `DEPLOYMENT.md`.
