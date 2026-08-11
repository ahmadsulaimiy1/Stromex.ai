# EdirasX Test Strategy and Status

**Version:** 1.9 · **Status as of:** session 5 — **621 passing, 0 failing**

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
| `test_scope_predicates.py` | Nobody learns anything they were not granted — by any route, count, total, search or aggregate |
| `test_entitlements.py` | What a person may do and what the institution has bought stay separate in both directions |
| `test_experience.py` | No institution is shown complexity it does not use |
| `test_attendance.py` | A register is fast enough to be taken, and solid enough to be quoted |
| `test_assessment.py` | A published result is what the institution said, and stays it |
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

### `test_scope_predicates.py` — 36 tests

A university with two faculties, three departments, three programmes, four class
groups, a teacher allocated to one of them, a guardian with one child, a student
who is their own subject, and an applicant with no placement at all. Every
assertion is about one of them reaching — or failing to reach — the others.

*Fail closed.* No principal sees nothing. A principal holding a permission for
something else sees nothing. A scope kind the resource was never taught about
reaches nothing. An empty scope set compiles to `false`.

*Every kind.* Class, level, programme, cohort, department, nested faculty
(recursively, stopping at the other faculty's boundary), `taught_by_self`,
`own_children`, `self`, institution-wide. A scope naming a class that does not
exist reaches nothing rather than everything. A student with no placement is
reached by no structural scope and by the institution-wide one — correct in both
directions, and easy to get wrong in either.

*Composition.* Two departments union. A caller's own filter can only narrow. A
plan that returns an unrestricted clause raises. And the one that matters most:
**a school-wide grant for announcements does not widen the student scope** —
the defect that existed before scopes were resolved per permission.

*Leakage.* The scoped count is 2 where the table holds more. An aggregate over
the scoped statement returns the caller's minimum, and `None` for a caller with
no reach. Fetching an out-of-scope id and an invented id both return `None`, and
over HTTP both return byte-identical 404s. Paging one row at a time never walks
past the scope. Searching for a name outside the scope returns exactly what
searching for nonsense returns.

*Tenant boundaries, again.* A scope naming another school's class reaches
nothing — and the same principal with its own school's class id does, so the
refusal is about the tenant rather than about a broken query. A guardian at one
school reaches no children at another, which is ADR-027's separation doing
authorization work.

*Elevation.* Scopeless reads succeed only inside `system_access`, which refuses
without a tenant, refuses without a reason, writes a security event, and ends
with the block.

Five sabotages caught: a fail-open default, scopes unioned across permissions, a
count over the table, a 403 distinguishing out-of-scope from non-existent, and
elevation with no audit record. **A sixth was not** — see the load-bearing table.

### `test_experience.py` — 20 tests

The Universal Education Test asked the other way round. Four institutions on one
deployment — a nursery, a secondary school, a university, a doctoral institute —
and mostly *negative* assertions, because the law is about what people are not
shown.

A nursery administrator meets none of programmes, qualifications, credits,
faculties, cohorts, supervision, milestones or transcripts, and reads
"Children", "Rooms" and "Parents". A university registrar finds faculties,
programmes, levels, credits, cohorts and semesters, reads "Faculties" and
"Modules", and is shown no research concepts. A doctoral institute additionally
finds supervision and milestones and, running no classes, is shown no classes or
timetable. **The four produce four distinct capability sets**, asserted directly.

Within one institution a teacher, a parent and a bursar open three different
products: the teacher's world leads with attendance, the parent's is smaller than
the teacher's on purpose, and the bursar is not handed the academic engine.

Zero states: a present capability with no records carries "Add your first child";
an absent one carries nothing, because it has no state. Empty groups are dropped
rather than rendered.

Declaration: a university on its first morning declares its layers and sees them
immediately; an institution cannot suppress a layer full of its own records.

Structural: no `institution_type` anywhere in product code, every capability
names a real permission, feature, group and layer, and every label resolves to a
known terminology key.

Four sabotages caught: showing every concept the database supports, rendering
unpermitted capabilities as disabled rows, advertising upgrades to everybody, and
hiding a layer that has rows.

### `test_documents.py` — 52 tests

One engine, three institutions. A school report card (identity, placement,
weighted subject results, attendance, comments, grading key, signatures,
verification), a university transcript (results grouped by semester, ECTS
credits, a credit-weighted grade-point average, the qualification framework),
and a certificate of enrolment that is the same machine with four rows instead
of nine.

**Historical integrity is most of the suite.** A grade boundary is moved from 70
to 90 and an already-issued A stays an A. A module is revalued from 20 credits
to 30 and a transcript issued *afterwards* still reports what the graduate
earned. The school renames its vocabulary and a report card that said "Subject"
keeps saying "Subject". A student is transferred from 10A to 10B and a report
card issued after the transfer still places them in 10A for the autumn term. A
published result is amended and the issued document is untouched — while
`outdated()` reports that it has been overtaken. A reprint after all of it is
byte-identical.

**And the line on the other side.** The institution rebrands; the letterhead
changes and not one grade does. A template that sets `freeze_branding` keeps the
identity that awarded it.

**Numbering, verification, withdrawal.** Numbers are sequential, never repeat,
and restart with the year when the series says so; a preview allocates none. A
verification code confirms who a document is about and whether it is still the
institution's current word, and the disclosed surface is pinned by a test rather
than sampled from a repr. A voided document still prints, with VOID across it,
and the application role cannot delete it at all.

**Authorization and entitlement, separately.** Permission to print report cards
is not permission to print transcripts. A guardian reaches documents about their
own child and the scoped count agrees with the scoped select. An institution
that switched the feature off cannot issue however permitted its registrar is.

**Two structural checks.** The renderer imports nothing that can reach a
database — a renderer that can query is one that will eventually be asked to
refresh the totals on a historical transcript. And a nursery designing a
document is never *offered* a credit summary or a grade-point average.

Fifteen sabotages, all caught.

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
| Scopes fail closed | Empty scope set made to compile to `true` | Two tests failed immediately |
| Scopes are per-permission | The permission filter removed from `scopes_for` | The widening test failed — the same defect that existed before this phase |
| A page total is scoped | The endpoint made to count the table | Flagged: the total exceeded what the caller could read |
| Out-of-scope and non-existent are the same answer | A 403 introduced for records that exist | Flagged on the byte-comparison of the two responses |
| Elevation is audited | The security event removed | Flagged |
| An unlisted limit is zero | Made to default to unlimited | Flagged — the failure mode of every entitlement system that defaults to allow |
| An institution cannot enable what it never bought | The setting made to override the plan | Flagged |
| Disabled and not-in-plan are different answers | Collapsed into one 402 | Two tests failed |
| `past_due` keeps the register | Made to stop entitling | Flagged |
| Absent concepts stay absent | Every concept the database supports made visible | Eight tests failed |
| Unpermitted capabilities are absent, not disabled | The permission gate removed | Two tests failed |
| An upgrade is shown only to somebody who could buy | Offered to everybody | Flagged: a teacher was handed a padlock |
| An institution cannot hide data it is using | Suppression made absolute | Flagged |
| A submitted register cannot change silently | The reason requirement removed | Flagged |
| Corrections leave a trace | The amendment write skipped | Flagged |
| An unexplained absence holds the register | The check removed | Flagged |
| Register membership is derived from the day | Made to list everyone ever in the group | Flagged — a register from before a child joined had her in it |
| A published result snapshots its grading | Band, points and pass flag left null | Two tests failed, including the one that moves a grade boundary afterwards |
| An amendment keeps the previous value | Previous score and band discarded | Flagged |
| An amendment needs a reason | The check removed | Flagged |
| An amendment needs authority | The permission check removed | Flagged |
| A correction leaves an audit event | The audit write skipped | Flagged |
| Publication needs the required approvals | Outstanding steps forced empty | Flagged — and `force` still did not cover it |
| A reprint reads the payload | `render` made to recompose from live data | Two tests failed, including the one that moves a grade boundary |
| Terminology is frozen at issue | Resolved at render instead | Flagged: a report card started using words the school adopted afterwards |
| Branding is *not* frozen | Frozen always | Flagged: a rebrand never reached an old document |
| Credits come from the snapshot | Read from the live course | Flagged on a transcript issued after a revaluation |
| An empty section is dropped | `omit_when_empty` disabled | Flagged: a school's report card grew a blank Credit heading |
| A nursery is not offered what it cannot use | `available_to` made to offer everything | Flagged |
| A configured sentence cannot reach attributes | `str.format` used on administrator text | Flagged: `{student_name.__class__}` resolved |
| A guardian reaches only their own child | The clause widened to every student | Flagged |
| Document numbers do not repeat | The counter made not to advance | Flagged |
| Verification does not disclose contents | A `payload` field added to `Verification` | Flagged by the pinned surface |
| The renderer escapes | Escaping removed | Flagged on a name containing markup |
| A draft template cannot issue | The status check removed | Flagged |
| Entitlement is checked | `billing.require` removed | Flagged |
| Placement is historical | Resolved from today's enrolment | Flagged — after the test was strengthened; see below |
| A mark is published once | The already-published guard removed | Flagged |
| **Routes cannot query a scoped table directly** | `from sqlalchemy import select as _select` in a handler | **Not caught.** The check listed unsafe call *names*, and a rename walked past it. Now inverted: every call taking a scoped model is suspect unless it is one of the four helpers that carry a predicate by construction. Re-sabotaged; caught |

---

## 6. The twelve critical journeys

| # | Journey | Status |
|---|---|---|
| 1 | Teacher marks attendance | ✅ **Covered — three requests, end to end** |
| 2 | Student submits an assignment | Phase 6 |
| 3 | Teacher grades a submission | Phase 6 |
| 4 | Admin publishes results | ✅ **Covered — with the workflow, the readiness review, and the six attacks** |
| 5 | Parent views a published result | ✅ **Scope covered — a guardian reaches published results and never a draft score, and reaches the documents about their own child and no others** |
| 6 | Admin issues a fee; parent sees it | Phase 3 |
| 7 | Parent records a payment | Phase 3 |
| 8 | School publishes a theme | Phase 7 |
| 9 | School renames a term; it propagates | Phase 2 |
| 10 | AI proposes a design; admin approves | Phase 7 |
| 11 | Admin bulk-imports students | ✅ **Covered — with the half-applied case attacked directly** |
| 12 | **Tenant A attempts to access Tenant B → fails** | ✅ **Covered, at both the database and HTTP boundaries** |

---

## 7. Gaps, stated plainly

**Two sabotages that did not fire, and what they were worth.** A sabotage that
passes is more useful than one that fails, because it names a test that was
never discriminating. Reading credits from the live course did not fail the
transcript test, because that test only inspected a payload frozen *before* the
revaluation — the assertion looked right and proved nothing. Resolving placement
from today did not fail the placement test, because the test issued the autumn
card before the transfer, so both readings gave the same answer. Both tests were
rewritten to act after the change rather than before it, and both sabotages then
fired. A third sabotage found machinery rather than a weak test: composition
suppressed sections whose academic layer had no rows, and removing that rule
changed nothing the `omit_when_empty` rule did not already do. It was deleted
(ADR-034).

Not yet written, because the features they would test do not yet exist:
authentication endpoint tests (login, refresh rotation, reuse detection,
lockout), scope-predicate leak tests, escalation and delegation-ceiling tests,
SSRF egress tests, AI approval-gate bypass tests, accessibility tests,
performance budget assertions, and E2E journeys 1–11.

Coverage percentage is not tracked and is not a goal. What is tracked is whether
each guarantee in `EDTECHX_SECURITY.md` §11 has a test that would fail if the
guarantee were removed.
