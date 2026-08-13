# VOLUME IV — ENGINEERING, AI ARCHITECTURE, CLOUD & SECURITY

### How it is built · How it stays up · How it stays safe · What "done" means

*Edition II. Incorporates the Security Bible (Chapters 12–17). Authority: Volume I.*

---

## Contents

1. [Engineering Principles](#chapter-1--engineering-principles)
2. [The Reference Architecture](#chapter-2--the-reference-architecture)
3. [Multi-Tenancy & the No-Fork Rule](#chapter-3--multi-tenancy--the-no-fork-rule)
4. [Data Architecture](#chapter-4--data-architecture)
5. [The Credential & Verification Architecture](#chapter-5--the-credential--verification-architecture)
6. [API & Integration Standards](#chapter-6--api--integration-standards)
7. [The AI Architecture](#chapter-7--the-ai-architecture)
8. [AI Governance & the Human-in-the-Loop Enforcement](#chapter-8--ai-governance--human-in-the-loop-enforcement)
9. [Data Rights & Model Training Policy](#chapter-9--data-rights--model-training-policy)
10. [Performance & the Constrained-Environment Standard](#chapter-10--performance--the-constrained-environment-standard)
11. [Frontend, Design System & Internationalisation Engineering](#chapter-11--frontend-design-system--internationalisation-engineering)
12. [SECURITY BIBLE I — Principles & Zero Trust](#chapter-12--security-bible-i--principles--zero-trust)
13. [SECURITY BIBLE II — Identity & Access](#chapter-13--security-bible-ii--identity--access)
14. [SECURITY BIBLE III — Cryptography & Data Protection](#chapter-14--security-bible-iii--cryptography--data-protection)
15. [SECURITY BIBLE IV — Secure Development](#chapter-15--security-bible-iv--secure-development)
16. [SECURITY BIBLE V — Resilience, Backup & Continuity](#chapter-16--security-bible-v--resilience-backup--continuity)
17. [SECURITY BIBLE VI — Incident Response](#chapter-17--security-bible-vi--incident-response)
18. [Quality, Testing & the Definition of Done](#chapter-18--quality-testing--the-definition-of-done)
19. [Release Engineering](#chapter-19--release-engineering)
20. [Observability](#chapter-20--observability)
21. [Technical Debt & Architecture Decision Records](#chapter-21--technical-debt--architecture-decision-records)

---

# CHAPTER 1 — ENGINEERING PRINCIPLES

**E1 — Boring beneath, ambitious above.** Payments, authentication, credential signing, backups and audit logs use conservative, proven, widely-reviewed technology. Novelty budget is spent on the customer-visible frontier. A clever database is a liability; a clever admissions experience is an asset.

**E2 — Build for the constrained case first.** A 5-year-old Android on 3 Mbps with intermittent power is the reference environment. If it works there, it works everywhere. The inverse is never true.

**E3 — One platform, many surfaces.** Layers 1–4 of the ecosystem stack (Volume I §2.3) are shared by every sector. Forking them is a governed exception (Chapter 3), not an engineering convenience.

**E4 — Reversibility over velocity.** Every deployment rolls back. Every migration reverses. Every destructive user action has a recovery window. We ship faster *because* mistakes are cheap, not despite it.

**E5 — Data is the customer's.** Export is complete, open-format, self-service, free and immediate. This is enforced in code, in tests, and in the contract.

**E6 — Correctness beats cleverness in the record.** The system of record is the moat (Volume II §9). An elegant abstraction that risks a wrong grade, a wrong fee balance, or a wrongly-issued certificate is not elegant.

**E7 — Everything is auditable.** Who did what, to which record, when, from where, and what it was before. Not a feature — a property of the platform.

**E8 — Observable before scalable.** We do not optimise what we cannot measure, and we do not ship what we cannot see failing.

**E9 — Composition over configuration over customisation.** Prefer combining existing modules; then configuring them; then, last and reluctantly, writing bespoke code for one customer.

**E10 — The build must be reproducible by a new hire on day two.** If setup requires tribal knowledge, that is a defect with a ticket.

---

# CHAPTER 2 — THE REFERENCE ARCHITECTURE

## 2.1 The shape

```
┌──────────────────────────────────────────────────────────────┐
│ SURFACES   Web · PWA · Android · iOS · Kiosk · Signage ·      │
│            USSD · Print · Card · Gate · API consumers         │
├──────────────────────────────────────────────────────────────┤
│ EDGE       CDN · WAF · DDoS · rate limit · geo-routing        │
├──────────────────────────────────────────────────────────────┤
│ BFF        Per-surface aggregation, response shaping, caching │
├──────────────────────────────────────────────────────────────┤
│ DOMAIN     Identity · Records · Academic · Finance ·          │
│ SERVICES   Credentials · Comms · Automation · Intelligence    │
├──────────────────────────────────────────────────────────────┤
│ PLATFORM   AuthN/Z · Audit · Search · Files · Events · Jobs · │
│            Notifications · Payments · Tenancy · Feature flags │
├──────────────────────────────────────────────────────────────┤
│ AI         Router · Agents · RAG · Guardrails · Evaluation    │
├──────────────────────────────────────────────────────────────┤
│ DATA       PostgreSQL · Object store · Vector · Search ·      │
│            Cache · Queue · Warehouse                          │
├──────────────────────────────────────────────────────────────┤
│ INFRA      Compute · Network · Secrets · Backup · Observ.     │
└──────────────────────────────────────────────────────────────┘
```

## 2.2 The canonical stack

Chosen for hiring depth in our markets, operational simplicity, and longevity — not for novelty.

| Layer | Choice | Why |
|---|---|---|
| Primary database | **PostgreSQL** | Relational integrity for a record system; JSONB where flexibility is genuinely needed; enormous operational knowledge base |
| API services | **Python (FastAPI)** for domain services | Already the MVP's stack; strong AI/ML adjacency; fast to hire for |
| Web | **Next.js / TypeScript / Tailwind** | Already the MVP's stack; SSR for performance on weak devices; huge talent pool |
| Static institutional sites | **Token-driven static build** | The pattern proven across four reference sites: partials + a page manifest + a build script; no framework, no runtime, near-zero hosting cost, trivially cacheable, survives a decade |
| Mobile | **Capacitor wrapper** first, native where justified | Already delivered; one codebase; native only where the platform genuinely requires it |
| Vector store | **Qdrant** | Already in the MVP |
| Cache / queue | **Redis** | Already in the MVP |
| Search | **PostgreSQL FTS**, then a dedicated cluster at scale | Do not add an engine before the query volume justifies it |
| Containers | **Docker / Compose** → orchestrated at scale | Already in `infra/` |
| Edge | **Cloudflare** | Already the production topology |

**The two-stack rule:** the group runs at most two primary backend languages and two frontend frameworks at any time. A third requires CTO approval and a written retirement plan for one of the existing two.

## 2.3 The static-site pattern, promoted to a product

The four institutional reference sites converged independently on the same architecture, which is now the group standard for institutional web presence:

- `partials/` — shared chrome as language-neutral templates carrying `{{t:key}}` translation tokens; **one file serves every language**
- `pages/` — page body content only, one file per page per locale
- `pages/manifest.json` — the registry: slug, output path, title, description, content file, `lang`, `dir`, `altHref`
- `i18n/<code>.json` — one flat, dot-keyed dictionary per language
- `i18n/locales.json` — the single source of truth for which languages exist
- `scripts/build.js` — assembles partials + content into complete documents, deriving untranslated locales with translated chrome and a labelled notice rather than emitting a broken URL

**Why this is the standard.** It produces a four-language site whose marginal cost per additional language is a dictionary rather than a codebase; it has no runtime and therefore no runtime vulnerabilities; it is trivially CDN-cacheable, which is decisive on 3 Mbps connections; it costs almost nothing to host, which is what makes the Foundation tier affordable; and it will still build in ten years because it depends only on the language's standard library. This is the architectural expression of principle E1.

**Never do:** hand-edit built output. Regenerate.

---

# CHAPTER 3 — MULTI-TENANCY & THE NO-FORK RULE

## 3.1 The tenancy model

**Shared schema with a mandatory tenant discriminator**, enforced at the data layer rather than trusted to application code, with row-level security as the backstop. Dedicated schemas or dedicated databases are available at Elite/Enterprise/Government tiers where residency, regulation or scale require it.

| Model | Who gets it | Cost to us |
|---|---|---|
| Shared schema, RLS-enforced | Foundation → Premium | Lowest |
| Dedicated schema | Elite, large multi-campus | Moderate |
| Dedicated database | Enterprise, regulated | High |
| Dedicated deployment | Government, air-gapped | Highest (Volume III §4.6) |

**Non-negotiable:** a tenant-scoped query that could return another tenant's row is a **P0 security incident**, not a bug. Every data-access path has a test that attempts cross-tenant access and asserts failure. This test suite may never be skipped in CI.

## 3.2 The no-fork rule

Forking platform layers 1–4 for a single customer requires written CTO approval, a documented justification, and a **sunset date**. Without a sunset date the answer is no.

The reason is arithmetic: breadth across twenty sectors is affordable only because the lower layers are shared (Volume I §2.3). Every fork multiplies the maintenance surface by the number of forks, and forks never get deleted unless someone was made responsible for deleting them on a date.

Legitimate alternatives, in order of preference: a feature flag, a configuration option, a tenant-scoped extension point, a plugin, a sector module, and only then a fork.

---

# CHAPTER 4 — DATA ARCHITECTURE

## 4.1 The record principles

**D1 — One institution, one person record.** A student who becomes an alumnus who becomes a parent who becomes a staff member is one person with four relationships, not four records. This is harder and it is correct.

**D2 — Events, not just state.** Enrolment, role changes, fee movements, credential issuance and governance decisions are recorded as **events with a time**, from which state is derived. Auditability, reversibility and historical reconstruction all fall out of this for free, and none of them can be retrofitted.

**D3 — Soft delete by default, hard delete on request.** Nothing is destroyed accidentally; everything is destroyable deliberately, verifiably, and in fulfilment of a data subject's rights.

**D4 — Every record carries provenance.** Created by, modified by, source system, and confidence where derived.

**D5 — Reference data is versioned.** Curricula, fee structures, grading scales and policies change between years. A 2029 transcript must render under 2029's grading scale, not today's.

## 4.2 The canonical domain model

Validated against the 73-table credential-and-commerce schema in the group's reference implementation, which covers: users and roles; academic bodies, programmes, levels, courses, units and learning outcomes; enrolments and enrolment-integrity events; competencies, skills, assessments and marks; evidence items and versions; quizzes, exercises, vocabulary and self-checks; recordings, pronunciation targets and feedback; time-on-task and unit progress; awards, distinctions and award verifications; credential signatures, signing keys and issued documents; verifying institutions and institution checks; graduate profiles, profile shares and alumni chapters; payments, receipts, refunds, instalment plans, promo codes, scholarships, currencies and country payment routing; corporate accounts and seats; CPD records; live sessions; notifications.

```
PERSON ──┬── enrolment ──── PROGRAMME ── LEVEL ── COURSE ── UNIT
         │                                              └── LEARNING OUTCOME
         ├── role ───────── ORGANISATION UNIT
         ├── assessment ─── COMPETENCY / SKILL ── EVIDENCE
         ├── credential ─── ISSUED DOCUMENT ── SIGNATURE ── VERIFICATION
         ├── financial ──── INVOICE ── PAYMENT ── RECEIPT ── INSTALMENT
         └── identity ───── CARD · BIOMETRIC · CREDENTIAL · DEVICE
```

## 4.3 Data classification

| Class | Examples | Handling |
|---|---|---|
| **Public** | Published pages, verification results | CDN-cacheable |
| **Internal** | Aggregate statistics, non-identifying config | Authenticated |
| **Confidential** | Person records, grades, finance | Encrypted at rest, access-logged, least-privilege |
| **Sensitive** | Health, safeguarding, discipline, biometrics | Additionally: field-level encryption, named-role access only, every read logged and reviewable |
| **Children's data** | Any record of a person under 18 | **Strictest class in the group.** Minimisation, short retention, no behavioural profiling, no advertising use, parental access rights, and a standing prohibition on any secondary use |

## 4.4 Retention

Defaults, overridable upward by regulation and downward by customer instruction: operational logs 90 days · audit logs 7 years · financial records per jurisdiction (typically 6–7 years) · academic records **permanent by default** (a transcript must be producible in forty years) · biometric templates deleted on relationship end · marketing data 24 months from last engagement · AI conversation logs 12 months, or 30 days where they contain sensitive-class data.

---

# CHAPTER 5 — THE CREDENTIAL & VERIFICATION ARCHITECTURE

*The single most strategically important subsystem in the group (Volume II §9). Specified in detail because getting it wrong is unrecoverable — a credential system that is found to be forgeable destroys the institution's trust and ours simultaneously.*

## 5.1 The four requirements

1. **Unforgeable** — a credential cannot be fabricated by anyone without the issuer's private key.
2. **Verifiable by anyone, free, forever** — the constitutional commitment (Volume I §5.3).
3. **Verifiable offline where possible** — a border officer with no connectivity should still get signal.
4. **Revocable** — issuance is not irreversible; a credential obtained fraudulently must be withdrawable and the withdrawal must be visible.

## 5.2 The identifier architecture

Every credential carries a **structured, human-transcribable identifier** designed with the institution (a service line — Volume III §3.1). It encodes issuing institution, document class, year, and sequence, with a check character. It must be readable aloud over a phone call without ambiguity, which rules out characters that collide when spoken or handwritten (0/O, 1/I/l, 5/S, 8/B).

## 5.3 The signing model

- Each issuing institution holds a distinct key pair. **StromeX never signs on an institution's behalf** — the institution is the issuer, in fact and in cryptography.
- Private keys live in a hardware security module or an equivalent managed key service. Key material is never in application memory longer than a signing operation, never in logs, never in backups in plaintext.
- Key generation, custody, rotation and revocation follow a documented ceremony with two-person control and a written record. This is a priced service (Volume III §3.1) because it is real work with real consequences.
- Compromise of one institution's key affects that institution only. There is no group-wide master key, deliberately — a single key whose compromise invalidates every credential the group ever issued is an unacceptable concentration of risk.

## 5.4 The verification surfaces

Four distinct surfaces are in production across the reference implementations — certificate, identity, receipt and graduation document — because they have genuinely different verification semantics and conflating them produces confusing results.

| Surface | Answers |
|---|---|
| Certificate verification | Was this award made, to this person, by this institution, on this date, and is it still valid? |
| Identity verification | Is this person currently who this card says they are, in this role? |
| Receipt verification | Was this payment actually received and applied? |
| Document verification | Is this multi-page document the sealed original, unaltered? |

Every verification response states plainly: **valid**, **revoked** (with date and reason class), **not found**, or **superseded** — never an ambiguous result, and never a bare "invalid" that fails to distinguish a forgery from a typo.

## 5.5 The layered verification model

| Layer | Mechanism | Works offline | Strength |
|---|---|---|---|
| 1 | Human-readable identifier | Yes | Weak alone |
| 2 | QR → verification URL | No | Strong, convenient |
| 3 | Detached digital signature embedded in the document | Yes | Strong |
| 4 | Physical security features (guilloche, microtext, UV, foil) | Yes | Deters casual forgery |
| 5 | Optional public-ledger anchor | Yes | Independent of us existing |

**Layer 5 exists for one reason and it is an honest one:** it lets an institution's credentials remain verifiable even if StromeX ceases to exist. Offering it costs us a theoretical lock-in advantage and buys the customer real assurance. That trade is required by Volume I P5.

## 5.6 Revocation

A public, append-only revocation register. Revocation reasons are classified (issued in error, obtained fraudulently, superseded, withdrawn by institution) and the class is public while the narrative is not. Revocation requires a documented approval chain — one person must not be able to revoke a graduate's degree alone.

---

# CHAPTER 6 — API & INTEGRATION STANDARDS

| Standard | Rule |
|---|---|
| Style | REST + JSON. GraphQL only where a surface genuinely needs client-shaped queries |
| Versioning | URL-versioned (`/v1/`). A version is supported for **24 months** after its successor ships |
| Breaking changes | Never within a version. New version, dual-run, deprecation notice, telemetry-verified migration |
| Auth | OAuth 2.1 / OIDC; API keys for server-to-server; short-lived tokens; refresh rotation |
| Pagination | Cursor-based. Offset pagination is prohibited on any table that can exceed 100k rows |
| Errors | Structured: machine code, human message, remediation hint, correlation ID |
| Rate limits | Published, returned in headers, generous by default |
| Idempotency | Mandatory on every state-changing endpoint. Payments without idempotency keys are rejected |
| Webhooks | Signed, retried with exponential backoff, replayable for 7 days, with a delivery log the customer can see |
| Documentation | OpenAPI, generated from code, published, with runnable examples. **Free and public** |
| SDKs | JS/TS, Python, PHP. Open source. Generated where possible, hand-polished where not |
| Deprecation | Announced, dated, telemetry-monitored, and never enforced before the announced date |

**The dogfooding rule:** every StromeX surface consumes the same public API a third party would. There is no privileged internal API. If it is awkward for us, it is awkward for them, and we will find out first.

---

# CHAPTER 7 — THE AI ARCHITECTURE

## 7.1 The provider-independence doctrine

**No StromeX capability may depend on a single AI provider.** This is a commercial risk control (Volume II R7) as much as an architectural preference: provider pricing, availability, terms and model behaviour all change without our consent.

The MVP already implements multi-provider routing across Claude, OpenAI-compatible endpoints, DeepSeek and Perplexity, with a development provider for offline work. That router is the group standard and every AI capability goes through it.

```
Request → Policy gate → Router → Provider (primary)
                          │           └─ fallback chain
                          ├─ Cost / latency / capability routing
                          ├─ Self-hosted model (for sensitive classes)
                          └─ Deterministic fallback (never a blank failure)
```

**Routing criteria, in order:** data classification (sensitive-class work may be pinned to a self-hosted or residency-compliant model) → required capability → latency budget → cost. Cost is last, always. A cheaper model that gets a grade wrong is not cheaper.

## 7.2 Retrieval before generation

Institution-facing answers are **grounded in the institution's own records and documents**, retrieved and cited, not recalled from a model's training. The pattern:

```
Query → tenant-scoped retrieval → relevance filter → context assembly
      → generation with mandatory citation → citation validation
      → confidence assessment → response, or escalation
```

**Citation validation is a real check, not a prompt instruction.** A generated citation that does not resolve to a retrieved source is stripped, and if stripping leaves the answer unsupported the system says it does not know. Volume I §7.2.3 prohibits fabricated authority, and prompts alone do not enforce prohibitions.

## 7.3 The agent model

An agent is a **bounded role**, not a personality: a scope of data it may read, a set of actions it may take, a refusal boundary, an escalation target, and an audit trail. Agents are configured per institution, and the institution can see and change every one of those five things.

| Property | Rule |
|---|---|
| Data scope | Explicit allow-list. An agent cannot read what its role would not read |
| Actions | Explicit allow-list. Write actions require a configured approval where they affect a person's record |
| Refusal boundary | Per-domain, enforced in the policy gate, not in the prompt |
| Escalation | Every agent has a named human target. An agent with no escalation path may not be deployed |
| Audit | Every invocation logged: prompt, retrieved context IDs, model, output, action taken, cost |
| Kill switch | Per-agent, per-institution, immediate, available to the institution |

## 7.4 Evaluation

Agents are evaluated before release and continuously in production against: **factual accuracy** (against a held-out set of the institution's real records), **citation validity**, **refusal correctness** (does it decline what it must decline), **consistency** (repeated identical queries must not vary factually), **latency**, and **cost per task**.

A model or prompt change ships only when the evaluation suite is at or above the incumbent on accuracy, citation validity and refusal correctness. Latency and cost improvements do not license accuracy regressions.

---

# CHAPTER 8 — AI GOVERNANCE & HUMAN-IN-THE-LOOP ENFORCEMENT

## 8.1 The stakes ladder

| Stakes | Examples | Rule |
|---|---|---|
| **Low** | Draft an email, summarise a document, suggest a lesson activity | AI acts; human may review |
| **Medium** | Mark homework, draft a policy, propose a timetable, triage an enquiry | AI proposes; **human approves before it reaches the affected person** |
| **High** | Final grade, admission decision, disciplinary outcome, fee write-off, safeguarding classification, staff performance outcome | **AI may inform; a named human decides and is recorded as the decider** |
| **Prohibited** | Religious rulings, legal conclusions, medical diagnosis, immigration advice, credential issuance without human authorisation | **AI does not decide. It routes to a qualified human and says so to the user** |

This ladder is enforced in the policy gate. A capability that would breach it cannot be configured into existence, and an institution cannot opt out of the High and Prohibited rows — not even by request, and not for a discount. Volume I P10 and §7.2.4.

## 8.2 Disclosure

Every AI surface is labelled as AI, in the user's language, at the point of interaction — not in a footer, not in a terms page. Where a deliverable is produced with AI assistance and human review, both facts are stated. Where a human reviewed it, that human is identifiable internally and accountable for it.

## 8.3 Faith and cultural content

Qur'anic text is **retrieved from verified sources and reproduced verbatim** — never generated, never paraphrased, never completed by a model. Translations and tafsir are attributed to their named scholars and editions. Questions of ruling route to qualified human scholars with the routing visible to the user. The same standard of fidelity applies to every tradition the group serves; there is no primary tradition and no set of afterthoughts (Volume I §7.5).

## 8.4 The prohibited-use enforcement

Prompt injection, jailbreak attempts and scope-escape attempts are detected, logged, and rate-limited. Repeated attempts against a sensitive-class agent trigger a human review of the account. Users are told when a request was declined and why, in plain language, without a lecture.

---

# CHAPTER 9 — DATA RIGHTS & MODEL TRAINING POLICY

Stated as flatly as possible because ambiguity here is worth more to a competitor than any feature:

1. **Customer data is the customer's.** StromeX is a processor.
2. **We do not train third-party models on customer data.** Not with de-identification, not with aggregation, not with consent buried in terms. Where a provider's default terms would permit training, we contract out of it, and where we cannot, we do not route customer data to that provider.
3. **We do not sell, broker, licence or share customer data.** No exceptions for "partners", "analytics", or "research".
4. **Aggregate benchmarking is opt-in, anonymised, and never leaves the group** (Volume III Division 9).
5. **We may train our own models on our own operational data** — our documentation, our code, our support transcripts where the customer's content is removed — and on data a customer has explicitly and separately licensed to us, with the licence revocable and the benefit shared.
6. **Sub-processors are published**, with the data classes they receive, and customers are notified before a new one is added.
7. **Export is complete, open-format, self-service and free**, at any time, including after termination, for a defined post-termination window that is stated in the contract and is never shorter than 90 days.

---

# CHAPTER 10 — PERFORMANCE & THE CONSTRAINED-ENVIRONMENT STANDARD

## 10.1 Budgets — release blockers, not aspirations

| Metric | Target | Measured on |
|---|---|---|
| First contentful paint | < 1.5s | 3 Mbps, mid-range Android |
| Largest contentful paint | < 2.5s | same |
| Time to interactive | < 3.5s | same |
| Interaction to next paint | < 200ms | same |
| Cumulative layout shift | < 0.1 | same |
| API p50 / p95 / p99 | 120ms / 400ms / 900ms | production |
| Initial JS payload | < 180 KB gzipped | per route |
| Total page weight | < 900 KB | first load, incl. images |
| Fonts | ≤ 4 files, subset, `font-display: swap` | — |

## 10.2 The degraded-mode requirement

Every surface has a **defined behaviour under failure**, designed and tested, not emergent:

| Failure | Required behaviour |
|---|---|
| No network | Cached read access; queued writes; explicit "not synced" state; nothing silently lost |
| Slow network | Progressive rendering; skeleton states; no blocking spinners over 3s |
| No power (device) | Work is persisted continuously; nothing depends on a clean shutdown |
| Payment provider down | Queue and retry; offer alternative channel; never take money without recording it |
| AI provider down | Fall back through the chain; then a deterministic non-AI path; never a blank error |
| Our platform down | Static institutional site stays up (it has no runtime); status page states truth |

**Offline-first is not a feature flag.** Service workers, local persistence and sync-conflict resolution are architectural, and the reference implementations already ship them.

## 10.3 Data-cost awareness

In our founding markets users pay for data by the megabyte. A heavy page is a real cost transferred to a parent. Image budgets, lazy loading, and a "low-data mode" that ships text-first are therefore engineering requirements, not optimisations.

---

# CHAPTER 11 — FRONTEND, DESIGN SYSTEM & INTERNATIONALISATION ENGINEERING

## 11.1 The design system

`StromeX Design System` — open source (Volume I §5.5) — is the single source of truth: tokens (colour, type, space, radius, motion, elevation), primitives, components, patterns, and per-sector theme layers. Divisions extend it; they do not fork it. A component used by three products is promoted into the system, and the third team to need it does the promotion.

Accessibility is enforced mechanically: contrast ratios checked in CI, keyboard traversal tested, focus visible always, `prefers-reduced-motion` honoured, semantic HTML before ARIA, and every interactive element reachable and labelled. WCAG 2.2 AA is the floor and it is verified, not asserted.

## 11.2 Internationalisation engineering

The group ships English, Arabic, Yorùbá and French today across its reference implementations. The standards that made that affordable:

1. **One dictionary per language**, flat and dot-keyed. Nested structures produce merge conflicts and orphaned keys.
2. **A locale registry as the single source of truth** for which languages exist and their direction.
3. **Language-neutral chrome templates** carrying translation tokens — one file per component, not one per language. Per-language copies are technical debt with a migration path, and the reference implementations record exactly this transition.
4. **Bidirectional layout is a property, not a mode.** Logical CSS properties (`margin-inline-start`, not `margin-left`) everywhere. Physical properties require an RTL counterpart in the same commit.
5. **Embedded LTR runs inside RTL text are wrapped explicitly** (`dir="ltr"` spans) for phone numbers, emails, addresses, acronyms and codes. The Unicode bidi algorithm does not reliably keep them in reading order, and this produces subtly wrong phone numbers that nobody notices until a parent cannot call the school.
6. **Script-specific typography is engineered, not fallen back to.** Arabic renders in Amiri/Cairo, Yorùbá in a face with correct diacritic support. A Latin font's fallback for Arabic is a defect.
7. **Untranslated pages are derived with translated chrome and a labelled notice**, never omitted. A language switcher that points at a 404 is worse than an honest partial translation.
8. **Machine translation is never shipped as finished work.** AI-assisted, human-reviewed, and disclosed (Volume I §7.2).
9. **Locale-correct formatting** for dates (including Hijri where relevant), numbers, currency, names and address order. A Nigerian date rendered US-style is a small error that costs real trust.

---

# CHAPTER 12 — SECURITY BIBLE I: PRINCIPLES & ZERO TRUST

## 12.1 The security principles

**S1 — Assume breach.** Design so that a compromised component does not compromise the system.
**S2 — Least privilege, always, including for us.** A StromeX engineer's default access to customer data is none.
**S3 — Defence in depth.** No single control is load-bearing.
**S4 — Secure by default.** The safe configuration is the one you get without asking.
**S5 — Fail closed.** When an authorisation check cannot complete, deny.
**S6 — Security is free** (Volume I §6.1). Patches, TLS, WAF, backups and audit logs are never a paid upgrade.
**S7 — Children's data receives the strictest handling in the group**, without exception and without a customer having to request it.
**S8 — Disclose fast and completely.** Reputational damage comes from concealment, not from incidents.

## 12.2 Zero trust, concretely

| Principle | Implementation |
|---|---|
| No implicit network trust | Every service-to-service call is authenticated and authorised; being "inside" grants nothing |
| Verify explicitly | Identity, device posture and context evaluated per request, not per session |
| Least privilege | Short-lived, scoped credentials; no long-lived shared secrets; no shared accounts, ever |
| Micro-segmentation | Network policy between services; databases reachable only from their owning service |
| Continuous verification | Session re-evaluation on privilege change, anomalous location, or new device |
| Encrypted everywhere | TLS 1.3 in transit including internally; encryption at rest by default |
| Assume compromise | Anomaly detection on access patterns; blast-radius limits designed in |

## 12.3 Staff access to customer data

- Default access: **none**.
- Access requires a ticket, a stated reason, a time limit, and it is **logged and visible to the customer** in their audit log.
- Production database access requires two-person approval and is session-recorded.
- Access to sensitive-class data (health, safeguarding, biometrics, children's records) requires a named role, additional approval, and generates a customer-visible notification.
- Access reviews quarterly; departure revokes everything within one hour and this is tested.

---

# CHAPTER 13 — SECURITY BIBLE II: IDENTITY & ACCESS

| Control | Standard |
|---|---|
| Password storage | Argon2id, per-user salt. Never anything else, never reversible |
| Password policy | Length over complexity; breached-password screening; no forced rotation without cause |
| MFA | Available on every tier including free; **mandatory** for admin, finance, credential-issuing and sensitive-data roles |
| Passkeys / WebAuthn | Supported and preferred; the recommended default as adoption allows |
| Sessions | Short-lived access tokens, rotating refresh tokens, server-side revocation, device list visible to the user |
| Token denylist | Immediate revocation capability — already implemented in the MVP |
| SSO | SAML 2.0 and OIDC for institutions |
| Authorisation | Role-based with attribute conditions; deny by default; evaluated server-side always |
| Privilege escalation | Requires approval; time-boxed; logged; auto-expiring |
| Service accounts | Scoped, rotated, never shared, never interactive |
| Account recovery | Verified out-of-band; recovery is the most-attacked path and is treated as such |
| Brute force | Progressive delays and lockout with a documented, non-punitive recovery route |
| Rate limiting | Per-identity and per-IP, at the edge and at the application |

---

# CHAPTER 14 — SECURITY BIBLE III: CRYPTOGRAPHY & DATA PROTECTION

| Concern | Standard |
|---|---|
| In transit | TLS 1.3; HSTS with preload; modern cipher suites only; certificate transparency monitored |
| At rest | AES-256 volume and database encryption as the baseline |
| Field-level | Sensitive-class fields (health, safeguarding, biometric templates, bank details) encrypted at field level with separate key custody |
| Key management | HSM or managed KMS; documented rotation; two-person control for credential-signing keys (Chapter 5.3) |
| Signing | Per-institution key pairs; no group master key |
| Secrets | A secrets manager, never in source, never in environment files committed to a repository, never in logs. Scanned for in CI and in the repository history |
| Randomness | Cryptographically secure sources only |
| Hashing | SHA-256+ for integrity; Argon2id for passwords; never MD5 or SHA-1 for anything security-relevant |
| PII in logs | Redacted at the logging layer, not by convention |
| Backups | Encrypted, key-separated from the primary system |
| Biometrics | **Templates only, never raw images**; encrypted; deleted on relationship end; never leave the institution's tenancy |
| Payment data | Never stored. Tokenised at the processor. PCI scope minimised deliberately |
| Quantum posture | Track NIST post-quantum standards; prioritise **credential signatures** for migration, since a certificate issued in 2027 may need to remain verifiable in 2067 and is therefore the group's longest-lived cryptographic commitment (Volume IX, Chapter 7) |

---

# CHAPTER 15 — SECURITY BIBLE IV: SECURE DEVELOPMENT

| Practice | Rule |
|---|---|
| Threat modelling | Required for any feature touching auth, payments, credentials, or sensitive-class data |
| Code review | Every change, by someone who did not write it. No exceptions for seniority or urgency |
| SAST / DAST | In CI, blocking on high severity |
| Dependency scanning | Continuous; critical vulnerabilities patched within 48h, high within 7 days |
| Supply chain | Pinned dependencies; lockfiles committed; provenance verified; a new dependency requires a justification |
| Secrets scanning | Pre-commit and in CI, including history |
| Input validation | Server-side always; client-side is UX, never security |
| Output encoding | Context-appropriate; templating auto-escapes by default |
| SQL | Parameterised queries only. String-built SQL is a blocking review failure |
| **SSRF** | **Allow-list outbound destinations; validate and re-validate redirects; block private address ranges.** This is called out specifically because a critical SSRF vulnerability was found, reproduced and fixed during the group's own independent MVP audit — the lesson is retained here rather than quietly forgotten |
| File uploads | Type and size validated; content-sniffed; stored outside the web root; served from a separate origin; scanned |
| Deserialisation | Never deserialise untrusted input into executable structures |
| Error handling | No stack traces, internal paths, or version strings to users |
| Security headers | CSP, HSTS, X-Content-Type-Options, Referrer-Policy, Permissions-Policy — verified in tests |
| Penetration testing | Annual minimum; before any government or enterprise go-live; after any architectural change to auth or credentials |
| Bug bounty | Public programme from Phase I; safe harbour stated; researchers paid and credited |

---

# CHAPTER 16 — SECURITY BIBLE V: RESILIENCE, BACKUP & CONTINUITY

## 16.1 Backup

| Property | Standard |
|---|---|
| Frequency | Continuous WAL archiving + daily full |
| Retention | 30 days standard; 1 year and 7 years available |
| Geography | At least two regions; at least one outside the primary jurisdiction |
| Encryption | Always, with separate key custody |
| Immutability | Write-once retention on at least one copy — ransomware defence |
| **Restore testing** | **Monthly, automated, verified against a checksum and a functional smoke test.** An untested backup is not a backup and may not be described as one |

## 16.2 Recovery objectives

| Tier | RPO | RTO |
|---|---|---|
| Standard | 24h | 8h |
| Professional | 4h | 4h |
| Premium | 1h | 2h |
| Elite | 15 min | 1h |
| Enterprise | 5 min | 30 min |

## 16.3 Continuity

Documented and **rehearsed**: regional failure, database failure, provider failure, payment-processor failure, AI-provider failure, key-person unavailability, office inaccessibility, and extended power or connectivity loss in a market. A plan that has never been rehearsed is a document, not a capability. Rehearsal cadence: at least annually, with findings recorded and acted on.

---

# CHAPTER 17 — SECURITY BIBLE VI: INCIDENT RESPONSE

## 17.1 Severity

| Sev | Definition | Response |
|---|---|---|
| **S0** | Customer data exposed; credential system compromised; funds at risk | Immediate, all hands, executive informed within 15 min |
| **S1** | Platform down; auth broken; data integrity at risk | Immediate, on-call escalated |
| **S2** | Major feature broken; performance severely degraded | Same business day |
| **S3** | Minor defect with a workaround | Next release |

**Cross-tenant data access is automatically S0**, regardless of how many records were involved, including one.

## 17.2 The response sequence

Detect → declare (anyone may declare; nobody is penalised for a false alarm) → assign an incident commander → contain → preserve evidence → **notify the customer** → eradicate → recover → verify → **publish**.

## 17.3 Notification commitments

| Audience | Timing |
|---|---|
| Affected customers | **Within 24 hours of confirmation**, before we fully understand it, saying what we do and do not yet know |
| Regulators | Per statute (NDPA, GDPR: 72 hours) |
| Public | With the post-incident review |
| Data subjects | Where required by law, or where the risk to them is material regardless of legal requirement |

## 17.4 The post-incident review

Published, blameless, and specific. It states what happened, the timeline, the impact including the number of records, the root cause, what we fixed, and what we changed so it cannot recur. It names no individual. It does not use the passive voice to obscure agency (Volume I §11.2.4).

**We publish these even when nobody would have found out.** The willingness to do so is the asset; the incident is just an event.

---

# CHAPTER 18 — QUALITY, TESTING & THE DEFINITION OF DONE

## 18.1 The test pyramid

Unit (fast, numerous) → integration (real database, real dependencies) → contract (API compatibility) → end-to-end (critical journeys only) → performance (against Chapter 10 budgets) → security (the cross-tenant suite, auth suite, injection suite) → accessibility (automated, plus manual on new patterns) → **restore** (Chapter 16.1).

**Mandatory suites that may never be skipped in CI:** cross-tenant isolation, authentication and authorisation, payment idempotency, credential signing and verification, and data export completeness.

## 18.2 The Definition of Done

A change is done when **all** of the following are true:

1. It works on a mid-range Android on 3 Mbps.
2. It works in RTL and in at least one non-English locale.
3. It meets WCAG 2.2 AA, verified.
4. It is within the Chapter 10 performance budgets.
5. It has tests at the appropriate levels, and they pass.
6. It has been reviewed by someone who did not write it.
7. Its failure modes are defined and its degraded mode is implemented.
8. It is observable — logs, metrics, and an alert if it matters.
9. It is documented where a user or an integrator would look.
10. It exports. Any new record type is in the export.
11. It has a rollback, and the rollback has been considered rather than assumed.
12. Its audit events are emitted.
13. A migration, if any, has a tested reverse path.

"Done" is not "merged". It is not "works on my machine". It is not "we'll add tests later".

---

# CHAPTER 19 — RELEASE ENGINEERING

Trunk-based development with short-lived branches · every commit builds and tests · staging mirrors production in shape if not scale · progressive rollout (internal → 5% → 25% → 100%) with automatic rollback on error-rate or latency regression · feature flags for anything user-visible and risky · database migrations are backward-compatible and deployed separately from the code that requires them · **never deploy on a Friday afternoon or during an institution's examination window, results period, or admissions deadline** — the customer's calendar constrains our release calendar, and this is a hard rule that has cost us less than one incident would have.

Release cadence: continuous for fixes, weekly for features, quarterly for anything requiring customer preparation. Institutions receive 30 days' notice of any change that alters a workflow they have trained staff on.

---

# CHAPTER 20 — OBSERVABILITY

Structured logs with correlation IDs and redacted PII · RED metrics (rate, errors, duration) per service and USE metrics (utilisation, saturation, errors) per resource · distributed tracing across service boundaries · real user monitoring from the actual devices and networks our users have, not synthetic tests from a data centre · error tracking with grouping and ownership · a **public** status page with real uptime and full incident history · alerting that pages a human only for things a human must act on immediately, because an alert nobody acts on trains everyone to ignore alerts.

**The customer-visible half:** every institution sees its own audit log, its own uptime, its own SLA credit position (applied automatically — Volume III §17.2), and its own consumption against caps.

---

# CHAPTER 21 — TECHNICAL DEBT & ARCHITECTURE DECISION RECORDS

## 21.1 ADRs

Every architecturally significant decision is recorded: context, options considered, decision, consequences, and what would make us revisit it. Stored in the repository, numbered, immutable once accepted, superseded rather than edited. A decision whose reasoning is undocumented will be re-litigated by someone who does not know it was already settled — that is the actual cost this prevents.

## 21.2 Debt

Debt is **registered, not tolerated silently**. Each item carries its cost (what it slows or risks), its interest (whether it worsens with time), and a decision: pay now, pay by a date, or accept permanently with a stated reason. **20% of engineering capacity is reserved for debt, tooling and reliability** and is not reallocated to features under delivery pressure. Under sustained pressure, scope is cut before this reserve is — because the reserve is what makes the next quarter possible.

---

*Volume IV ends. Volume V — [Go-to-Market](VOLUME-V-GTM-SALES-PARTNERS.md).*
