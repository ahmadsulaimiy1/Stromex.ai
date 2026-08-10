# EdirasX Implementation Checklist

Tracks *what exists*, phase by phase. `EDTECHX_PROGRESS.md` carries the
narrative and the next actions; this is the inventory.

Legend: ✅ done · 🔨 in progress · ⬜ not started

---

## Phase 0 — Constitution ✅

- ✅ Repository and environment inspected
- ✅ Placement decision recorded (ADR-001)
- ✅ Editorial Bible · Product Spec · UX Principles · Design System
- ✅ Architecture · Database · Security · Permission Model
- ✅ AI Architecture · Billing · Customization Engine
- ✅ Roadmap · Decisions · Progress · Tests · Runbook · Checklist

## Phase 1 — Isolation spine ✅

**Foundation**
- ✅ Project skeleton and module layout
- ✅ Configuration with production boot guard
- ✅ Structured logging with request correlation
- ✅ Error taxonomy (403 permission / 404 scope / 402 entitlement)
- ✅ Security headers, strict CSP, body-size limit
- ✅ Redis-backed rate limiting, atomic and tenant-scoped
- ✅ Session liveness checked per request (sign-out is immediate)

**Tenancy**
- ✅ `tenants`, `tenant_domains`
- ✅ Host resolution: subdomain, custom domain, platform host
- ✅ Custom-domain verification gate
- ✅ Suspended/archived schools fail closed
- ✅ Token/host agreement check with security event
- ✅ Provisioning service — real, audited, and now driving the test fixtures

**Isolation**
- ✅ `TenantOwned` marker driving column, policy, and test generation
- ✅ `ENABLE` + `FORCE ROW LEVEL SECURITY` on every tenant-owned table
- ✅ Application role without `BYPASSRLS`, owning no tables
- ✅ Per-transaction tenant setting (re-applied on every begin)
- ✅ ORM insert stamping and select filtering
- ✅ RLS verification helper, run at schema build
- ✅ Generated isolation suite over the model registry
- ✅ **Tenant-scoped foreign keys** — `(tenant_id, id)`, closing the hole RLS
  does not cover (ADR-026)
- ✅ Append-only grants over `audit_events`, `security_events`,
  `enrolment_events`; no `DELETE` on `enrolments`
- ✅ **Proven load-bearing by sabotage** (32 rows leaked with RLS off; a
  cross-tenant reference succeeded before the foreign keys were scoped)
- ⬜ Cache and storage key prefixing — with the first cache and first upload
- ⬜ Background-job tenant envelope — with the first job

**Identity**
- ✅ Global `User`; tenant-scoped `Membership`; `UserSession`
- ✅ Argon2id, bcrypt import path, timing-equalized verification
- ✅ Access tokens with `tid`/`mid`; keyed-hash refresh tokens
- ✅ Elevation window for high-risk actions
- ✅ Sign-in / refresh / sign-out / sign-out-everywhere endpoints
- ✅ Refresh rotation with reuse detection, revoking the whole family
- ✅ Lockout enforcement
- ✅ TOTP MFA (enrolment, activation, challenge, recovery codes, replay rejection) · ⬜ SSO

**Authorization**
- ✅ Permission catalogue validated at boot
- ✅ `manage` and wildcard expansion, without cross-resource leakage
- ✅ Nine scope kinds with union semantics
- ✅ Eleven system role templates
- ✅ `RequirePermission` dependency
- ✅ Scope → SQL predicate compilation, per permission, failing closed (ADR-029)
- ⬜ Delegation ceiling · ⬜ Dual control · ⬜ Sensitive-field redaction

**Audit**
- ✅ `audit_events` (append-only; `UPDATE`/`DELETE` revoked from the app role)
- ✅ `security_events` (platform-level, so pre-auth events are recordable)
- ✅ Denials recorded
- ✅ Audit service (`audit.service.record`) — every module writes through it, no model imports cross boundaries

**Quality gates**
- ✅ Module boundary test — **exception list empty**
- ✅ Core-layering test
- ✅ Provider-SDK confinement test
- ✅ Route coverage test — **proven load-bearing**
- ✅ 534 tests passing; ruff clean
- ✅ Alembic baseline migration with an RLS gate · ⬜ CI pipeline

## Phase 2 — Institution 🔨

✅ Alembic baseline · ✅ provisioning service · ✅ auth endpoints · ✅ rate
limiting · ✅ TOTP MFA · ✅ stages, levels, years, terms · ✅ class groups and
subjects · ✅ grading scales and bands · ✅ progression rule engine · ✅
terminology configuration · ✅ **the Universal Education acceptance suite** ·
✅ academic units · ✅ programmes · ✅ qualifications · ✅ credit systems ·
✅ cohorts · ✅ supervision roles and milestone definitions · ✅ **people,
relationships, and enrolment history** · ✅ guardianships · ✅ staff
relationships · ✅ qualification awards · ✅ the people-and-enrolment
acceptance suite across all nine institutions

✅ **bulk import** — CSV and XLSX, column mapping proposed from the
institution's own vocabulary, per-row validation, duplicate detection, dry run,
single-transaction apply, refusing reversal, import history and audit ·
✅ journey 11

✅ **scope predicate compilation** — every scope kind compiled to SQL, resolved
per permission, leak-tested through counts, totals, search, aggregates and error
shape · ✅ teaching allocations · ✅ the first scoped endpoints

✅ **entitlement engine** — plans, subscriptions, overrides, institution
settings, limits, meters and usage, with permission and entitlement kept
strictly apart (ADR-030)

⬜ custom fields · ⬜ journey 9.

## Phase 3 — Operations ⬜

Attendance (configurable model, school-defined codes, corrections, absence
workflow) · assessment and results with an explicit publish step · report cards ·
announcements and the notification port · fees, invoices, payments, receipts,
money invariants · payment port with sandbox adapter · journeys 1, 4, 5, 6, 7.

## Phase 4 — Experience 🔨

✅ **Contextual complexity resolution** — one call returns this person's world:
only what the institution uses, only what they may see, only what the plan
includes, ordered by what they came to do (ADR-031) · ✅ capability catalogue ·
✅ role shapes · ✅ interface profiles and user preferences · ✅ zero-state
intelligence · ✅ **the UX acceptance test** — nursery ≠ secondary ≠ university
≠ doctoral, four distinct experiences from one deployment

⬜ design-system implementation · ⬜ app shell · ⬜ persona dashboards ·
⬜ teacher attendance under 30 seconds · ⬜ theme resolution · ⬜ PWA and
offline queue · ⬜ accessibility pass · ⬜ performance budgets.

Design-system implementation · app shell · six persona dashboards · teacher
attendance under 30 seconds · theme resolution and per-tenant stylesheet · PWA
and offline attendance queue · accessibility pass · performance budgets.

## Phase 5 — Intelligence ⬜

AI Gateway · provider adapters · routing, fallback, circuit breaker · metering
and quotas · **approval gate with a bypass-attempt test** · prompt registry ·
first assistants · BYO keys · SSRF egress guard.

## Phase 6 — Learning ⬜

Courses, modules, lessons, resources · assignments and submissions · rubrics and
gradebook · quizzes and question banks · completion, paths, prerequisites ·
cohorts, groups, discussions, certificates · journeys 2 and 3.

## Phase 7 — Studios ⬜

Design Studio · AI Design Studio · document designer · navigation and dashboard
editors · journeys 8 and 10.

## Phase 8 — Scale ⬜

Admissions · timetabling · conduct · operator console and break-glass · custom
domains with TLS · SSO · analytics · restore drills · penetration test.

## Phase 9 — Pilot ⬜

One real school, real devices, real networks, instrumented.

---

## Standing gates — every feature, every phase

- [ ] All thirteen Definition-of-Done items (`EDTECHX_EDITORIAL_BIBLE.md` §11)
- [ ] Tenant-owned models inherit `TenantOwned`, or the exception is documented in the model
- [ ] Every route declares a permission or is listed in `PUBLIC_ROUTES`
- [ ] Authorization enforced server-side, with scope in the query
- [ ] Mutations audited
- [ ] All five view states implemented
- [ ] 360 / 768 / 1280 verified
- [ ] Keyboard and screen-reader path verified
- [ ] Terminology from tenant configuration, never a literal
- [ ] Blocking test suites green
