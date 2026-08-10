# EdirasX Test Strategy and Status

**Version:** 1.0 · **Status as of:** end of session 1 — **121 passing, 0 failing**

---

## 1. Principle

A test is worth having only if it can fail for a real reason. Two habits enforce
that here:

1. **Generated coverage over remembered coverage.** The tenant-isolation suite
   is generated from the model registry. A new tenant-owned model is covered by
   existing, not by anyone remembering to write a case.
2. **Prove the test is load-bearing.** Where a test guards something critical,
   we break the guarantee once and confirm the test notices. A green suite that
   would stay green with the protection removed is worse than no suite, because
   it manufactures confidence.

---

## 2. Layers

| Layer | Scope | Database |
|---|---|---|
| Unit | Pure logic — permission expansion, scope parsing, hashing, host normalization | None |
| Integration | Services against a real schema with RLS live | **PostgreSQL, mandatory** |
| API | Full stack through the router | PostgreSQL |
| Authorization | Role × route matrix | PostgreSQL |
| **Tenant isolation** | Every tenant-owned resource from a foreign context | PostgreSQL |
| Structural | Module boundaries, layering, route coverage, SDK confinement | None |
| E2E | The twelve critical journeys | PostgreSQL + browser |
| Accessibility | axe pass + manual keyboard/screen-reader script per journey | — |
| Performance | Budgets asserted on key routes | PostgreSQL |

**SQLite is not permitted** (ADR-016). The isolation guarantee is a PostgreSQL
feature; a green SQLite suite would be false confidence about the one thing that
must never be wrong.

---

## 3. Blocking suites

A release does not go out with any of these red. They are not "known failures".

| Suite | Guarantee |
|---|---|
| `test_tenant_isolation.py` | No tenant reaches another's data by any path |
| `test_boundaries.py` | Boundaries hold; no route is unguarded |
| `test_authz.py` | Permissions cannot leak across resources |
| `test_security.py` | Credentials, tokens, and production configuration |
| `test_api.py` | The request lifecycle enforces all of the above |

Added as their phases land: SSRF egress suite (Phase 5), escalation/IDOR suite
(Phase 2), AI approval-gate bypass suite (Phase 5).

---

## 4. Current status

### `test_tenant_isolation.py` — 23 tests

Structural: every tenant-owned table has `ENABLE` **and** `FORCE` RLS with a
policy; the application role holds no `BYPASSRLS`, is not a superuser, and owns
no tables; the audit log rejects `UPDATE` and `DELETE`.

Generated per model (8 tenant-owned models × 2): a foreign tenant's session sees
zero rows; a session with **no** tenant context sees zero rows — the failure mode
that matters most, because a background job or forgotten code path must be blind
rather than omniscient.

Targeted: cross-tenant insert refused by `WITH CHECK`; ORM guard refuses a
foreign `tenant_id` before the database does; cross-tenant `UPDATE` and `DELETE`
affect zero rows and leave the victim intact; `session.get()` on a foreign id
returns `None` (the IDOR case); each school sees exactly its own roles.

### `test_authz.py` — 23 tests

Catalogue integrity and boot-time validation. Expansion: `manage` covers its
resource and no other; module wildcards stay in their module; **`people.student.manage`
does not confer `people.student_sensitive.read`** — the prefix-matching bug that
would otherwise expose medical and SEN notes to any broad grant.

Role restraint: teachers cannot publish or approve results; guardians cannot
write; students cannot read other students; **no tenant role carries `platform.*`**;
**no broad role inherits safeguarding access**; admin has neither HR nor billing;
privileged roles require MFA.

Scopes: id-bearing scopes require ids and non-id scopes reject them; JSON round
trip; malformed scopes are rejected rather than silently ignored; scopes union
rather than intersect (a head of two departments reaches both).

### `test_security.py` — 22 tests

Argon2id output and verification; salting; length floor and ceiling (the ceiling
matters — unbounded input to a memory-hard hash is a DoS lever); **verification
against a missing hash returns false without erroring**, so the response shape
does not leak account existence; bcrypt flagged for upgrade.

Tokens: round trip; `tid` and `mid` present; tampered signature rejected;
**`alg: none` forgery rejected**; expired rejected; **a refresh token cannot be
used as an access token**. Refresh tokens: 200 unique samples, stored only as a
keyed hash. Elevation window honoured.

Production guard: five misconfigurations each refuse to construct `Settings`,
including **the shared migration role** — the one mistake that would void
isolation while every other test stayed green.

### `test_tenant_resolution.py` — 21 tests

Host normalization (case, port, trailing dot, whitespace, IPv6 literals);
platform hosts carry no tenant; **nested subdomains do not resolve**, so nobody
can construct a plausible hostname and probe; token/host agreement accepted,
refused, and correctly permissive for anonymous requests.

Database-backed: resolution by hostname and by subdomain fallback; port and case
tolerated; unknown host refused; **suspended school does not resolve**;
**unverified custom domain does not resolve** while a verified one does; each
school's hostname resolves only to itself.

### `test_boundaries.py` — 16 tests

No module imports another's models — **the exception list is empty**; `core` does
not depend on `modules` (layering not inverted); **provider SDKs are confined to
their adapters**, enforced before the first adapter exists so the gateway
abstraction cannot rot; every route declares a permission or appears in
`PUBLIC_ROUTES`.

### `test_api.py` — 16 tests

Health is public; security headers present; unknown host refused; `/context`
returns the school for its host. Authentication: required, returns the
principal, refuses garbage and non-bearer schemes.

Tenant agreement at the HTTP boundary: **School A's genuinely valid token is
refused on School B's hostname** (403 `tenant_mismatch`); a token naming B's
tenant but A's membership fails closed (401); **`X-Tenant-Id` headers and
`?tenant_id=` parameters are inert**.

Authorization: guarded route allows a holder, refuses anonymous, and refuses a
principal whose grant was removed. Hygiene: errors leak no tracebacks, SQL, or
driver names; oversized bodies rejected at the edge.

---

## 5. Load-bearing verification performed

| Guarantee | Sabotage | Result |
|---|---|---|
| RLS enforces isolation | Disabled the policy on `roles`, queried from a stranger's context | **32 rows leaked**; restored → **0**. The ORM guard did not catch the raw-SQL path — which is why layer 2 exists |
| Route coverage is checked | Added an unguarded `GET /api/v1/leaky` | Flagged, and nothing else |
| Boundaries are enforced | A reverse dependency (identity → authz) introduced mid-session | Caught by the suite; fixed by removing the back-reference rather than by widening the exception list |

---

## 6. The twelve critical journeys

| # | Journey | Status |
|---|---|---|
| 1 | Teacher marks attendance | Phase 3 |
| 2 | Student submits an assignment | Phase 6 |
| 3 | Teacher grades a submission | Phase 6 |
| 4 | Admin publishes results | Phase 3 |
| 5 | Parent views a published result | Phase 3 |
| 6 | Admin issues a fee; parent sees it | Phase 3 |
| 7 | Parent records a payment | Phase 3 |
| 8 | School publishes a theme | Phase 7 |
| 9 | School renames a term; it propagates | Phase 2 |
| 10 | AI proposes a design; admin approves | Phase 7 |
| 11 | Admin bulk-imports students | Phase 2 |
| 12 | **Tenant A attempts to access Tenant B → fails** | ✅ **Covered, at both the database and HTTP boundaries** |

---

## 7. Gaps, stated plainly

Not yet written, because the features they would test do not yet exist:
authentication endpoint tests (login, refresh rotation, reuse detection,
lockout), scope-predicate leak tests, escalation and delegation-ceiling tests,
SSRF egress tests, AI approval-gate bypass tests, accessibility tests,
performance budget assertions, and E2E journeys 1–11.

Coverage percentage is not tracked and is not a goal. What is tracked is whether
each guarantee in `EDTECHX_SECURITY.md` §11 has a test that would fail if the
guarantee were removed.
