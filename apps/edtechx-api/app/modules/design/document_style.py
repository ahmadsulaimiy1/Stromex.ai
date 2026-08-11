"""How an issued academic document is set.

The screen and the document share one design system and are not the same
artefact, so they do not share one stylesheet. A transcript is set for paper: it
carries ceremonial ornament the interface does not, it has a masthead rather than
a page header, and it has to be readable when somebody photographs it and emails
it to an embassy.

The brief for this file, stated so it can be argued with: **the document must
look authoritative enough for a registrar, an embassy, a credential evaluator
and a scholarship board** — and it must do that without a single gradient, an
ornamental border, or a drop shadow. Authority here comes from a strong
institutional masthead, gold rules with the seal at their origin, a grade set
large in the display face, and enough air that the page looks composed rather
than filled.

**The mobile treatment is a composition, not a squeeze.** An academic history
becomes stacked records; results become course-and-grade with the grade held
large at the right; a grading key becomes a wrapped run. Nothing scrolls
sideways and nothing is set below 13px, because the person most likely to read
this on a phone is a parent in a car park.
"""

from __future__ import annotations

from app.modules.design.foundation import FOUNDATION
from app.modules.design.theme import Theme, stylesheet

__all__ = ["DOCUMENT_CSS", "document_stylesheet"]


DOCUMENT_CSS = """
/* --- the sheet ----------------------------------------------------------- */

body.ed-doc {
  background: var(--surface-sunken);
  padding: var(--space-7) var(--space-4);
}
.ed-sheet {
  position: relative;
  max-width: 52rem;
  margin: 0 auto;
  background: var(--surface-raised);
  border: 1px solid var(--border-hairline);
  padding: var(--space-9) var(--space-8) var(--space-8);
}
.ed-sheet__ground {
  position: absolute; inset: 0; opacity: var(--ornament-opacity);
  color: var(--accent-metal); pointer-events: none; overflow: hidden;
}
.ed-sheet > *:not(.ed-sheet__ground) { position: relative; }
.ed-sheet__corner { position: absolute; }
.ed-sheet__corner--bl {
  bottom: var(--space-3); inset-inline-start: var(--space-3); transform: scaleY(-1);
}
.ed-sheet__corner--br {
  bottom: var(--space-3); inset-inline-end: var(--space-3); transform: scale(-1);
}

/* --- masthead ------------------------------------------------------------ */

.ed-doc__masthead {
  display: grid; grid-template-columns: auto 1fr; gap: var(--space-5);
  align-items: center;
  padding-block-end: var(--space-5);
  border-block-end: var(--border-thick) solid var(--accent-strong);
}
.ed-doc__crest { width: 4.5rem; height: auto; }
.ed-doc__institution {
  font-family: var(--font-display);
  font-size: var(--text-2xl); font-weight: var(--weight-bold);
  letter-spacing: var(--tracking-tight); line-height: 1.05;
  color: var(--accent-strong); margin: 0;
}
.ed-doc__motto {
  font-family: var(--font-display); font-style: italic;
  color: var(--text-gold); margin: var(--space-2) 0 0; font-size: var(--text-sm);
}
.ed-doc__contact {
  margin: var(--space-2) 0 0; font-size: var(--text-3xs);
  color: var(--text-secondary); letter-spacing: var(--tracking-wide);
}
/* The gold hairline directly beneath the navy rule. Two weights of line, one
   dark one metal, is the whole letterhead. */
.ed-doc__band { height: 2px; background: var(--accent-metal); margin-block-end: var(--space-7); }

.ed-doc__title {
  text-align: center; margin: 0;
  font-family: var(--font-display);
  font-size: var(--text-xl); font-weight: var(--weight-semibold);
  letter-spacing: var(--tracking-widest); text-transform: uppercase;
}
.ed-doc__context {
  text-align: center; margin: var(--space-2) 0 var(--space-8);
  font-size: var(--text-2xs); color: var(--text-secondary);
  letter-spacing: var(--tracking-wider); text-transform: uppercase;
}

/* --- sections ------------------------------------------------------------ */

.ed-doc section { margin-block-end: var(--space-7); break-inside: avoid; }
.ed-doc__head {
  display: flex; align-items: center; gap: var(--space-3);
  margin-block-end: var(--space-4);
}
.ed-doc__head h2 {
  margin: 0; flex: none;
  font-size: var(--text-3xs); font-weight: var(--weight-semibold);
  letter-spacing: var(--tracking-widest); text-transform: uppercase;
  color: var(--text-gold);
}
.ed-doc__head .ed-rule { flex: 1; }

.ed-doc dl.fields {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr));
  gap: var(--space-4) var(--space-6); margin: 0;
}
.ed-doc dl.fields > div { min-width: 0; }
.ed-doc dl.fields dt {
  font-size: var(--text-3xs); letter-spacing: var(--tracking-wider);
  text-transform: uppercase; color: var(--text-tertiary);
  margin-block-end: 2px;
}
.ed-doc dl.fields dd {
  margin: 0; font-size: var(--text-md); font-family: var(--font-display);
  font-weight: var(--weight-semibold); line-height: 1.25;
}

.ed-doc table { width: 100%; border-collapse: collapse; }
.ed-doc thead th {
  text-align: start; padding: var(--space-2) var(--space-3);
  font-size: var(--text-3xs); font-weight: var(--weight-semibold);
  letter-spacing: var(--tracking-wider); text-transform: uppercase;
  color: var(--text-secondary);
  border-block-end: 1px solid var(--accent-metal);
}
.ed-doc tbody td {
  padding: var(--space-3); font-size: var(--text-sm);
  border-block-end: 1px solid var(--border-hairline); vertical-align: baseline;
}
.ed-doc .num { text-align: end; font-variant-numeric: tabular-nums; }
.ed-doc td[data-role="detail"] {
  display: flex; flex-wrap: wrap; gap: 2px var(--space-5);
  color: var(--text-secondary); font-size: var(--text-2xs);
}
.ed-doc td[data-role="detail"] span::before {
  content: attr(data-label) ' ';
  text-transform: uppercase; letter-spacing: var(--tracking-wider);
  color: var(--text-tertiary); font-size: 0.92em;
}
.ed-doc td[data-role="grade"], .ed-doc .ed-doc__grade {
  font-family: var(--font-display); font-size: var(--text-lg);
  font-weight: var(--weight-semibold); line-height: 1; white-space: nowrap;
}
.ed-doc__period {
  font-family: var(--font-display); font-size: var(--text-md);
  font-weight: var(--weight-semibold); margin: var(--space-5) 0 var(--space-2);
}
.ed-doc__totals {
  display: flex; flex-wrap: wrap; gap: var(--space-2) var(--space-6);
  padding-block: var(--space-3);
  font-size: var(--text-2xs); color: var(--text-secondary);
}
.ed-doc__totals b {
  font-family: var(--font-display); font-size: var(--text-md);
  color: var(--text-primary); font-weight: var(--weight-semibold);
  margin-inline-start: var(--space-2);
}

.ed-doc__narrative {
  font-family: var(--font-display); font-size: var(--text-md);
  line-height: 1.85; max-width: 44ch; margin: var(--space-9) auto;
  text-align: center;
}
.ed-doc__comment { margin: 0 0 var(--space-4); font-size: var(--text-sm); }
.ed-doc__comment b {
  display: block; font-size: var(--text-3xs);
  letter-spacing: var(--tracking-wider); text-transform: uppercase;
  color: var(--text-tertiary); font-weight: var(--weight-semibold);
  margin-block-end: 2px;
}

.ed-doc__signatures {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr));
  gap: var(--space-7); margin-block-start: var(--space-10);
}
.ed-doc__sign-line {
  border-block-start: 1px solid var(--text-primary);
  padding-block-start: var(--space-2);
  font-family: var(--font-display); font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
}
.ed-doc__sign-title {
  font-size: var(--text-3xs); letter-spacing: var(--tracking-wider);
  text-transform: uppercase; color: var(--text-tertiary);
}

/* The verification block is set as a record rather than as a footnote: it is
   what an embassy actually reads. */
.ed-doc__verify {
  margin-block-start: var(--space-8);
  padding: var(--space-4) var(--space-5);
  background: var(--surface-sunken);
  border-inline-start: var(--border-rule) solid var(--accent-metal);
  display: grid; grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr));
  gap: var(--space-4);
}
.ed-doc__verify dt {
  font-size: var(--text-3xs); letter-spacing: var(--tracking-wider);
  text-transform: uppercase; color: var(--text-tertiary);
}
.ed-doc__verify dd {
  margin: 2px 0 0; font-family: var(--font-mono); font-size: var(--text-2xs);
  word-break: break-all;
}
.ed-doc__foot {
  margin-block-start: var(--space-6); padding-block-start: var(--space-3);
  border-block-start: 1px solid var(--border-hairline);
  font-size: var(--text-3xs); color: var(--text-tertiary); text-align: center;
}
.ed-doc__void {
  position: absolute; inset: 0; display: grid; place-items: center;
  font-family: var(--font-display); font-size: 5rem; letter-spacing: 0.24em;
  color: color-mix(in srgb, var(--state-danger) 16%, transparent);
  transform: rotate(-22deg); pointer-events: none;
}

/* --- the phone ------------------------------------------------------------
   Not a squeeze. Each kind of data gets the composition it needs, and the one
   thing that never happens is a sideways scroll. */

@media (max-width: 46rem) {
  body.ed-doc { padding: 0; background: var(--surface-raised); }
  .ed-sheet { border: 0; padding: var(--space-6) var(--space-4) var(--space-8); }
  .ed-sheet__corner { display: none; }
  .ed-doc__masthead { grid-template-columns: 1fr; gap: var(--space-3); text-align: center; }
  .ed-doc__crest { margin: 0 auto; }
  .ed-doc__institution { font-size: var(--text-lg); }
  .ed-doc__title { font-size: var(--text-md); letter-spacing: var(--tracking-wider); }

  .ed-doc dl.fields { grid-template-columns: 1fr 1fr; gap: var(--space-4); }
  .ed-doc dl.fields dd { font-size: var(--text-sm); }

  /* results: course on the left, grade held large at the right, marks beneath */
  .ed-doc table[data-shape="matrix"] thead { display: none; }
  .ed-doc table[data-shape="matrix"] tbody tr {
    display: grid; grid-template-columns: minmax(0, 1fr) auto;
    padding-block: var(--space-4);
    border-block-end: 1px solid var(--border-hairline);
    column-gap: var(--space-4); align-items: center;
  }
  .ed-doc table[data-shape="matrix"] td { border: 0; padding: 0; }
  .ed-doc table[data-shape="matrix"] td[data-role="subject"] {
    grid-column: 1; grid-row: 1;
    font-family: var(--font-display); font-size: var(--text-md);
    font-weight: var(--weight-semibold); line-height: 1.2;
  }
  .ed-doc table[data-shape="matrix"] td[data-role="detail"] {
    grid-column: 1; grid-row: 2;
    display: flex; flex-wrap: wrap; gap: 2px var(--space-4);
    font-size: var(--text-2xs); color: var(--text-secondary);
    margin-block-start: var(--space-1);
  }
  .ed-doc table[data-shape="matrix"] td[data-role="detail"] span::before {
    content: attr(data-label) ' ';
    text-transform: uppercase; letter-spacing: var(--tracking-wider);
    color: var(--text-tertiary); font-size: 0.92em;
  }
  .ed-doc table[data-shape="matrix"] td[data-role="grade"] {
    grid-column: 2; grid-row: 1 / span 2;
    font-size: var(--text-2xl); text-align: end;
  }
  .ed-doc table[data-shape="matrix"] td[data-role="note"] {
    grid-column: 1 / -1; font-size: var(--text-2xs); font-style: italic;
    color: var(--text-secondary); margin-block-start: var(--space-2);
  }

  /* an academic history: a stack of records, nothing hidden */
  .ed-doc table[data-shape="ledger"] thead { display: none; }
  .ed-doc table[data-shape="ledger"] tbody tr {
    display: block; padding-block: var(--space-4);
    border-block-end: 1px solid var(--border-hairline);
  }
  .ed-doc table[data-shape="ledger"] td {
    display: flex; justify-content: space-between; gap: var(--space-4);
    border: 0; padding: 2px 0; font-size: var(--text-sm);
  }
  .ed-doc table[data-shape="ledger"] td::before {
    content: attr(data-label);
    font-size: var(--text-3xs); letter-spacing: var(--tracking-wider);
    text-transform: uppercase; color: var(--text-tertiary); flex: none;
  }
  .ed-doc table[data-shape="ledger"] td:first-child {
    display: block; font-family: var(--font-display); font-size: var(--text-md);
    font-weight: var(--weight-semibold); margin-block-end: var(--space-2);
  }
  .ed-doc table[data-shape="ledger"] td:first-child::before { content: none; }

  /* a grading key: a wrapped run of bands rather than a five-column table */
  .ed-doc table[data-shape="key"] thead { display: none; }
  .ed-doc table[data-shape="key"] tbody { display: flex; flex-wrap: wrap; gap: var(--space-2); }
  .ed-doc table[data-shape="key"] tr {
    display: flex; gap: var(--space-2); align-items: baseline;
    border: 1px solid var(--border-hairline); border-radius: var(--radius-sm);
    padding: var(--space-1) var(--space-3);
  }
  .ed-doc table[data-shape="key"] td { border: 0; padding: 0; font-size: var(--text-2xs); }
  .ed-doc table[data-shape="key"] td:first-child {
    font-family: var(--font-display); font-weight: var(--weight-semibold);
    font-size: var(--text-sm);
  }
  .ed-doc table[data-shape="key"] td:empty { display: none; }

  .ed-doc__signatures { grid-template-columns: 1fr; gap: var(--space-6); }
  .ed-doc__verify { grid-template-columns: 1fr; }
  .ed-doc__narrative { font-size: var(--text-base); text-align: start; }
}

@media print {
  body.ed-doc { background: #fff; padding: 0; }
  .ed-sheet { border: 0; max-width: none; padding: 0; }
}
"""


def document_stylesheet(theme: Theme) -> str:
    """Everything one document needs, in one block."""
    return stylesheet(theme) + FOUNDATION + DOCUMENT_CSS
