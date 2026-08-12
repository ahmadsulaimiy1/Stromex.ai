# EdirasX — where we are, and where we are going

*A full audit, run against a real database rather than a green summary.*

Senior developer: **Imam Ahmad Sulaimiy**, the expert behind these developments.

---

## 0. The one-paragraph answer

EdirasX has a **deep, genuinely tested institutional core and almost no way in**.
Fourteen domain modules, 68 tables, 61 of them under row-level security, 51,000
lines of Python, 1,214 passing tests against real PostgreSQL — and **16 HTTP
operations**. The engine is built and the doors are not. The document system is
the most advanced part of it: 24 editable templates, five compositions, every
size measured rather than claimed. What stands between this and a school using
it is not more architecture. It is an API surface, a browser that does something
when you click, and one real school.

---

## 1. What was found in this audit, and corrected

Three findings, in the order they matter.

### 1.1 The test suite was proving half of what it appeared to prove

PostgreSQL was not running. The suite reported **619 passed** and looked healthy.
It had **silently skipped 593 tests** — every row-level-security test, every
tenant-isolation test, auth, documents, imports, entitlements, scope predicates.
A green summary that skips half of itself says nothing about the half it skipped,
and it does not announce that unless somebody looks at the skip reasons.

**Corrected.** The database was started, roles and extensions confirmed, and the
suite run in full: **1,214 passed, 1 skipped, 0 failed.** The one skip is a
size test that correctly excludes a sheet the template does not offer.

> **Standing rule from this finding:** a suite that skips more than a handful of
> tests has not run. The skip count is part of the result, not a footnote.

### 1.2 The product had decided which education system it serves

With the database up, one test failed — and it was right.
`test_no_product_code_names_a_particular_school_system` found one education
tradition's vocabulary compiled into product code: *Diploma Supplement,
Ibtidāʼiyyah, Junior Secondary* in the template library; *doctorate, masters,
bachelor, diploma* in the prompt vocabulary.

This is not pedantry. A German institution issues a *Diplom*, a French one a
*licence*, an Islamic seminary an *ijāzah*. Vocabulary compiled into a module is
a product that has chosen its market, and the flexibility becomes documentation
rather than architecture.

**Corrected**, and the correction is also what "imported here for their quick
edit" asked for:

| Moved to data | Stayed in the product |
|---|---|
| `app/data/document-templates.toml` — the 24 documents | what a template *is*, what a slot is, what an edition is |
| `app/data/prompt-vocabulary.toml` — the 32 terms | which reissues are permitted and which are refused |
| every sentence, name and default | that character resolves before metal |
| | that a family is a composition somebody must write |

A tenant now ships its own file and gets its own library **with no deploy** —
exercised by a test, not asserted. Nothing was transcribed by hand: the files
were generated from the live structures, all 24 templates render byte-identically
afterwards, and the visual audit is unchanged.

### 1.3 Four documents had never been looked at

Every composition had passed the machine audit. Rendering four of them found six
defects the audit could not see — a custom property that never reached the
stylesheet, so the seal rendered at 79mm instead of 22 on every sheet in the
library; a foot that did not grow with the sheet; inline rows that pushed
instead of wrapping; an Arabic overprint laid out left-to-right; a Diploma
Supplement carrying the transcript's course list. All corrected, and the audit
now measures horizontal overflow, which it previously did not.

> **Standing rule from this finding:** measurement and looking catch different
> defects. Neither substitutes for the other.

---

## 2. Where we are — measured, not claimed

### 2.1 The core

| | |
|---|---|
| Domain modules | **14** |
| Tables | **68**, of which **61 under RLS** |
| Tables deliberately global | 7 — `tenants`, `tenant_domains`, `users`, `plans`, `plan_features`, `plan_limits`, `security_events` |
| Migrations | 12, with an RLS gate |
| Python | ~51,000 lines |
| Tests | **1,214 passing, 0 failing** against real PostgreSQL |
| Architecture decisions recorded | 42 ADRs |
| Lint | clean |
| Stubs, TODOs, `NotImplementedError` | **none** |

### 2.2 What is genuinely finished

**The isolation spine.** Two database roles, neither bypassing RLS; a request
path that cannot connect as the owner; scope predicates compiled to SQL and
failing closed; leak-by-row-count tests. This is the part most multi-tenant
products get wrong and it is done.

**The institution.** Academic structure across four school systems, people and
identity kept properly separate, enrolment as immutable history rather than a
mutable `class_id`, bulk import with dry run and single-transaction apply,
entitlements distinct from permissions.

**The document system** — the most developed part of the product:

- 24 editable templates in 5 compositions, now **data rather than code**
- 15 reference-number families, 3 security classes
- Certified True Copy and Duplicate editions, with a duplicate lacking its
  original's number refused outright
- **279 compositions rendered and measured across 14 sheet sizes; 201 sizes
  honestly refused with the arithmetic; zero millimetres over**
- A resolution-free constructed ground: epitrochoid lathe work, real Code 128,
  serial-bearing rails, embossed khatam watermark

**The design system.** 25 modules, ~10,000 lines: geometry, gilding, heraldry,
language architecture with 8 bilingual arrangements, ceremony levels, 25 grounds,
signature background removal, a prompt resolver.

### 2.3 What is thin, and by how much

| | State |
|---|---|
| **HTTP API** | **16 operations.** Auth (7), attendance (3), students (2), health/context/me/experience (4) |
| **Frontend** | 17 server-rendered HTML journeys exist. **No client script at all** |
| Assessment, documents, academics, billing, imports | Service layer complete, **no endpoints** |
| Notifications, fees, admissions, timetabling | Not started |
| Screen-reader verification | Not done, not claimed |
| Dialog and palette focus behaviour | Markup correct, **behaviour unimplemented** |
| CI pipeline | **None** |
| Anything printed on paper | **Nothing** |

**The shape of the gap, stated plainly:** ~51,000 lines of domain logic behind
16 endpoints. The service layer is complete for six modules that have no way to
be called over HTTP.

### 2.4 What is specified but not proven

Every one of these is a specification, and none is claimed as verified:

- Foil, emboss and raised type are **simulations**, labelled as such
- The fine-text rails are fine text at ~0.41mm cap height — **not microprint**,
  which requires 0.25mm or below
- The anti-copy rulings are **screens, not a latent image**
- The printed fibres are **cosmetic**, not a substrate guarantee
- The QR bay is **reserved, not drawn** — EdirasX does not mint the code
- No press, no paper, no foil, no loupe, no measurement on a physical sheet

---

## 3. The phases — where we have been, where we are, where we go

### Behind us

| Phase | | |
|---|---|---|
| **0** | Constitution | ✅ complete |
| **1** | The Isolation Spine | ✅ complete — RLS, two roles, compiled scopes |
| **2** | The Institution | ✅ complete but for **custom fields** |
| **7 (early)** | Studios — the document system | ✅ substantially ahead of schedule |

Phase 7 ran early because the certificate work demanded it. That was the right
call — the document system is the product's most visible surface — but it means
Phases 3 and 4 are now the critical path.

### Where we are standing

**Phase 2 remainder, and the API gap.** One item closes Phase 2: custom fields on
core entities. But the more consequential fact is that Phase 2's work has no
doors. The next phase is not more domain modelling.

### Where we go — the sequence, and why it is this sequence

**Phase 3 · Doors — the API surface.** *The critical path.*
Endpoints for assessment, documents, academics, imports and billing; the
document library exposed so an institution can list templates, fill one, choose a
size, and get a sheet. The roadmap deliberately deferred routes until a real
caller existed. That caller now exists — it is the studio — so the deferral has
served its purpose and should end.

**Phase 4 · The Experience — a browser that responds.**
The 17 journeys are server-rendered HTML with correct markup and no behaviour.
Focus trapping, Escape, the command palette, the drawer, and the studio screen
where an institution picks a template, types a prompt, uploads a logo and a
signature, and sees a sheet.

**Phase 4½ · Paper.** Not in the original roadmap and it belongs here.
Everything about foil, emboss, hairline survival and Code 128 module width is a
specification. One press run against one proof sheet converts a chapter of
specifications into facts — or into corrections, which is more valuable.

**Phase 3 (parallel) · Ports.** Notifications, fees and finance, admissions,
timetabling. Each has a specified port and no adapter, blocked on credentials
rather than on design.

**Phase 5–6 · Intelligence and Learning.** The AI gateway is specified and
provider-agnostic; the institution studio's `AssistPort` returns a *brief*, never
artwork, which is the right boundary and should hold.

**Phase 8 · Operations at Scale.** CI is the honest first item. There is none,
and a suite that can silently skip 593 tests without a pipeline noticing is a
suite that will eventually be believed when it should not be.

**Phase 9 · Pilot.** One real school. Everything before this is preparation, and
nothing before this tells the truth about whether it works.

**Phase 10 · Ecosystem.**

### The three things that stand between here and a school using this

1. **An API surface** — the domain is built and unreachable.
2. **A browser that responds** — the markup is right and inert.
3. **One school** — no amount of internal audit substitutes for it.

Everything else is refinement of work that is already good.

---

## 4. Standing rules this audit adds

- **A suite that skips is a suite that has not run.** Report the skip count with
  the pass count, always.
- **Content is not product code.** Anything naming one institution's vocabulary
  belongs in a data file a tenant can replace.
- **Measurement and looking catch different defects.** Ship neither alone.
- **A refusal without a number is an opinion.** Every "does not fit" carries the
  arithmetic.
- **Never claim a security, accessibility or product property the implementation
  has not demonstrated.** Nothing here has been printed, and the document says so
  in every place it could be misread.
