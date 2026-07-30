# STROMEX MVP — ARCHITECTURE & ENGINEERING NOTES

*Governed by the STROMEX EDITORIAL BIBLE. This document records what was actually built, run, and verified during the MVP execution pass — not a plan, a build log.*

---

## System Overview

```
apps/web (Next.js 15, TypeScript, Tailwind)
    │  fetch, JWT bearer auth
    ▼
apps/api (FastAPI, Python 3.11)
    │
    ├── Postgres — system of record: users, conversations, messages,
    │              memory metadata, Qur'an plans/revision items/review logs,
    │              books/chapters, audit logs
    ├── Redis    — rate limiting (fixed-window)
    └── Qdrant   — memory embeddings only (Postgres holds everything
                    list/edit/delete-able; Qdrant holds just the vector,
                    keyed by the same id)
```

Ten MVP modules were built, per the execution order, none stubbed:
Authentication, Chat Interface, Conversation History, Memory System,
Multi-Model Routing Engine, Qur'an Tutor, Arabic-English Assistant (a
conversation mode + system prompt, not a separate service), PDF Export, Book
Writing Workspace, Admin Dashboard.

## Key Engineering Decisions

**Enum columns store `.value`, not the Python member name.** SQLAlchemy's
default `Enum(SomePyEnum)` persists the member *name* ("ADMIN") rather than
its `.value` ("admin"), which silently diverges from what the API serializes
over JSON. `app/db/enum_utils.py::pg_enum` fixes this once, used by every
enum column. Caught by hand-testing the admin-promotion flow with raw SQL —
worth documenting because it is exactly the kind of bug that looks fine until
someone queries the database directly.

**Password hashing calls `bcrypt` directly, not `passlib`.** `passlib`'s
`CryptContext` runs a one-time backend self-test (`detect_wrap_bug`) that
crashes against `bcrypt>=4.1`'s stricter 72-byte input enforcement — a real
compatibility break in the currently-published versions, hit and fixed during
this build. `app/core/security.py` truncates to 72 bytes explicitly and calls
`bcrypt.hashpw`/`checkpw` directly.

**The routing engine is a static table, not a model call.** Each
`ConversationMode` maps to an ordered provider chain (e.g. `research` →
`perplexity, claude, openai`). The engine tries each provider in order,
catches `ProviderError`, and fails over automatically — verified with fake
providers in `app/tests/test_router.py` (preferred-provider selection,
failover on error, skip-when-unconfigured, force-override, total-failure).
This keeps routing behavior deterministic and auditable rather than another
model's judgment call.

**Memory embeddings degrade gracefully without an API key.** If
`OPENAI_API_KEY` is set, memory search uses real `text-embedding-3-small`
vectors. If not, `app/services/embeddings.py::HashingEmbeddingProvider` uses
deterministic feature-hashing (Weinberger et al.) — a real, if lower-recall,
embedding technique, not a placeholder. Verified in `test_memory.py`: a query
about "the book the user is writing" correctly ranks a book-related memory
above an unrelated one using only the hashing fallback.

**SM-2 spaced repetition, not a bespoke scheduler.** `app/services/
spaced_repetition.py` implements the SuperMemo-2 algorithm (Wozniak, 1987)
as pure functions — quality below 3 resets repetitions and interval to
force re-drilling, ease factor has a 1.3 floor, interval grows
geometrically on success. Exhaustively unit-tested independent of the
database.

**PDF export embeds real brand fonts, not system fonts.** `app/services/
pdf_service.py` renders books with WeasyPrint using Fraunces/Archivo/Amiri/
Cairo loaded from local `.woff2` files — verified by actually rendering a
bilingual (English + Arabic) test book and visually inspecting the output
pages, including correct RTL shaping for Amiri/Cairo. The alternative (system
fonts) would have produced incorrect or missing Arabic glyphs depending on
the host, which is precisely the failure mode a bilingual product cannot
ship with.

## What Was Actually Run (not just written)

- Real local Postgres 16 + Redis, real Alembic migration generated and
  applied, schema inspected directly with `psql`.
- Full backend test suite: **30/30 passing** against the real database (unit
  tests for auth/SM-2/routing with fakes, integration tests through the real
  FastAPI app + TestClient + in-memory Qdrant).
- Live `curl` smoke test of every MVP endpoint: register → login → chat
  (routed to the dev-echo fallback, since no provider keys are configured in
  this environment) → conversation history → memory create/search → Qur'an
  plan creation → due-item scheduling → review submission → analytics →
  book creation → chapter authoring → PDF export → admin overview/user list.
- Frontend: `tsc --noEmit` clean, `next build` clean (after bumping
  `next` from a version with a disclosed critical DoS CVE to a patched 15.5.x
  release, and pinning `postcss`/`sharp` overrides to close two more
  transitive advisories nested inside Next's own dependency tree).
- Full browser-driven end-to-end pass with Playwright: register → chat
  (message sent, routed reply rendered with provider/model badge) → Qur'an
  plan created and correctly chunked into revision items → book created,
  chapter authored, **PDF actually downloaded through the browser and
  visually verified**, including the Arabic-capable font pipeline.
- One real bug found and fixed via that browser pass: `Input` components in
  the Qur'an and Books forms were missing `id` props (label `htmlFor` wasn't
  wired to anything) — cosmetically invisible, a real accessibility and
  test-automation defect, fixed in both files.

## What Was Not Run (and why)

- **No live traffic against Claude, OpenAI, DeepSeek, or Perplexity** — no
  API keys were available in this environment. The provider clients
  (`app/services/llm/claude_provider.py`, `openai_compatible.py`) call the
  real SDKs and are exercised by the routing engine's unit tests via fakes,
  but a real credential is required to confirm an actual model response
  end-to-end.
- **No Docker Compose run** — the sandbox has no Docker daemon. Postgres and
  Redis were run as native local services instead (equivalent schema/query
  behavior); the `docker-compose.yml` and Dockerfiles are written but their
  build was not executed here.
- **No Cloudflare/VPS deployment** — see `infra/DEPLOYMENT.md`, written as a
  runbook, not executed.
