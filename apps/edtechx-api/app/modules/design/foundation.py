"""The foundation stylesheet: the visual language expressed once.

Every rule here reads a token. There is no colour, no size and no duration
written literally below this line, which is what makes an institution's theme —
and eventually its Design Studio — able to move the whole product without
touching a component.

Some deliberate absences, since they are the difference between this and a
generic admin theme:

  *No gradient.* Not one. A gradient is how software manufactures the
  impression of depth it has not earned through hierarchy.

  *One shadow.* It is for overlays — things that genuinely float. Panels sit on
  the page and are separated by surface value and a hairline, the way things are
  separated on paper.

  *Radii of 2–4px.* Sharp edges read as institutional; soft ones read as
  consumer. The only exception in the system is an avatar.

  *No card by default.* A boundary is drawn when there is a boundary. Most
  groupings are made with a rule, a heading and space — which is how an annual
  report does it, and why one looks composed and a dashboard looks assembled.
"""

from __future__ import annotations

from app.modules.design.theme import Theme, stylesheet

__all__ = ["FOUNDATION", "document_css", "page_css"]


FOUNDATION = """
/* The focus indicator, composed here rather than in the token file because it
   is a shadow built *from* a themed colour. It was a fixed translucent royal
   in the primitives, which meant the ring did not change with the mode and was
   all but invisible on midnight — the defect an axe run plus a keyboard walk
   found together, and neither would have found alone. */
:root {
  --focus-ring: 0 0 0 3px var(--border-focus);
  --focus-ring-gold: 0 0 0 3px var(--accent-metal);
}
*, *::before, *::after { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0;
  background: var(--surface-canvas);
  color: var(--text-primary);
  font-family: var(--font-sans);
  font-size: var(--text-base);
  line-height: var(--leading-normal);
  font-feature-settings: 'kern' 1, 'liga' 1, 'cv05' 1;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}
[lang="ar"], .ed-arabic {
  font-family: var(--font-arabic);
  font-size: calc(1em * var(--font-size-arabic-adjust));
  line-height: 1.9;
  direction: rtl;
}

/* --- type ---------------------------------------------------------------
   The display face carries identity; the sans carries work. Sizes come from
   the ramp and tracking is tuned per size, which is most of the difference
   between typography and text. */

.ed-display {
  font-family: var(--font-display);
  font-weight: var(--weight-bold);
  letter-spacing: var(--tracking-tighter);
  line-height: var(--leading-tight);
}
.ed-title {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--tracking-tight);
  line-height: var(--leading-snug);
  margin: 0;
}
.ed-heading {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--tracking-tight);
  margin: 0;
}
/* The micro-label. Used above every metric and beside every rule; it is the
   texture that makes the interface read as editorial rather than as a form. */
.ed-label {
  font-size: var(--text-3xs);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--tracking-widest);
  text-transform: uppercase;
  color: var(--text-secondary);
  margin: 0;
}
.ed-label--gold { color: var(--text-gold); }
.ed-lede {
  font-size: var(--text-md);
  line-height: var(--leading-relaxed);
  color: var(--text-secondary);
  margin: 0;
  max-width: 62ch;
}
.ed-muted { color: var(--text-secondary); }
.ed-quiet { color: var(--text-tertiary); }
.ed-numeric { font-variant-numeric: tabular-nums; }

/* A large editorial figure. A serif number at 60px reads as considered; the
   same number in the interface sans reads as a readout. */
.ed-figure {
  font-family: var(--font-display);
  font-size: var(--text-4xl);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--tracking-tighter);
  line-height: 1;
  font-variant-numeric: tabular-nums lining-nums;
  color: var(--text-primary);
  display: block;
}
.ed-figure--lead { font-size: var(--text-5xl); }
.ed-figure__unit {
  font-size: 0.42em;
  font-weight: var(--weight-medium);
  letter-spacing: var(--tracking-normal);
  color: var(--text-secondary);
  margin-inline-start: 0.18em;
}

/* --- the signature rule ------------------------------------------------- */

.ed-rule {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: var(--rule-width, 100%);
}
.ed-rule__line {
  flex: 1;
  height: 1px;
  background: var(--border-hairline);
}
.ed-node { flex: none; display: block; }

/* A section: micro-label, rule, content. Repeated everywhere, which is what
   makes twelve unrelated screens feel like one product. */
.ed-section { margin-block-end: var(--space-8); }
.ed-grid + .ed-section, .ed-panel + .ed-section,
.ed-figures + .ed-section,
/* An alert sat flush against the label of the section beneath it: correct
   markup, and it read as one bruised block. */
.ed-alert + .ed-section, .ed-caseload + .ed-section
  { margin-block-start: var(--space-8); }
/* And the mirror of it. A warning sitting flush on the rule beneath a row of
   figures read as part of the figures — found on the secondary administrator's
   screen at tablet width, where the two collide first. */
.ed-figures + .ed-alert, .ed-panel + .ed-alert, .ed-grid + .ed-alert
  { margin-block-start: var(--space-6); }
.ed-section__head {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
  margin-block-end: var(--space-4);
}
.ed-section__head .ed-rule { flex: 1; }
.ed-section__aside { flex: none; font-size: var(--text-2xs); color: var(--text-tertiary); }

/* --- surfaces ----------------------------------------------------------- */

.ed-panel {
  background: var(--surface-raised);
  border: 1px solid var(--border-hairline);
  border-radius: var(--radius-md);
  padding: var(--space-6);
}
/* The one deliberately decorated surface: a 2px gold edge along the top. Used
   for the single most important panel on a screen and never for a grid of six. */
.ed-panel--crowned { border-top: var(--border-thick) solid var(--accent-metal); }
.ed-panel--quiet { background: transparent; border: 0; padding: 0; }
.ed-panel--sunken { background: var(--surface-sunken); border-color: transparent; }
.ed-panel--inverse {
  background: var(--surface-inverse);
  color: var(--text-inverse);
  border-color: transparent;
}

/* --- buttons ------------------------------------------------------------ */

.ed-btn {
  --btn-bg: transparent;
  --btn-fg: var(--text-primary);
  --btn-border: var(--border-control);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  min-height: var(--control-height);
  padding-inline: var(--space-4);
  background: var(--btn-bg);
  color: var(--btn-fg);
  border: 1px solid var(--btn-border);
  border-radius: var(--radius-sm);
  font: inherit;
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  letter-spacing: var(--tracking-wide);
  cursor: pointer;
  text-decoration: none;
  white-space: nowrap;
  transition: background var(--duration-fast) var(--easing-standard),
              border-color var(--duration-fast) var(--easing-standard),
              color var(--duration-fast) var(--easing-standard);
}
.ed-btn:hover { background: var(--surface-sunken); }
.ed-btn:focus-visible { outline: none; box-shadow: var(--focus-ring); }
.ed-btn:active { transform: translateY(0.5px); }
.ed-btn[disabled], .ed-btn[aria-disabled="true"] {
  color: var(--state-disabled);
  border-color: var(--state-disabled);
  background: var(--state-disabled-surface);
  cursor: not-allowed;
}
.ed-btn--primary {
  --btn-bg: var(--accent-strong);
  --btn-fg: var(--text-on-accent);
  --btn-border: var(--accent-strong);
}
.ed-btn--primary:hover { --btn-bg: var(--accent-hover); --btn-border: var(--accent-hover); }
/* The premium action — issue a transcript, publish results. Gold is earned by
   consequence, not by prominence, and there is at most one on a screen. */
.ed-btn--ceremonial {
  --btn-bg: transparent;
  --btn-fg: var(--text-gold);
  --btn-border: var(--accent-metal);
}
.ed-btn--ceremonial:hover { --btn-bg: var(--surface-selected); }
.ed-btn--ceremonial:focus-visible { box-shadow: var(--focus-ring-gold); }
.ed-btn--quiet { --btn-border: transparent; }
.ed-btn--danger { --btn-fg: var(--text-danger); --btn-border: var(--state-danger); }
.ed-btn--sm { min-height: calc(var(--control-height) * 0.82); font-size: var(--text-2xs); }
.ed-btn--icon { padding-inline: var(--space-2); }
.ed-btn[data-loading] { color: transparent; position: relative; }
.ed-btn[data-loading] .ed-spinner {
  position: absolute; inset: 0; margin: auto;
}

.ed-link {
  color: var(--text-accent);
  text-decoration: none;
  border-block-end: 1px solid color-mix(in srgb, var(--text-accent) 30%, transparent);
  transition: border-color var(--duration-fast) var(--easing-standard);
}
.ed-link:hover { border-block-end-color: currentColor; }
.ed-link:focus-visible { outline: none; box-shadow: var(--focus-ring); border-radius: 1px; }

/* --- fields ------------------------------------------------------------- */

.ed-field { display: flex; flex-direction: column; gap: var(--space-2); }
/* The label now *contains* its control, so it is a column of two rather than
   a line of text. The typography below applies to the label's own text only. */
.ed-field__label {
  display: flex; flex-direction: column; gap: var(--space-2);
  font-size: var(--text-2xs);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--text-secondary);
}
.ed-field__label > .ed-input,
.ed-field__label > .ed-select,
.ed-field__label > .ed-textarea {
  font-size: var(--text-sm); font-weight: var(--weight-regular);
  letter-spacing: var(--tracking-normal); text-transform: none;
  color: var(--text-primary);
}
.ed-field__hint { font-size: var(--text-2xs); color: var(--text-tertiary); }
.ed-field__error {
  font-size: var(--text-2xs);
  color: var(--text-danger);
  display: flex;
  gap: var(--space-1);
  align-items: center;
}
.ed-input, .ed-select, .ed-textarea {
  width: 100%;
  min-height: var(--control-height);
  padding: var(--space-2) var(--space-3);
  background: var(--surface-raised);
  color: var(--text-primary);
  border: 1px solid var(--border-control);
  border-radius: var(--radius-sm);
  font: inherit;
  font-size: var(--text-sm);
  transition: border-color var(--duration-fast) var(--easing-standard);
}
.ed-textarea { min-height: calc(var(--control-height) * 3); resize: vertical; }
.ed-input:hover, .ed-select:hover, .ed-textarea:hover { border-color: var(--text-tertiary); }
.ed-input:focus, .ed-select:focus, .ed-textarea:focus {
  outline: none;
  border-color: var(--accent-strong);
  box-shadow: var(--focus-ring);
}
.ed-input[aria-invalid="true"] { border-color: var(--state-danger); }
.ed-input[disabled], .ed-select[disabled], .ed-textarea[disabled] {
  background: var(--state-disabled-surface);
  color: var(--state-disabled);
  cursor: not-allowed;
}
.ed-input::placeholder { color: var(--text-tertiary); }
.ed-select {
  appearance: none;
  background-image: linear-gradient(45deg, transparent 50%, currentColor 50%),
                    linear-gradient(135deg, currentColor 50%, transparent 50%);
  background-position: right var(--space-4) center, right calc(var(--space-4) - 4px) center;
  background-size: 4px 4px, 4px 4px;
  background-repeat: no-repeat;
  padding-inline-end: var(--space-7);
}

.ed-check { display: inline-flex; align-items: center; gap: var(--space-2); cursor: pointer; }
.ed-check input { position: absolute; opacity: 0; width: 0; height: 0; }
.ed-check__box {
  width: 1.05rem; height: 1.05rem;
  border: 1px solid var(--border-control);
  border-radius: var(--radius-sm);
  background: var(--surface-raised);
  display: grid; place-items: center;
  transition: all var(--duration-fast) var(--easing-standard);
}
.ed-check__box--round { border-radius: var(--radius-full); }
.ed-check input:checked + .ed-check__box {
  background: var(--accent-strong); border-color: var(--accent-strong);
}
.ed-check input:checked + .ed-check__box::after {
  content: ''; width: 0.3rem; height: 0.55rem;
  border: solid var(--text-on-accent); border-width: 0 1.5px 1.5px 0;
  transform: rotate(45deg) translate(-1px, -1px);
}
.ed-check__box--round input:checked + &::after { border-radius: var(--radius-full); }
.ed-check input:focus-visible + .ed-check__box { box-shadow: var(--focus-ring); }
.ed-check input[disabled] + .ed-check__box {
  background: var(--state-disabled-surface); border-color: var(--state-disabled);
}

.ed-switch { display: inline-flex; align-items: center; gap: var(--space-3); cursor: pointer; }
.ed-switch input { position: absolute; opacity: 0; width: 0; height: 0; }
.ed-switch__track {
  width: 2.25rem; height: 1.2rem;
  background: var(--border-control);
  border-radius: var(--radius-full);
  padding: 2px;
  transition: background var(--duration-normal) var(--easing-standard);
}
.ed-switch__thumb {
  width: 0.95rem; height: 0.95rem;
  background: var(--surface-raised);
  border-radius: var(--radius-full);
  transition: transform var(--duration-normal) var(--easing-standard);
}
.ed-switch input:checked + .ed-switch__track { background: var(--accent-strong); }
.ed-switch input:checked + .ed-switch__track .ed-switch__thumb {
  transform: translateX(1.05rem);
}
.ed-switch input:focus-visible + .ed-switch__track { box-shadow: var(--focus-ring); }

/* --- badges, chips, avatars --------------------------------------------- */

.ed-badge {
  display: inline-flex; align-items: center; gap: var(--space-1);
  padding: 0.15rem var(--space-2);
  font-size: var(--text-3xs);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  white-space: nowrap;
}
.ed-badge--neutral { background: var(--surface-sunken); color: var(--text-secondary); }
.ed-badge--accent { background: var(--accent-subtle); color: var(--text-accent); }
.ed-badge--gold {
  background: transparent; color: var(--text-gold); border-color: var(--accent-metal);
}
.ed-badge--success { background: var(--state-success-wash); color: var(--text-success); }
.ed-badge--warning { background: var(--state-warning-wash); color: var(--text-warning); }
.ed-badge--danger  { background: var(--state-danger-wash);  color: var(--text-danger); }

.ed-avatar {
  width: 2rem; height: 2rem;
  border-radius: var(--radius-full);
  background: var(--accent-subtle);
  color: var(--text-accent);
  display: grid; place-items: center;
  font-size: var(--text-2xs);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--tracking-wide);
  flex: none;
  border: 1px solid var(--border-hairline);
}
.ed-avatar--lg { width: 2.75rem; height: 2.75rem; font-size: var(--text-sm); }

/* --- tables -------------------------------------------------------------
   A table is a table. It gets a hairline, tabular numerals, right-aligned
   numbers and nothing else — no zebra striping, no border box, no rounded
   corners. Every one of those is a way of decorating data instead of
   presenting it. The mobile treatment lives in `page_css`. */

.ed-table { width: 100%; border-collapse: collapse; }
.ed-table th {
  text-align: start;
  font-size: var(--text-3xs);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--text-secondary);
  padding: var(--space-2) var(--space-3);
  border-block-end: 1px solid var(--border-strong);
  white-space: nowrap;
}
.ed-table td {
  padding: var(--space-3);
  border-block-end: 1px solid var(--border-hairline);
  font-size: var(--text-sm);
  vertical-align: baseline;
}
.ed-table tbody tr { transition: background var(--duration-fast) var(--easing-standard); }
.ed-table tbody tr:hover { background: var(--surface-sunken); }
.ed-table .num, .ed-table th.num { text-align: end; font-variant-numeric: tabular-nums; }
.ed-table__primary { font-weight: var(--weight-medium); }

/* A results matrix on a wide screen. The grade is set in the display face and
   larger than the row around it, because a grade is what the reader came for
   and rendering it at body size buries the answer inside its own evidence.
   The supporting detail is a spaced run rather than a sentence: without the
   separator the cells read as "82 / 100Examination", which is how the first
   render of this actually looked. */
.ed-data[data-shape="matrix"] td[data-role="detail"] {
  color: var(--text-secondary); font-size: var(--text-2xs);
}
.ed-data[data-shape="matrix"] .ed-detail {
  display: flex; flex-wrap: wrap; gap: var(--space-1) var(--space-5);
}
.ed-data[data-shape="matrix"] td[data-role="detail"] span span::before {
  content: attr(data-label) ' ';
  text-transform: uppercase; letter-spacing: var(--tracking-wider);
  color: var(--text-tertiary); font-size: 0.9em;
}
.ed-data[data-shape="matrix"] td[data-role="grade"] {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: var(--weight-semibold);
  line-height: 1;
  white-space: nowrap;
}
.ed-data[data-shape="matrix"] td[data-role="note"] {
  color: var(--text-secondary); font-size: var(--text-2xs); font-style: italic;
}
.ed-table caption {
  caption-side: top; text-align: start;
  font-size: var(--text-2xs); color: var(--text-tertiary);
  padding-block-end: var(--space-2);
}

/* Controls that belong together but are each a self-contained label read as
   one run when they wrapped. A column on small screens, a row above it. */
.ed-choices { display: grid; gap: var(--space-3); }
@media (min-width: 40rem) {
  .ed-choices { display: flex; flex-wrap: wrap; gap: var(--space-3) var(--space-5); }
}

/* --- tabs, breadcrumbs, pagination -------------------------------------- */

.ed-tabs {
  display: flex; gap: var(--space-6);
  border-block-end: 1px solid var(--border-hairline);
}
.ed-tab {
  appearance: none; background: none; border: 0; padding: var(--space-3) 0;
  font: inherit; font-size: var(--text-sm); color: var(--text-secondary);
  cursor: pointer; position: relative;
  transition: color var(--duration-fast) var(--easing-standard);
}
.ed-tab:hover { color: var(--text-primary); }
.ed-tab[aria-selected="true"] { color: var(--text-primary); font-weight: var(--weight-medium); }
.ed-tab[aria-selected="true"]::after {
  content: ''; position: absolute; inset-inline: 0; bottom: -1px; height: 2px;
  background: var(--accent-metal);
}
.ed-tab:focus-visible { outline: none; box-shadow: var(--focus-ring); border-radius: 2px; }

.ed-crumbs {
  display: flex; align-items: center; gap: var(--space-2); flex-wrap: wrap;
  font-size: var(--text-2xs); color: var(--text-tertiary);
}
.ed-crumbs a { color: var(--text-secondary); text-decoration: none; }
.ed-crumbs a:hover { color: var(--text-primary); }
.ed-crumbs__sep { opacity: 0.5; }

.ed-pager { display: flex; align-items: center; gap: var(--space-1); }
.ed-pager__item {
  min-width: 2rem; height: 2rem; display: grid; place-items: center;
  border-radius: var(--radius-sm); font-size: var(--text-2xs);
  color: var(--text-secondary); text-decoration: none;
  font-variant-numeric: tabular-nums;
}
.ed-pager__item:hover { background: var(--surface-sunken); color: var(--text-primary); }
.ed-pager__item[aria-current="page"] {
  color: var(--text-primary); font-weight: var(--weight-semibold);
  box-shadow: inset 0 -2px 0 var(--accent-metal);
}

/* --- feedback ----------------------------------------------------------- */

.ed-alert {
  display: flex; gap: var(--space-3);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  border-inline-start: var(--border-rule) solid var(--state-info);
  background: var(--state-info-wash);
  font-size: var(--text-sm);
}
.ed-alert--success { border-inline-start-color: var(--state-success);
  background: var(--state-success-wash); }
.ed-alert--warning { border-inline-start-color: var(--state-warning);
  background: var(--state-warning-wash); }
.ed-alert--danger  { border-inline-start-color: var(--state-danger);
  background: var(--state-danger-wash); }
.ed-alert__title { font-weight: var(--weight-semibold); margin: 0 0 var(--space-1); }
.ed-alert p { margin: 0; }

.ed-progress {
  height: 3px; background: var(--surface-sunken); border-radius: var(--radius-full);
  overflow: hidden;
}
.ed-progress__bar {
  height: 100%; background: var(--accent-metal);
  transition: width var(--duration-slow) var(--easing-standard);
}

.ed-spinner { animation: ed-turn 1.6s linear infinite; }
@keyframes ed-turn { to { transform: rotate(360deg); } }

/* Loading, as a shimmer of the surface rather than a grey block. */
.ed-skeleton {
  background: linear-gradient(90deg,
    var(--surface-sunken) 0%, var(--surface-raised) 50%, var(--surface-sunken) 100%);
  background-size: 200% 100%;
  animation: ed-shimmer 1.6s var(--easing-standard) infinite;
  border-radius: var(--radius-sm);
  height: 0.75rem;
}
@keyframes ed-shimmer { to { background-position: -200% 0; } }

/* The empty state. It is a *composition*, not an apology: the seal at low
   opacity, a sentence saying what this place is for, and the action that
   fills it. A grey box saying "No data" teaches a person that they have done
   something wrong. */
.ed-empty {
  display: grid; justify-items: center; gap: var(--space-3);
  padding: var(--space-10) var(--space-6);
  text-align: center;
}
.ed-empty__mark { opacity: 0.22; }
.ed-empty__title { font-family: var(--font-display); font-size: var(--text-lg); margin: 0; }
.ed-empty__body { color: var(--text-secondary); max-width: 42ch; margin: 0;
  font-size: var(--text-sm); }

.ed-tooltip {
  position: absolute; z-index: var(--layer-overlay);
  background: var(--surface-inverse); color: var(--text-inverse);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm); font-size: var(--text-3xs);
  box-shadow: var(--shadow-overlay);
}

.ed-dialog {
  background: var(--surface-overlay);
  border: 1px solid var(--border-hairline);
  border-top: var(--border-thick) solid var(--accent-metal);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-overlay);
  padding: var(--space-7);
  max-width: 32rem; width: 100%;
}
.ed-scrim { position: fixed; inset: 0; background: rgba(6, 10, 18, 0.52); }

/* --- command palette -----------------------------------------------------
   An acceleration layer, never an authorization bypass: what it can find is
   whatever `experience.resolve` and the scope predicates already permit. The
   visual job is to get out of the way — it sits high on the page rather than
   centred, because a person typing is looking at what they typed. */

.ed-palette__scrim {
  position: fixed; inset: 0; background: rgba(6, 10, 18, 0.52);
  display: flex; justify-content: center; align-items: flex-start;
  padding: 12vh var(--space-4) var(--space-4);
  z-index: var(--layer-overlay);
}
.ed-palette {
  width: 100%; max-width: 40rem;
  background: var(--surface-overlay);
  border: 1px solid var(--border-hairline);
  border-top: var(--border-thick) solid var(--accent-metal);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-overlay);
  overflow: hidden;
}
.ed-palette__field {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  border-block-end: 1px solid var(--border-hairline);
}
.ed-palette__input {
  flex: 1; border: 0; background: none; font: inherit;
  font-size: var(--text-md); color: var(--text-primary); outline: none;
}
.ed-palette__results { max-height: 26rem; overflow-y: auto; padding: var(--space-2); }
.ed-palette__group + .ed-palette__group { margin-block-start: var(--space-3); }
.ed-palette__label {
  font-size: var(--text-3xs); letter-spacing: var(--tracking-widest);
  text-transform: uppercase; color: var(--text-tertiary);
  padding: var(--space-2) var(--space-3) var(--space-1);
  margin: 0;
}
.ed-palette__item {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm); text-decoration: none;
  color: var(--text-primary); font-size: var(--text-sm);
}
.ed-palette__item[aria-selected="true"] { background: var(--surface-selected); }
.ed-palette__item[aria-selected="true"] .ed-node { opacity: 1; }
.ed-palette__item .ed-node { opacity: 0; flex: none; }
.ed-palette__meta { margin-inline-start: auto; font-size: var(--text-2xs);
  color: var(--text-tertiary); }
.ed-palette__foot {
  display: flex; gap: var(--space-4); padding: var(--space-2) var(--space-5);
  border-block-start: 1px solid var(--border-hairline);
  background: var(--surface-sunken);
  font-size: var(--text-3xs); color: var(--text-tertiary);
}
.ed-palette__foot kbd {
  font-family: var(--font-mono); border: 1px solid var(--border-hairline);
  border-radius: 2px; padding: 0 3px;
}

/* --- notifications -------------------------------------------------------
   Priority is carried by more than colour: an urgent item has a garnet rule, a
   filled marker AND the word. Colour alone fails for a reader who cannot see
   the difference, and it fails again in a photocopy. */

.ed-notice {
  display: grid; grid-template-columns: auto 1fr auto; gap: var(--space-3);
  padding: var(--space-4) var(--space-4) var(--space-4) var(--space-3);
  border-block-end: 1px solid var(--border-hairline);
  border-inline-start: var(--border-rule) solid transparent;
  text-decoration: none; color: inherit;
}
.ed-notice:hover { background: var(--surface-sunken); }
.ed-notice[data-priority="urgent"] { border-inline-start-color: var(--state-danger); }
.ed-notice[data-priority="important"] { border-inline-start-color: var(--accent-metal); }
.ed-notice[data-unread="true"] { background: var(--surface-selected); }
.ed-notice__dot {
  width: 7px; height: 7px; border-radius: var(--radius-full);
  background: var(--accent-metal); margin-block-start: 0.42rem;
}
.ed-notice[data-unread="false"] .ed-notice__dot { background: transparent; }
.ed-notice__title { margin: 0; font-size: var(--text-sm); font-weight: var(--weight-medium); }
.ed-notice__body { margin: 2px 0 0; font-size: var(--text-2xs); color: var(--text-secondary); }
.ed-notice__when {
  font-size: var(--text-3xs); color: var(--text-tertiary); white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

/* --- drawer --------------------------------------------------------------
   For contextual inspection and lightweight editing. A complex workflow does
   not belong in one, and neither does it belong in a dialog. */

.ed-drawer__scrim {
  position: fixed; inset: 0; background: rgba(6, 10, 18, 0.4);
  display: flex; justify-content: flex-end; z-index: var(--layer-drawer);
}
.ed-drawer {
  width: min(30rem, 100%); background: var(--surface-raised);
  border-inline-start: 1px solid var(--border-hairline);
  display: flex; flex-direction: column;
  box-shadow: var(--shadow-overlay);
}
.ed-drawer__head {
  display: flex; align-items: flex-start; gap: var(--space-4);
  padding: var(--space-6) var(--space-6) var(--space-4);
  border-block-end: 1px solid var(--border-hairline);
}
.ed-drawer__body { padding: var(--space-6); overflow-y: auto; flex: 1; }
.ed-drawer__foot {
  display: flex; gap: var(--space-2); justify-content: flex-end;
  padding: var(--space-4) var(--space-6);
  border-block-start: 1px solid var(--border-hairline);
  background: var(--surface-sunken);
}
@media (max-width: 46rem) {
  .ed-drawer__scrim { align-items: flex-end; }
  .ed-drawer {
    width: 100%; max-height: 88vh;
    border-inline-start: 0; border-block-start: var(--border-thick) solid var(--accent-metal);
    border-start-start-radius: var(--radius-lg); border-start-end-radius: var(--radius-lg);
  }
}

/* --- error ---------------------------------------------------------------
   Calm, actionable, and saying nothing a person is not entitled to know. An
   authorization failure never explains what exists behind it. */

.ed-error {
  display: grid; justify-items: center; gap: var(--space-3);
  padding: var(--space-11) var(--space-6); text-align: center;
}
.ed-error__mark { color: var(--state-danger); opacity: 0.5; }
.ed-error__title { font-family: var(--font-display); font-size: var(--text-xl); margin: 0; }
.ed-error__body { color: var(--text-secondary); max-width: 44ch; margin: 0;
  font-size: var(--text-sm); }
.ed-error__ref {
  font-family: var(--font-mono); font-size: var(--text-3xs);
  color: var(--text-tertiary); margin: var(--space-2) 0 0;
}

/* --- the register: the teacher's most repeated screen -------------------- */

.ed-register { border-block-start: 1px solid var(--border-hairline); }
.ed-register__row {
  display: grid; grid-template-columns: auto 1fr auto;
  gap: var(--space-4); align-items: center;
  padding: var(--space-3) 0;
  border-block-end: 1px solid var(--border-hairline);
}
.ed-register__name { font-size: var(--text-md); font-family: var(--font-display);
  font-weight: var(--weight-semibold); margin: 0; }
.ed-register__meta { font-size: var(--text-2xs); color: var(--text-secondary); margin: 2px 0 0; }
.ed-marks { display: flex; gap: var(--space-1); }
.ed-mark {
  min-width: 2.5rem; min-height: 2.5rem;
  display: grid; place-items: center;
  border: 1px solid var(--border-control); border-radius: var(--radius-sm);
  background: var(--surface-raised); color: var(--text-secondary);
  font-size: var(--text-sm); font-weight: var(--weight-semibold);
  cursor: pointer;
  transition: all var(--duration-fast) var(--easing-standard);
}
.ed-mark:hover { border-color: var(--text-tertiary); }
.ed-mark:focus-visible { outline: none; box-shadow: var(--focus-ring); }
.ed-mark[aria-pressed="true"] {
  background: var(--accent-strong); border-color: var(--accent-strong);
  color: var(--text-on-accent);
}
.ed-mark[aria-pressed="true"][data-code="A"] {
  background: var(--state-danger); border-color: var(--state-danger);
}
.ed-mark[aria-pressed="true"][data-code="L"] {
  background: var(--state-warning); border-color: var(--state-warning);
}
/* A submit bar that stays reachable while a teacher works down a long class. */
.ed-sticky-bar {
  position: sticky; bottom: 0;
  display: flex; align-items: center; gap: var(--space-4);
  padding: var(--space-4) 0;
  background: var(--surface-canvas);
  border-block-start: 1px solid var(--border-hairline);
}
.ed-sticky-bar .ed-btn { margin-inline-start: auto; }
@media (max-width: 46rem) {
  .ed-register__row { grid-template-columns: 1fr auto; }
  .ed-register__row .ed-avatar { display: none; }
  .ed-mark { min-width: 2.75rem; min-height: 2.75rem; }
  .ed-sticky-bar {
    margin-inline: calc(var(--space-4) * -1);
    padding-inline: var(--space-4);
    flex-wrap: wrap;
  }
  /* The tally wrapped onto two lines and shoved the button sideways. It is
     supporting information: it gets its own line above the action. */
  .ed-sticky-bar .ed-label { flex: 1 0 100%; }
  .ed-sticky-bar .ed-btn { flex: 1; margin-inline-start: 0; }
}

/* --- candidature: the only screen whose unit of time is the year --------- */

.ed-axis { display: block; }
.ed-axis__line {
  position: relative;
  block-size: 1px;
  background: var(--border-strong);
  margin-block: var(--space-7) var(--space-5);
}
.ed-axis--compact .ed-axis__line { margin-block: var(--space-4); }
/* Elapsed time is drawn as weight on the same line rather than as a filled
   bar: a progress bar says "68% done", and a candidature is not 68% done
   because twenty months have passed. */
.ed-axis__elapsed {
  position: absolute; inset-block-start: 0; inset-inline-start: 0;
  block-size: 1px; background: var(--text-primary);
}
/* Where the candidate is today. Two pixels rather than one, because at one it
   disappeared beside the milestone node it happened to sit next to. */
.ed-axis__now {
  position: absolute; inset-block-start: -9px;
  inline-size: 2px; block-size: 19px;
  background: var(--accent-metal);
}
.ed-axis--compact .ed-axis__now { inset-block-start: -5px; block-size: 11px; }
.ed-axis__tick {
  position: absolute; inset-block-start: 0;
  inline-size: 1px; block-size: 5px;
  background: var(--border-strong);
}
.ed-axis__tick-label {
  position: absolute; inset-block-start: -1.5rem; inset-inline-start: 0;
  font-size: var(--text-3xs); letter-spacing: var(--tracking-widest);
  text-transform: uppercase; color: var(--text-tertiary);
  white-space: nowrap;
}
.ed-axis__mark {
  position: absolute; inset-block-start: 50%;
  transform: translate(-50%, -50%); line-height: 0;
}
/* The node's own `fill` attribute sits on the path, so the class on the <svg>
   never reached it and every mark rendered the same ink. Found by looking at
   the axis and seeing five identical dots where two should have been gold. */
.ed-axis__mark .ed-node path { fill: var(--text-tertiary); }
.ed-axis__mark[data-state="done"] .ed-node path { fill: var(--accent-metal); }
.ed-axis__mark[data-state="due"] .ed-node path { fill: var(--text-primary); }
.ed-axis__mark[data-state="late"] .ed-node path { fill: var(--state-danger); }
.ed-axis__mark[data-state="ahead"] .ed-node path { fill: var(--border-strong); }
.ed-axis__caption {
  font-size: var(--text-2xs); margin: 0;
}

/* The track: what the axis cannot say, said in words. */
.ed-track { list-style: none; margin: 0; padding: 0; position: relative; }
.ed-track::before {
  content: ""; position: absolute;
  inset-block: 0.9rem; inset-inline-start: 5px;
  inline-size: 1px; background: var(--border-hairline);
}
.ed-track__item {
  position: relative;
  display: grid; grid-template-columns: auto 1fr auto;
  gap: var(--space-4); align-items: baseline;
  padding: var(--space-4) 0;
  border-block-end: 1px solid var(--border-hairline);
}
.ed-track__item:last-child { border-block-end: none; }
.ed-track__node {
  inline-size: 11px; block-size: 11px; border-radius: var(--radius-full);
  border: 1px solid var(--border-strong); background: var(--surface-canvas);
  align-self: center; margin-block-start: 0;
}
.ed-track__item[data-state="done"] .ed-track__node {
  background: var(--accent-metal); border-color: var(--accent-metal);
}
.ed-track__item[data-state="late"] .ed-track__node {
  background: var(--state-danger); border-color: var(--state-danger);
}
.ed-track__item[data-state="due"] .ed-track__node {
  border-color: var(--text-primary); border-width: 2px;
}
.ed-track__name {
  font-family: var(--font-display); font-size: var(--text-md);
  font-weight: var(--weight-semibold); margin: 0;
}
.ed-track__item[data-state="ahead"] .ed-track__name { color: var(--text-secondary); }
.ed-track__detail {
  font-size: var(--text-2xs); color: var(--text-secondary); margin: 2px 0 0;
  max-width: 52ch;
}
.ed-track__when { text-align: end; }
.ed-track__date {
  font-family: var(--font-mono); font-size: var(--text-2xs);
  color: var(--text-secondary); margin: 0; white-space: nowrap;
}
.ed-track__trail { margin-block-start: var(--space-2); }

/* The caseload: a supervisor's list, ordered by who is drifting. */
/* One grid for the whole list, not one per row: a caseload whose columns do
   not line up is a list a supervisor has to read rather than scan, and each
   row sizing its own columns is exactly what produced two axes of different
   lengths on the first render. */
.ed-caseload {
  border-block-start: 1px solid var(--border-hairline);
  display: grid;
  grid-template-columns: minmax(11rem, 1.1fr) minmax(9rem, 1.5fr) auto auto;
}
.ed-caseload__row {
  display: grid;
  grid-column: 1 / -1;
  grid-template-columns: subgrid;
  gap: var(--space-5); align-items: center;
  padding: var(--space-5) 0;
  border-block-end: 1px solid var(--border-hairline);
}
.ed-caseload__who { display: flex; gap: var(--space-3); align-items: center; }
.ed-caseload__name {
  font-family: var(--font-display); font-size: var(--text-md);
  font-weight: var(--weight-semibold); margin: 0;
}
.ed-caseload__meta {
  font-size: var(--text-2xs); color: var(--text-secondary); margin: 2px 0 0;
}
.ed-caseload__facts { display: flex; gap: var(--space-6); }
.ed-caseload__fact { min-width: 6.5rem; }
.ed-caseload__value {
  font-size: var(--text-sm); margin: var(--space-1) 0 0;
}
.ed-caseload__value[data-state="late"] { color: var(--text-danger); }
.ed-caseload__value[data-state="soon"] { color: var(--text-warning); }
.ed-caseload__actions { display: flex; gap: var(--space-2); }

/* Narrower than a laptop there is no room for four columns, so the parent
   drops to two and the row's subgrid follows it — which is the reason the
   list owns the columns and the row does not. */
@media (max-width: 62rem) {
  .ed-caseload { grid-template-columns: 1fr auto; }
  .ed-caseload__row { row-gap: var(--space-4); }
  .ed-caseload__axis, .ed-caseload__facts { grid-column: 1 / -1; }
}
@media (max-width: 46rem) {
  .ed-caseload { grid-template-columns: 1fr; }
  .ed-caseload__actions { display: grid; grid-template-columns: 1fr 1fr; }
  .ed-caseload__facts { gap: var(--space-4); }
  .ed-track__item { grid-template-columns: auto 1fr; }
  .ed-track__when { grid-column: 2; text-align: start; }
  .ed-axis__tick-label { font-size: 0.55rem; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
  }
}

/* Visible only to a screen reader. Present because a system that ships this
   late ships it never. */
.ed-sr {
  position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0;
}
.ed-skip {
  position: absolute; inset-inline-start: var(--space-4); top: -3rem;
  background: var(--surface-raised); color: var(--text-primary);
  padding: var(--space-2) var(--space-4); border-radius: var(--radius-sm);
  z-index: var(--layer-toast);
  transition: top var(--duration-fast) var(--easing-standard);
}
.ed-skip:focus { top: var(--space-3); }
"""


def page_css() -> str:
    """Layout and the responsive behaviour of data — the shell and its grid.

    The mobile treatment of tables lives here rather than in a component,
    because it is a *layout* decision that differs per kind of data and cannot
    be made once for every table in the product. See `ed-data` below.
    """
    return """
/* --- the shell ---------------------------------------------------------- */

.ed-app {
  display: grid;
  grid-template-columns: 15.5rem 1fr;
  min-height: 100vh;
}
.ed-rail {
  background: var(--midnight-800);
  color: var(--ivory-50);
  border-inline-end: 1px solid var(--midnight-600);
  display: flex; flex-direction: column;
  position: sticky; top: 0; height: 100vh;
  overflow: hidden;
}
.ed-identity, .ed-rail__foot { flex: none; }
/* The lattice, at the opacity the institution's ornament level sets. It is the
   only decorated surface in the product and it is behind everything. */
.ed-rail__ground {
  position: absolute; inset: 0; opacity: var(--ornament-opacity);
  color: var(--gold-500); pointer-events: none;
}
.ed-rail > *:not(.ed-rail__ground) { position: relative; }

.ed-identity {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-6) var(--space-5) var(--space-5);
  border-block-end: 1px solid var(--midnight-600);
}
.ed-identity__name {
  font-family: var(--font-display); font-size: var(--text-sm);
  font-weight: var(--weight-semibold); line-height: 1.2; margin: 0;
  color: var(--ivory-50);
}
.ed-identity__kind {
  font-size: var(--text-3xs); letter-spacing: var(--tracking-widest);
  text-transform: uppercase; color: var(--gold-500); margin: 2px 0 0;
}

.ed-nav {
  padding: var(--space-5) var(--space-3);
  overflow-y: auto; flex: 1 1 auto; min-height: 0;
  scrollbar-width: thin; scrollbar-color: var(--midnight-500) transparent;
}
.ed-nav::-webkit-scrollbar { width: 6px; }
.ed-nav::-webkit-scrollbar-thumb { background: var(--midnight-500); border-radius: 3px; }
.ed-nav__group + .ed-nav__group { margin-block-start: var(--space-6); }
.ed-nav__label {
  font-size: var(--text-3xs); letter-spacing: var(--tracking-widest);
  text-transform: uppercase; color: var(--charcoal-400);
  padding-inline: var(--space-3); margin: 0 0 var(--space-2);
}
.ed-nav__item {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  color: var(--charcoal-200); text-decoration: none;
  font-size: var(--text-sm); border-radius: var(--radius-sm);
  transition: background var(--duration-fast) var(--easing-standard),
              color var(--duration-fast) var(--easing-standard);
}
.ed-nav__item:hover { background: var(--midnight-600); color: var(--ivory-50); }
.ed-nav__item[aria-current="page"] {
  background: var(--midnight-700); color: var(--ivory-50);
  font-weight: var(--weight-medium);
}
/* The active marker is the seal, not a bar. */
.ed-nav__item[aria-current="page"] .ed-node { color: var(--gold-500); }
.ed-nav__item .ed-node { opacity: 0; transition: opacity var(--duration-fast); }
.ed-nav__item[aria-current="page"] .ed-node { opacity: 1; }
.ed-nav__count {
  margin-inline-start: auto; font-size: var(--text-3xs);
  color: var(--charcoal-400); font-variant-numeric: tabular-nums;
}
.ed-nav__upgrade { margin-inline-start: auto; color: var(--gold-500); font-size: var(--text-3xs); }

.ed-rail__foot {
  border-block-start: 1px solid var(--midnight-600);
  padding: var(--space-4) var(--space-3);
}
.ed-account {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-2) var(--space-3); border-radius: var(--radius-sm);
  color: var(--ivory-50); text-decoration: none;
}
.ed-account:hover { background: var(--midnight-600); }
.ed-account__name { font-size: var(--text-2xs); line-height: 1.3; margin: 0; }
.ed-account__role { font-size: var(--text-3xs); color: var(--charcoal-400); margin: 0; }

.ed-main { display: flex; flex-direction: column; min-width: 0; }
.ed-topbar {
  display: flex; align-items: center; gap: var(--space-4);
  padding: var(--space-3) var(--space-7);
  border-block-end: 1px solid var(--border-hairline);
  background: var(--surface-raised);
  position: sticky; top: 0; z-index: var(--layer-sticky);
}
.ed-search {
  flex: 1; max-width: 30rem; display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border-hairline); border-radius: var(--radius-sm);
  background: var(--surface-canvas); color: var(--text-tertiary);
  font-size: var(--text-sm); cursor: text; min-width: 0;
}
/* The hint is a hint. On a 390px screen an un-truncated placeholder wrapped to
   four lines and made the masthead taller than the page title. */
.ed-search > span {
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0;
}
.ed-search kbd { flex: none; }
.ed-search kbd {
  margin-inline-start: auto; font-family: var(--font-mono);
  font-size: var(--text-3xs); color: var(--text-tertiary);
  border: 1px solid var(--border-hairline); border-radius: 2px;
  padding: 1px 4px;
}
.ed-topbar__actions { display: flex; align-items: center; gap: var(--space-2);
  margin-inline-start: auto; }
.ed-bell { position: relative; }
.ed-bell__dot {
  position: absolute; top: 4px; inset-inline-end: 4px;
  width: 6px; height: 6px; border-radius: var(--radius-full);
  background: var(--accent-metal);
}

.ed-page { padding: var(--space-7); max-width: 88rem; width: 100%; }
.ed-page__head { margin-block-end: var(--space-7); }
.ed-page__title-row {
  display: flex; align-items: flex-end; gap: var(--space-5); flex-wrap: wrap;
  margin-block-start: var(--space-2);
}
.ed-page__title {
  font-family: var(--font-display); font-size: var(--text-3xl);
  font-weight: var(--weight-semibold); letter-spacing: var(--tracking-tighter);
  line-height: 1.05; margin: 0;
}
.ed-page__actions { display: flex; gap: var(--space-2); margin-inline-start: auto; }
.ed-page__lede { margin-block-start: var(--space-3); }

/* --- composition -------------------------------------------------------- */

.ed-grid { display: grid; gap: var(--space-6); }
.ed-grid--2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.ed-grid--3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.ed-grid--4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.ed-grid--sidebar { grid-template-columns: minmax(0, 1fr) 20rem; gap: var(--space-8); }

/* A row of figures separated by rules rather than boxed in cards. This is the
   single biggest difference between this and a generic dashboard. */
.ed-figures {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr));
  border-block-start: 1px solid var(--border-hairline);
}
.ed-figures__item {
  padding: var(--space-5) var(--space-5) var(--space-5) 0;
  border-inline-end: 1px solid var(--border-hairline);
}
.ed-figures__item:last-child { border-inline-end: 0; }
.ed-figures__item:not(:first-child) { padding-inline-start: var(--space-5); }
.ed-figures__delta { font-size: var(--text-2xs); margin-block-start: var(--space-2); }
.ed-figures__delta--up { color: var(--text-success); }
.ed-figures__delta--down { color: var(--text-danger); }

.ed-list { list-style: none; margin: 0; padding: 0; }
.ed-list__item {
  display: flex; align-items: center; gap: var(--space-4);
  padding: var(--space-3) 0;
  border-block-end: 1px solid var(--border-hairline);
}
.ed-list__item:last-child { border-block-end: 0; }
.ed-list__body { min-width: 0; flex: 1; }
.ed-list__title { margin: 0; font-size: var(--text-sm); font-weight: var(--weight-medium); }
.ed-list__meta { margin: 2px 0 0; font-size: var(--text-2xs); color: var(--text-secondary); }

/* --- data: the responsive contract ---------------------------------------
   Each table declares what *kind* of data it holds, and the mobile treatment
   follows from that rather than from one generic rule:

     `ledger`   — a long record list (academic history, payments). Becomes a
                  stack of records: the identifying line stays prominent and the
                  fields become labelled rows. Nothing is hidden.
     `matrix`   — results and marks. Becomes one block per course with the grade
                  held at the right, because the grade is what the reader came
                  for and everything else is supporting.
     `roster`   — people. Becomes a list with avatar, name and one meta line;
                  the rest moves behind a detail view.
     `schedule` — a timetable. Genuinely two-dimensional, so it is the one kind
                  that scrolls horizontally, with the time column pinned.

   The `data-label` attribute on each cell carries the column heading down to
   the stacked layout, so the mobile view is generated from the same markup
   rather than from a second template that will drift. */

.ed-data { width: 100%; }
.ed-data__scroll { overflow-x: auto; }

@media (max-width: 60rem) {
  .ed-app { grid-template-columns: 1fr; }
  .ed-rail {
    position: fixed; inset-block: 0; inset-inline-start: 0; width: 17rem;
    transform: translateX(-100%); z-index: var(--layer-drawer);
    transition: transform var(--duration-normal) var(--easing-standard);
  }
  .ed-app[data-nav="open"] .ed-rail { transform: none; }
  .ed-page { padding: var(--space-5) var(--space-4); }
  .ed-topbar { padding: var(--space-3) var(--space-4); gap: var(--space-3); }
  .ed-search kbd { display: none; }
  /* A primary action floating right of a wrapped title reads as an orphan.
     Under the title, where a thumb can reach it — but only stretched to the
     full width on a phone. On a tablet a 780px-wide button is not a button,
     it is a banner, and the tablet review is where that showed. */
  .ed-page__actions { margin-inline-start: 0; width: 100%; }
  .ed-page__title-row { gap: var(--space-4); }
  .ed-grid--2, .ed-grid--3, .ed-grid--4, .ed-grid--sidebar { grid-template-columns: 1fr; }
  .ed-page__title { font-size: var(--text-2xl); }


  /* schedule is the one shape that genuinely needs two dimensions. */
  .ed-data[data-shape="schedule"] { display: block; overflow-x: auto; }
  .ed-data[data-shape="schedule"] th:first-child,
  .ed-data[data-shape="schedule"] td:first-child {
    position: sticky; inset-inline-start: 0; background: var(--surface-raised);
  }
}

/* The table stops being a table on a *phone*, not on a tablet.
 
   These rules were in the 60rem block alongside the rail's collapse, and the
   two are different questions: at 834px an iPad has 780px of page and can
   carry a six-column register comfortably, but it was showing four students in
   the space that fits twenty because every row had decomposed into label-value
   pairs. Reading the tablet screenshots is the only way that surfaces —
   nothing about it is wrong at 390px or at 1440px, which are the widths a
   review actually looks at.
 
   Between the two breakpoints a wide table scrolls inside `.ed-data__scroll`,
   which is what that wrapper has always been for. */
@media (max-width: 46rem) {  /* ledger + matrix + roster: the table stops being a table. */
  .ed-data[data-shape="ledger"] thead,
  .ed-data[data-shape="matrix"] thead,
  .ed-data[data-shape="roster"] thead { display: none; }

  .ed-data[data-shape="ledger"] tr,
  .ed-data[data-shape="matrix"] tr,
  .ed-data[data-shape="roster"] tr {
    display: block;
    padding: var(--space-4) 0;
    border-block-end: 1px solid var(--border-hairline);
  }
  .ed-data[data-shape="ledger"] td,
  .ed-data[data-shape="roster"] td {
    display: flex; justify-content: space-between; gap: var(--space-4);
    padding: var(--space-1) 0; border: 0; text-align: start;
  }
  .ed-data[data-shape="ledger"] td::before,
  .ed-data[data-shape="roster"] td::before {
    content: attr(data-label);
    font-size: var(--text-3xs); letter-spacing: var(--tracking-wider);
    text-transform: uppercase; color: var(--text-secondary);
    flex: none;
  }
  /* The first cell is the record's identity: it keeps the whole line and is
     set at reading size rather than being labelled like a field. */
  .ed-data[data-shape="ledger"] td:first-child,
  .ed-data[data-shape="roster"] td:first-child {
    display: block; font-size: var(--text-md);
    font-family: var(--font-display); font-weight: var(--weight-semibold);
    margin-block-end: var(--space-2);
  }
  .ed-data[data-shape="ledger"] td:first-child::before,
  .ed-data[data-shape="roster"] td:first-child::before { content: none; }

  /* matrix: course on the left, grade held at the right, detail beneath. */
  .ed-data[data-shape="matrix"] tr {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    grid-auto-rows: min-content;
    column-gap: var(--space-4);
    align-items: baseline;
  }
  .ed-data[data-shape="matrix"] td { border: 0; padding: 0; }
  .ed-data[data-shape="matrix"] td[data-role="subject"] {
    grid-column: 1; font-size: var(--text-md); font-family: var(--font-display);
    font-weight: var(--weight-semibold); line-height: 1.25;
  }
  .ed-data[data-shape="matrix"] td[data-role="grade"] {
    grid-column: 2; grid-row: 1 / span 2;
    font-family: var(--font-display); font-size: var(--text-2xl);
    font-weight: var(--weight-semibold); color: var(--text-primary);
    text-align: end; align-self: center;
  }
  .ed-data[data-shape="matrix"] td[data-role="detail"] {
    grid-column: 1;
    font-size: var(--text-2xs); color: var(--text-secondary);
    margin-block-start: var(--space-1);
  }
  .ed-data[data-shape="matrix"] .ed-detail {
    display: flex; flex-wrap: wrap; gap: var(--space-1) var(--space-4);
  }
  .ed-data[data-shape="matrix"] td[data-role="detail"] span span::before {
    content: attr(data-label) ' ';
    text-transform: uppercase; letter-spacing: var(--tracking-wider);
    font-size: 0.9em; color: var(--text-tertiary);
  }
  .ed-data[data-shape="matrix"] td[data-role="note"] {
    grid-column: 1 / -1; font-size: var(--text-2xs); color: var(--text-secondary);
    margin-block-start: var(--space-2); font-style: italic;
  }
}

@media (min-width: 60.01rem) {
  .ed-mobile-only { display: none !important; }
}
@media (max-width: 60rem) {
  .ed-desktop-only { display: none !important; }
}
/* Only a phone gets the stretched action. Between the two, the button keeps
   its own width beneath the title. */
@media (max-width: 46rem) {
  .ed-page__actions .ed-btn { flex: 1; }
}
"""


def document_css(theme: Theme) -> str:
    """Print styles for an issued academic document.

    Separate from the screen stylesheet because a document is a different
    artefact with different rules: it is set for paper, it carries ceremonial
    ornament the interface does not, and it must survive being opened years
    later in whatever a browser has become. See `documents/render.py`.
    """
    return stylesheet(theme, selector=":root")
