# EdirasX Progress

**The resumption document.** A session that picks this up cold should be able to
continue without re-deriving anything. Consolidated from the nine state files
the brief specified — see `EDTECHX_DECISIONS.md` ADR-015 for why three files
beat nine.

**Last updated:** session 7
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
(ADR-026), bulk import lands whole or not at all (ADR-028), and scopes now
compile to SQL predicates resolved per permission and failing closed (ADR-029).
Entitlement is separated from authorization in both directions (ADR-030), and
the experience layer now resolves each institution's world from its own
configuration so a nursery never meets the academic engine (ADR-031), and
Phase 3 has begun with attendance — journey 1, end to end, in three requests
(ADR-032), assessment and results now carry a real academic-record
lifecycle with snapshot publication (ADR-033), and the configurable academic
document engine issues report cards, transcripts, certificates and statements
from one machine while guaranteeing that a document says what it said (ADR-034).
(ADR-034), and Phase 4 has established the EdirasX visual identity — a royal
institution rendered by a precision instrument, with the Arabic geometric seal
whose central void is the X, tokens an institution can retheme, guardrails that
refuse to let it ruin its own readability, and a configuration-aware shell
rendered from four real institutions (ADR-035). 760 tests pass; ruff is clean.
Nothing is stubbed or faked.

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

**Scope predicate compilation** (`modules/authz/predicates.py`,
`modules/people/scopes.py`). Scopes are compiled into `WHERE` clauses, so rows a
caller may not see never enter the result set — and therefore cannot be counted,
paged, searched or aggregated into an answer.

A defect was found before a line was written: `_load_grants` merged every grant's
scope into one set and threw the ids away, so a teacher who also held a
school-wide role for announcements read as *unrestricted*. The principal now
carries its grants unmerged and `scopes_for(principal, permission)` returns only
the scopes attached to grants that actually confer it (ADR-029).

Everything fails closed: no principal, no scopes, an unknown kind, or a resource
with no clause for the kind held all yield `false`. A scopeless read succeeds
only inside `system_access(reason=…)`, which is tenant-bound and writes a
security event — so a background job that forgets it reads nothing, visibly, on
its first run.

Thirty-six tests across every scope kind, composition, leakage through counts,
totals, search, aggregates and error shape, and cross-tenant attempts with a
genuinely valid token. The first real scoped endpoints (`/api/v1/students`)
replace the placeholder route, so the whole chain — token, grants, per-permission
scopes, predicate, SQL — is exercised over HTTP.

**A lesson about checks, not about code.** Five sabotages were caught. The sixth
was not: a route made to query the table directly with
`from sqlalchemy import select as _select` walked past a structural check that
listed the *unsafe* call names. The check now inverts — every call taking a
scoped model is suspect unless it is one of the four helpers that carry a
predicate by construction. A check a rename defeats measures nothing.

**Entitlement engine** (`modules/billing/`). Seven concepts kept apart, and two
one-way rules: a person may be entitled to do what the institution has not
bought (402 and an upgrade path), and buying a feature never grants anybody a
permission (the engine has no opinion about who may act).

Four negative answers rather than one, asked in an order that never tells a
school it disabled something it could not have had — no subscription, not in
plan, switched off by the institution, allowance spent. They map to three HTTP
answers because the reader is three different people: upgrade the plan, ask your
administrator, wait for the period to roll.

A limit (students on the roll) and a meter (tokens this month) are different
things. A school over its student limit must still be able to take a register.
`past_due` still entitles, for the same reason. A limit the plan never mentions
is zero, not unlimited.

Twenty-nine tests; four sabotages caught. A fifth finding came from a test
rather than a sabotage: the "no plan name outside billing" check flagged the
`institution.*` permission module, so plan keys are now prefixed `plan.` and the
check is exact rather than approximate.

**Contextual complexity** (`modules/experience/`). The UX law — *complexity must
be capability, never burden* — made architecture rather than convention. One
call returns a person's world: only the concepts their institution actually
uses, only what they may see, only what the plan includes, in the institution's
own words, ordered by what they came here to do.

Four questions, and what happens when each says no differs. Not configured and
not permitted are both *absent* — not empty, not disabled, not a padlock. Not
entitled becomes an offer, but only to somebody who could actually buy it: a
padlock a teacher cannot open is an advertisement placed in their way. Role
affects order, never access.

Configuration is derived from the rows an institution has, never from an
institution *type* — a static check forbids `institution_type` and its variants
anywhere in product code. `interface_profiles` covers the two cases derivation
cannot: a university on its first morning declares what it intends to use, and
an institution may suppress a layer it has stopped using — but never one that
has rows, because data that exists stays reachable.

Twenty tests across four institutions on one deployment, producing four distinct
capability sets. Four sabotages caught.

**A defect the suite found on its first run.** A registrar could not see academic
units: the capability requires `institution.department.read` and the role
template never had it. The backend was correct and every isolation test was
green, and the product was unusable for one of its most important roles. That is
what the experience acceptance suite is for.

**Attendance** (`modules/attendance/`). Journey 1, and the first operational
feature. A register arrives complete — everybody in the room, in order, with the
school's codes and the default — and goes back in one write. Three requests for
a full register, asserted as a count, because round trips are what a school's
network multiplies.

Membership is derived from the enrolments covering the day rather than stored, so
a child who transferred in on Monday is on Monday's register and last March's
register still shows last March's class.

The codes are the school's; the `category` is not, because a percentage-present
figure has to know which marks count. `counts_as_present` is a separate column
from the category, so a school that counts an educational visit as present and
one that does not can both be right.

Corrections are additions: `attendance_amendments` is append-only at the
database, and changing a *submitted* register needs a reason. A register will not
submit while somebody is unmarked or while a code demanding an explanation has
none — the absence workflow, as one boolean on a row the school owns.

`rate` returns `None` rather than zero for a student with no sessions, because a
progression rule reading zero would hold a child back for having no record.

Twenty-two tests, four sabotages caught. The module-boundary test caught a fifth
problem in the right place: the attendance scope plan reached for `people.models`
to build a guardian's clause. The exception list stayed empty and `people.scopes`
gained a published selectable — the better answer, because a parent's reach over
attendance must be the same reach they have over the child.

**Assessment and results** (`modules/assessment/`). Journeys 4 and 5. A score is
what a teacher entered; a result is what the institution has said. The lifecycle
is draft → submitted → in review → approved → published, and `published` is
terminal: corrections are amendments, never different values.

Publishing **snapshots** — the mark and the grading it was given, including the
band, the points, the pass flag and the scale's code. A test moves an A boundary
from 70 to 90 afterwards and asserts the already-published A stays an A. That
redundancy is the feature; recomputing from a live scale would silently rewrite
every award an institution ever made.

Approval workflows are rows: a school's Teacher → Principal and a university's
Lecturer → Coordinator → Department → Board from one machine, taken in order,
each step authorised by its own permission. An institution with no workflow
publishes in one action, which is a configuration rather than an omission.

Readiness *reports* rather than refuses — missing marks, marks outside the
scale, assessments still open, unmoderated papers — because "not ready" is
useless at four o'clock on results day. `force` overrides those warnings with a
stated reason and does **not** override the workflow.

Twenty-eight tests; six sabotages caught, one per attack in the brief. The suite
found a real defect: readiness took the class list as of *today* rather than as
of the period the results cover, so publishing an autumn term in January would
have reported an empty set as ready.

**Academic documents** (`modules/documents/`, `modules/customization/branding.py`).
Journey 5's other half, and the point at which every earlier decision is either
vindicated or found out.

A report card, a transcript, a progress report, a certificate and a completion
statement are one engine. `documents.sections` is a platform-fixed catalogue of
sixteen section kinds validated at boot; a template is an ordered list of keys
from it with the institution's own titles and options. Adding "certificate of
enrolment" is a row, not a release. The suite proves it by building a school
report card, a university transcript with ECTS credits and a credit-weighted
GPA, and a certificate — from the same `issue` call.

**The line between historical fact and current presentation is the whole
design**, and it is drawn explicitly (ADR-034). Frozen at issue: results and
their grading, credits and what they were called, the placement the student
actually held during the period covered, course names, attendance, comments,
progression, awards, the grading key, and every computed total. Resolved fresh
at render: the crest, the colours, the address, the letterhead — because a
school that has moved reprints an old transcript on the letterhead that reaches
it today. Terminology sits on the historical side: a report card that said
"Form" keeps saying "Form".

**Reprinting is not regenerating.** There is no path that recomposes an issued
document, and a structural test refuses to let the renderer import anything that
could reach a database. Corrections supersede rather than rewrite; `outdated()`
reports that a document predates an amendment without altering it; a voided
document still prints, with VOID across it, and cannot be deleted at all.

Fifty-two tests, fifteen sabotages, all caught. Two of the fifteen initially passed,
which was the more useful result: both named tests that were asserting against a
payload frozen *before* the change they were meant to detect. A third found
machinery rather than a weak test and led to a rule being deleted.

Two real defects surfaced. Publication republished assessments that a second
result set swept up — a January resit would have republished the whole autumn
term and every mark would have appeared twice on a transcript. And two templates
sharing a number prefix each kept their own counter, so both issued
`RC/2026/0001`; the counter now belongs to the series rather than to the
template.

**The design system** (`modules/design/`, `tools/design/`). The visual direction
was redirected at the token level rather than polished: *a royal institution
rendered by a precision instrument*. Midnight chrome, ivory work surface,
champagne used as jewellery, rules instead of cards, radii of 2–4px, one shadow,
no decorative gradient. The identity is the eight-point seal from two squares at
45°, with the X of EdirasX held in its centre as void — one construction
generating the mark, the rule terminator, the node, the lattice and the spinner.

Everything is a token and a theme is a validated schema, which is what makes the
future Design Studio able to emit overrides rather than CSS. Every institutional
colour passes a guardrail that answers with a remedy rather than a verdict, and
an institution's ornament gold is never used as its text gold.

Dense tables no longer overflow onto phones: a table declares its data shape and
its small-screen composition follows — labelled records, course-and-grade with
the grade held large, a people list, or the one genuinely two-dimensional shape
that scrolls with its time column pinned.

The shell renders from `experience.resolve`, and four real institutions were
provisioned and screenshotted at three widths to prove it: a nursery shows
Children, Rooms and Parents; a university shows Modules, Credits, Qualifications
and Transcripts; a doctoral institute shows Researchers, Research programmes,
Supervisors and Milestones. The review found six defects no test would have —
see ADR-035 — including a navigation that showed the same word twice in five
places and a nursery being offered Grades.

---

## Next — Phase 2 remainder

In priority order. Each carries the Bible's Definition of Done.

1. ~~**Academic structure**~~ — **done**. Stages, levels, years, terms, subjects, class groups, grading scales and bands, progression rule engine, terminology. The Four Schools acceptance test passes (ADR-022).
2. ~~**People**~~ — **done**. Identity, person, and student/staff/guardian relationships kept properly separate; one person holds several relationships without a duplicated identity (ADR-027).
3. ~~**Enrolment as history**~~ — **done**. Admission, enrolment, transfer, suspension, withdrawal, readmission, progression, completion, awarding. No `student.class_id`; records are added, never overwritten, and two structural tests fail the commit that reintroduces one.
4. ~~**Bulk import**~~ — **done**. Preview, column mapping, validation, duplicate detection, dry run, single-transaction apply, refusing reversal, history, audit (ADR-028).
5. ~~**Scope predicate compilation**~~ — **done**. Every scope kind compiled to SQL, resolved per permission, failing closed, with leak-by-row-count tests and an audited elevation path (ADR-029).
6. ~~**Entitlement engine**~~ — **done**. Distinct from permission, role, scope, plan, feature availability, usage limit and institution configuration, in both directions (ADR-030).
7. **Custom fields** on core entities — the remaining Phase 2 item.

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
| 3 | ~~Scopes are parsed and unioned but not compiled~~ | — | **Resolved** — ADR-029. The union was itself a widening defect and is gone |
| 4 | `starlette.testclient` deprecation warning from FastAPI 0.141 | Trivial | Upstream; revisit on the next FastAPI bump |
| 5 | `_IncludedRouter` traversal in `test_boundaries.py` reaches into a FastAPI internal | Low | Written to accept both routing shapes so it degrades to the public shape rather than silently checking nothing |
| 6 | No frontend yet | Expected | Phase 4 — the design system, the shell and fifteen rendered journeys exist as server-rendered HTML; no client script yet, which is why the drawer and the palette have correct markup and no focus behaviour |
| 7 | Assessment and documents ship service-first, with no HTTP endpoints | Expected | Deliberate: routes are written alongside the screens that call them, in Phase 4, so the API shape is decided by a real caller rather than guessed |
| 8 | No screen-reader verification | Medium | None is installed here and none can be driven headlessly. axe-core and a keyboard walk are clean; a NVDA/VoiceOver pass over the register, the candidature and the parent's page is outstanding and is **not** claimed as done (ADR-038) |
| 9 | Dialog and palette focus behaviour unimplemented | Medium | The markup is correct — `role="dialog"`, `aria-modal`, labelled — and there is no script to trap focus, restore it on close, or wire Escape. Reported as absent by the audit rather than passing as present |

---

## The flagship plate: my own review of the first render

Recorded here rather than in a commit message because the next increment starts
from this list. Rendered at `docs/edtechx/design/plates/01-doctorate-flagship.png`,
A4 landscape, Level IV, against deliberately hostile data — *Muhammad
Abdulrahman Ibrahim Abdulwahid Al-Sulaimiy*, *Doctor of Philosophy in
Educational Leadership and Institutional Development*, Arabic alongside Latin.

**Fixed between the first and second render**, all found by looking:

1. The sheet-scale lathe field read as a visible oval smudge — a sheet field
   must have neither a shape nor a visible presence. Widened past the short
   side so the trim crops its envelope, and dropped from 0.045 to 0.030 ink.
2. The microtext ring read as a grey band of noise along the top and bottom
   edges at arm's length. Microtext legible as a texture is not microtext.
   0.48 → 0.26 strength.
3. The rule beneath the name was drawn *through* the Arabic descenders.
4. The seal was a small stamp rather than the institution presiding; enlarged
   from 13mm to 19mm radius and lifted into the execution row properly.
5. Signature rules were pure black at 0.35mm — heavier than the frame's own
   innermost engraved rule, so they read as form fields.

**Not yet fixed, and the reason this is not called finished:**

1. **The vertical composition is still a strip.** Two dead bands remain — one
   between the authority rule and the conferral line, one between the statement
   and the execution row — because zones are positioned by arithmetic from a
   single anchor rather than distributed across the field. This is the central
   defect.
2. **The frame is four nested rectangles.** It decorates the edge; it does not
   relate to the content it frames. The reference implementation names exactly
   this failure, and quoting it did not prevent committing it.
3. **The centred stack.** Conferral, name, qualification, distinction and
   statement are five centred lines of decreasing weight. That is the
   composition every generic certificate uses.
4. **The peak's type scale is crude** — field width over name length, capped by
   field height. It is a formula, not a designed scale, and a short name and a
   long one do not sit in the composition the same way.
5. **The seal passes behind the footline serial.** A collision.

Honest assessment against the standard set for this work: the geometry and the
budget system are sound; the composition is not yet something an institution
would be proud to issue. It is not a rendering problem — the plate does what it
is told — it is that the arrangement has not yet been designed.

---

## The composition review: six architectures, ranked

`tools/design/compositions.py` renders six *architecturally* different
arrangements of one certificate — identical data, palette and geometry budget,
so the comparison is about composition and nothing else. Contact sheet at
`docs/edtechx/design/plates/contact-sheet.png`.

**One bug, appearing six times.** The recipient name wraps to two lines under
hostile data, and every zone beneath it is pinned at a fixed offset from the
name's *top*. So the Arabic name, the degree and the field of study overlap each
other in A, C, D, E and F. This is the single most useful thing the exercise
produced: absolute positioning against variable-height content is a defect the
short-name version of this data would never have shown. The fix is structural —
zones flow within a band, or the name is optically fitted to one line — and it
is the first thing the next increment does.

**The ranking, by architecture rather than by finish:**

| | Composition | Grade | Why |
|---|---|---|---|
| **F** | Institutional rule | **A** | No enclosing frame at all: two full-width rules, a left-aligned hierarchy, a wide margin, the seal as a right-hand counterweight. Reads as institutionally important before a word is read, and has none of the border-template feeling. The asymmetry is real and has a reason. |
| **C** | Administrative edge | **A−** | The passport-page column genuinely works. Document identity is legible and clearly subordinate; the ceremonial field is calm because the apparatus has left it. |
| **D** | Heraldic lintel | **B+** | Seal between the two institutional names, carried on a full-width rule, with the degree in a khatam-bounded cartouche. A real architecture; slightly conventional. |
| **B** | Ceremonial band | **B−** | Good idea, wrong proportions. The band is too tall and too pale — it reads as a grey box rather than a register, and it leaves dead field above and below. |
| **A** | Architectural axis | **C+** | The spine is nearly invisible at 0.24mm and the frame openings read as accidental gaps rather than as a deliberate interruption. |
| **E** | Geometric field | **C** | The construction is drawn but reads as a diagram *behind* text rather than as the architecture *of* it. |

**What the ranking says.** The two strongest compositions are the two that
abandon or subordinate the enclosing frame. That is the answer to the first
plate's central defect: four nested rectangles were not a weak frame, they were
the wrong idea. F and C both establish authority through alignment, margin and
one counterweight rather than through enclosure.

Next: fix the wrap defect structurally, then develop F and C to finish — and
only then the remaining fourteen certificates and five transcripts.

---

## Flagship F: flow, and the hostile set

`tools/design/flagship.py`. Contact sheet at `plates/f-hostile-contact.png`.

**The variable-height defect is fixed structurally.** The field is one flex
column; bands are its children; two flexible spacers absorb the difference.
There is no fixed vertical offset anywhere in the composition, so overlap is not
avoided — it is unrepresentable. A name that takes three lines pushes what
follows down. No shrink-to-fit: the recipient is sized within a stated range
(12.4mm → 8.2mm) and wraps beyond it, because reducing the peak until the
longest possible name fits on one line makes every ordinary name look timid to
protect an extraordinary one.

Verified across four variants — hostile baseline, an ordinary short name, a long
institution with three signatories, and the minimal case (no Arabic, no
distinction, no seal, one signatory). **No collisions in any of them.**

**Three defects found by looking and fixed:** the Level I plate was still
drawing one engraved register, which appeared as a gold rectangle inside F's own
two rules — a frame F had specifically been chosen for not having, so `build()`
gained `frameless`; the signature cells were shrink-to-content and therefore
unequal; and the seal legend truncated mid-word, reading "MERIDIAN INSTITUTE FOR
ADVANCE", a typo the institution did not make.

**Still open on F:**

1. **Without the seal the composition leans left.** The seal is the right-hand
   counterweight, and the minimal variant has nothing in its place — the right
   half of the lower sheet is empty. The composition needs a defined fallback
   counterweight, not a smaller margin.
2. **The short-name variant leaves the Arabic detached** — it aligns right
   against the Arabic institutional name, which is correct, but with a short
   Latin name the gap between them reads as a hole rather than as a diagonal.
3. The statement's 56% measure leaves the right half quiet, which works with the
   seal present and is part of defect 1 without it.

Not yet done on F: print review at 200%, greyscale hierarchy check beyond the
single capture, and the A4-portrait and Letter compositions. C has not been
started.

---

## Art-direction correction: controlled, not restrained

I had narrowed the target. "Restraint" was being read as minimalism — sparse
pages, little gold, ornament kept at the edge — and that is not the brief. The
brief is royal institutional luxury: magnificence that is *architecturally
controlled*, which is a different constraint entirely and a harder one.

The correction, stated so it governs everything that follows:

> **Do not confuse complexity with clutter. Do not confuse minimalism with
> luxury.** A magnificent document can carry a great deal of craftsmanship and
> still have exceptional hierarchy. Suppressing the grandeur of a royal
> institution's credential moves *away* from its identity.

`flagship_f(royal=True)` is the first response. It is deliberately **not a
colour switch**: F's architecture is unchanged — the exact left axis, the
margin, the institutional rule, the right-hand counterweight, the subordinate
verification — and the Level IV geometry budget is spent on it. Full frame
registers, guilloché in the band, khatam corners, a lattice field, a
three-tone engraved gold hinge, the degree set in engraved gold, and a
medallion seal with lathe work behind its ring rather than a stamp.

The hierarchy is identical to the restrained version. That is the point: the
page is magnificent and nothing shouts.

**Fixed on the first royal render:** the footline was struck through by the
frame's own bottom rule — the field cleared the innermost register but not the
band hanging beneath it.

**Still open:** the seal's blind-emboss offset reads slightly doubled at
medallion scale; the ceremonial levels' own descriptions in `ceremony.py` still
carry the over-restrained wording and need rewriting to "elegant and premium →
clearly luxurious → richly ornamented → exceptional royal craftsmanship"; and
F·R2 Imperial Midnight, F·R3 Royal Heritage, F·R4 Grand Ceremonial, F·R5 Royal
Islamic and F·R6 Future Royal are not yet built. C has not been started.

---

## Language architecture, and two instruments from the press specification

Arabic + English was becoming a compulsory formula, which is as templated as a
compulsory ornament. `design/language.py` makes the arrangement a design
decision recorded on the template: eight arrangements — Latin-only, Arabic-only,
Arabic-primary, Latin-primary, peer, zoned, integrated, three-run — all through
**one code path with no `if arabic:` anywhere**. The proof renders M02's plate
under six of them with nothing swapped but the architecture.

The module knows three things a translation table does not: optical size is not
nominal size (so "peer" means optically equal), direction belongs to the run and
not the page, and absence is ordinary — a missing translation re-balances the
composition instead of leaving a ghost.

Two composition rules came out of the hostile data. Subordinate scripts carry
identity, not prose: names and qualifications appear in every script, a
250-character legal paragraph appears once. And the plate responds to the
arrangement's typographic load, because a two-script sheet needs more field than
a one-script sheet. Both replaced shrinking the recipient's name.

**A collision audit now runs on every build.** Its first run said all four
finalists overflowed — M11 by 31.8mm, M12 by 16.4mm — three of them invisible at
contact-sheet size. This defect class had been found by eye four times and never
by a test.

**A counted stroke census** replaced the asserted hairline floor, and
immediately found 1,320 strokes at 0.050mm, all of them derived from sub-stroke
multipliers compounding inside the rosette. The floor is now enforced where the
multiplication happens.

Each specification also carries the three questions that block a press file:
ICC output profile, PDF/X part (X-1a and X-3 force a flatten that rasterises
every guilloché line), and TAC with whether pure black stays 100% K.


## The masterpiece pass: the ornament becomes the document's own

Four finalists — Imperial Islamic, Crimson Imperial, EdirasX Signature, Royal
Palace — developed individually at full resolution, each with eight standalone
separations and a production specification generated from the same plate as the
artwork. Written up in `docs/edtechx/design/EDTECHX_MASTERPIECE_PASS.md`.

`design/signature.py` is the substantive addition. A **Motif** is a geometric
family derived from an institution and a document type, appearing at six scales
on one sheet: the border lattice, the corner medallion, the seal device, the
institutional mark, the ground figure and the guilloché. For this institution's
doctoral award it is {10/3} with a 50-lobe lathe — fifty being five times ten,
so the lathe work and the star work are one hand at two frequencies.

Two generalisations made it possible. `INNER_RATIO` was √(2−√2) treated as a
constant; it is the (8,2) member of `cos(kπ/n)/cos((k−1)π/n)`, and writing the
family down lets ten- and twelve-fold documents be constructed rather than
drawn. `density_for` then picks the k that holds *sharpness* constant across
orders, so plates of different orders are recognisably from one house.

`gilding.Scheme` turns gold into five roles — primary, secondary, engraved,
security, heritage — and every drawing call names a role. That is what stops the
fine registers competing with the architecture: they are different metals, not
one metal at two weights.

**A defect in the shared lathe primitive that had been affecting every plate.**
`epitrochoid` derived its closure turn count by rounding the values passed to
it, and both callers pre-multiplied the wheels by a scale — so a 50-lobe figure
at a tenth scale ran 3.6 turns instead of 7, drew half its petals and closed
with a chord straight across the middle. Every rosette on every plate had been
an unclosed, mis-specified curve that happened to look dense enough to pass as
lathe work. Fixed with a `scale=` keyword; turns and lobes now come from the
integer specification, which is where they live.

Also fixed by looking rather than by testing: the star construction degenerated
for every even order ({10/2} is two pentagons); the lathe passes beat against
the lobe period and laid a moiré lens across the rosette; the kites read as
spikes; ornament ran through the signatories' authority lines; the first fix for
that made it worse because two even-odd subpaths overlapped and flipped the
middle back to filled; a two-line office pushed its engraved rule out of line
with the other two; and M11's execution band overflowed its panel so the
architrave cut through "Board of Examiners".

**The fine text is not microprint, and now that is measured.** At 0.58mm
(≈0.41mm cap height) it is illegible at 300 DPI and legible at 600. Security
microprint means 0.25mm or below. `microtext_ring` is renamed `fine_text_ring`
throughout and the ceremonial permit is `finetext`.

**Nothing has been printed.** No press, no paper, no foil, no loupe in this
environment, so the physical validation is not claimed: foil register on cotton,
emboss depth, whether any press holds the 0.07mm hairlines, how the metals read
under raking light. Getting a proof made needs a vendor, not more code.


## Art direction reset: royal maximalism, and twelve luxury concepts

The restraint reading was withdrawn. The previous flagship work had interpreted
"restrained" as the primary principle and produced plates that were technically
exact and visually inexpensive — the sparse F/C direction is archived, not
polished further. The target is royal institutional luxury: richness and order
together, ornament designed rather than applied, grandeur at a metre and
craftsmanship at five centimetres.

**Three new modules, because the old vocabulary could not express it.**

`design/gilding.py` makes gold a material rather than a hex value. Eight metals,
each four inks — a lit crest, a broad reflecting face, a body colour, a wall in
shadow — because that banded ramp is what the eye reads as metal and a single
value is what it reads as yellow. Each metal names the physical process it
stands for and a foil reference a vendor can order against. The treatments
(engraved rule, emboss, raised type, foil gradient) each carry a ledger entry in
`SIMULATION` saying what they are and what they are not, and a test fails if a
treatment exists without one.

`design/architecture.py` makes the frame a built thing: corner blocks with a
mitred elbow and an inset lathe medallion, register stacks where every band has
a stated job, a real octagon-and-square tiling, strapwork drawn as ribbon rather
than line, a two-centred arch that can be struck to a stated rise, cresting,
spreaders, spines, mandalas, medallions, radiant fields.

`design/ceremony.py` was rewritten. Levels I–IV now mean elegant → clearly
luxurious → richly ornamented → exceptional, and what rises is architecture,
ornament and material. `field_ink` became `content_ink` and is explicitly a
*legibility* guarantee about the area behind the words, not an ornament ban —
outside the content field a Level IV plate is routinely dense. **The whitespace
floor was deleted**: encoding air as a fraction of the sheet produced empty
documents that passed.

**Twelve concepts, one hostile record, ranked.** `tools/design/concepts.py`
builds twelve genuinely different design philosophies — not palette swaps: each
owns its ground, frame architecture, central composition, typographic pairing,
metal, and the job it gives Arabic. `tools/design/render.py` renders them at 300
DPI and composes the contact sheet. The board and the ranking are in
`docs/edtechx/design/EDTECHX_CONCEPT_BOARD.md`; the strongest three are **02
Imperial Islamic**, **11 Crimson Imperial** and **01 Royal Palace**, with **12
EdirasX Signature** fourth and strategically the most important because its
dissolving lattice is the one construction that could become unmistakably the
house's own — and it does not yet read.

**A typographic defect that had been shipping silently.** The flagship
stylesheet asked for `'EdirasX Display'`, a family `typeface.py` never declared,
so every certificate was set in Georgia. `typeface.py` now declares the
ceremonial faces (Fraunces 300/600/900, Archivo, Amiri 700, Cairo) and exposes a
`ROLES` table with `stack()`, which raises on an unknown role rather than
falling through to a system face.

**Ten defects found by looking rather than by testing**, each invisible in the
code: the recipient's name breaking at the hyphen on eleven of twelve plates;
the verification line landing on a midnight border as dark ink on dark ground;
the seal legend reading `INSMERIDIAN INSTITUTE` at the repeat seam; the corner
bracket's double step reading as a mis-registered plate; a cartouche drawn into
a viewBox twice its box and squashed across the qualification; a mihrab struck
at its natural proportion coming out 131mm tall over a 237mm opening; a radiant
field painted over by a 72% ground and vanishing; a crest that read as a circus
tent; microtext sitting 2.6mm from the trim, inside the knife; and a ground
mandala legible as a figure at arm's length. All fixed; the full table is in the
concept board.

`docs/edtechx/design/EDTECHX_PRODUCTION_SPEC.md` is new: dimensions and
tolerances, substrate by edition, inks and metals with foil references,
linework weights, finishing processes and dies, and the binding section
separating what is cryptographically verifiable in every edition, what is a
genuine production feature only in the editions that buy it, and what is visual
simulation everywhere. Nothing may be described in stronger terms than that
table allows.

**Verified:** 27 new tests in `test_architecture.py` — the octagon lattice is a
real tiling, a stated arch rise is the rise produced, all four corner brackets
are one shape rotated, no metal treatment emits an opacity on a line, every
metal ramp descends, the legend ring fills its circumference exactly, the levels
increase in registers/permits/peak together, and there is deliberately no
whitespace floor. Suite green, ruff clean.

**Implemented but not verified:** nothing has been printed. Foil, emboss and
raised type are simulations and are labelled as such. Microtext at 0.56–0.62mm
has not been measured on any press. Greyscale, 200% inspection, and the
portrait and Letter compositions have not been done for any of the twelve.


## Working notes for the next session

- **Start here:** `apps/edtechx-api/README.md`, then this file, then `EDTECHX_ROADMAP.md` Phase 2.
- **Environment:** PostgreSQL must be running (`service postgresql start`). Roles and databases are created by the block in the API README. Without them, integration tests skip — and a skipped isolation suite proves nothing.
- **Before writing any model:** if it belongs to a school, it inherits `TenantOwned`. That single decision gets it a policy and an isolation test automatically. If it does *not*, write down why, as `Tenant`, `TenantDomain`, `User`, and `SecurityEvent` each do in their docstrings.
- **Before adding a route:** give it a `RequirePermission` dependency, or add it to `PUBLIC_ROUTES` in `test_boundaries.py`. There is no third option.
- **Before adding a foreign key between two tenant-owned tables:** nothing. It is rewritten to `(tenant_id, id)` automatically by `app.db.tenant_fk`, and a test fails if any key escapes. Do not add a plain single-column key back "because the composite one is awkward to query" — that is the defect ADR-026 records.
- **Before reading a scoped table:** use `authz.predicates.scoped_select` / `scoped_count` / `scoped_get` / `scoped_exists`. They are the only calls that cannot produce a statement without a predicate, and `test_boundaries.py` fails any route that reaches for `select(Person)` instead — under any alias.
- **Before writing a background job:** it has no principal, so it reads nothing. Enter `system_access(reason=…)` deliberately. That is the design, not an obstacle.
- **Before gating a capability:** ask which question you mean. `RequirePermission` is what this person may do; `RequireEntitlement` is what this institution has bought; `billing.require_meter` is how much is left this period. They are three calls because they are three questions, and a route needing two declares both.
- **Before recording where somebody is:** it is an `Enrolment` row with a start and an end, never a column on a person or a relationship. If a screen needs "the current class", ask for the open enrolment. Two tests exist specifically to fail the shortcut.
- **Before adding a permission:** add it to `CATALOGUE` first. Roles referencing unknown permissions fail the boot.
- **Before adding a capability to the rail:** ask the four questions the
  catalogue asks, and then a fifth if the permission is not the distinction.
  Attendance needs a class or a course to exist; a candidature and a caseload
  are told apart by *scope*, not by permission, because a supervisor and a
  candidate hold the same two. `Capability.scopes` narrows access and is
  therefore in the catalogue, never in a role shape — a shape orders and
  promotes, it never hides.
- **Before shipping a screen to a new audience:** render it, open it, and read
  the rail as well as the page. Six of the last nine defects were things no
  test could see and every one was visible in four seconds of looking: a
  hamburger at 1440px, five duplicate rail labels, Attendance offered to a
  doctoral researcher, "Student" printed under a person the institution calls a
  researcher, a date rendered twice on a phone, and a table that had stopped
  being a table on an iPad.
- **Before claiming an accessibility property:** run
  `python tools/design/audit.py --axe <path to axe.min.js>`. axe-core is not
  vendored; fetch it with `npm pack axe-core@4.10.2`. The first run found 697
  violations in code written to be accessible, which is the whole argument for
  the rule.
- **Never** connect the request path as `edtechx_migrator`. It owns the tables, and `FORCE RLS` is bypassed for owners. The production guard refuses this; development would not notice.
