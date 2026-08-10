# EdirasX

> The education platform that becomes your school's own platform.

A multi-tenant education operating system — school information system and
learning management system in one — deeply customizable per institution, with an
AI assistance layer and a commercial platform underneath.

EdirasX lives in this repository alongside StromeX, in its own namespace
(`docs/edtechx/`, `apps/edtechx-*`), and is extractable to its own repository by
moving two directories. See `EDTECHX_DECISIONS.md` ADR-001.

---

## Read in this order

**1. The constitution**

| Document | What it settles |
|---|---|
| [`EDTECHX_EDITORIAL_BIBLE.md`](EDTECHX_EDITORIAL_BIBLE.md) | Brand, product philosophy, UX and visual philosophy, the six personas, the AI constitution, non-negotiables, definition of done. **Supreme — it wins over everything else here.** |
| [`EDTECHX_PRODUCT_SPEC.md`](EDTECHX_PRODUCT_SPEC.md) | Modules, LMS depth bar, per-persona information architecture, the twelve critical journeys |
| [`EDTECHX_ROADMAP.md`](EDTECHX_ROADMAP.md) | Ten phases, with the reasoning for the sequence |

**2. How it is built**

| Document | What it settles |
|---|---|
| [`EDTECHX_ARCHITECTURE.md`](EDTECHX_ARCHITECTURE.md) | Modular monolith, three-layer tenant isolation, request lifecycle, integration ports |
| [`EDTECHX_DATABASE.md`](EDTECHX_DATABASE.md) | Full schema, RLS policy, indexing, migration discipline |
| [`EDTECHX_SECURITY.md`](EDTECHX_SECURITY.md) | Threat model, authn/authz, SSRF guard, rate limits, audit, release gates |
| [`EDTECHX_PERMISSION_MODEL.md`](EDTECHX_PERMISSION_MODEL.md) | RBAC permissions + ABAC scopes compiled to SQL predicates |

**3. What makes it EdirasX**

| Document | What it settles |
|---|---|
| [`EDTECHX_CUSTOMIZATION_ENGINE.md`](EDTECHX_CUSTOMIZATION_ENGINE.md) | Versioned configuration documents, terminology, academic structure, Design Studio |
| [`EDTECHX_DESIGN_SYSTEM.md`](EDTECHX_DESIGN_SYSTEM.md) | Tenant-resolvable tokens, palette, type scale, spacing, motion, components |
| [`EDTECHX_UX_PRINCIPLES.md`](EDTECHX_UX_PRINCIPLES.md) | The rules a design review can fail against |
| [`EDTECHX_AI_ARCHITECTURE.md`](EDTECHX_AI_ARCHITECTURE.md) | Provider-agnostic gateway, BYO keys, the approval gate, AI Design Studio |
| [`EDTECHX_BILLING.md`](EDTECHX_BILLING.md) | Entitlement engine, plans as data, regional pricing, metering |

**4. Working state**

| Document | Purpose |
|---|---|
| [`EDTECHX_PROGRESS.md`](EDTECHX_PROGRESS.md) | **Start here to resume.** What is built, what is next, what is blocked |
| [`EDTECHX_CHECKLIST.md`](EDTECHX_CHECKLIST.md) | Phase-by-phase inventory |
| [`EDTECHX_TESTS.md`](EDTECHX_TESTS.md) | Test strategy and current status |
| [`EDTECHX_DECISIONS.md`](EDTECHX_DECISIONS.md) | Architecture decision record — every decision with its cost |
| [`EDTECHX_RUNBOOK.md`](EDTECHX_RUNBOOK.md) | Operational procedures |

---

## Code

[`apps/edtechx-api`](../../apps/edtechx-api) — FastAPI + SQLAlchemy + PostgreSQL.
Its README covers local setup and the isolation model.

---

## The four ideas that explain the rest

**1. It should feel like their school.** Not "we use EdirasX" but "this is our
school's digital environment". Every visual value, every navigation label, and
every domain noun is tenant-resolvable data. There is no per-tenant code.

**2. Isolation is structural, not conventional.** It cannot depend on a developer
remembering a `WHERE` clause. `FORCE ROW LEVEL SECURITY`, an application role
that owns nothing and bypasses nothing, and a test suite generated from the model
registry so new models are covered by existing.

**3. Nothing about a school is hard-coded.** Terms, levels, grading scales,
attendance codes, promotion rules, and vocabulary are data. The acceptance test
is the Bible's Four Schools test: four genuinely different institutional shapes,
zero code changes.

**4. AI assists; it never writes the record.** No AI-originated change to a
grade, attendance mark, invoice, or published result without a persisted proposal
and an attributed human approval — enforced in code, with a test that attempts
the bypass and must fail.
