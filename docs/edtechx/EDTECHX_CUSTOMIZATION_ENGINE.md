# EdirasX Customization Engine

**Version:** 1.0
**Governing principle:** `EDTECHX_EDITORIAL_BIBLE.md` §6 — "It should feel like our school."

---

## 1. The requirement

A school must be able to customize deeply — not "upload your logo." And it must be able to do so **without** a separate codebase, a file-system change, a redeployment, any effect on another tenant, or any break in tenant isolation.

That constraint has one solution: **every customizable thing is a versioned, schema-validated document in the database, resolved at request time.** There is no per-tenant code. There is no per-tenant build. There is only data.

---

## 2. Uniform model

Every configuration object — theme, terminology, navigation, dashboards, documents, forms, workflows — shares one shape:

| Field | Meaning |
|---|---|
| `tenant_id` | Owner |
| `kind` + discriminator | What it configures |
| `status` | `draft` · `published` · `archived` |
| `version` | Monotonic per tenant per kind |
| `parent_version_id` | Lineage, enabling rollback by reference |
| `payload jsonb` | The configuration, valid against a versioned JSON Schema |
| `created_by` / `published_by` / `published_at` | Attribution |

And one lifecycle:

```
edit draft → validate → preview → publish (audited) → live
                                      ↓
                              rollback to any prior version
```

Publishing never mutates a previous version. Rollback restores by reference. History is complete and permanent. This uniformity is what makes the Design Studio, the AI Design Studio, and a future marketplace all the same machinery.

---

## 3. Resolution cascade

```
EdirasX default → tenant → campus → role → user preference (where the school permits)
```

Resolved once per request into an immutable configuration bundle, cached in Redis keyed by `(tenant_id, kind, version)`, invalidated on publish. Cache misses are cheap; publishes are rare.

**The school controls how far down the cascade goes.** A school that wants absolute uniformity disables user-level preferences entirely; a school that wants teachers to choose density permits that one key.

---

## 4. Brand identity

- **Logos:** primary, compact/square, monochrome, and email variants; SVG preferred with raster fallback; validated dimensions and file size.
- **Favicon:** generated from the square mark across required sizes.
- **Colours:** every semantic role in `EDTECHX_DESIGN_SYSTEM.md` §3.1, light and dark. Supply the accent and the rest is derived for approval — never silently applied.
- **Typography:** heading, body, mono, and regional families from a licensed catalogue; own licensed webfonts on Premium+, subset and served from tenant storage.
- **Style presets:** curated starting points ("Classical", "Contemporary", "Warm", "Minimal", "Regional") that set tokens coherently. A preset is a starting point, not a lock.
- **Background treatments:** subtle patterns or crests for login and document headers, from a curated set or uploaded.

**Validation is a feature, not an obstacle.** On save, the engine checks every foreground/background pair for WCAG contrast, both themes, and refuses to publish a failing palette — offering the nearest compliant value with an explanation. A school cannot accidentally publish a portal its own dyslexic or low-vision students cannot read.

---

## 5. Interface customization

| Surface | What the school controls |
|---|---|
| Navigation | Items present, labels, order, grouping, icons, visibility per role |
| Dashboards | Widget set, order, size, per persona |
| Homepage / landing | Layout, hero content, quick links, announcements placement |
| Login page | Layout variant, background, message, support contact, SSO prominence |
| Portals | Per-persona layout emphasis and density |
| Components | Card style, border weight, radius, elevation level, table style, button style, form style |
| Density | `comfortable` \| `compact`, per persona |

Bounded on purpose: the school chooses among coherent options rather than authoring arbitrary CSS. Arbitrary CSS would be a styling injection vector (`EDTECHX_SECURITY.md` §5), would break on every upgrade, and would let a school build something inaccessible. Depth comes from the breadth of the token surface, not from an escape hatch. (`EDTECHX_DECISIONS.md` ADR-007.)

---

## 6. Terminology

The single most under-appreciated customization, and the one schools notice most.

```json
{
  "class":   { "singular": "form",   "plural": "forms" },
  "student": { "singular": "pupil",  "plural": "pupils" },
  "grade":   { "singular": "year",   "plural": "years" },
  "term":    { "singular": "half-term", "plural": "half-terms" }
}
```

Rules that make this work:
- **No domain noun is ever a literal in the UI.** Every one comes from the term map. A lint rule fails a build containing a hard-coded domain noun in user-facing copy.
- Singular, plural, and grammatical gender where the locale needs it; the interface is authored so that no sentence is built by concatenation.
- Multiple locales per tenant; a term map per locale.
- Terms flow through everything: navigation, headings, buttons, emails, notifications, documents, exports, and AI assistant output.

---

## 7. Academic structure

Configured, never coded — the Bible's "Four Schools test" is the acceptance criterion.

- **Stages and levels:** any names, any depth ("Primary/Secondary", "Elementary/Middle/High", "Nursery/Primary/College", "Foundation/Undergraduate/Postgraduate").
- **Year and term structure:** any number of terms/semesters, any dates, any names.
- **Grading scales:** letter, percentage, GPA, descriptor, or points; bands with thresholds, pass marks, and descriptors; multiple scales in one school (different scales per stage or subject).
- **Attendance model:** daily, per-session, or per-period; school-defined mark codes each mapped to a stable category.
- **Assessment structure:** components, weights, aggregation rules, moderation policy.
- **Promotion rules:** expressed as declarative conditions over results, attendance, and conduct; evaluated by the rule engine; always producing an explainable outcome per student rather than an opaque verdict.
- **Organizational structure:** campuses, departments, houses, cohorts — any or none.

---

## 8. Documents

Report cards, transcripts, certificates, invoices, receipts, and letters are template documents the school owns.

- Composed from typed blocks: header, student identity block, results table, attendance summary, comments, signature area, footer, page furniture.
- Bound to real data by named fields, validated against what the school's academic structure actually produces.
- Page geometry (A4 / Letter), margins, running headers and footers, page numbering, and controlled page breaks.
- **Deterministic:** identical inputs produce byte-identical output. A report card regenerated in five years is the same document.
- Every issued document carries an immutable verification identifier and, where enabled, a public verification URL.

Email templates follow the same model: school identity, school voice, per-notification-type control.

---

## 9. Custom fields, forms, and workflows

**Custom fields:** any core entity (student, guardian, staff, class, course) can carry school-defined fields — type, label, options, validation, requiredness, visibility per role, and inclusion in exports. Values are stored in the entity's `custom jsonb`, validated against the field definitions on every write.

**Forms:** a definition-driven engine (fields, sections, conditional logic, validation, file uploads, signatures) used by admissions, consent collection, incident reporting, and anything a school invents. Submissions are first-class records with audit.

**Workflows:** declarative approval chains — trigger, stages, approvers by role or scope, escalation, timeout, and outcome actions — applied to result publication, fee waivers, leave, admissions decisions, and school-defined processes.

**Roles and permissions:** schools clone and edit system roles, create their own, and set scopes (`EDTECHX_PERMISSION_MODEL.md`). Delegation cannot manufacture privilege.

---

## 10. Design Studio

A professional design environment, not a settings page. This distinction is the whole point: schools have seen settings pages, and they do not feel like ownership.

**Layout:** a control rail on the left, a live canvas at the centre, a version and publish rail on the right.

**Capabilities**
- Live preview — every change renders immediately, with no page refresh and no flash of unstyled content.
- Preview *as*: administrator, teacher, student, parent, principal — the same theme across genuinely different information architecture.
- Preview *at*: mobile, tablet, desktop; light and dark; LTR and RTL.
- Preview *on*: real screens with the school's real (or sample) data, never lorem ipsum.
- Typography controls: family, scale, weight, line height, with live specimens.
- Colour controls: palette editing with a **live contrast report** — not a warning after the fact, a running score.
- Layout controls: grid, spacing, density.
- Component controls: style per component family.
- Navigation editor: drag to reorder, rename inline, toggle visibility per role.
- Dashboard editor: add, remove, resize, reorder widgets per persona.
- Login and document editors.
- Undo / redo across the whole session.
- Draft management: name, duplicate, compare drafts side by side.
- Publish with a summary of exactly what will change and who it affects.
- Version history with visual diff and one-click rollback.

**UX requirements:** immediate, smooth, no technical jargon, no raw token names exposed unless the user asks for advanced mode, and a clear draft/published distinction at all times. It should feel like a design tool that a competent administrator can use confidently in twenty minutes.

---

## 11. AI Design Studio

Natural language in, structured design proposal out, human approval always. Full specification in `EDTECHX_AI_ARCHITECTURE.md` §8.

The customization-engine requirement is only this: an AI proposal is written to `ai_design_proposals`, and on approval it becomes an ordinary **draft theme version** which is then published through the ordinary, audited publish path. The AI has no privileged write. It produces a document like any other author, and a human publishes it.

---

## 12. Portability

Because every configuration is a versioned, schema-validated document, a complete "experience" — theme, terminology, navigation, dashboards, documents — is a portable bundle. This gives, with no further architecture:

- Export a school's configuration and import it into a sandbox or a sister campus.
- Templates for onboarding ("British independent school", "Nigerian secondary school", "GCC international school") as starting bundles.
- Professional-services delivery: a designer works in a sandbox tenant and delivers a bundle.
- The future marketplace: an "experience" is a signed bundle, reviewed by EdirasX, installed as a draft the school then customizes.

---

## 13. Invariants

1. No per-tenant code, files, or builds. Ever.
2. A tenant's configuration cannot affect another tenant.
3. Configuration cannot break accessibility — validation refuses it.
4. Configuration cannot inject executable content — values only, never raw CSS, HTML, or script.
5. Every publish is audited and reversible.
6. Missing configuration falls back cleanly to the EdirasX default; a partial theme never yields a broken interface.
7. A tenant can always export its configuration.
8. Publishing configuration never mutates or endangers institutional data.
