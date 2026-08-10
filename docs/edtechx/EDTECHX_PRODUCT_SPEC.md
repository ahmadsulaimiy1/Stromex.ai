# EdTechX Product Specification

**Derives from:** `EDTECHX_EDITORIAL_BIBLE.md`
**Version:** 1.0

---

## 1. What EdTechX is

EdTechX is a multi-tenant **education operating system**: a school information system (SIS) and a learning management system (LMS) in one product, deeply customizable per institution, with an AI assistance layer and a commercial platform underneath.

It is deliberately *both* SIS and LMS. The market's central failure is the seam between them: a school runs PowerSchool-shaped operations and Moodle-shaped learning, and reconciles by hand. In EdTechX, a class roster, a gradebook, an assignment, an attendance register, and a report card are all views over one coherent domain model.

### 1.1 What EdTechX is not

- Not a course marketplace.
- Not a consumer study app.
- Not a generic no-code platform that happens to have school templates.
- Not a proctoring or surveillance system.

---

## 2. Module map

Seventeen modules in four groups. Each is a bounded context with an owning schema namespace (see `EDTECHX_ARCHITECTURE.md` §3).

### Group A — Platform (tenant-independent or tenant-defining)

| Module | Responsibility |
|---|---|
| `tenancy` | Tenants, domains, subscriptions, provisioning, tenant lifecycle |
| `identity` | Users, credentials, sessions, MFA, SSO, memberships |
| `authz` | Roles, permissions, scopes, policy evaluation |
| `billing` | Plans, entitlements, pricing, invoices, quotas, metering |
| `platform_ops` | Operator console, tenant health, break-glass, support |

### Group B — Institution (the school's own shape)

| Module | Responsibility |
|---|---|
| `institution` | Campuses, departments, houses, staff, org structure |
| `academics` | Academic years, terms, levels, classes/sections, subjects, curriculum |
| `people` | Students, guardians, enrolment, relationships |
| `customization` | Themes, terminology, navigation, dashboards, documents, forms |

### Group C — Operations (running the school)

| Module | Responsibility |
|---|---|
| `admissions` | Applications, stages, decisions, offers, conversion to enrolment |
| `attendance` | Sessions, marks, policies, absence workflows |
| `timetable` | Periods, rooms, allocations, constraints |
| `assessment` | Exams, marks, grading scales, results, promotion |
| `reporting` | Report cards, transcripts, certificates, statements |
| `finance` | Fee structures, invoices, payments, receipts, ledgers |
| `communication` | Announcements, messages, notifications, channels |
| `conduct` | Behaviour, merits, incidents, interventions |

### Group D — Learning (the LMS)

| Module | Responsibility |
|---|---|
| `learning` | Courses, modules, lessons, resources, learning paths, prerequisites |
| `activities` | Assignments, submissions, quizzes, question banks, rubrics, grading |
| `engagement` | Discussions, groups/cohorts, completion, progress, certificates |

### Group E — Intelligence

| Module | Responsibility |
|---|---|
| `intelligence` | AI gateway, assistants, design studio, metering, safety rails |

---

## 3. LMS depth requirement

The bar is **Moodle-level functional depth with a materially better experience.** Specifically:

- Courses, course categories, course templates
- Modules, lessons, sequencing, release conditions
- Resources: files, links, embedded media, pages, folders
- Assignments: instructions, attachments, due/cutoff dates, late policy, resubmission, group submission, plagiarism-hook interface
- Submissions: file, text, link, offline; versioning; draft vs submitted
- Quizzes: multiple question types, question banks, categories, randomization, shuffling, attempt limits, time limits, review rules
- Question types (v1): multiple choice, multiple response, true/false, short answer, numeric, matching, essay, file response
- Grading: points, percentage, scale, rubric, letter; blind marking; moderation
- Gradebook: per-course and per-student views, weighted categories, drop-lowest, overrides with reason, export
- Rubrics: criteria, levels, descriptors, per-criterion feedback
- Completion tracking: activity-level and course-level criteria
- Progress: per-student, per-cohort, per-course
- Certificates: template-driven, issued on completion criteria
- Discussions: forums, threads, subscriptions, moderation
- Announcements: course, class, cohort, institution scope
- Learning paths and prerequisites
- Cohorts and groups, with group-level assignment and grading
- Calendar integration with all dated entities

**What we deliberately do not copy from Moodle:** its information architecture, its administration model (a settings tree of thousands of nodes), its plugin-driven inconsistency, and its visual language.

---

## 4. Information architecture per persona

Six distinct navigation trees. The *same* underlying data; genuinely different organization.

### 4.1 Administrator / registrar

**Landing:** operations dashboard.
Priority order: pending approvals → today's exceptions (unmarked attendance, absent staff) → enrolment and roll numbers → finance position → recent audit activity.

**Navigation:** People (Students, Guardians, Staff) · Academics (Years, Terms, Classes, Subjects, Timetable) · Operations (Attendance, Assessment, Conduct) · Admissions · Finance · Communication · Reports · Configure.

**Non-negotiable capabilities:** bulk import, bulk edit, bulk message, saved views, export of every list, audit trail on every mutation.

### 4.2 Teacher

**Landing:** today.
Priority order: next lesson (with one-tap attendance) → today's remaining lessons → grading queue with counts → items needing my response → my classes.

**Navigation:** Today · My Classes · Grading · Assignments · Attendance · Students · Messages.

**Design constraint:** attendance for a class of 40 in under 30 seconds on a phone; assignment creation in under 90 seconds; grading a submission without leaving the keyboard.

### 4.3 Student

**Landing:** today and next.
Priority order: due next (with time remaining) → today's timetable → new feedback and grades → course progress → announcements.

**Navigation:** Home · Courses · Assignments · Grades · Timetable · Messages.

**Design constraint:** the answer to "what do I have to do, and when is it due?" is visible without scrolling on a 360px screen.

### 4.4 Parent / family

**Landing:** child overview (with a child switcher if more than one).
Priority order: anything needing action (unpaid fee, unsigned form, absence to explain) → attendance summary → recent results → upcoming events → announcements.

**Navigation:** Overview · Attendance · Results · Fees · Messages · School.

**Design constraint:** plain language; every number is accompanied by its meaning; no unexplained acronyms; the whole portal usable by someone who has never used a school app before.

### 4.5 Principal / owner

**Landing:** executive overview.
Priority order: enrolment trend → attendance rate with trend → academic performance distribution → financial position (collected vs outstanding) → staffing → risk flags (chronic absence, failing cohorts, overdue fees).

**Navigation:** Overview · Academic · Operations · Finance · Staff · Reports.

**Design constraint:** every figure is drillable to the underlying records within two clicks, and every figure carries a comparison (previous term, previous year, or target).

### 4.6 Platform operator

**Landing:** platform health.
Priority order: incidents → tenants at risk (quota, billing, error rate) → provisioning queue → support tickets → usage and cost.

**Navigation:** Tenants · Health · Billing · Support · Usage · Security · Configuration.

**Constraint:** access to tenant *content* requires an explicit break-glass action with reason, time limit, tenant notification, and audit entry.

---

## 5. Core school operations — functional requirements

### 5.1 People
Students with full profile, identifiers, enrolment history, documents, guardians with relationship type and contact preferences and custody flags, staff with roles and qualifications and contracts.

### 5.2 Academics
Academic years with terms; levels (year groups) with configurable names; classes/sections with a form tutor; subjects with departments; subject-to-class allocations; teaching assignments.

### 5.3 Admissions
Configurable pipeline stages; application forms built from the form engine; document upload; assessment/interview scheduling; decision with reason; offer, acceptance, and automatic conversion to enrolment.

### 5.4 Attendance
Configurable models: daily, per-session, per-period. Configurable mark codes (present, absent, late, excused, and school-defined codes) each with a semantic category. Bulk marking, defaults, corrections with reason and audit, absence explanation workflow with guardian involvement, statutory-style reporting.

### 5.5 Timetable
Period structures per level; rooms with capacity; allocation of class × subject × teacher × room × period; clash detection as a hard constraint; cover/substitution; per-user timetable views.

### 5.6 Assessment and results
Exams and assessment components; configurable weighting; mark entry with validation against maxima; grading scales as data (letter, percentage, GPA, descriptor); moderation; results approval workflow with an explicit publish step; publish controls per audience.

### 5.7 Reporting documents
Report cards, transcripts, certificates, and statements from a template engine with school-owned designs; deterministic rendering; versioning; regeneration produces identical output for the same inputs.

### 5.8 Finance
Fee structures per level/term with optional per-student adjustments; invoices; payment records; receipts; discounts and scholarships; instalment plans; outstanding-balance reporting; payment-provider abstraction with adapters.

### 5.9 Communication
Announcements with audience targeting; direct and group messaging with school-controlled policy; notification delivery across channels (in-app, email, SMS, WhatsApp) via a provider abstraction; per-user preferences; delivery status.

### 5.10 Conduct
Positive and negative records with configurable types and point values; incident workflow; intervention tracking; guardian visibility rules configurable per record type.

### 5.11 Analytics
Institution-level, cohort-level, and student-level analytics. Every figure traceable to source records.

---

## 6. Customization requirement (summary)

Full specification in `EDTECHX_CUSTOMIZATION_ENGINE.md`. The school controls: brand identity, interface appearance, navigation structure and labels, dashboard composition, terminology, document templates, academic structure, workflows, forms and custom fields, roles and permissions, and notification behaviour — **without a separate codebase, file-system change, redeployment, or any effect on another tenant.**

---

## 7. Commercial requirement (summary)

Full specification in `EDTECHX_BILLING.md`. Five plans (Free, Starter, Professional, Premium, Enterprise) expressed as **entitlement sets evaluated at runtime**, never as `if plan == "premium"` scattered through the code. Pricing is configuration: currency, region, school size, billing cycle, promotions.

---

## 8. Release scope

### v1 — Institutional Core (the pilot-ready product)
Tenancy · identity · authz · institution · academics · people · attendance · assessment (core) · reporting (report cards) · finance (fees/invoices/payments) · communication (announcements + notifications) · customization (theme, terminology, navigation) · billing (plans + entitlements + metering) · intelligence (gateway + first assistants).

### v2 — Learning Core
learning · activities · engagement · gradebook depth · admissions · timetable · conduct.

### v3 — Differentiation
Design Studio · AI Design Studio · advanced analytics · marketplace foundations · professional services workflow.

Detailed sequencing in `EDTECHX_ROADMAP.md`.

---

## 9. Critical user journeys (the test set)

These twelve journeys define the product. Each has an end-to-end test (`EDTECHX_TESTS.md`).

1. Teacher marks attendance for a class
2. Student submits an assignment
3. Teacher grades a submission
4. Admin publishes results
5. Parent views a published result
6. Admin issues a fee and a parent sees it
7. Parent records a payment against an invoice
8. School changes and publishes its theme
9. School renames a core term and it propagates everywhere
10. AI proposes a design; an administrator reviews and approves it
11. Administrator bulk-imports students
12. **Tenant A attempts to access Tenant B's data — must fail, at every layer**

Journey 12 is not a feature test. It is the product's licence to exist.
