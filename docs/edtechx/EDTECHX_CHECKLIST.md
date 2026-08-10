# EdTechX Implementation Checklist

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
- ⬜ Redis wiring (rate limits, token denylist) — Phase 2, with the endpoints it protects

**Tenancy**
- ✅ `tenants`, `tenant_domains`
- ✅ Host resolution: subdomain, custom domain, platform host
- ✅ Custom-domain verification gate
- ✅ Suspended/archived schools fail closed
- ✅ Token/host agreement check with security event
- ⬜ Provisioning service (logic exists in the test fixture; must become real)

**Isolation**
- ✅ `TenantOwned` marker driving column, policy, and test generation
- ✅ `ENABLE` + `FORCE ROW LEVEL SECURITY` on every tenant-owned table
- ✅ Application role without `BYPASSRLS`, owning no tables
- ✅ Per-transaction tenant setting (re-applied on every begin)
- ✅ ORM insert stamping and select filtering
- ✅ RLS verification helper, run at schema build
- ✅ Generated isolation suite over the model registry
- ✅ **Proven load-bearing by sabotage** (32 rows leaked with RLS off)
- ⬜ Cache and storage key prefixing — with the first cache and first upload
- ⬜ Background-job tenant envelope — with the first job

**Identity**
- ✅ Global `User`; tenant-scoped `Membership`; `UserSession`
- ✅ Argon2id, bcrypt import path, timing-equalized verification
- ✅ Access tokens with `tid`/`mid`; keyed-hash refresh tokens
- ✅ Elevation window for high-risk actions
- ⬜ Login / refresh / logout endpoints — Phase 2
- ⬜ Refresh rotation with reuse detection (modelled; endpoint pending)
- ⬜ Lockout enforcement (fields and config exist; enforcement pending)
- ⬜ TOTP MFA · ⬜ SSO

**Authorization**
- ✅ Permission catalogue validated at boot
- ✅ `manage` and wildcard expansion, without cross-resource leakage
- ✅ Nine scope kinds with union semantics
- ✅ Eleven system role templates
- ✅ `RequirePermission` dependency
- ⬜ Scope → SQL predicate compilation — Phase 2
- ⬜ Delegation ceiling · ⬜ Dual control · ⬜ Sensitive-field redaction

**Audit**
- ✅ `audit_events` (append-only; `UPDATE`/`DELETE` revoked from the app role)
- ✅ `security_events` (platform-level, so pre-auth events are recordable)
- ✅ Denials recorded
- ⬜ Audit-write helper on every mutation path — with the first mutations

**Quality gates**
- ✅ Module boundary test — **exception list empty**
- ✅ Core-layering test
- ✅ Provider-SDK confinement test
- ✅ Route coverage test — **proven load-bearing**
- ✅ 121 tests passing; ruff clean
- ⬜ CI pipeline · ⬜ Alembic baseline migration

## Phase 2 — Institution ⬜

Alembic baseline · provisioning service · auth endpoints · rate limiting ·
stages, levels, years, terms · class groups, subjects, allocations · grading
scales and bands · students, enrolments, guardians · custom fields · bulk import
with dry-run · terminology configuration · entitlement engine · scope predicates
· **the Four Schools acceptance fixture** · journeys 9 and 11.

## Phase 3 — Operations ⬜

Attendance (configurable model, school-defined codes, corrections, absence
workflow) · assessment and results with an explicit publish step · report cards ·
announcements and the notification port · fees, invoices, payments, receipts,
money invariants · payment port with sandbox adapter · journeys 1, 4, 5, 6, 7.

## Phase 4 — Experience ⬜

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
