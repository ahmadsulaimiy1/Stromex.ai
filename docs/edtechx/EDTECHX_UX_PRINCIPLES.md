# EdTechX UX Principles — Operational Rules

**Derives from:** `EDTECHX_EDITORIAL_BIBLE.md` §3
**Purpose:** the Bible states the philosophy; this document states the rules you can fail a review against.

---

## 1. Screen contract

Every screen must answer five questions without the user asking:

1. **Where am I?** — page title, breadcrumb where depth > 1, active navigation state.
2. **What is this?** — a one-line purpose when the title is not self-evident.
3. **What is most important?** — exactly one primary action or one primary datum.
4. **What can I do?** — actions visible, grouped, and ordered by frequency.
5. **What happens next?** — the outcome of the primary action is predictable before it is taken.

A screen missing any of these is incomplete.

---

## 2. The state quintet

Every data-bearing view ships **five** states. A view with only the happy path is not done.

| State | Rule |
|---|---|
| **Loading** | Skeleton matching final layout. Never a bare spinner where structure is known. Never a layout shift on resolve. |
| **Empty (no data yet)** | Explain what will appear here, why it is empty, and the single action that fills it. |
| **Empty (filtered to nothing)** | Distinct from the above. Say which filters are active and offer to clear them. |
| **Error** | Say what failed, in the user's terms; offer retry; preserve their input; never blame the user; never expose internals. |
| **Populated** | The designed state. |

Plus, where relevant: **partial** (some data loaded, some failed) and **stale** (showing cached data while revalidating, labelled).

---

## 3. Feedback timing

| Elapsed | Required response |
|---|---|
| < 100ms | Nothing needed — feels instant |
| 100ms–1s | Immediate visual acknowledgement (button pressed/disabled state) |
| 1s–3s | Inline progress indicator; UI stays responsive |
| > 3s | Determinate progress if possible; explain what is happening; allow cancel |
| > 10s | Move to background; notify on completion; never block the user |

**Optimistic UI** is permitted only where rollback is safe and visible: attendance marking, read/unread, draft saves. It is forbidden for grades, payments, publishing, and anything irreversible.

---

## 4. Destructive and irreversible actions

- Confirmation dialog naming the object and the consequence, not "Are you sure?"
- Confirm button labelled with the verb ("Delete 24 students"), never "OK".
- Type-to-confirm for actions affecting more than 10 records or any published academic record.
- Soft delete by default; hard delete only through a retention policy.
- Every destructive action writes an audit entry with actor, target, and reason where reason is required.
- Undo offered wherever technically possible, with a stated window.

---

## 5. Forms

- Labels above fields. Placeholders are never labels.
- Required fields marked; optional fields marked instead when most fields are required.
- Validate on blur; re-validate on change once a field has errored; never validate on first keystroke.
- Errors adjacent to the field, in text, with an icon — never colour alone.
- Server-side validation is authoritative; client-side is a courtesy.
- Never lose user input on error, navigation, or session refresh.
- Group related fields; use a fieldset with a legend.
- One column by default. Two columns only for genuinely paired short fields (e.g. postcode/city).
- Submit is primary; Cancel is tertiary; they are never adjacent-and-identical.
- Long forms autosave as drafts and say when they last saved.

---

## 6. Tables and lists

- Column headers describe content, not database columns.
- Sortable columns indicate sort state; the default sort is meaningful, not `id`.
- Numeric columns right-aligned and tabular-figured; text left-aligned.
- Row actions in a consistent position; destructive actions never first.
- Selection state is visible and counted ("12 selected") with a clear-selection affordance.
- Bulk actions appear in a bar that does not obscure content.
- Pagination shows total where cheap to compute; keyset pagination for large sets.
- Every list is exportable, respecting current filters, and the export says which filters applied.
- On narrow viewports, tables become cards — never horizontally scrolling tables as the primary presentation.
- Sticky header when the list is longer than a viewport.

---

## 7. Navigation

- Maximum two levels of persistent navigation. A third level is in-page.
- Active state is unambiguous.
- Back always works, including after a modal.
- Deep-linkable: every meaningful view has a URL, including filter and tab state.
- Never trap focus outside a modal; always trap it inside one.
- Navigation labels come from the tenant's terminology configuration, never from hard-coded strings.

---

## 8. Accessibility rules (WCAG 2.2 AA, enforced)

- Every interactive element reachable and operable by keyboard, in a logical order.
- Visible focus indicator with at least 3:1 contrast against adjacent colours; never `outline: none` without a replacement.
- Text contrast ≥ 4.5:1; large text and UI components ≥ 3:1.
- Colour is never the only carrier of meaning; pair with text, icon, or pattern.
- Semantic HTML first; ARIA only where semantics are insufficient.
- Every form control has a programmatically associated label.
- Images have alt text; decorative images have empty alt.
- Live regions announce async changes (toast, validation summary, save state).
- Dialogs: role, label, focus moved in, focus restored out, Escape closes.
- Respect `prefers-reduced-motion`: replace movement with fade, or nothing.
- Minimum target size 24×24 CSS px (2.2 AA), 44×44 recommended for primary touch targets.
- Page has one `h1`; heading levels are not skipped.
- Zoom to 200% without loss of content or function.

---

## 9. Responsive rules

Breakpoints: **360 (floor) · 640 · 768 · 1024 · 1280 · 1536**.

- Design mobile-first; the phone layout is the real design, not a compromise.
- No horizontal page scroll at any width ≥ 320px.
- Touch targets ≥ 44px on touch devices.
- Primary actions reachable in the lower half of the screen on mobile where the flow is one-handed (attendance, marking).
- Data tables → cards below 768.
- Modals → full-screen sheets below 640.
- Sidebars → drawer below 1024.

---

## 10. Copy rules

- Sentence case for everything except proper nouns. No Title Case Headings.
- Buttons are verbs: "Save changes", "Publish results", not "Submit" or "OK".
- Numbers: format per tenant locale; never render a raw float.
- Dates: never ambiguous. "12 Mar 2026", not "12/03/2026".
- Errors: what happened, why if known, what to do next.
- Never expose internal identifiers, stack traces, or provider names in user-facing copy.
- No exclamation marks except in genuine celebration, and no more than one.
- Every user-facing string is translatable and free of concatenation.

---

## 11. Performance budgets

Measured on a mid-range Android device over throttled Fast 3G.

| Metric | Budget |
|---|---|
| First Contentful Paint | ≤ 1.8s |
| Largest Contentful Paint | ≤ 2.5s |
| Interaction to Next Paint | ≤ 200ms |
| Cumulative Layout Shift | ≤ 0.1 |
| Initial JS (compressed), per route | ≤ 180KB |
| API p95 (read) | ≤ 300ms |
| API p95 (write) | ≤ 600ms |

A route exceeding budget is a defect, tracked in `EDTECHX_PROGRESS.md`.

---

## 12. Low-bandwidth rules

- Every list endpoint paginated; no unbounded responses.
- Sparse field selection where payloads are large.
- Images responsive, lazily loaded, modern formats, correctly sized.
- Fonts subset and preloaded; system-font fallback that does not shift layout.
- PWA shell cached; static assets immutable and fingerprinted.
- Offline-capable where the task is offline-natural: attendance marking queues locally and syncs, with visible sync state and conflict resolution.
- Uploads are resumable and chunked.
- Never re-fetch what has not changed; use ETags and conditional requests.

---

## 13. Review checklist

Before any UI is declared finished:

- [ ] Screen contract (§1) satisfied
- [ ] All five states (§2) implemented and viewable
- [ ] Feedback timing (§3) respected
- [ ] Destructive actions guarded (§4)
- [ ] Keyboard-only pass completed end to end
- [ ] Screen-reader pass on the primary flow
- [ ] 360 / 768 / 1280 verified
- [ ] Contrast verified with a tool, not by eye
- [ ] Copy reviewed against §10
- [ ] Terminology comes from tenant configuration, not literals
- [ ] Performance budget measured
- [ ] Would a prestigious school project this in a board meeting?
- [ ] Would a teacher enjoy this every day for a year?
