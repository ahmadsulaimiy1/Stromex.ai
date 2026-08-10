# StromeX

StromeX is an AI Operating System for knowledge work — unifying learning, research, writing, design, and publishing behind one trusted, memory-bearing intelligence layer, with Arabic and Islamic scholarship engineered as first-class domains rather than an afterthought.

## Founding Documents

Every future decision in this repository — features, architecture, design, and process — derives from these three governing documents. Where any future work conflicts with them, these documents win until formally amended.

1. **[The StromeX Editorial Bible](docs/00-STROMEX-EDITORIAL-BIBLE.md)** — the strategic constitution and product philosophy manual: vision, product/user/intelligence philosophy, editorial standards, design philosophy, AI architecture philosophy, trust & safety constitution, and scalability constitution.
2. **[The StromeX Master Feature Atlas](docs/01-STROMEX-MASTER-FEATURE-ATLAS.md)** — the classified, scored inventory of features across all 14 product domains, including what was reviewed and rejected and why.
3. **[The StromeX 10-Year Master Roadmap](docs/02-STROMEX-10-YEAR-ROADMAP.md)** — the phased build plan (MVP → Growth → Platform → Ecosystem → Global Scale), including explicit non-goals per phase and the assumptions challenged along the way.

Read the Bible first. It is the supreme governing authority of the StromeX ecosystem.

## MVP Codebase

- **[`apps/api`](apps/api)** — FastAPI backend: auth, chat + multi-model routing (Claude/OpenAI/DeepSeek/Perplexity), memory (Postgres + Qdrant), Qur'an tutor (SM-2 spaced repetition), book writing + PDF export, admin dashboard.
- **[`apps/web`](apps/web)** — Next.js 15 + TypeScript + Tailwind frontend, styled with the StromeX brand system (Fraunces/Archivo/Amiri/Cairo, brass/verdigris/ink palette).
- **[`infra`](infra)** — Docker Compose for local development, `DEPLOYMENT.md` for the Cloudflare + VPS production topology.
- **[`docs/03-STROMEX-MVP-ARCHITECTURE.md`](docs/03-STROMEX-MVP-ARCHITECTURE.md)** — what was actually built, run, and verified vs. what's deferred pending real credentials/infra.
- **[`docs/04-STROMEX-INDEPENDENT-AUDIT.md`](docs/04-STROMEX-INDEPENDENT-AUDIT.md)** — the security/scalability/reliability/performance audit run against the MVP, including a critical SSRF vulnerability found, reproduced, and fixed; real benchmarks; and per-dimension grades.

Quickest way to run it locally is `apps/api/README.md` and `apps/web/README.md`, in that order.

---

## EdirasX

This repository also carries **[EdirasX](docs/edtechx/)** — a separate product, in its own namespace, sharing conventions but no code with StromeX.

> EdirasX: the education platform that becomes your school's own platform.

A multi-tenant education operating system (school information system + LMS in one), deeply customizable per institution, with a provider-agnostic AI layer and a commercial platform underneath.

- **[`docs/edtechx/`](docs/edtechx/)** — the governing documents. Start with the [Editorial Bible](docs/edtechx/EDTECHX_EDITORIAL_BIBLE.md), then [PROGRESS](docs/edtechx/EDTECHX_PROGRESS.md) to see current state.
- **[`apps/edtechx-api`](apps/edtechx-api)** — FastAPI backend. Phase 1 (the tenant isolation spine) is built and tested against real PostgreSQL.

EdirasX is deliberately extractable: moving `docs/edtechx/` and `apps/edtechx-*` to their own repository is the whole migration. See [ADR-001](docs/edtechx/EDTECHX_DECISIONS.md).
