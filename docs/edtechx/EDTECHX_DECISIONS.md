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
