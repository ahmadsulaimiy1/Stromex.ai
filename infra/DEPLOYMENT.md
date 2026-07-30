# StromeX MVP Deployment — Cloudflare + VPS

This describes the target production topology per the execution order's
technology stack. It is written to be followed step by step; it has **not**
been executed in this build (no VPS or Cloudflare account credentials were
available), unlike everything under `apps/`, which was run and verified
directly.

## Topology

```
Browser
  │
  ▼
Cloudflare (DNS, TLS, CDN, WAF, DDoS protection)
  │
  ▼
VPS (Docker host)
  ├── nginx or Caddy reverse proxy (terminates from Cloudflare, routes by host)
  │     ├── stromex.ai            → web (Next.js, port 3000)
  │     └── api.stromex.ai        → api (FastAPI, port 8000)
  ├── postgres (or managed Postgres — see Scaling below)
  ├── redis
  └── qdrant
```

## Steps

1. **Provision the VPS.** Any provider with Docker support (4 vCPU / 8GB RAM
   is a reasonable MVP floor given Postgres + Redis + Qdrant + two app
   containers on one box). Install Docker + Docker Compose.

2. **DNS via Cloudflare.** Point `stromex.ai` and `api.stromex.ai` A/AAAA
   records at the VPS, proxied (orange-clouded) through Cloudflare for TLS
   termination, caching, and WAF rules. Set SSL/TLS mode to "Full (strict)"
   once the origin has its own certificate (Caddy/nginx + Let's Encrypt, or a
   Cloudflare Origin CA certificate).

3. **Secrets.** Populate `apps/api/.env` on the VPS from `.env.example` with
   real values — a freshly generated `SECRET_KEY` (never reuse the dev
   value), real Postgres credentials, and whichever LLM provider keys are
   available. Never commit this file; it should exist only on the VPS and in
   your secrets manager.

4. **Bring the stack up:**
   ```bash
   cd infra
   docker compose up -d --build
   ```
   The `api` service runs `alembic upgrade head` on boot before starting
   uvicorn, so schema migrations are applied automatically on every deploy.

5. **Reverse proxy.** Point your VPS-local nginx/Caddy at `web:3000` for the
   apex/`www` host and `api:8000` for `api.stromex.ai`, then let Cloudflare
   sit in front of that as described above. Set `CORS_ORIGINS` in the API's
   env to the real frontend origin(s) before going live — the default only
   allows `localhost:3000`.

   Also set a request body size limit here: `client_max_body_size` in nginx
   (or Caddy's equivalent), and Cloudflare has its own plan-dependent request
   size cap in front of that. The API has its own `MaxBodySizeMiddleware`
   (`app/core/middleware.py`, 2MB) as a second layer, but it only inspects
   `Content-Length` — a client using chunked transfer-encoding bypasses it
   entirely, so the reverse proxy is the layer that actually closes that gap.

6. **Admin bootstrap.** There is no public "become admin" endpoint by design
   (Bible Part VIII: least privilege). Promote the first admin directly:
   ```bash
   docker compose exec postgres psql -U stromex -d stromex \
     -c "UPDATE users SET role='admin' WHERE email='you@stromex.ai';"
   ```

## Scaling beyond the MVP (Bible Part IX)

- **100–1,000 users:** this single-VPS topology is sufficient.
- **10,000 users:** move Postgres and Redis to managed services (connection
  pooling and failover matter more than raw capacity at this point); keep
  Qdrant colocated unless query volume demands otherwise.
- **100,000+ users:** multi-region deployment, managed Qdrant cluster,
  dedicated read replicas for Postgres, and the rate-limiting/audit-logging
  already built into the API becomes load-bearing rather than precautionary.

## What was NOT done in this build

- No VPS was provisioned and nothing was actually deployed — this document
  is the runbook, not a deployment log.
- No Cloudflare zone was configured.
- No production secrets were generated or stored.
