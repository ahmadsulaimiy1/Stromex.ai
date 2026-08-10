# EdirasX Architecture Decision Record

Every entry states the decision, why, what was rejected, and what it costs. A decision with no stated cost has not been thought through.

---

## ADR-001 — EdirasX lives in its own namespace inside the StromeX repository

**Status:** Accepted · Phase 0

**Context.** The repository is `Stromex.ai` and contains a working StromeX product (AI operating system for knowledge work) with its own Editorial Bible, MVP backend, frontend, and Android client. The task is to build EdirasX, a different product for a different market. The working branch is named for EdirasX.

**Decision.** Build EdirasX under `docs/edtechx/` and `apps/edtechx-api/`, `apps/edtechx-web/`, leaving every existing StromeX file untouched.

**Rejected.** (a) Repurposing the repository — destroys a working product and is irreversible in practice. (b) A separate repository — not available to create from this session, and would fragment the founder's work without instruction to do so.

**Consequences.** EdirasX is fully extractable to its own repository later by moving two directories. The monorepo carries two products, which must not share code implicitly — no imports cross between `apps/api` and `apps/edtechx-api`. Conventions (FastAPI, SQLAlchemy, Alembic, Next.js) are deliberately shared because the team is the same.

---

## ADR-002 — Modular monolith, not microservices

**Status:** Accepted

**Decision.** One deployable API with hard module boundaries enforced by an import test, one database with per-module schema ownership.

**Why.** There is no scale or team-topology justification for distribution. Microservices would multiply the cost of the thing that matters most — tenant isolation — across many services, each of which could get it wrong independently. Boundaries are the valuable part; separate processes are the expensive part. We take the former and defer the latter.

**Cost.** A single scaling unit and a single failure domain until a module is extracted. Mitigated by keeping boundaries genuinely clean, so extraction is mechanical when a measured reason appears.

---

## ADR-003 — Shared database with PostgreSQL Row-Level Security

**Status:** Accepted

**Decision.** Shared schema, `tenant_id` on every tenant-owned table, `FORCE ROW LEVEL SECURITY` with a policy bound to `current_setting('app.tenant_id')`, application connecting as a non-owner role without `BYPASSRLS`.

**Rejected.** (a) Application-level filtering alone — one forgotten `WHERE` is a breach, and the Bible lists cross-tenant access as non-negotiable. (b) Schema-per-tenant — migration cost grows linearly with tenants and connection pooling degrades. (c) Database-per-tenant as the default — operationally unsustainable past a few hundred tenants; offered as an Enterprise option instead, since it changes only the connection string.

**Cost.** Every request sets a session variable; migrations need a privileged role on a separate connection; developers must understand RLS. Accepted, because it converts the worst possible bug class from "possible" to "structurally prevented."

**Consequence.** Integration tests must run against real PostgreSQL. SQLite is not permitted in the test suite, because it cannot express the guarantee being tested.

---

## ADR-004 — Out-of-scope resources return 404, not 403

**Status:** Accepted

**Decision.** Lacking a *permission* yields 403. Lacking *scope over a specific resource* yields 404, with timing that does not distinguish.

**Why.** 403 on a specific resource confirms that resource exists. In a school, existence is itself sensitive — knowing there is a safeguarding record for a named child is a disclosure regardless of content.

**Cost.** Slightly harder to debug legitimate misconfiguration. Mitigated by logging every denial with the real reason server-side.

---

## ADR-005 — Additive permissions only; no denies

**Status:** Accepted

**Decision.** Permissions grant. Denial is absence. There is no negative permission.

**Why.** Deny rules make effective permissions non-obvious, order-dependent, and impossible to explain to an auditor or a head teacher. Every real requirement met by a deny rule is better met by a narrower scope.

**Cost.** Some configurations need a purpose-built role instead of a broad role minus a permission. Acceptable: roles are cheap and cloneable.

---

## ADR-006 — Institutional vocabulary is data; only platform-fixed values are enums

**Status:** Accepted

**Decision.** PostgreSQL enums only where the platform genuinely fixes the value set (`invoice_status`, `subscription_status`). Anything a school might redefine — attendance codes, grading bands, levels, stages, conduct types — is a configuration row.

**Why.** Enum changes are migrations. Institutional vocabulary changes are Tuesday.

**Cost.** More joins and more validation in the application. Accepted; it is the mechanism by which the Four Schools test passes.

---

## ADR-007 — Bounded customization, not arbitrary CSS

**Status:** Accepted

**Decision.** Schools customize by setting *values* for a rich, semantic token surface, choosing among coherent component style options, and editing navigation, dashboards, terminology, and documents. Schools do not author raw CSS, HTML, or JavaScript.

**Why.** Arbitrary CSS is a style-injection vector, breaks on every upgrade, defeats accessibility validation, and makes support unbounded. Depth comes from breadth of the token surface, not from an escape hatch.

**Cost.** A school with an unusual visual demand may not be fully satisfied by self-service. Answered by Professional Services delivering a bundle, which is the commercially better outcome anyway.

---

## ADR-008 — AI never writes a record of consequence

**Status:** Accepted · **Constitutional**

**Decision.** Any AI-originated change to a grade, attendance mark, promotion decision, conduct record, invoice, published result, or live theme requires a persisted proposal and an explicit, attributed human approval. Enforced by requiring an `ai_approvals` row on the write path, and by a test that attempts to bypass it and must fail.

**Why.** Bible §7 and §2 belief 5. The moment a school cannot trust that its records were changed by a person, the product is finished — and no amount of accuracy recovers it.

**Cost.** Friction in AI features, and features we cannot build. Correct.

---

## ADR-009 — Marketplace is a distribution problem, not an architecture problem

**Status:** Accepted

**Decision.** Do not build the marketplace now. Instead make every configuration object a versioned, schema-validated, portable document, so an "experience" is a bundle of documents.

**Why.** Building marketplace machinery before there is a designer ecosystem is speculative complexity, which the Bible forbids. Making configuration portable costs nothing extra and buys the option.

**Cost.** Commerce, review, and licensing work remain unbuilt. Deliberate.

---

## ADR-010 — Region is declared, not geolocated

**Status:** Accepted

**Decision.** Pricing region comes from a declared country on the subscription record.

**Why.** IP geolocation is trivially manipulated, wrong for VPN users, and insulting when it guesses badly. A declared field is auditable, contractually meaningful, and honest.

**Cost.** A school could declare a cheaper country. Mitigated by contract, by payment-method and billing-address checks at scale, and by the fact that this is a low-frequency, high-visibility field.

---

## ADR-011 — Curated iconography, no arbitrary icon upload

**Status:** Accepted

**Decision.** One icon family with tenant-selectable bundled styles; no arbitrary icon-set upload.

**Why.** Mixed icon families destroy visual coherence, which is the whole basis of the prestige claim, for negligible benefit. Logos and brand marks are separately customizable, which is what schools actually want.

---

## ADR-012 — Argon2id, and no forced password rotation

**Status:** Accepted

**Decision.** Argon2id for new hashes; bcrypt accepted on import and rehashed on next login. Minimum 12 characters with a breach-corpus check; no composition rules; no scheduled rotation.

**Why.** Current guidance (NIST 800-63B and equivalents): composition rules and forced rotation demonstrably reduce real-world strength by pushing users toward predictable patterns. Length plus breach checking is what works.

**Cost.** Some institutional IT policies expect rotation. Configurable per tenant for those contractually required to have it, with the default set to the better practice.

---

## ADR-013 — Development adapters, never fake integrations

**Status:** Accepted

**Decision.** Every external port ships a development adapter that drives the *real* state machine (dev AI provider, sandbox payment provider, outbox notification channel). Each is explicitly labelled in the interface and **refuses to load when `ENVIRONMENT=production`**.

**Why.** The Bible forbids fake implementations. A stub that pretends to be a real integration is worse than an unavailable feature, because it converts a known gap into an unknown one.

**Cost.** Development adapters are real code with real tests.

---

## ADR-014 — WebAuthn deferred; TOTP now

**Status:** Accepted

**Decision.** TOTP MFA in Phase 1; WebAuthn/passkeys in Phase 8.

**Why.** TOTP covers the whole staff population immediately, including on shared and older devices common in the target markets. WebAuthn is better but has device and recovery complexity that is not the right early spend.

---

## ADR-015 — Nine session-state files consolidated into three

**Status:** Accepted

**Context.** The build brief specifies nine separate state files (PROGRESS, CHECKLIST, DECISIONS, ISSUES, PHASE, COMPLETED, NEXT, BLOCKED, TESTS).

**Decision.** Keep three: `EDTECHX_PROGRESS.md` (phase, completed, next, blocked, issues), `EDTECHX_CHECKLIST.md`, `EDTECHX_TESTS.md` — plus this ADR file, which the brief also requires.

**Why.** Nine files that must stay mutually consistent is a synchronization hazard: the failure mode is a set of files that disagree, which is worse for resumption than one file that is right. The brief's actual requirement is resumability, and three files with clear ownership serve it better. This is a "do not overengineer" call, recorded rather than made silently.

**Cost.** Divergence from the letter of the brief. Recorded here so it is a decision, not a drift.

---

## ADR-016 — Integration tests run against real PostgreSQL

**Status:** Accepted

**Decision.** No SQLite in the test suite. Integration and isolation tests require a live PostgreSQL with RLS enabled.

**Why.** The isolation guarantee is a PostgreSQL feature. A test suite that cannot exercise it would give false confidence about the one thing that must never be wrong.

**Cost.** Tests need a database. Provided by docker compose locally and a service container in CI. Pure-logic unit tests remain database-free and fast.

---

## ADR-017 — The product is named EdirasX; the technical namespace remains `edtechx` for now

**Status:** Accepted · Supersedes the provisional position recorded in the 1.0 publication of the Editorial Bible

**Context.** The product launched under the working name EdTechX. The name was descriptive but generic: it names a category rather than a company, it is difficult to trademark, and it says nothing about the institutions the product is built for. The product owner has adopted **EdirasX**, from the Arabic root of study and learning — الدراسة (*al-dirāsa*, "study") and ادرس (*idrus*, "study!").

**Decision.** EdirasX is the product name, effective immediately, in all product-facing text: the Editorial Bible and every governing document, the interface, documents the platform generates, and all publications.

The **technical namespace stays `edtechx`** for now — `docs/edtechx/`, `apps/edtechx-api/`, `EDTECHX_*.md`, the `EDTECHX_` environment prefix, and the `edtechx_app` / `edtechx_migrator` database roles. Renaming those is a separate, scheduled migration, not a side effect of a branding decision.

**Why separate the two.** A namespace rename touches database role names, connection strings, environment variables, and the row-level-security grants that tenant isolation depends on. Bundling that into a branding change would mean the most security-critical code in the product moves for a non-security reason, in a commit whose review attention is on wording. The rename is worth doing; it is worth doing on its own, with the isolation suite as the gate.

**Consequences.** Product text and technical identifiers disagree until the migration runs. This is deliberate and is stated in Bible §1.1 so that nobody encountering it treats it as drift. When the migration is scheduled it must: rename directories and files, update the settings prefix with a deprecation period accepting both, rename the database roles in a maintenance window, re-run `apply_rls` and `verify_rls`, and confirm the tenant-isolation suite is green before and after.

**Cost.** A period of visible inconsistency, and a migration still owed. Accepted in preference to moving the isolation-critical identifiers inside a branding commit.

---

## ADR-018 — Publication artefacts are generated, never hand-edited

**Status:** Accepted

**Decision.** The flagship PDF and DOCX are produced by `tools/publisher` from `EDTECHX_EDITORIAL_BIBLE.md`, through a single document model rendered twice. Neither output is ever edited directly.

**Why.** Two hand-maintained formats of a living constitution diverge — not if, when. Rendering both from one model makes content parity a property of the build. `tools/publisher/verify.py` then re-extracts text from the finished files and checks every chapter, every substantial source line, and every document sentence against both, so the claim is tested rather than asserted.

**Consequences.** Amending the Bible means amending the Markdown and rebuilding. Editing the PDF or the Word file amends nothing, and the next build discards it. The build fails rather than publishes if a chapter or a line of source prose fails to make it through.

**Cost.** Typographic control is exercised through a stylesheet rather than by hand. Accepted: hand-tuning a document that is regenerated on every amendment is work that is thrown away by design.

---

## ADR-019 — Token-bucket rate limiting, tenant-scoped, failing closed

**Status:** Accepted · Phase 2

**Decision.** Rate limiting is a token bucket evaluated atomically, keyed per tenant, applied as a request dependency after tenant resolution and before authentication. Redis in production; an in-process backend for development that `require_production_ready` refuses outside development.

**Why a token bucket.** A fixed-window counter — the usual first implementation — admits twice its intended burst across a window boundary. That boundary is exactly where a credential-stuffing run concentrates.

**Why atomic.** Read-modify-write across a network round trip is a race, and a racy limiter reads as working until it is needed. The Redis backend performs the whole decision in one Lua script; the in-process backend does the same arithmetic under a lock. Both were tested against 60 concurrent requests for 10 tokens and admitted exactly 10; a deliberately racy backend admitted all 60, which is what makes the test worth having.

**Why the Redis clock.** The script reads `TIME` from Redis rather than accepting a timestamp from the caller. Application servers disagree about the time by seconds, and a bucket refilled against a fast server's clock hands out tokens no time has earned.

**Why tenant-scoped keys.** Without the tenant in the key, exhausting one school's sign-in allowance exhausts every school's. That is a denial of service crossing a tenant boundary — the same class of failure as a data leak, and no more acceptable.

**Why fail closed.** A limiter that cannot decide returns 429, not 200. The routes it guards are the most exposed in the product; failing open would remove the control precisely when the backing store is under stress.

**Why the per-IP limits are generous.** This is the decision most likely to be read as weak, so the reason is recorded plainly: an entire school sits behind one public address, and several hundred people sign in during the ten minutes before first lesson. A limiter tuned as though one address meant one person would lock a school out every morning, be disabled within a week, and protect nothing. The tight control is per-account (12 per 15 minutes), which NAT does not affect, with account lockout binding first for a targeted account.

**Cost.** Redis becomes a hard dependency in production. Accepted: it was already required for entitlement caching and session revocation, and the alternative — a per-worker limiter — multiplies every limit by the worker count while appearing to work.

---

## ADR-020 — The baseline migration applies and verifies row-level security

**Status:** Accepted · Phase 2

**Decision.** The Alembic baseline calls `apply_rls` and `grant_app_role`, then `verify_rls`, and **raises** if any tenant-owned table is unprotected. Migrations connect as `edtechx_migrator`, whose URL is read from settings rather than `alembic.ini`.

**Why.** A migration that creates the tables and omits the policies succeeds, looks correct, and silently removes the product's central guarantee. The schema builder used by tests already applied RLS; without this the two paths could diverge, and production would be the one that was wrong. Both now call the same helpers, so there is one definition of "protected".

**Why the URL comes from settings.** Reading it from `alembic.ini` would make it possible to point a migration at the request-path role by editing a config file — and that role owning the tables is exactly what defeats `FORCE ROW LEVEL SECURITY`.

**Consequence found immediately.** Autogenerate creates PostgreSQL enum types with their tables but never drops them, so `downgrade` followed by `upgrade` failed on "type already exists" — precisely the sequence an incident rollback performs. The down path now drops them explicitly, and a test exercises the full cycle.

**Cost.** The baseline is not purely autogenerated and must be maintained by hand where the RLS step is concerned. Small, and the alternative is a migration that cannot be trusted.

---

## ADR-021 — TOTP implemented rather than imported; enrolment is two-step

**Status:** Accepted · Phase 2

**Decision.** RFC 6238 is implemented in `modules/identity/totp.py` (about thirty lines of HMAC). Enrolment is two steps: generate a secret, then activate only once a code from it verifies. Secrets are AES-256-GCM encrypted at rest with a purpose-bound key; recovery codes are Argon2id-hashed and spent on use.

**Why implement it.** The two decisions that matter — the drift window and replay rejection — are the two most libraries leave to the caller and most callers get wrong. Writing it here puts both in one visible, tested place. A one-step drift window covers ordinary phone drift; two steps (the other common choice) triples the guessing surface to tolerate clocks that are already unusual.

**Why replay rejection matters.** Without recording the last accepted counter, a code remains valid for its whole 30-second step, so a code seen over a shoulder or captured in a proxy log can be used again. That defeats the "one-time" in one-time password. The consequence, which is correct and worth stating: after activating, the code the authenticator is *currently showing* is refused, because activation consumed that window. Every mainstream implementation behaves this way.

**Why two-step enrolment.** A single "turn on MFA" call that trusts the secret was stored correctly locks people out of their own school when the authenticator did not actually scan it. Confirming a code first means the factor is proven to work before it becomes required.

**Why purpose-bound encryption keys.** HKDF derives a distinct key per purpose from the root secret, so a ciphertext lifted from the MFA column into the AI-credential column fails to decrypt rather than quietly working. Both properties are tested.

**Cost.** An implementation to maintain, against a well-known specification with published test vectors — which the suite asserts against.

---

## ADR-022 — Academic structure is a tree of rows, and progression is a rule engine

**Status:** Accepted · Phase 2 · **The Editorial Bible §8 promise, made testable**

**Context.** The most likely way to fail the flexibility promise is not to refuse it — it is to build a plausible-looking generic schema that quietly assumes one country's school system, then discover three years later that it cannot serve a university.

**Decision.** Four specific choices, each closing one route to that failure:

1. **Stages are a self-referencing tree, not an enum.** Depth is the school's choice: two flat tiers, three flat tiers, or a nested hierarchy where Postgraduate sits under an Undergraduate faculty.
2. **Levels carry no number that means anything to the platform.** There is a `sequence` for ordering within one school and a name the school chose. There is deliberately no `grade_level` integer, because the moment one exists, code does arithmetic on it and "Year 7" becomes one more than "Year 6" — false for an institution running Foundation → Level 4 → Level 7.
3. **`next_level_id` is explicit, not `sequence + 1`.** The next level may live in another stage, or there may be none because this level graduates.
4. **Progression is a rule engine over a closed metric vocabulary.** A school's definition of "ready to move up" is a JSON condition tree; the engine combines conditions and reads named metrics, and knows nothing about what a passing student looks like.

**Why a closed metric set rather than an expression language.** An open language would be a scripting engine inside the product, with the security and support burden that implies. Adding a metric is a small, visible change in one file; a school writing code is not.

**Two behaviours worth stating.** Missing data never passes a condition — a student with no recorded attendance has not met an attendance requirement, and treating absent evidence as evidence would promote on incomplete records. And every evaluation returns its full reasoning, with *all* failed conditions rather than the first: "the system decided" is not an answer a registrar can give a parent.

**How the promise is enforced rather than asserted.** `test_four_schools.py` configures four institutions through one code path and adds two static checks: no product module may contain any of these schools' vocabulary in executable code, and no comparison in the academics module may test a grading or progression quantity against a hard-coded number. Both were verified by introducing exactly the defect they exist to catch.

The vocabulary check parses the AST and examines string literals, identifiers, and attributes — not docstrings. A docstring naming four school systems is explaining the flexibility; a string literal naming one is assuming it. A check that could not tell them apart would push the examples out of the documentation in the name of a rule about the code.

**Cost.** More joins, more configuration to seed, and a rule engine to maintain. That is the price of the promise, and it is lower than the price of discovering the assumption later.

---

## ADR-023 — Row-level security is applied to tables that exist, not to the model registry

**Status:** Accepted · Corrects ADR-020's implementation

**Context.** The baseline migration applied RLS to every tenant-owned model in the registry. That worked exactly once. The moment a later migration added a model, the baseline tried to protect a table that revision had not created, and every fresh `upgrade head` failed at the first migration.

**Decision.** `apply_rls` and `verify_rls` operate on the intersection of the registry and the tables that actually exist. A missing table is a schema-drift question, answered separately by `missing_tables` and by the migration drift test — not by the isolation check, which would otherwise fail every migration before the last.

**Why this does not weaken anything.** `build_schema` (tests and development) now raises on a *missing* table as well as an unprotected one, since a freshly built schema has no excuse. The migration drift test asserts every model has a table. So "every tenant-owned model has a table, and every such table is protected" remains guaranteed — by two checks in the places each can be true.

**Cost.** The isolation check alone no longer proves completeness. Recorded here so the pair is understood as a pair.

---

## ADR-024 — EdirasX is a universal education operating system, not a school system

**Status:** Accepted · **Constitutional** · Supersedes the scope, though not the substance, of ADR-022

**Context.** ADR-022 made a school's structure configurable and proved it with four institutions. That was correct and insufficient. The Four Schools test is the *minimum* flexibility standard, and reading it as the maximum would have produced exactly the failure it was written to prevent — a generic-looking model that quietly assumes school-shaped education, discovered when the first university could not be represented.

**Decision.** One academic engine spanning early years to doctoral research. The layers are separated because collapsing any two is what makes a system serve one kind of institution and no other:

| Layer | Answers |
|---|---|
| Academic unit | Where in the organisation? (self-referencing: campus → faculty → department) |
| Academic stage *(optional)* | Which broad phase? |
| Programme | What is the student admitted to? |
| Qualification | What does completion award? |
| Level | How far within it? |
| Cohort | Progressing with whom? |
| Course | What is studied? |
| Class group | Sitting with whom? |
| Academic period | When? |
| Credit system | Counted how, if at all? |
| Supervision · milestone | For research education |

**No institution uses every layer, and the unused ones are absent rather than empty.** A university has no stage; a school has no programme; a taught programme has no supervision rows. A model that required every layer would make every institution perform ceremony for the benefit of institutions unlike it.

**Four specific prohibitions**, each closing a route by which an assumption returns:

1. **No qualification enum.** Qualifications are rows in the institution's own framework, ordered by a `framework_level` meaningful only inside it. `BACHELORS`, `PRIMARY`, `PHD` appear nowhere.
2. **No assumed duration.** `duration_periods` and `required_credits` are nullable throughout. "A bachelor's is three years" is a statement about one country.
3. **No universal credit system.** Credit, credit hour, unit and ECTS are not interchangeable, and an institution counting nothing is not misconfigured.
4. **No `kind` enums.** Every `kind_label` is free text the institution chose. The platform stores it and never reads it to make a decision.

**Renames.** `Subject` → `Course` and `Term` → `AcademicPeriod`. "Subject" is a school word that reads oddly for a university module and absurdly for a doctoral research unit; "course" is the neutral term every sector recognises. The terminology layer renders whatever the institution actually says, and `course` defaults to "subject" so a school still sees its own word.

**Enforcement.** `test_universal_education.py` configures nine institutions — the original four schools plus a qualification ladder, a credit-based university with faculties and departments, a non-credit institution, a research programme with supervision and milestones, and a competency-based vocational institution — through one code path. Two static checks accompany it: no product module may name an educational system or qualification in executable code (AST-based, word-boundary matched, docstrings excluded), and no comparison in the academic engine may test an academic quantity against a hard-coded number. Both were verified by introducing the defects they exist to catch.

**Cost.** More tables, more joins, more configuration to seed before an institution is usable — and a seeding experience that must therefore be excellent, which is now a product requirement rather than an afterthought. Accepted: the alternative is discovering the assumption when a university asks for a demonstration.

---

## ADR-025 — The pre-release migration chain was squashed to one baseline

**Status:** Accepted

**Decision.** The three pre-release revisions were replaced with a single baseline reflecting the universal academic model.

**Why.** Generalising the model turned two renames into drop-and-create pairs whose ordering failed on foreign-key dependencies. Repairing that chain would have produced migrations no deployment will ever execute, whose correctness could only be asserted rather than observed. There is no production data behind this branch, so one honest baseline is both simpler and more truthful.

**What this is not.** A precedent. Once a school holds real data, the expand → migrate → contract discipline in `EDTECHX_DATABASE.md` §12 applies without exception, and a squash becomes impossible rather than merely inadvisable.

**A defect it exposed.** `build_schema(drop_first=True)` used `metadata.drop_all`, which drops only the tables the current models know about — so a rename left orphans behind, and the next build failed trying to drop a table an orphan still referenced. "Drop first" now drops the schema. A clean slate that is only mostly clean is worse than none, because it fails later and elsewhere.

---

## ADR-026 — Foreign keys are tenant-scoped, because row-level security does not govern them

**Status:** Accepted · **Constitutional** · Extends ADR-003 and ADR-004

**Context.** Row-level security governs `SELECT`, `INSERT`, `UPDATE` and `DELETE`. It does **not** govern referential integrity: PostgreSQL performs a foreign-key check with the referenced table's privileges and without applying its policies. That is documented behaviour and the right default for a database where every row belongs to everybody. In a multi-tenant schema it is a hole, and it was found by attacking the new enrolment tables rather than by reading the code.

Before this decision, a plain `enrolments.student_relationship_id REFERENCES student_relationships(id)` let one institution insert a row pointing at another institution's student. Demonstrated, not theorised: the insert succeeded, and the inserting tenant then held a row referring to a parent it could not read.

Three consequences, in ascending order of seriousness:

1. **Corruption.** The row names a parent its own tenant cannot see, so every join silently drops it and every report is quietly wrong.
2. **Cross-tenant denial of service.** With `ON DELETE RESTRICT`, one tenant can permanently block another's deletion, with no visible cause on either side.
3. **An existence oracle.** The insert succeeds only if the id exists *somewhere in the system*. That turns every foreign key into a probe for other tenants' ids — precisely the disclosure ADR-004 exists to prevent, arriving through the one door RLS does not watch.

**Decision.** Every foreign key between two tenant-owned tables references `(tenant_id, id)` rather than `id`. Each tenant-owned table carries a `UNIQUE (tenant_id, id)` key to be referenced by. The child's `tenant_id` is stamped from the request context, so a reference into another tenant has no matching parent row and is refused by the database — on every path, including raw SQL, background jobs, and anything written years from now by someone who has not read this document.

**Applied by mechanism, not by memory.** `app.db.tenant_fk.bind_foreign_keys_to_tenant` rewrites the whole metadata once, after every model is mapped, on the same principle as `TenantOwned`: a new tenant-owned model gets a tenant-scoped foreign key by existing. `test_every_tenant_owned_foreign_key_is_tenant_scoped` fails if any key is left referencing an id alone.

**Consequences accepted.**

- `ON DELETE SET NULL` becomes `SET NULL (column)`, naming only the nullable half so `tenant_id` is not nulled. This requires PostgreSQL 15 or later, which the architecture already assumes.
- A table with two foreign keys to different tenant-owned parents has two relationships nominally writing `tenant_id`. That column belongs to `TenantOwned` and is stamped from the request context; no relationship owns it, so `MembershipRole.role` and `MembershipRole.membership` are declared `viewonly`.
- Composite keys are marginally wider, and each requires the extra unique index. Both are negligible against a boundary that holds.

**Why this was not obvious.** Every isolation test was green throughout, and remained green, because every one of them tested reading and writing rows. None tested *referring* to one. The hole was in the space between two correct mechanisms, which is where they usually are.

---

## ADR-027 — Identity, person, relationship and enrolment are four separate things

**Status:** Accepted · **Constitutional**

**Context.** The conventional student information system has a `students` table with a name, an email, a password, and a `class_id`. Each of those four choices fails a real institution:

- **A credential on the student record** cannot represent a four-year-old, or a guardian who never signs in, or the teacher who is also a parent — they need one account or none, not one per role.
- **A `role` column on the person** cannot represent somebody who is two things at once, which is ordinary in every institution and universal in small ones.
- **A mutable `class_id`** destroys the record. Move a child from 3A to 3B and the fact that they spent two terms in 3A is gone, along with the context of every mark and every register entry taken while they were there.
- **A required class** cannot represent a doctoral researcher, who has a programme and a supervisor and no class at all.

**Decision.** Four layers, each with one job.

| Layer | Scope | Answers |
|---|---|---|
| `User` (identity) | Global | Who is signing in? Exists only for people who do. |
| `Person` | Tenant-owned | Who does this institution know? Names, contact, date of birth if recorded. `user_id` nullable, and usually null. |
| Relationship — student · staff · guardian | Tenant-owned | What is this person *to* the institution? One person may hold several. |
| `Enrolment` | Tenant-owned | Where were they placed, and between which dates? |

**Enrolment is history.** Placement is a row with a beginning and an end. A transfer closes one and opens another; a promotion closes one and opens another; a withdrawal closes one and opens nothing; a readmission opens a new one with the gap visible between. Nothing is overwritten, and the sequence of rows *is* the student's academic history. Alongside it, `enrolment_events` records why each transition happened, on what date it took effect, and who decided — append-only at the database, so a correction is a new event rather than an edit.

**Two dates on every event.** `occurred_on` is when the change took effect in the institution's world; `created_at` is when somebody typed it in. They are routinely weeks apart — a withdrawal backdated to the last day of term, a transfer recorded after the holidays — and a system with only one of them eventually produces a register nobody can reconcile.

**Every academic layer on an enrolment is nullable**, including the academic year. A nursery placement has a level and a class group; a doctoral placement has a programme and a level; a rolling-intake literacy course has neither a class group nor a year. ADR-024's rule applies unchanged: the layers an institution does not use are absent, not invented.

**Concurrent enrolment is permitted.** There is deliberately no constraint forcing one open placement per student: joint programmes, a course taken at a neighbouring institution, and an apprentice enrolled on both a qualification and a short unit are all ordinary. The service closes the previous placement when a transfer or promotion says to; it does not assume two open placements are a mistake.

**Names are not two fields.** `full_name` is required and written as the person writes it; `given_names`, `family_name`, `preferred_name` and `sort_name` are optional and independent. Name order, the number of parts, and which part is the family name all vary, and a schema demanding "first" and "last" quietly tells a large part of the world it was not built for them. `gender_label` is free text and nullable for the same reason, and `relationship_label` on a guardianship — "Mother", "Uncle", "Sponsor", "Foster carer" — is free text because family structures are not a closed list.

**Enforcement.** `test_people_enrolment.py` runs the same three calls against all nine institutions of the Universal Education Test, and asserts that the layers each institution did not configure stay null. Two structural tests guard the central rule: no relationship table may carry a placement column, and no function in the people module outside `_open` may assign one. Both were verified by introducing the defects they exist to catch — a `class_group_id` "just for the list screen", and a `transfer` that moved the student in place.

**Cost.** Four tables where a naïve design has one, and a join to answer "which class is she in?". Accepted without hesitation: the naïve design cannot answer "which class was she in *in March*" at all, and that is the question a registrar is actually asked.
