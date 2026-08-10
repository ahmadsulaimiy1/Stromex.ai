# EdirasX Progress

**The resumption document.** A session that picks this up cold should be able to
continue without re-deriving anything. Consolidated from the nine state files
the brief specified — see `EDTECHX_DECISIONS.md` ADR-015 for why three files
beat nine.

**Last updated:** session 5
**Current phase:** Phase 1 complete · Phase 2 in progress

---

## Current state in one paragraph

The eleven governing documents exist and are internally consistent. EdirasX is
placed in its own namespace (`docs/edtechx/`, `apps/edtechx-api/`) leaving
StromeX untouched. Phase 1 — the isolation spine — is built and tested against
real PostgreSQL: three-layer tenant isolation with `FORCE ROW LEVEL SECURITY`
proven load-bearing, host-based tenant resolution with a token/host agreement
check, an additive permission catalogue with ABAC scopes, eleven system role
templates, append-only audit, Argon2id credentials, and a FastAPI request
lifecycle that enforces all of it. Phase 2 has since added the universal
academic engine (ADR-024) and the people-and-enrolment model (ADR-027), and a
cross-tenant *reference* hole in the isolation spine has been found and closed
(ADR-026), and bulk import lands whole or not at all (ADR-028). 387 tests pass;
ruff is clean. Nothing is stubbed or faked. Scope predicate compilation and the
entitlement engine remain in Phase 2.

---

## Completed

### Phase 0 — Constitution ✅
- Repository and environment inspected; PostgreSQL 16, Python 3.11, Node 22 confirmed available.
- Placement decision made and recorded (ADR-001): EdirasX in its own namespace; StromeX untouched.
- Eleven governing documents written: Editorial Bible, Product Spec, UX Principles, Design System, Architecture, Database, Security, Permission Model, AI Architecture, Billing, Customization Engine.
- Roadmap, decision record, and this progress system established.

### Phase 1 — Isolation spine ✅

| Area | What was built |
|---|---|
| Configuration | `Settings` with two database URLs; production guard that **refuses to boot** on a default secret, debug mode, localhost database, plaintext CORS, or a shared migration role |
| Context | `ContextVar`-based tenant/principal/request-id context; tenant-scoped work cannot run without a tenant established |
| Tenant isolation L1 | Host → tenant resolution; token `tid` checked against host tenant; mismatch → 403 + critical security event |
| Tenant isolation L2 | `ENABLE` + **`FORCE` ROW LEVEL SECURITY** on every tenant-owned table, policy on `current_setting('app.tenant_id')`; app role holds no `BYPASSRLS` and owns no tables; applied idempotently and verified |
| Tenant isolation L3 | SQLAlchemy `after_begin` re-applies the setting per transaction; `do_orm_execute` filters selects; `before_flush` stamps `tenant_id` and refuses foreign ones |
| Registry | `TenantOwned.__init_subclass__` registers models, driving policy emission *and* test generation from one marker |
| Identity | Global `User`, tenant-scoped `Membership`, `UserSession` (refresh family with rotation lineage and revocation) |
| Authorization | ~150-permission catalogue validated at boot; `manage`/wildcard expansion; 9 scope kinds with union semantics; 11 system role templates |
| Audit | `AuditEvent` (tenant-owned, append-only — `UPDATE`/`DELETE` revoked from the app role) and `SecurityEvent` (platform-level, so pre-auth events are recordable) |
| Credentials | Argon2id; bcrypt accepted on import and flagged for rehash; timing-equalized verification; keyed-hash refresh tokens; elevation window |
| HTTP | Request-id + structured access logging, strict CSP and security headers, body-size limit, error taxonomy that maps missing-permission→403 and out-of-scope→404 |
| Request lifecycle | Steps 2/4/5/6/8 of Architecture §5 enforced as FastAPI dependencies |

### Verification performed

| Claim | How it was proven |
|---|---|
| RLS is load-bearing, not decorative | Disabled the policy on `roles` and re-ran a stranger-context query: **32 rows leaked**. Re-enabled: **0 rows**. The ORM guard alone did not catch the raw-SQL path — which is exactly the point of layer 2 |
| Isolation coverage cannot rot | Cases generated from the model registry; 8 tenant-owned models × 2 generated checks, plus targeted write/update/delete/IDOR cases |
| Route coverage check works | Added a deliberately unguarded route; the check flagged `GET /api/v1/leaky` and nothing else |
| Module boundaries hold | Boundary test caught a real reverse dependency (identity → authz) introduced mid-session; fixed by removing the back-reference. **Exception list is now empty** |
| Production guard works | Five separate misconfigurations each refuse to construct `Settings` |

### Test suite — 152 passing, 0 failing, 0 skipped (with PostgreSQL available)

| Suite | Tests | Covers |
|---|---|---|
| `test_tenant_isolation.py` | 23 | Journey 12; generated per model; forced-policy audit; append-only audit log |
| `test_authz.py` | 23 | Catalogue integrity, expansion leaks, role restraint, scope parsing |
| `test_security.py` | 22 | Hashing, token forgery/expiry/type-confusion, production guard |
| `test_tenant_resolution.py` | 21 | Host normalization, subdomain rules, custom-domain verification, suspension |
| `test_boundaries.py` | 16 | Module imports, core layering, provider-SDK confinement, route coverage |
| `test_api.py` | 16 | Full lifecycle: host → auth → tenant agreement → permission → response |
| `test_auth.py` | 24 | Provisioning, sign-in uniformity, lockout, rotation, reuse detection, sign-out, audit |
| `test_rate_limit.py` | 22 | Atomicity under concurrency, tenant scoping, oracle resistance, fail-closed — on both backends |
| `test_migrations.py` | 5 | Upgrade, RLS gate, model drift, full downgrade → upgrade cycle |
| `test_mfa.py` | 20 | RFC 6238 vectors, drift window, replay rejection, encryption at rest, challenge scoping, recovery-code spending |
| `test_universal_education.py` | 45 | **The flexibility promise, widened to the whole continuum.** Nine institutions from nursery to doctoral research through one code path; two static checks proving no special-case code |

**Session liveness.** Every authenticated request now checks that its session
is live, so sign-out takes effect immediately rather than at token expiry, and
a correctly-signed token naming a session the product has no record of is
refused. Done as a database check rather than a Redis denylist: the state
already exists and is already authoritative, so a second source of truth could
only disagree with it. The API tests were tightened as a result — they now sign
in for real instead of hand-minting tokens.

---

## Phase 2 — completed so far

**Tenant provisioning** (`modules/tenancy/service.py`). Creates tenant, domain,
system roles, owner account and membership, with an audit entry. Slug
validation with a reserved list. A school is created `provisioning` and only
flipped to `active` once complete, so a half-built school never resolves for
traffic; a failure leaves it suspended rather than reachable. An existing
account is reused across schools and its password is never touched. The test
fixtures now provision through this service, so they exercise the same path
production does.

**Authentication** (`modules/identity/service.py`, `api/v1/auth.py`).
Sign-in, refresh, sign-out, sign-out-everywhere. Every failure path returns an
identical 401 and performs a password verification even when no password could
match, so neither response nor timing distinguishes unknown account from wrong
password from *not a member of this school*. Failure counting and lockout on
the user row. Refresh tokens rotate on every use with reuse detection that
revokes the whole family.

**Service layers** for `audit` and `authz`, so provisioning orchestrates
through services rather than reaching into other modules' models — the module
boundary test caught this and the architecture was fixed rather than the test
weakened. Its exception list is still empty.

### Bugs found and fixed this session

| Bug | Why it mattered |
|---|---|
| Reuse detection revoked the token family on the request's session, then the 401 rolled it back | Detection would have fired, logged, and changed nothing in production |
| `EmailStr` on sign-in returned 422 for a malformed address | Distinguished "malformed" from "wrong" — the enumeration leak the uniform 401 exists to close. Sign-in now takes a bounded string; strict validation belongs on registration |
| Slug pattern admitted a single character despite promising 2–63 | Minor, but the docstring and the code disagreed |

---

### Session 3 — migrations and rate limiting

**Alembic baseline** (ADR-020). Migrations connect as `edtechx_migrator`, with
the URL read from settings so a config edit cannot point one at the
request-path role. The baseline applies RLS, grants the app role, then
**verifies** and raises if any tenant-owned table is unprotected. Five tests
cover it, including a full downgrade → upgrade cycle and an autogenerate drift
check that fails if a model changes without a migration.

Found immediately: autogenerate creates enum types with their tables and never
drops them, so downgrade-then-upgrade failed on "type already exists" — exactly
what an incident rollback does. The down path now drops them explicitly.

**Rate limiting** (ADR-019). Token bucket, atomic, tenant-scoped, failing
closed. Redis via a Lua script that reads its own clock; an in-process backend
for development that is refused in production. Applied to sign-in (per IP, per
submitted account, per tenant) and refresh (per IP), after tenant resolution and
before authentication.

Verified adversarially: 60 concurrent requests for 10 tokens admit exactly 10 on
both backends, while a deliberately racy backend admits all 60 — so the test is
load-bearing. Tenant scoping proven both at the key level and end to end through
HTTP. The per-account limit is keyed on the *submitted* address, so a 429 cannot
distinguish a real account from an invented one; the test compares both
responses byte for byte.

The per-IP limits are deliberately generous because a school is one NATed
address with several hundred sign-ins before first lesson. The reasoning is in
ADR-019 so it is not later mistaken for carelessness.

---

### Session 5 — people, enrolment, and a hole in the isolation spine

**People** (`modules/people/`). Four layers kept apart (ADR-027): the global
`User` credential, the tenant-owned `Person`, three relationship tables
(student, staff, guardian), and `enrolments`. A person may have no identity at
all — most do not — and one person may be a teacher, a parent and a learner at
once as a single row. Guardianships are person to person, with a free-text
`relationship_label`, because family structures are not a closed list.

**Enrolment as history.** Placement is a row with a beginning and an end. The
service has no function that moves a student: `transfer` and `progress` close
one placement and open another, and the closed row keeps the class group it
always had. `enrolment_events` is the append-only ledger of why each transition
happened, protected by the same grant discipline as the audit log. Admission,
enrolment, transfer, suspension, resumption, withdrawal, readmission,
progression, completion and awarding are all implemented and all tested.

Fifty-one tests run this against **all nine institutions** of the Universal
Education Test through one code path, asserting that the layers each institution
did not configure stay null.

**A real defect, found by attacking rather than by reading.** Row-level security
does not govern foreign-key checks — PostgreSQL performs them with the
referenced table's privileges and without its policies. One tenant could
therefore insert a row referencing another tenant's row. Demonstrated, then
fixed structurally: every foreign key between tenant-owned tables now references
`(tenant_id, id)`, applied to the whole metadata by
`app.db.tenant_fk.bind_foreign_keys_to_tenant` so a new model gets it by
existing (ADR-026). 46 constraints converted; the migration does it in place and
round-trips.

The serious part was not the corrupt row but the oracle: the insert succeeded
only if the id existed *somewhere*, which made every foreign key a probe for
other tenants' ids — the disclosure ADR-004 exists to prevent, arriving through
the one door RLS does not watch. Every isolation test was green before and
after, because all of them tested reading and writing rows and none tested
referring to one.

**Five sabotages, all caught.** The tenant-scoped foreign keys, the ledger's
immutability, the no-placement-column rule, and the no-overwrite rule were each
broken once to confirm the tests notice. One finding worth keeping: the
*generated* append-only test cannot catch a table being removed from the list it
is generated from, which is why `enrolment_events` is also named explicitly in a
second test.

**Bulk import** (`modules/imports/`). CSV and XLSX, read without interpreting:
every value comes back as text, because a leading zero on an admission number is
data and not a formatting accident. Column mapping is *proposed* from the
institution's own configured vocabulary and corrected by the person — so a
school that calls a class an "arm" gets a column headed "Arm" recognised, while
no country's vocabulary appears anywhere in the product. Validation reports
every problem in the file at once, per row, with the file's own line numbers.

Applying is one transaction: an import with any invalid row is refused outright,
and an unexpected failure part way through rolls the whole thing back. The dry
run is the same code path inside a savepoint. Reversal exists and *refuses* when
work has been built on the import, rather than choosing between two kinds of
damage on its own.

Thirty-four tests, built from the files schools actually send — a byte-order
mark, semicolons, a title row, a repeated heading, `4512.0` where an admission
number should be, a phone number starting `+`. Three sabotages caught.

---

## Next — Phase 2 remainder

In priority order. Each carries the Bible's Definition of Done.

1. ~~**Academic structure**~~ — **done**. Stages, levels, years, terms, subjects, class groups, grading scales and bands, progression rule engine, terminology. The Four Schools acceptance test passes (ADR-022).
2. ~~**People**~~ — **done**. Identity, person, and student/staff/guardian relationships kept properly separate; one person holds several relationships without a duplicated identity (ADR-027).
3. ~~**Enrolment as history**~~ — **done**. Admission, enrolment, transfer, suspension, withdrawal, readmission, progression, completion, awarding. No `student.class_id`; records are added, never overwritten, and two structural tests fail the commit that reintroduces one.
4. ~~**Bulk import**~~ — **done**. Preview, column mapping, validation, duplicate detection, dry run, single-transaction apply, refusing reversal, history, audit (ADR-028).
5. **Scope predicate compilation** — `taught_by_self`, `own_children`, `department` as SQL predicates applied to list queries, with leak-by-row-count tests.
6. **Entitlement engine** — kept distinct from permission, role, plan, feature availability, usage limit and institution configuration. Being authorized to act is not the same as the institution having purchased the capability.

---

## Blocked

Nothing is blocked. Items awaiting external input, none of which stop Phase 2:

| Item | Needs | Interim |
|---|---|---|
| Real AI provider calls | Provider API keys | Gateway + adapters are Phase 5; a deterministic development provider is specified and refuses to load in production |
| Real payment capture | Paystack/Flutterwave/Stripe credentials | Payment port + sandbox adapter driving the real state machine (Phase 3) |
| Email and SMS delivery | SMTP / provider credentials | Notification port + outbox adapter (Phase 3) |
| Custom domain TLS | Deployment environment | Verification model exists; unverified domains already refuse to resolve |
| Pilot data | A partner school | Phase 9 |

---

## Known issues

| # | Issue | Severity | Plan |
|---|---|---|---|
| 1 | ~~Schema created by `build_schema()`, not by a migration~~ | — | **Resolved** — Alembic baseline with an RLS gate (ADR-020) |
| 2 | ~~Sign-out left the access token valid until expiry~~ | — | **Resolved** — every request checks that its session is live. A token naming a session that does not exist, or one that was revoked or rotated away, is refused |
| 3 | Scopes are parsed and unioned but not yet compiled to SQL predicates | Medium | Next Phase 2 item. No route currently returns scoped lists, so nothing is under-enforced today |
| 4 | `starlette.testclient` deprecation warning from FastAPI 0.141 | Trivial | Upstream; revisit on the next FastAPI bump |
| 5 | `_IncludedRouter` traversal in `test_boundaries.py` reaches into a FastAPI internal | Low | Written to accept both routing shapes so it degrades to the public shape rather than silently checking nothing |
| 6 | No frontend yet | Expected | Phase 4 |

---

## Working notes for the next session

- **Start here:** `apps/edtechx-api/README.md`, then this file, then `EDTECHX_ROADMAP.md` Phase 2.
- **Environment:** PostgreSQL must be running (`service postgresql start`). Roles and databases are created by the block in the API README. Without them, integration tests skip — and a skipped isolation suite proves nothing.
- **Before writing any model:** if it belongs to a school, it inherits `TenantOwned`. That single decision gets it a policy and an isolation test automatically. If it does *not*, write down why, as `Tenant`, `TenantDomain`, `User`, and `SecurityEvent` each do in their docstrings.
- **Before adding a route:** give it a `RequirePermission` dependency, or add it to `PUBLIC_ROUTES` in `test_boundaries.py`. There is no third option.
- **Before adding a foreign key between two tenant-owned tables:** nothing. It is rewritten to `(tenant_id, id)` automatically by `app.db.tenant_fk`, and a test fails if any key escapes. Do not add a plain single-column key back "because the composite one is awkward to query" — that is the defect ADR-026 records.
- **Before recording where somebody is:** it is an `Enrolment` row with a start and an end, never a column on a person or a relationship. If a screen needs "the current class", ask for the open enrolment. Two tests exist specifically to fail the shortcut.
- **Before adding a permission:** add it to `CATALOGUE` first. Roles referencing unknown permissions fail the boot.
- **Never** connect the request path as `edtechx_migrator`. It owns the tables, and `FORCE RLS` is bypassed for owners. The production guard refuses this; development would not notice.
