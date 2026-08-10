# EdirasX Test Strategy and Status

**Version:** 1.4 · **Status as of:** session 5 — **387 passing, 0 failing**

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
| `test_tenant_isolation.py` | No tenant reaches another's data — or *references* it — by any path |
| `test_people_enrolment.py` | A person's record and history cannot be rewritten, lost, or seen by another institution |
| `test_bulk_import.py` | No import can leave a school's records half-changed |
| `test_boundaries.py` | Boundaries hold; no route is unguarded |
| `test_authz.py` | Permissions cannot leak across resources |
| `test_security.py` | Credentials, tokens, and production configuration |
| `test_api.py` | The request lifecycle enforces all of the above |

Added as their phases land: SSRF egress suite (Phase 5), escalation/IDOR suite
(Phase 2), AI approval-gate bypass suite (Phase 5).

---

## 4. Current status

### `test_tenant_isolation.py` — 27 tests

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

**Referential integrity, added this session.** Two tests, because row-level
security does not govern foreign-key checks. The structural one asserts that
every foreign key between tenant-owned tables references `(tenant_id, id)`; the
behavioural one has School B attempt to grant its own membership one of School
A's roles, and asserts the database refuses — *and* that the refusal is
identical to the refusal for a wholly invented id, so the attempt cannot be used
to learn whether the id exists. Before ADR-026 the first of those two inserts
succeeded.

Append-only grants are checked over every table in `APPEND_ONLY_TABLES` and
`UNDELETABLE_TABLES` rather than only `audit_events`. That generated check
cannot notice a table being *removed* from the list, which is why
`test_people_enrolment.py` also names `enrolment_events` explicitly — the two
together are complete, and neither is alone.

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

### `test_auth.py` — 24 tests

Provisioning: a complete school with system roles; active and resolvable; slug
validation and the reserved list; duplicate addresses refused; an existing
account reused across schools **without its password being touched**; a failed
provisioning leaves nothing resolvable.

Sign-in: correct credentials work and the issued token works. **Wrong password
and unknown account return byte-identical responses.** A member of one school
signing in at another is refused, and indistinguishably so — School B cannot
discover that the person exists at School A. Suspended schools refuse sign-in.
Repeated failures lock the account, after which even the correct password is
refused.

Rotation: refresh returns a new pair; a refresh token works exactly once;
**reuse of a rotated token burns the whole family**, including the legitimate
holder's newer token; a refresh token is not usable at another school; tokens
are stored only as hashes.

Sign-out: revokes the session and its refresh token; sign-out-everywhere
revokes every session; sign-out requires authentication.

Audit: a successful sign-in leaves an audit entry scoped to the school; a
failed one leaves a security event.

### `test_universal_education.py` — 45 tests

**The most important suite in the product**, because it tests the claim that is
easiest to make and hardest to keep.

Nine institutions configured through one code path: four schools (British,
American, Nigerian, a foundation-to-postgraduate university) plus a
qualification ladder running Diploma → HND → Bachelor's → Master's → PhD, a
credit-based university with faculties and departments, a non-credit adult
literacy institution, a doctoral research programme with supervision and
milestones, and a competency-based vocational institution.

*Structure.* Stage depth is the institution's choice — two flat tiers, three,
or nested. A university has **no stages at all**: its levels hang off a
programme, and a model requiring a stage would force every university to invent
one. Academic units nest to the institution's own depth: Faculty → Department,
School → Institute, or a single flat board.

*Qualifications.* Five in one institution's own framework, ordered by numbers
meaningful only inside it, grouped by category labels it chose.

*Credits.* Ten contact hours per credit in one institution, twenty-five in
another. Three institutions count nothing at all and are not forced to pretend.
No programme in any of the nine has an assumed duration.

*Periods.* Semester, Block, Session, Term — one to four per year, with the
institution's own word on every row.

*Grading.* The same mark of 85 bands as A, B, A and Distinction. 45 passes in
three institutions and fails in the fourth.

*Progression.* One engine, fifteen scenarios: core subjects plus attendance,
GPA, aggregate plus class position, credits accumulated, milestones plus two
human approvals, competencies plus a workplace placement. Two of these involve
no marks of any kind. Missing data never promotes; a pending approval is not a
refusal.

*Isolation.* Nine configured institutions in one database, each seeing exactly
what was configured for it. Codes are unique per tenant, so two institutions
both calling their first year "y1" is correct rather than a leak — the
assertion checks identity, not global uniqueness.

*And no special-case code.* Two static checks: no product module may name an
educational system or qualification in executable code, and no comparison in
the academic engine may test an academic quantity against a hard-coded number.
The first parses the AST and inspects string literals, identifiers, definitions
and attributes — never docstrings, because a docstring naming nine systems
explains the flexibility while a literal naming one assumes it. Matching is
word-boundary, because "ects" occurs inside "subjects" and a check that cries
wolf gets deleted rather than obeyed.

Both were verified by introducing exactly the defects they exist to catch: a
`_jss_promotion_override` with `average >= 50`, and later an `_is_doctorate`
returning `("phd", "dphil")` alongside a `_standard_bachelor_duration` of 3.
All fired.

### `test_people_enrolment.py` — 51 tests

The people model, run against the same nine institutions as the Universal
Education Test, because a model validated only against a school is a
school-shaped model with confidence.

*The sweep.* One function — record a person, register a student relationship,
admit, enrol — reaches an active enrolment in all nine, with the placement built
from whatever layers each institution actually configured. The four schools come
out with a class group and no programme; the five programme-based institutions
with a programme and no class group; one has a cohort and another, whose cohort
belongs to a different programme, correctly does not. No branch anywhere names
an institution.

*Identity is not a person.* A four-year-old is enrolled with no `user_id` and no
email. One person holds a staff relationship, a guardianship and a student
relationship at once, as **one** row. One global identity produces two entirely
separate person records at two institutions, and neither can see the other's.
Three guardians of one child carry the labels "Mother", "Uncle" and "Sponsor" —
free text, with the payer and the first contact deliberately different people.

*Enrolment is history.* A transfer leaves the closed row with the class group it
always had; asking where the pupil was in October and in March returns different
placements. A promotion decided by the institution's own configured rule opens
the next placement and copies the rule's reasoning into the ledger, so the answer
to "why was he held back?" survives the rule being rewritten. A withdrawal
followed by a readmission leaves the months away visible rather than smoothed
over. Two concurrent open enrolments are permitted, and leaving one of them does
not end the student's relationship. A doctoral candidate completes on milestones
and two human approvals, with no mark anywhere.

*And none of it can be rewritten.* `UPDATE` and `DELETE` on `enrolment_events`
are refused by the database for the application role, as is `DELETE` on
`enrolments`. Closing a closed placement, ending one before it began, and a
closed placement with no stated outcome are each refused — the last two by the
service *and* independently by a check constraint. Another institution cannot
read a person, a relationship, an enrolment or an event, including through raw
SQL, and cannot create an enrolment referencing a foreign student.

*Two structural tests carry the central rule.* No relationship table may carry a
placement column (`class_group_id`, `level_id`, `programme_id`, …), and no
function in the people module outside `_open` may assign one. Together they fail
the commit that reintroduces `student.class_id` "just for the list screen".

### `test_bulk_import.py` — 34 tests

Built from the files schools actually send, not from clean ones: a byte-order
mark, semicolons from a European locale, a title row above the header, a
repeated column heading, an admission number Excel turned into `4512.0`, a
phone number beginning with `+`, a class code the school does not have, and the
same child twice.

*Safety.* One bad row prevents the whole import — the four good rows around it
do not land either. A failure forced part way through `apply` (a monkeypatched
explosion on row three) leaves nothing behind and marks the batch `failed` with
the reason. A dry run performs the identical writes and rolls back, and the
count it reports is the count the real run would create.

*Judgement.* `=1+1`, `@SUM(A1)`, `+SUM(A1)` and `-cmd|…` are flagged;
`+2348012345678` and `-12.50` are not — the standard advice, narrowed so it does
not reject every Nigerian mobile number. `03/04/2015` is read as two different
dates under two different options, because the file cannot say which and
guessing produces records wrong by months.

*Vocabulary.* A column headed "Form" is recognised for a school that configured
that word, though "form" appears in no alias list in the product. That is the
design: the static aliases are sector-neutral and the institution's own words
come from its terminology, so the importer covers institutions nobody thought of.

*And it is not school-shaped.* The same importer, the same file format and the
same code path enrol matriculating students on a programme with no class group
at all, and import a contact list as people with no student relationship.

Three sabotages, all caught: committing each row as it goes, applying past
known-invalid rows, and reversing an import that has been built upon.

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
| Reuse detection actually revokes | Written first as a same-session revoke | The test failed: the 401's rollback undid the revocation. Fixed by committing the revocation on its own session |
| RLS enforces isolation | Disabled the policy on `roles`, queried from a stranger's context | **32 rows leaked**; restored → **0**. The ORM guard did not catch the raw-SQL path — which is why layer 2 exists |
| Route coverage is checked | Added an unguarded `GET /api/v1/leaky` | Flagged, and nothing else |
| Boundaries are enforced | A reverse dependency (identity → authz) introduced mid-session | Caught by the suite; fixed by removing the back-reference rather than by widening the exception list |
| Foreign keys respect the tenant boundary | `bind_foreign_keys_to_tenant` made a no-op | Both the structural and the behavioural test failed. Before the fix, the behavioural one **succeeded in referencing another tenant's row** — the defect, observed rather than argued |
| Enrolment history is append-only | `enrolment_events` removed from `APPEND_ONLY_TABLES` | The named test failed. The *generated* test passed, which is the known limit of generating a check from the list it checks — hence both |
| No relationship carries a placement | `class_group_id` added to `StudentRelationship` | Flagged, naming the column and the reason |
| A transfer does not overwrite | `transfer` made to move the student in place | Two tests failed: the behavioural one on the closed row's class group, and the AST one on the assignment itself |
| An import lands entirely or not at all | Each row committed as it went | Both the dry-run and the forced-failure tests failed — the dry run created records, and the failure left three students behind |
| Invalid rows cannot be applied | The refusal removed and bad rows skipped instead | Flagged: the good rows landed from a file the preview had refused |
| A reversal refuses when work has been built on it | `blockers()` short-circuited | Flagged: a reversal was offered over a pupil who had since been transferred |

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
| 11 | Admin bulk-imports students | ✅ **Covered — with the half-applied case attacked directly** |
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
