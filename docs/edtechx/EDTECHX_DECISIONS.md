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

---

## ADR-028 — An import lands entirely or not at all

**Status:** Accepted

**Context.** A school's data arrives in bulk exactly once — at the start — and that is the moment its records are most fragile and least reviewed. The brief's requirement is one sentence: *never allow a malformed import to partially corrupt a school's records without an explicit, well-designed workflow.*

The failure to design against is not a bad file. It is a *half-applied* one. Four hundred students exist and the rest do not; nobody who was not watching can tell which; re-running the file creates four hundred duplicates; and the school discovers this in week three when a register is short.

**Decision.**

1. **Reading is not deciding.** A file is read, mapped and validated without touching anything. The result is a preview with every problem in it — all of them, per row, with the file's own line numbers.
2. **Applying is one transaction.** Every row lands or none does. An import with any invalid row is refused outright rather than applied in part, and an unexpected failure part way through rolls the whole thing back and records why.
3. **A dry run is the same code as the real run.** It performs the identical writes inside a savepoint and rolls back. A dry run down a different path is a rehearsal in a different building.
4. **A reversal is explicit, and refuses when it cannot be honest.** An import that has been built upon — a child moved, a placement progressed — cannot be undone by deletion without destroying records that are not the import's to destroy. `blockers()` says what stands in the way; `reverse()` refuses rather than choosing between two kinds of damage. Where it does proceed, people are soft-deleted and enrolments are *withdrawn*, because `enrolments` holds no `DELETE` grant (ADR-027) and an import's mistake does not change that.

**Three judgements worth recording.**

*Formula detection is narrower than the usual advice.* The standard rule rejects any cell beginning `=`, `+`, `-` or `@`. A great many real telephone numbers begin with `+` and a great many real figures begin with `-`, so a leading `+`/`-` counts only when what follows could start a function name. Rejecting every Nigerian mobile number to mitigate a risk that lives at *export* time would be a security control that breaks the product.

*Column-heading aliases are sector-neutral, and the institution's own words come from its terminology.* Writing "homeroom" and "arm" into an alias list would have put one country's vocabulary back into executable code, and the static check in `test_universal_education.py` would have been right to fail it. Instead `propose_mapping` consults the configured vocabulary: a school that calls a class an "arm" gets a column headed "Arm" recognised *because it said so*. This is better than the hard-coded list in every respect — it covers institutions we never thought of.

*There is no "update on duplicate" option yet.* Merging two records is a decision with consequences — whose date of birth wins, what happens to the absorbed record's enrolment history — and offering it as a checkbox before that workflow exists would quietly overwrite correct data with a spreadsheet's. Duplicates are skipped or refused; merging gets its own design.

**Enforcement.** `test_bulk_import.py` — 34 tests, built from the files schools actually send: a byte-order mark, semicolons, a title row above the header, a repeated heading, an admission number Excel turned into a float, a phone number beginning with `+`, a class code the school does not have, the same child twice. Three sabotages confirm the safety properties are load-bearing: committing each row as it goes, applying past known-invalid rows, and reversing without checking what has been built on top. All three were caught.

---

## ADR-029 — Scopes compile to SQL, resolved per permission, failing closed

**Status:** Accepted · **Constitutional** · Completes ADR-005 and ADR-004

**Context.** A permission answers *may this person do it*. A scope answers *to which records*. Until this decision the second was parsed and unioned but never enforced, and the way it was carried made enforcement impossible: `_load_grants` merged every grant's scope into one set and discarded the ids.

That was not merely incomplete. It was a live widening defect. A teacher who also held a school-wide role — for announcements, say — read as **unrestricted**, because the union contained a `tenant` scope. Had a scoped list endpoint existed, it would have handed them every student record in the institution on the strength of a permission to write notices.

**Decision.**

1. **Scope is a property of a grant, never of a person.** The principal carries its grants unmerged (`core.context.Grant`), and `authz.scopes.scopes_for(principal, permission)` returns only the scopes attached to grants that actually confer that permission — expansion included, so `people.student.manage` carries its scope to a read. A broad scope on one permission cannot widen another.

2. **A scope becomes a `WHERE` clause.** `authz.predicates` compiles a `ScopeSet` into SQL. Rows the caller may not see never enter the result set, so they are not in the process, the log line, the page total, or whatever the next handler does with the list.

3. **Fail closed on every path.** No principal, no scopes, an unknown scope kind, a resource with no clause for the kind held — every one yields `false`. `true` is reachable only from an explicit `tenant` scope on a plan that permits it, or from an audited `system_access` block. A clause builder that returns `true` raises rather than widening.

4. **The plan belongs to the module that owns the table.** `authz` owns the vocabulary and the composition; `people.scopes` owns the joins. Anything crossing into academics comes from `academics.service` as a `Select`, so the boundary composes into one statement without a module importing tables it does not own.

5. **Composition: union within a permission, intersection between concerns.** Two department scopes reach both departments. Everything else `AND`s and cannot be loosened by a scope — the tenant predicate (RLS, in the database), the permission check (before the query), and any filter the caller adds. A scope only ever narrows.

6. **Elevation is explicit, tenant-bound and audited.** `system_access(reason=...)` is the only way a scopeless read succeeds. It refuses without a tenant — it widens reach within one school, never across two — refuses without a reason, and writes a `system_access` security event. A background job that forgets it reads *nothing*, which fails visibly on the first run instead of invisibly forever.

**Two judgements recorded, because neither is recoverable from the SQL.**

*Scope follows the open placement.* A teacher allocated to 7B reaches the children in 7B now, not a child who left in October. A scope that quietly accumulated everyone who ever sat in the room would grow for years without anybody deciding it should. Historical reach is a separate permission. The one exception is the enrolment plan's unit clause, which reads the placement directly — a head of department asks "which placements were in my department", and the answer must include the ones that ended.

*`subject` is deliberately absent from the student plan.* A subject scope says which courses somebody may configure. Letting it through would turn "may edit the Chemistry syllabus" into "may read every chemistry student's record".

**This complements row-level security; it does not replace it.** RLS is the tenant boundary, enforced by PostgreSQL on every path including raw SQL, and remains load-bearing. Scope is the boundary *within* a tenant, enforced in the query the application builds — which is why `scoped_select`, `scoped_count`, `scoped_get` and `scoped_exists` are the sanctioned path and why `test_boundaries.py` fails any route that queries a scoped table directly.

**Enforcement, and one lesson about enforcement.** `test_scope_predicates.py` — 36 tests across every scope kind, composition, leakage through counts, aggregates, pagination, search and error shape, cross-tenant attempts with a genuinely valid token, and the elevated context. Five sabotages were caught: a fail-open default, scopes unioned across permissions, a count over the table, a 403 that distinguished "out of scope" from "does not exist", and elevation without an audit record.

The sixth was not. A route was made to query the table directly with `from sqlalchemy import select as _select`, and the structural check — which listed the *unsafe* call names — walked straight past it. The check now inverts: every call taking a scoped model is suspect unless it is one of the four helpers that carry a predicate by construction. A check a rename defeats is a check that measures nothing, and that is worth more than the defect it missed.

**Cost.** Every scoped read goes through a helper, and every new scoped resource needs a plan. Both are the point: the helper is the thing that cannot be used without producing a predicate, and a resource with no plan is unreadable rather than unprotected.

---

## ADR-030 — Entitlement is not authorization, and neither implies the other

**Status:** Accepted · **Constitutional**

**Context.** Seven things are routinely collapsed into one boolean, and each collapse breaks something specific:

| Concept | Question | Where it lives |
|---|---|---|
| Identity | Who is signing in? | `identity.User` |
| Role | Who is this person here? | `authz` role grants |
| Permission | May they perform this action at all? | `authz.permissions` |
| Scope | Over which records? | `authz.predicates` (ADR-029) |
| Entitlement | Has the institution bought this? | `billing` |
| Feature availability | Has the institution switched it on? | `billing`, and **not** the same question |
| Usage limit | How much may be consumed? | `billing`, and not that question either |

**Decision.** Two one-way rules, both enforced by keeping the checks separate.

*A permission is not an entitlement.* A registrar may be entirely entitled to publish AI-drafted comments while the school has not bought the assistants. The answer is **402** with an upgrade path, not 403.

*An entitlement is not a permission.* Buying the Design Studio must never make a teacher able to rebrand the platform. The entitlement engine has no opinion about who may act, which is exactly right.

**Permission is checked before entitlement**, a deliberate departure from the order in `EDTECHX_PERMISSION_MODEL.md` §5. Two reasons agree: a permission check is a set-membership test and an entitlement check is a database read, so permission first is cheaper; and answering 402 to somebody who could never use the feature anyway tells them what their school has and has not paid for.

**Four negative answers, not one.** `no_subscription`, `not_in_plan`, `disabled_by_institution`, `limit_reached` — asked in that order, so a school is never told it disabled something it could not have had. They map to three HTTP answers because the reader is three different people:

- **402** — upgrade the plan. Said to the person who signs cheques.
- **403** — an administrator switched this off. Said to the person down the corridor. Telling a teacher to upgrade a plan their school already pays for sends them to the wrong person and implies a cost that does not exist.
- **429** — this period's allowance is spent. Said to nobody; it resolves when the period rolls.

**Feature availability is a fourth table, and the asymmetry is the point.** `feature_settings` can only ever *disable*. An institution enabling something its plan does not include would put the entitlement boundary inside the tenant, and plans are the one thing a school must not be able to write to — which is why `plans`, `plan_features` and `plan_limits` are the only non-tenant-owned tables in the module.

**A limit and a meter look alike and behave differently.** A limit is a ceiling on a standing quantity (students on the roll); a meter is a rate over a billing period (AI tokens). A school with 400 students on a 150 plan is over its limit and **must still be able to take a register** — that is a commercial workflow, not an authorization decision. A school that has spent its tokens simply cannot spend more until the period rolls. Modelling them as one forces the same answer to both, and one of those answers is always wrong.

**Three further choices worth recording.**

*`past_due` still entitles.* A card that expired must not lose a school the register on Monday. Dunning is a workflow; withholding a child's attendance record to collect a debt would be indefensible.

*A limit the plan never mentions is zero, not unlimited.* Silence is not generosity. Defaulting to "allow" when no row is found is the failure mode of every entitlement system that has one.

*Recording usage does not check the ceiling.* A caller asks before doing the expensive thing and records after it succeeded. Merging the two would either bill for work that failed or refuse work already done.

**Enforcement.** `test_entitlements.py` — 29 tests over both one-way rules, all four negative answers, the limit/meter distinction, overrides and their expiry, subscription states, and cross-institution isolation. Four sabotages caught: an unlisted limit defaulting to unlimited, an institution enabling what it never bought, the disabled/not-in-plan answers collapsed into one, and `past_due` withholding the register.

A fifth finding came from the tests rather than from a sabotage: the check forbidding plan names outside the billing module flagged the `institution.*` **permission** module. Rather than loosen it, plan keys are now prefixed `plan.` so a plan key reads as one everywhere it appears and the check can be exact. A check that cries wolf gets deleted rather than obeyed.

---

## ADR-031 — Complexity must be capability, never burden

**Status:** Accepted · **Constitutional** · The interface counterpart to ADR-024

**Context.** ADR-024 made EdirasX able to represent early years through doctoral research in one engine. That is worth nothing — worse than nothing — if a nursery administrator has to walk past *Programmes*, *Qualifications*, *Credit systems* and *Research milestones* to reach the register. Flexibility a person has to step around is not a feature they have; it is a tax they pay for other people's features.

**Decision.** A capability appears only when four independent questions all say yes, and **what happens when one says no differs by question**:

| Question | Answered from | When the answer is no |
|---|---|---|
| Does this institution's world contain the concept? | Its own configuration | **Absent.** Not empty, not disabled, not a padlock |
| May this person see it? | Their permissions | **Absent.** Existence is sensitive (ADR-004) |
| Has the institution bought it? | The plan (ADR-030) | Absent — *unless* the viewer could actually buy it, in which case it becomes an offer |
| Is it what this person came here to do? | Their role | Present, lower down. Ordering, never access |

Resolved once on the server, in `experience.service.resolve`. Not in the client: if the interface decides, then the web app, the phone, and every future consumer decide again, and they drift.

**Configuration is derived, not declared as a type.** An institution's world contains programmes because it has programme rows — not because somebody chose `NURSERY | SECONDARY | UNIVERSITY` from a list. That enum is ADR-024's forbidden one arriving through the interface's back door, and it would be wrong for the first institution that is two things at once, which is most of them. A static test forbids `institution_type`, `school_type` and their variants anywhere in product code.

Two cases derivation cannot cover, and one small table (`interface_profiles`) that covers them: a university on its first morning has no rows to infer from, so it may **declare** the layers it intends to use; and an institution may **suppress** a layer it has stopped using. The asymmetry is deliberate — declaration is additive, suppression cannot remove a layer that has rows. *An institution can always show a layer it does not yet use, and can never hide one it is actively using.* Data that exists stays reachable.

**Zero states are the other half.** A capability that is present with no records gets a useful empty state — "Add your first child", in the institution's own word for a child. A capability that is *absent* gets no empty state, because it has no state: there is nothing to be empty.

**Three judgements worth recording.**

*An upgrade shown to somebody who cannot buy is an advertisement placed in their way.* A teacher who cannot authorise a purchase gains nothing from a padlocked *Design Studio* in their navigation, and loses a little attention every day. So an unentitled capability is an offer only to somebody holding `billing.subscription.write`, and absent for everybody else.

*Absences carry reasons.* "This institution does not use programmes" and "you may not see programmes" are different facts, and a support conversation that cannot tell them apart goes nowhere. The reasons are returned only to somebody who could act on them.

*Preferences are tenant-owned.* A teacher who works at two institutions has two working lives; the density they chose for a nursery register should not follow them into a university's results screen. The person is one human (ADR-027); their preferences are about a place.

**Enforcement.** `test_experience.py` — 20 tests over four institutions on one deployment. A nursery administrator is shown none of programmes, qualifications, credits, faculties, cohorts, supervision, milestones or transcripts, and reads "Children" and "Rooms" because that is what the institution says. A university sees faculties, programmes, levels, credits, cohorts and semesters, reads "Faculties" and "Modules", and is shown no research concepts. A doctoral institute additionally sees supervision and milestones and, running no classes, is shown no classes or timetable. **All four produce four distinct sets** — asserted directly. Within one institution, a teacher, a parent and a bursar open three different products.

Four sabotages caught: showing every concept the database supports, rendering unpermitted capabilities as disabled rows, advertising upgrades to everybody, and letting an institution hide a layer full of its own records.

**A defect the suite found on its first run.** A registrar could not see academic units — the capability requires `institution.department.read` and the role template never had it, so a registrar who places students into departments could not find their own institution's structure. The role gained the permission; the test was not weakened. It is a small illustration of why the experience layer earns its acceptance suite: the backend was correct, every isolation test was green, and the product was unusable for one of its most important roles.

---

## ADR-032 — A register is evidence, and it has thirty seconds

**Status:** Accepted

**Context.** Attendance is the reason a teacher opens the product, and it is also the record most likely to be quoted years later — in a safeguarding referral, an exclusion appeal, a funding audit, a court. The two facts pull in opposite directions, and most systems resolve them by picking one: a fast checkbox grid nobody can audit, or an auditable form nobody has time to fill in. A teacher who cannot mark a room in thirty seconds takes the register at lunchtime from memory, and *that* record is worth nothing — so speed is not a nicety, it is what makes the evidence real.

**Decision.**

1. **The register arrives complete.** One call returns everybody in the room, in order, with their marks, the school's codes, and the default. Membership is *derived* from the open enrolments in the group on the day (ADR-027), never stored: a child who transferred in on Monday is on Monday's register with nobody rebuilding anything, and last March's register still shows last March's class.
2. **Marking is one write.** The whole register goes in a single request and a single transaction. A full register is three round trips — open, mark, submit — and that number is asserted, because round trips are what a school's network multiplies.
3. **`open` is a state, not a draft.** A fire alarm at 09:04 must not lose the eleven marks already taken.
4. **A correction is an addition.** `attendance_amendments` joins the append-only tables. A mark changes all the time and legitimately — the child who arrived at half past nine *was* absent at nine — but the change records who, when, and why, and the application role holds no UPDATE or DELETE on the ledger. Correcting a *submitted* register additionally requires a reason: the first correction finishes the job, the second changes a record that has been relied on.

**The codes are the school's; the category is not.** Present, Absent, Late, Authorised, Educational visit, Religious observance — every institution has its own list and its own letters. What is platform-fixed is `category`, because a percentage-present figure has to know which marks count, and no amount of configuration makes that an arbitrary choice. `counts_as_present` is deliberately a *separate* column from the category: a school that counts an educational visit as present and one that does not both use `other` and disagree about the flag.

**Two refusals, both about what the record would mean.** A register will not submit while somebody is unmarked — an incomplete register says nothing about the people missing from it — or while a code demanding an explanation has none. That second is the whole absence workflow, and it is one boolean on a row the school owns.

**No attendance is not zero attendance.** `rate` returns `None` for a student with no sessions, not `0.0`. A progression rule reading zero would hold a child back for having no record, and `academics.progression` already treats missing data as missing rather than as failure (ADR-022). The two had to agree.

**A guardian reaches marks; nobody reaches a register they do not teach.** The sessions plan has no `own_children` clause at all, because a register *is* a list of other people's children. The marks plan composes the people module's own clause rather than writing its own, so a parent's reach over attendance cannot drift from their reach over the child.

**Enforcement.** `test_attendance.py` — 22 tests. Four sabotages caught: silently changing a submitted register, corrections leaving no trace, submitting an unexplained absence, and membership taken from everyone-ever rather than from the enrolments covering the day.

**A defect the boundary test caught, in the right place.** The attendance scope plan reached for `people.models` to build a guardian's clause. The exception list stayed empty and `people.scopes` gained a published `student_ids_where`, which is the better answer for a reason beyond tidiness: a parent's reach over attendance must be the *same* reach they have over the child, and two copies of it drift.

---

## ADR-033 — A score is not a result, and a published result is a snapshot

**Status:** Accepted · **Constitutional**

**Context.** In most school systems a teacher types a mark and it is instantly official. That single design choice removes the institution's ability to correct a transcription error before a parent sees it, to moderate two markers of the same paper, to hold results until a board has met — and, most damagingly, to answer *what did we actually publish in July?* once somebody edits a cell in September.

**Decision.** Two tables and an explicit act between them.

    a score  is what a teacher entered — working, revisable, theirs
    a result is what the institution has said — official, immutable, quoted

The lifecycle is `draft → submitted → in_review → approved → published`, with `published` terminal. There is no transition out of it: a published result is corrected by an **amendment**, which is a new fact about it rather than a different value in it.

**Publishing snapshots.** A `published_result` carries the mark *and the grading it was given* — band label, points, pass flag, and the scale's code — because a school that moves its grade boundaries next summer must not silently change what it awarded last summer. A transcript reprinted in 2031 has to say what the 2026 transcript said. Recomputing from live scores and a live scale would be smaller, tidier, and wrong. A test moves an A boundary from 70 to 90 and asserts that an already-published A stays an A.

**The workflow is the institution's.** `approval_workflows` holds an ordered list of steps, each naming a permission validated against the catalogue when the workflow is saved. A school configures Teacher → Principal; a university Lecturer → Programme Coordinator → Department → Examination Board. Steps are taken **in order** and each is authorised by *its own* permission, so a coordinator cannot take the board's step however senior they are. Returning a set makes its step outstanding again, because sending work back is the point of a review.

An institution with **no** workflow row publishes in one action. That is a legitimate configuration, not a missing one: a small school where the head teacher enters and publishes the marks herself should not have to invent a committee.

**Readiness reports; it does not refuse.** Missing marks, marks outside the scale, assessments still open, unmoderated papers — listed as problems a person can act on, because "not ready" is useless at four o'clock on results day. A school may knowingly publish over them, with `force` and a stated reason. **`force` does not cover the workflow**: an approval nobody gave is not an approval, and the only override is the one that says out loud what is being overridden.

**Moderation keeps both numbers.** A moderated score sits alongside the original rather than over it. Overwriting would destroy the evidence that moderation happened, which is the only reason a department asks for it.

**A draft is a teacher's; a result is a family's.** The scores plan has no `own_children` or `self` clause at all. A parent reading a working score would be reading a mark before the institution had decided it was right.

**Enforcement.** `test_assessment.py` — 28 tests. Six sabotages caught, one per attack named in the brief: publishing without snapshotting the grading, an amendment that discards the previous value, an amendment without a reason, an amendment without authority, a correction with no audit event, and publication without the required approvals. Cross-institution access is refused by row-level security and asserted directly.

**A defect the suite found.** `readiness` took the class list as of *today* rather than as of the period the results cover. Publishing an autumn term in January would have found nobody expected — every child having since moved on — and reported a result set with no marks in it as ready to publish. It now asks who was in the class on the last day of the period, which is what "the autumn term's results" means.
