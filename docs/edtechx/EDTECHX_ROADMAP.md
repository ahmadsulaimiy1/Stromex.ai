# EdirasX Implementation Roadmap

**Version:** 1.0
**Sequencing principle:** build the load-bearing walls first. Every phase ends with something a real school could use, and nothing in a later phase requires demolishing an earlier one.

---

## Phase 0 — Constitution *(complete)*

Repository and environment inspected; EdirasX placed in its own namespace alongside StromeX; the eleven governing documents written; the progress system established.

**Exit criterion:** an engineer or agent joining cold can derive the right answer to a design question without asking. ✅

---

## Phase 1 — The Isolation Spine

The single most important phase. Everything else assumes it is correct, and it is the hardest thing to retrofit.

- Project skeleton, configuration, structured logging, error handling
- `tenants`, `tenant_domains`, `users`, `memberships`, `roles`, `membership_roles`, `sessions`, `audit_events`
- Tenant resolution from host; token/host agreement check
- **PostgreSQL RLS on every tenant-owned table**, application role without `BYPASSRLS`, `FORCE ROW LEVEL SECURITY`
- ORM tenant guard (stamp on insert, filter on query)
- Authentication: Argon2id, access + rotating refresh with reuse detection, revocation
- Permission catalogue, role templates, scope compilation
- Audit infrastructure
- **The generated tenant-isolation test suite** — enumerates every tenant-owned model automatically, so new models are covered without anyone remembering
- Module-boundary test; route-coverage test (no route without a declared permission or explicit public marker)

**Exit criterion:** journey 12 passes — Tenant A cannot reach Tenant B by any route, parameter, header, or body field — and it will keep passing as models are added.

---

## Phase 2 — The Institution

The school's own shape, so that nothing downstream needs to assume one.

- Campuses, departments, houses, staff profiles
- Academic years, terms, stages, levels, class groups, subjects, class-subject allocation
- Grading scales and bands as data
- People, distinct from identities; student, staff and guardian relationships
- Enrolment as history — admission, enrolment, transfer, suspension, withdrawal, readmission, progression, completion, awarding — never a mutable `student.class_id`
- Custom fields on core entities
- Bulk import with validation, dry-run, and a per-row error report
- Terminology configuration and resolution
- Entitlement engine and plan seeding

**Exit criterion:** every institution in the Bible's Universal Education Test — early years through doctoral research — can be configured with zero code changes.

---

## Phase 3 — Daily Operations

The reason a teacher opens the product.

- Attendance: configurable model, school-defined codes, session/mark, bulk marking, corrections with reason, absence workflow
- Assessment: assessments, mark entry with validation, moderation, results approval and the explicit publish step
- Report cards from templates; deterministic document rendering
- Communication: announcements with audience targeting; notification abstraction with email adapter; delivery status
- Finance: fee structures, invoices, payments, receipts, balances, the money invariants
- Payment provider abstraction with sandbox adapter

**Exit criterion:** journeys 1, 4, 5, 6, 7 pass end to end.

---

## Phase 4 — The Experience

Where EdirasX stops being a competent system and starts being a prestigious one.

- Design system implementation: tokens, primitives, form, data, layout, feedback, navigation components — every state, keyboard, RTL, light/dark
- App shell and per-persona navigation resolved from configuration
- The six dashboards, each with its own information architecture
- Teacher: today, attendance marking (the 30-second target), grading queue
- Student: due next, courses, grades
- Parent: child overview, attendance, results, fees
- Admin: people, academics, operations, bulk actions
- Principal: executive overview with drill-down
- Theme resolution and per-tenant stylesheet delivery
- PWA shell, offline attendance queue, low-bandwidth budgets
- Accessibility pass on every journey

**Exit criterion:** the design review questions in the Bible §4.3 are answered yes, by someone who did not build it.

---

## Phase 5 — Intelligence

- AI Gateway: request/response contract, adapters (Anthropic, OpenAI, Google, DeepSeek, OpenAI-compatible, dev), routing, fallback, circuit breaker
- Metering, quotas, per-tenant usage visibility
- The approval gate and `ai_approvals` — with the test that proves no AI path can write a record of consequence
- Prompt registry with versioning and golden-set evaluation
- First assistants: Teacher (comments, questions, lesson planning), Administrator (natural-language search within the principal's authority), Parent (plain-language explanation)
- BYO AI keys: encrypted storage, validation on save, rotation, revocation

**Exit criterion:** provider can be swapped by configuration alone, and no AI path can mutate an academic record.

---

## Phase 6 — Learning

- Courses, categories, modules, lessons, resources, release conditions
- Assignments, submissions (multi-type, versioned, late policy, resubmission, group)
- Grading with rubrics; gradebook with weighted categories and overrides
- Quizzes: question banks, types, randomization, attempts, time limits, review rules
- Completion tracking, progress, learning paths, prerequisites
- Cohorts, groups, discussions, certificates

**Exit criterion:** journeys 2 and 3 pass; the LMS depth list in the Product Spec §3 is met.

---

## Phase 7 — Studios

- Design Studio: live preview, all editors, undo/redo, drafts, compare, publish, version history, rollback
- AI Design Studio: natural-language request → validated proposal → contrast-corrected → preview across personas and breakpoints → refine → approve → publish
- Document designer
- Navigation and dashboard editors

**Exit criterion:** journeys 8, 9, 10 pass; a non-technical administrator rebrands the platform unaided in under twenty minutes.

---

## Phase 8 — Operations at Scale

- Admissions pipeline; timetabling with clash constraints; conduct
- Platform operator console; break-glass with notification and expiry
- Custom domains with managed TLS
- SSO (SAML/OIDC)
- Advanced analytics
- Backup/restore drills; performance work against measured budgets
- Penetration test

**Exit criterion:** production-ready for the pilot.

---

## Phase 9 — Pilot

One real school. Real administrators, teachers, students, parents. Real courses, attendance, exams, results, fees, communications. Real phones, real networks.

Instrumented for: task completion time, error rate, support contacts per user per week, page performance on actual devices, and the questions people ask — which are the true measure of discoverability.

**Exit criterion:** teachers prefer it to what they had. Nothing else counts.

---

## Phase 10 — Ecosystem

Professional services workflow · experience marketplace · integrations · regional expansion.

---

## Sequencing rationale

**Why isolation before features:** retrofitting tenant isolation means auditing every query ever written. Building it first means it is never wrong.

**Why institution before operations:** if attendance is built before academic structure is configurable, attendance will assume a structure, and the Four Schools test fails permanently.

**Why operations before the LMS:** schools buy the SIS and tolerate the LMS. Attendance, results, and fees are what makes a school switch.

**Why the design system after the first working operations:** components designed against real screens with real data are right; components designed in the abstract get rebuilt.

**Why intelligence after operations:** AI over an empty database is a demo. AI over a term of real attendance and marks is a product.

**Why the studios late:** they are the differentiator, but they are configuration editors — they need something to configure.

---

## Standing rules across all phases

1. No phase is complete until its features meet the Bible's Definition of Done — all thirteen items.
2. Security and accessibility are done inside each phase, never scheduled as a later phase of their own.
3. The isolation, authorization, escalation, and SSRF suites are blocking on every commit.
4. Design review at the end of every phase, conducted as a designer, not as the implementer.
5. Competitive review at the end of every second phase.
6. `EDTECHX_PROGRESS.md` is updated as work happens, not at the end.
