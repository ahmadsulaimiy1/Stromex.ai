/* Publication apparatus: front matter, editorial devices, appendices, index.
   Everything here is presentation scaffolding around the Bible — it summarises,
   locates and frames the source text; it does not alter it. */
const D = require('/tmp/node_modules/docx');
const {
  Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  BorderStyle, AlignmentType, InternalHyperlink, Bookmark, TabStopType, Tab,
  VerticalAlign,
} = D;
const { C, F, PAGE } = require('./theme');
const K = require('./content');

const P = (o) => new Paragraph(o);
const T = (t, o = {}) => new TextRun({ text: t, ...o });
const NONE = K.NONE;
const spacer = (h = 160) => P({ children: [T('')], spacing: { before: 0, after: h } });

const head = (anchor, text) => P({ style: 'FrontHeading',
  children: [new Bookmark({ id: anchor, children: [T(text)] })] });
const kicker = (t) => P({ style: 'Kicker', children: [T(t)] });
const body = (t, o = {}) => P({ style: 'Body', children: [T(t, o)] });
const lead = (t) => P({ style: 'Body', children: [T(t, { size: 23, color: C.void600 })] });

// ------------------------------------------------------------------ tables
function dataTable(header, rows, widths, opts = {}) {
  const total = PAGE.content;
  const w = widths.map((x) => Math.round((x / widths.reduce((a, b) => a + b, 0)) * total));
  w[0] += total - w.reduce((a, b) => a + b, 0);
  const mk = (cells, isHead, ri) => new TableRow({
    tableHeader: !!isHead,
    cantSplit: true,
    children: cells.map((c, i) => new TableCell({
      width: { size: w[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR,
        fill: isHead ? C.orbit950 : (ri % 2 ? C.void25 : C.void0), color: 'auto' },
      margins: { top: 85, bottom: 85, left: 130, right: 130 },
      verticalAlign: isHead ? VerticalAlign.CENTER : VerticalAlign.TOP,
      borders: { top: NONE, left: NONE, right: NONE,
        bottom: isHead ? NONE : K.hair(C.void200) },
      children: [P({ style: isHead ? 'TableHead' : 'TableCell',
        children: typeof c === 'string'
          ? [T(c, isHead ? { color: C.void0, bold: true } : {})] : c })],
    })),
  });
  return new Table({
    columnWidths: w,
    width: { size: total, type: WidthType.DXA },
    borders: { top: NONE, bottom: NONE, left: NONE, right: NONE,
      insideHorizontal: NONE, insideVertical: NONE },
    rows: [mk(header, true), ...rows.map((r, i) => mk(r, false, i))],
  });
}

// ------------------------------------------------------------- front matter
const FRONT_ENTRIES = [
  ['Copyright and colophon', 'f_copyright', 'f_copyright'],
  ['Document control', 'f_control', 'f_control'],
  ['Version history', 'f_versions', 'f_versions'],
  ['How to use this document', 'f_howto', 'f_howto'],
  ['Executive summary', 'f_exec', 'f_exec'],
  ['Contents', 'f_contents', 'f_contents'],
];

const BACK_ENTRIES = [
  ['Appendix A  —  Decision register', 'b_adr', 'b_adr'],
  ['Appendix B  —  The numbers, consolidated', 'b_numbers', 'b_numbers'],
  ['Appendix C  —  Glossary', 'b_glossary', 'b_glossary'],
  ['Index', 'b_index', 'b_index'],
];

function copyrightPage() {
  return [
    spacer(600),
    head('f_copyright', 'Copyright and colophon'),
    body('SpaceTalk Editorial Bible, Version 1.0. Ratified edition.'),
    body('© SpaceTalk. All rights reserved. This document is internal reference material. It is the governing constitution of the SpaceTalk product and is intended for employees, contractors, investors and partners under confidence.'),
    body('No part of this document may be reproduced or distributed outside the organisation without written permission.'),
    spacer(220),
    kicker('AUTHORITY'),
    body('This document supersedes all prior product, brand and architecture guidance. Where any roadmap, ticket, mockup, specification or opinion conflicts with it, this document prevails until it is formally amended. Amendments require a written rationale recorded in Part 0 §0.10 and sign-off from the CEO, CPO and CDO.'),
    spacer(220),
    kicker('COLOPHON'),
    body('Set in Inter and Inter Display, designed by Rasmus Andersson, with JetBrains Mono for code, values and safety numbers. Inter is the interface typeface specified in Part 2 §2.13, so the manual is set in the same face as the product it governs.'),
    body('Composed at US Letter, 6.30 inch measure, on a 4-point vertical rhythm. Colour throughout is drawn only from the palette defined in Part 2; every contrast ratio quoted in this document was computed against the WCAG relative-luminance formula rather than estimated.'),
    body('Twenty figures were drawn as vectors specifically for this edition and rasterised at approximately 430 dots per inch for print.'),
    spacer(220),
    kicker('A NOTE ON STATUS'),
    body('Everything in this document is specification. At the time of this edition no SpaceTalk application code has been written; the numbers in Part 8 are budgets to be defended, not measurements taken. Where a claim rests on evidence we do not yet have, the text says so.'),
  ];
}

function documentControl() {
  return [
    spacer(600),
    head('f_control', 'Document control'),
    lead('Who owns this document, what governs a change to it, and how it is reviewed.'),
    spacer(200),
    dataTable(
      ['Field', 'Value'],
      [
        ['Document title', 'SpaceTalk Editorial Bible'],
        ['Version', '1.0 — ratified edition'],
        ['Status', 'Active. Governing document.'],
        ['Classification', 'Internal — confidential'],
        ['Document owner', 'Office of the CEO'],
        ['Approvers', 'Chief Executive Officer · Chief Product Officer · Chief Design Officer'],
        ['Contributing authorities', 'CTO · Principal Mobile Engineer · Principal Backend Architect · AI Systems Architect · Security Architect · Principal UX Researcher · Design Systems Lead · Brand Director · Growth Strategist'],
        ['Scope', 'All SpaceTalk product, design, brand, engineering and business decisions'],
        ['Supersedes', 'All prior product, brand and architecture guidance'],
        ['Review cadence', 'Quarterly, and on any Part 0 §0.10 amendment'],
        ['Amendment procedure', 'Written rationale appended to Part 0 §0.10, with CEO, CPO and CDO sign-off'],
        ['Source of record', 'docs/spacetalk/ — fifteen Markdown documents under version control'],
        ['Composition', '14 parts · 179 headings · 70 tables · 20 figures · 12 decision records'],
        ['Formats', 'DOCX and PDF, generated from one source; content is identical by construction'],
      ],
      [26, 74],
    ),
    spacer(240),
    K.calloutPanel(null, [
      { t: 'Both editions are generated from the same parsed source. ', b: true },
      { t: 'The Word and PDF editions are not produced independently and then compared — they are rendered from a single intermediate representation of the Markdown source, so their content cannot drift apart. The PDF is produced from the DOCX itself.' },
    ], 'orbit'),
  ];
}

function versionHistory() {
  return [
    spacer(600),
    head('f_versions', 'Version history'),
    lead('Every change to a governing document is recorded. Nothing is edited silently.'),
    spacer(200),
    dataTable(
      ['Version', 'Scope of change', 'Authority'],
      [
        [[T('1.0', { bold: true })],
          [T('Founding ratified edition. Establishes Parts 0–13: the constitution and its ten non-negotiables, the brand system, the visual design system with measured contrast, the UX bible, the AI philosophy, thirteen MVP feature specifications, the technical architecture, the design system, performance budgets, the five-phase roadmap, the scope register, business and compliance, twelve architecture decision records, and the research programme with journeys and information architecture.')],
          'CEO · CPO · CDO'],
        ['1.0', [T('Publication edition. Typeset for print and distribution: cover, front matter, twenty commissioned figures, cross-references, index. '), T('No change to the governed content.', { bold: true })], 'CDO'],
      ],
      [12, 72, 16],
    ),
    spacer(260),
    kicker('PENDING AMENDMENTS'),
    body('One question is open and is recorded in Part 12, ADR-011. SpaceTalk is treated throughout this document as a new product line, distinct from the StromeX AI knowledge-work product that shares its repository. If SpaceTalk was instead intended as a rename of StromeX, ADR-011 is wrong and must be superseded — beginning with Part 0 §0.1, because the two products have different missions, different users and different architectures.'),
    spacer(200),
    kicker('AMENDMENT RECORD'),
    body('Part 0 §0.10 carries the authoritative amendment table. It is empty at version 1.0 beyond the founding ratification, which is the correct state for a document that has not yet been contradicted by reality.'),
  ];
}

function howToUse(ir) {
  const kids = [
    spacer(600),
    head('f_howto', 'How to use this document'),
    lead('Fourteen parts, four reading paths, one rule about precedence.'),
    spacer(200),
    kicker('THE RULE ABOUT PRECEDENCE'),
    body('Part 0 is the constitution. Parts 1–13 elaborate it. If any of them appears to contradict Part 0, Part 0 wins and the contradiction is a defect to be fixed. If this document contradicts a decision made in a meeting, this document wins until it is amended.'),
    spacer(200),
    kicker('READING PATHS'),
  ];
  const paths = [
    ['If you have twenty minutes', 'Executive summary, then Part 0 (the constitution), then Part 10 §10.1 (why the scope is what it is).'],
    ['If you are joining as a designer', 'Parts 1, 2, 3 and 7 in order, then Part 13 for the journeys the interface has to serve.'],
    ['If you are joining as an engineer', 'Part 6, then Part 12 (the decision records — they explain why Part 6 looks the way it does), then Part 8 for the budgets you will be held to.'],
    ['If you are evaluating the business', 'Executive summary, Part 11, Part 9, then Part 10 for what was deliberately declined and why.'],
    ['If you are about to propose a feature', 'Part 10 §10.12 first. It asks six questions, and most proposals do not survive the fourth.'],
    ['If you are about to break a rule', 'Part 0 §0.6. Ten clauses may not be traded away for growth, revenue, a deadline, or a competitor’s launch.'],
  ];
  kids.push(dataTable(['Situation', 'Read'], paths.map((p) => [[T(p[0], { bold: true })], p[1]]), [30, 70]));
  kids.push(spacer(260));
  kids.push(kicker('CONVENTIONS'));
  const conv = [
    ['Section numbers', 'Numbering matches the source documents exactly. A reference to §6.8 means Part 6, section 6.8, everywhere in this document.'],
    ['Cross-references', 'Blue text is a live link. References of the form “Part 6 §6.8” and “ADR-003” jump to their target in both the Word and PDF editions.'],
    ['Figures', 'Numbered by part — Figure 6.2 is the second figure in Part 6. All twenty are listed in the contents.'],
    ['Callout panels', 'A tinted panel marks a passage that changes what you should do, not merely what you should know.'],
    ['Measured values', 'Every contrast ratio, every budget and every threshold is a specific number. Where a number is a target rather than a measurement, the text says so.'],
  ];
  kids.push(dataTable(['Convention', 'Meaning'], conv.map((c) => [[T(c[0], { bold: true })], c[1]]), [24, 76]));
  return kids;
}

function executiveSummary() {
  const kids = [
    spacer(600),
    head('f_exec', 'Executive summary'),
    lead('SpaceTalk is a communication space that is fast, quiet and private, in which intelligence is ambient, invited and accountable.'),
    spacer(160),
    body('Messaging is the highest-traffic software on earth, and almost all of it has drifted away from its purpose. Feeds, stores, badge counts and discovery surfaces have accumulated around the act of sending a message to someone you care about. The interfaces have grown louder while the conversations have not grown better. Separately, a real capability arrived — models that translate, summarise, transcribe and detect fraud in real time — and it has been bolted on as a chatbot in a tab.'),
    body('SpaceTalk is the correction to both drifts. It is allowed to be known for exactly three things: the fastest messaging experience in the world, the most useful intelligence ever integrated into communication, and the cleanest interface in the category. Every proposal is tested against those three, and one that strengthens none of them is rejected regardless of merit.'),
    spacer(200),
    kicker('THE FIVE DECISIONS EVERYTHING ELSE FOLLOWS FROM'),
  ];
  const five = [
    ['No advertising, ever', 'ADR-009', 'Which is why there is no feed, no ranking model and no profiling pipeline. Those absences are load-bearing, not incidental. Revenue comes from subscriptions, a business platform and a 10 % creator take rate — deliberately below the market’s 30 %, because we do not have an advertising business to fund.'],
    ['AI runs on the device by default', 'ADR-005', 'It never touches end-to-end encrypted content without a visible, revocable, per-conversation grant. Target: over 85 % of AI invocations on-device. This is the privacy promise made measurable, and it also makes the largest cost line in a modern AI product close to zero.'],
    ['Delivered messages are deleted from the server', 'ADR-004', 'The server is a relay, not an archive. A privacy decision that turns out to be what makes the economics work: the hot dataset scales with undelivered traffic, not with total history.'],
    ['No address-book upload', 'ADR-010', 'The largest deliberate growth cost in the product, taken with open eyes. Hashed phone numbers leak; we decline to ship a discovery system we cannot make private. Growth comes instead from share links, channels and language-led market entry.'],
    ['Performance budgets are release gates', 'Part 8 §8.11', 'Not dashboards, not tickets. Cold start, frame rate, memory and battery are measured in CI on physical hardware, per pull request, per device tier. A regression fails the build.'],
  ];
  kids.push(dataTable(['Decision', 'Where', 'Consequence accepted'],
    five.map((f) => [[T(f[0], { bold: true })],
      [new InternalHyperlink({ anchor: f[1].startsWith('ADR') ? 'a_' + f[1].slice(4) : 's_8_11',
        children: [T(f[1], { color: C.orbit600, bold: true })] })], f[2]]),
    [24, 13, 63]));

  kids.push(spacer(240));
  kids.push(kicker('THE PRODUCT'));
  kids.push(body('The first public version ships thirteen features and nothing else: secure messaging, voice notes, voice calls, video calls, group conversations, channels, stories, an AI assistant, file sharing, search, a profile system, notifications and multi-device support. Each is specified in Part 5 to purpose, user problem, success metrics, interface behaviour, edge cases, failure cases and future roadmap.'));
  kids.push(body('The founding brief for this project asked for every feature of seven competing products, plus payments, healthcare, education, commerce and a creator studio — roughly ninety proposals. Part 10 triages all of them: thirteen in the MVP, fifty-one scheduled across four later phases, twenty-six rejected permanently with the reasoning recorded so it does not have to be re-derived under pressure. Nothing was silently dropped, including what we declined.'));

  kids.push(spacer(200));
  kids.push(kicker('THE STACK'));
  kids.push(body('Flutter on every client surface. A modular monolith in Go — four deployables, not twelve microservices. PostgreSQL, Redis and object storage. The Signal Protocol by way of libsignal, never a cryptographic implementation of our own. A local-first SQLite store with a durable outbox, so the device is the source of truth and the network is a synchronisation mechanism. A LiveKit SFU with insertable-stream encryption for group calls, so the media server forwards frames it cannot decrypt.'));

  kids.push(spacer(200));
  kids.push(kicker('WHAT WOULD MAKE THIS FAIL'));
  kids.push(body('Part 11 §11.10 carries the full risk register. The two entries that matter most are not technical. The first is network effects: nobody switches messenger alone, and ADR-010 makes that harder on purpose. The second is dilution — thirty small, individually reasonable compromises over four years, at the end of which the product is another loud messenger with an AI tab. No competitor will beat SpaceTalk in a way that shows up on a dashboard. That is what the constitution in Part 0 exists to prevent, and it only works if people actually invoke it.'));

  kids.push(spacer(220));
  kids.push(K.calloutPanel(null, [
    { t: 'The standards do not scale with the company. ', b: true },
    { t: 'Cold start under 1,500 ms on entry-level hardware, end-to-end encryption by default, zero AI processing without an explicit grant, zero notifications from non-humans, four primary navigation destinations, and no advertising — these are identical at Phase 1 and Phase 5. The infrastructure required to hold them changes enormously. The standards themselves do not change at all. That is what makes them standards.' },
  ], 'orbit'));
  return kids;
}

// ------------------------------------------------------------------ devices
const PULL_QUOTES = {
  0: '“The hardest work in this product is deletion. Every feature we do not ship is a feature nobody has to learn.”',
  1: '“The word space in this product means room, not outer space.”',
  2: '“Human content and machine content never wear the same colour.”',
  3: '“Latency is a moral property, not a technical one.”',
  4: '“Do it on the device. If it cannot be done on the device, ask. If neither is acceptable, the feature does not ship.”',
  5: '“No metric in this document is an engagement metric.”',
  6: '“Design so that a compromised server still cannot read what we promised not to read.”',
  7: '“A designer may not invent a value, and an engineer may not hard-code one.”',
  8: '“A budget that is not measured in CI does not exist.”',
  9: '“A phase does not begin because the previous one ran out of time.”',
  10: '“Some of the requested items are not features. They are companies.”',
  11: '“If a metric could be improved by making the product more annoying, it is not one of our metrics.”',
  12: '“An ADR is never edited after acceptance — it is superseded by a new one.”',
  13: '“A persona presented as fact is one of the most reliably damaging artefacts in product development.”',
};

// Passages elevated to callout panels: matched on a distinctive opening.
const CALLOUTS = [
  [0, 'These are the clauses that may not be traded away', 'danger'],
  [0, 'When a decision is genuinely close', 'orbit'],
  [1, 'This is the single most-violated brand rule', 'danger'],
  [2, 'A measured note on colour-blind safety', 'warning'],
  [2, 'Why one accent and not two', 'orbit'],
  [2, 'The bubble rule.', 'orbit'],
  [3, 'The 100 ms rule.', 'orbit'],
  [3, 'A notification is a promise', 'warning'],
  [4, 'We promise that personal messages are end-to-end encrypted', 'danger'],
  [4, 'Rule of thumb for any future feature', 'orbit'],
  [5, 'A note on metrics.', 'orbit'],
  [6, 'Honest statement of limits.', 'warning'],
  [6, 'A rule with teeth', 'orbit'],
  [6, 'Logging discipline', 'warning'],
  [7, 'The rule that makes a design system real', 'orbit'],
  [8, 'How to read this.', 'neutral'],
  [8, 'Tier C is the design target', 'warning'],
  [9, 'The rule that makes this roadmap real', 'orbit'],
  [10, 'The honest engineering assessment', 'warning'],
  [11, 'Nothing that protects a user is behind a paywall', 'success'],
  [11, 'The foundational distinction, stated plainly', 'danger'],
  [12, 'Why it is an ADR and not just a policy', 'orbit'],
  [13, 'An honest framing, up front.', 'warning'],
  [13, 'The rule:', 'orbit'],
];

function calloutFor(chapter, text) {
  for (const [ch, needle, tone] of CALLOUTS) {
    if (ch === chapter && text.startsWith(needle)) return tone;
  }
  return null;
}

const TITLES = {
  0: 'The Constitution', 1: 'The Brand Bible', 2: 'The Visual Design System',
  3: 'The UX Bible', 4: 'The AI Philosophy', 5: 'The Feature Bible',
  6: 'The Technical Bible', 7: 'The Design System', 8: 'Performance Standards',
  9: 'The Roadmap', 10: 'Scope Governance', 11: 'Business, Growth & Compliance',
  12: 'Architecture Decision Records', 13: 'Research, Journeys & IA',
};
const chapterTitle = (ch) => TITLES[ch.num] || ch.short;

module.exports = {
  FRONT_ENTRIES, BACK_ENTRIES, PULL_QUOTES, calloutFor, chapterTitle,
  copyrightPage, documentControl, versionHistory, howToUse, executiveSummary,
  dataTable,
  backMatter: require('./backmatter'),
};
