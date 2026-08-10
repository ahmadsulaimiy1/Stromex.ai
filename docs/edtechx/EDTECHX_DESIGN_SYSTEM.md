# EdTechX Design System

**Derives from:** `EDTECHX_EDITORIAL_BIBLE.md` §4, `EDTECHX_UX_PRINCIPLES.md`
**Version:** 1.0

---

## 1. The central constraint

Every visual value in EdTechX is a **token**, and every token is **tenant-resolvable at runtime**. There is no hard-coded colour, font, radius, or spacing value anywhere in application code.

This is not a stylistic preference. It is what makes §6 of the Bible ("it should feel like our school") architecturally possible. A theme is data; the design system is the schema and the defaults.

```
Design token (name + semantic role)
  → EdTechX default value
  → tenant theme override (optional)
  → resolved CSS custom property, served per tenant
```

Consequently: **a component may only reference semantic tokens.** A component that references `--ex-blue-600` is wrong; it must reference `--ex-color-accent`.

---

## 2. Token architecture

Three layers. Components touch only layer 3.

**Layer 1 — Primitives.** Raw values. `--ex-p-slate-900: #0f172a`. Never referenced by components.

**Layer 2 — Semantic roles.** Meaning-bearing. `--ex-color-surface`, `--ex-color-text-primary`, `--ex-color-accent`. Mapped from primitives. **This is the tenant override surface.**

**Layer 3 — Component tokens.** Optional, for components needing local variation. `--ex-button-primary-bg: var(--ex-color-accent)`.

---

## 3. Colour

### 3.1 Semantic roles (the complete set)

| Token | Role |
|---|---|
| `--ex-color-canvas` | Page background |
| `--ex-color-surface` | Card / panel background |
| `--ex-color-surface-raised` | Elevated surface (menu, dialog) |
| `--ex-color-surface-sunken` | Inset areas (table header, code) |
| `--ex-color-border` | Default border |
| `--ex-color-border-strong` | Emphasized border, dividers under headings |
| `--ex-color-text-primary` | Body and headings |
| `--ex-color-text-secondary` | Supporting text |
| `--ex-color-text-tertiary` | Metadata, timestamps |
| `--ex-color-text-inverse` | Text on accent fills |
| `--ex-color-accent` | Brand / primary action |
| `--ex-color-accent-hover` | Primary action hover |
| `--ex-color-accent-subtle` | Tinted background for accent contexts |
| `--ex-color-accent-text` | Accent used as text (link, active nav) |
| `--ex-color-focus` | Focus ring |
| `--ex-color-success` / `-subtle` / `-text` | Positive outcome |
| `--ex-color-warning` / `-subtle` / `-text` | Caution, needs attention |
| `--ex-color-danger` / `-subtle` / `-text` | Destructive, error, failure |
| `--ex-color-info` / `-subtle` / `-text` | Neutral information |

Five status families (accent, success, warning, danger, info), each with fill / subtle / text variants. Nothing more. A design that needs a sixth status colour has a hierarchy problem, not a palette problem.

### 3.2 Default palette (EdTechX house theme)

A restrained institutional palette. Deep navy carries authority without the corporate-blue cliché; the neutral ramp is warm-tinted so surfaces read as paper rather than screen.

| Role | Light | Dark |
|---|---|---|
| canvas | `#f8f8f6` | `#111312` |
| surface | `#ffffff` | `#1a1d1c` |
| surface-raised | `#ffffff` | `#232726` |
| surface-sunken | `#f2f2ef` | `#0c0e0d` |
| border | `#e3e3de` | `#2f3432` |
| border-strong | `#c9c9c2` | `#434946` |
| text-primary | `#16191c` | `#f2f3f1` |
| text-secondary | `#4a5057` | `#a9b0ad` |
| text-tertiary | `#6f767d` | `#7d8582` |
| accent | `#16324f` | `#7ea6cc` |
| accent-hover | `#1f4468` | `#9dbcda` |
| accent-subtle | `#eaf0f6` | `#1c2a37` |
| success | `#1c6b4a` | `#5fbf93` |
| warning | `#8a5a10` | `#e0aa55` |
| danger | `#9b2226` | `#e58a8d` |
| info | `#2b5f7e` | `#84b4cd` |

### 3.3 Colour rules

1. Colour never carries meaning alone — always paired with text, icon, or shape.
2. Every foreground/background pair used in the product must be verified ≥ 4.5:1 (text) or ≥ 3:1 (UI components and large text). **The theme engine rejects a tenant palette that fails these ratios** and offers the nearest compliant value.
3. Accent is for *one* thing per screen: the primary action.
4. Status colours are never decorative.
5. Dark mode is a token map, not a separate stylesheet.
6. Both light and dark values are required for a tenant theme; if a tenant supplies only light, dark is derived and shown for approval — never silently guessed and applied.

---

## 4. Typography

### 4.1 Families

| Token | Default | Role |
|---|---|---|
| `--ex-font-heading` | Source Serif 4 | Headings, display, document titles |
| `--ex-font-body` | Inter | UI, body, tables, forms |
| `--ex-font-mono` | JetBrains Mono | Identifiers, codes, tabular technical data |
| `--ex-font-regional` | *(tenant-set)* | RTL / regional script pairing (e.g. Amiri for Arabic) |

Maximum three families in use at once, per the Bible. A serif heading against a neutral grotesque body is the institutional register we want: the serif reads as considered and permanent; the sans reads as operational and current.

Tenants may substitute families from a curated, licence-cleared set, or upload their own licensed webfont (Premium+). Font files are served from tenant storage, subset, and preloaded.

### 4.2 Scale

A modular scale at ratio 1.2 (minor third), rounded to the 4px grid where it does not damage rhythm.

| Token | Size / Line height | Weight | Use |
|---|---|---|---|
| `display` | 40 / 46 | 400 | Marketing, empty-state hero |
| `h1` | 30 / 38 | 500 | Page title |
| `h2` | 24 / 32 | 500 | Section |
| `h3` | 20 / 28 | 500 | Subsection, card title |
| `h4` | 17 / 24 | 600 | Group label |
| `body-lg` | 17 / 26 | 400 | Reading contexts, parent portal |
| `body` | 15 / 23 | 400 | Default UI |
| `body-sm` | 13 / 20 | 400 | Secondary, table body in compact mode |
| `caption` | 12 / 16 | 500 | Metadata, labels |
| `overline` | 11 / 16 | 600, 0.06em tracking, uppercase | Section eyebrows — used sparingly |

### 4.3 Rules

- Weights used: 400, 500, 600, 700. Never more.
- Line length 60–75 characters in reading contexts; unconstrained in tabular ones.
- Numerals: tabular figures in all tables, gradebooks, and financial views. Proportional elsewhere.
- Never justify text. Never letter-space lowercase body text.
- Headings never rely on colour for hierarchy; size and weight do the work.
- Density setting (`comfortable` | `compact`) shifts body to `body-sm` and reduces spacing by one step in tables and lists only — never in reading contexts or the parent portal.

---

## 5. Spacing and layout

### 5.1 Scale

4px base. `0, 1(4), 2(8), 3(12), 4(16), 5(20), 6(24), 8(32), 10(40), 12(48), 16(64), 20(80), 24(96)`.

Values outside the scale are not permitted.

### 5.2 Rules

- **Proximity encodes relationship.** The gap between related items is always smaller than the gap to the next group. This is the single most effective and most frequently violated rule.
- Section spacing: 32 (mobile) / 48 (desktop).
- Card padding: 16 (mobile) / 24 (desktop); compact density: 12 / 16.
- Form field vertical rhythm: 20 between fields, 32 between groups.
- Page gutters: 16 (mobile) / 24 (tablet) / 32 (desktop).
- Content max width: 1280 for application shells; 72ch for reading.

### 5.3 Grid

12-column, 24px gutter at ≥1024; 8-column, 16px at 768–1023; 4-column, 16px below 768.

### 5.4 Radius and elevation

Radius: `sm 4 · md 6 · lg 10 · xl 14 · full 9999`. Default component radius `md`.

Elevation — **four levels, and no more:**

| Level | Use | Shadow |
|---|---|---|
| 0 | Flat on canvas — the default for cards | none; 1px border |
| 1 | Hover / interactive lift | `0 1px 2px rgb(0 0 0 / .06), 0 1px 3px rgb(0 0 0 / .04)` |
| 2 | Menus, popovers, dropdowns | `0 4px 8px rgb(0 0 0 / .06), 0 2px 4px rgb(0 0 0 / .04)` |
| 3 | Dialogs, sheets | `0 12px 32px rgb(0 0 0 / .12), 0 4px 8px rgb(0 0 0 / .06)` |

**Cards are level 0.** Borders define structure; shadow indicates that something floats above the page. This is the primary lever separating our surface treatment from the shadowed-card aesthetic the Bible rejects.

---

## 6. Motion

| Token | Duration | Easing | Use |
|---|---|---|---|
| `instant` | 80ms | `ease-out` | Colour, opacity on hover |
| `fast` | 150ms | `cubic-bezier(.2,0,.2,1)` | Small transitions, tooltips |
| `base` | 220ms | `cubic-bezier(.2,0,.2,1)` | Panels, dropdowns, accordions |
| `slow` | 320ms | `cubic-bezier(.2,0,0,1)` | Page-level and sheet transitions |

Rules: animate `transform` and `opacity` only. Motion must be interruptible. Nothing loops except a genuine progress indicator. Under `prefers-reduced-motion: reduce`, all movement becomes an opacity change of ≤ 100ms.

---

## 7. Component inventory

**Primitives:** Button (primary/secondary/ghost/danger · sm/md/lg · loading/disabled/icon) · Link · Icon · Badge · Tag · Avatar · Spinner · Skeleton · Divider · Tooltip · Kbd

**Forms:** Input · Textarea · Select · Combobox · Multi-select · Checkbox · Radio · Switch · DatePicker · TimePicker · DateRange · FileUpload (chunked, resumable) · SearchInput · FormField (label/hint/error wrapper) · Fieldset · FormActions

**Data:** DataTable (sort, filter, select, bulk actions, sticky header, responsive card fallback, export) · DescriptionList · StatTile · Chart wrappers (line/bar/donut/distribution) · ProgressBar · ProgressRing · Timeline · Calendar · Gradebook grid

**Layout:** AppShell · Sidebar · Topbar · PageHeader · Section · Card · Panel · Tabs · Accordion · SplitView · Drawer · Sheet

**Feedback:** Alert · Toast · Dialog · ConfirmDialog · EmptyState · ErrorState · LoadingState · Banner

**Navigation:** NavList · Breadcrumb · Pagination · Stepper · CommandPalette

**Domain:** AttendanceMarker · SubmissionCard · GradeInput · RubricGrid · StudentCard · ClassCard · FeeStatus · AnnouncementCard · ChildSwitcher

**Every component must ship:** all interaction states (default, hover, active, focus-visible, disabled, loading, error), keyboard operation, an accessible name, RTL correctness, light and dark, and a story demonstrating each state.

---

## 8. Iconography

Single icon family, 24px grid, 1.5px stroke, rounded caps. Outline by default; solid reserved for active navigation state. Icons are never the sole label for a destructive or ambiguous action. Icon-only buttons require an accessible name and a tooltip.

Tenants may select from bundled icon styles; arbitrary icon-set upload is out of scope (it destroys visual coherence for negligible benefit — see `EDTECHX_DECISIONS.md` ADR-011).

---

## 9. RTL

Right-to-left is a first-class mode.

- Use logical CSS properties throughout (`margin-inline-start`, not `margin-left`).
- Directional icons (chevrons, arrows, progress) mirror; semantic icons (clock, checkmark, logo) do not.
- Numbers and Latin identifiers stay LTR inside RTL text, using isolation marks.
- Charts mirror axis order.
- Tested as a matter of course, not as a variant.

---

## 10. Document design (print / PDF)

Report cards, transcripts, certificates, and invoices are first-class designed artefacts, not HTML printed.

- Separate print token set: serif body for reading, higher contrast, no shadows or accent fills that waste ink.
- Explicit page geometry (A4 and US Letter), margins, running headers/footers, page numbers, and controlled page breaks.
- School identity block: mark, name, address, and authorized signature area.
- Deterministic rendering: identical inputs produce byte-identical output.
- Every generated document carries an immutable verification identifier and, where the school enables it, a public verification URL.

---

## 11. Governance

- No new colour, spacing, radius, or type value may be introduced outside this document.
- A component may not reference a primitive token directly.
- A pattern used three times becomes a component.
- Contrast is verified programmatically in CI for the default theme and at save time for tenant themes.
- Changes to this document require an entry in `EDTECHX_DECISIONS.md`.
