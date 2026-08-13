'use strict';
/* Flagship edition builder — The StromeX Editorial Bible.
   Produces the authoritative .docx master from the markdown corpus. */

const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType,
  ShadingType, BorderStyle, HeadingLevel, AlignmentType, PageBreak, Header, Footer,
  PageNumber, NumberFormat, TableOfContents, SimpleField, LevelFormat, VerticalAlign,
  HeightRule, TabStopType, TabStopPosition, Bookmark, InternalHyperlink,
  ExternalHyperlink, AlignmentType: AT,
} = require('docx');

const T = require('./lib/tokens');
const E = require('./lib/editorial');
const MD = require('./lib/md');

// Roman numeral of a single book to compose; omitted composes the omnibus.
const BOOK = process.argv[4] || process.env.BOOK || null;
const APPARATUS = (() => {
  const f = BOOK ? `apparatus-${BOOK}.json` : 'apparatus.json';
  try { return JSON.parse(fs.readFileSync(path.join(__dirname, f), 'utf8')); }
  catch (e) { return null; }
})();

const SRC = process.argv[2] || path.resolve(__dirname, '../../../../../home/user/Stromex.ai/docs/bible');
const OUT = process.argv[3] || path.resolve(__dirname, 'StromeX-Editorial-Bible.docx');
const CW = T.page.contentWidth;

// ── helpers ───────────────────────────────────────────────────────────────
const NONE = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const noBorders = { top: NONE, bottom: NONE, left: NONE, right: NONE, insideHorizontal: NONE, insideVertical: NONE };

function panel({ fill, height, children, margins, width, borders }) {
  return new Table({
    columnWidths: [width || CW],
    width: { size: width || CW, type: WidthType.DXA },
    layout: 'fixed',
    borders: borders || noBorders,
    rows: [new TableRow({
      height: height ? { value: height, rule: HeightRule.EXACT } : undefined,
      children: [new TableCell({
        width: { size: width || CW, type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, fill, color: 'auto' },
        margins: margins || { top: 400, bottom: 400, left: 400, right: 400 },
        verticalAlign: VerticalAlign.CENTER,
        borders: borders ? undefined : { top: NONE, bottom: NONE, left: NONE, right: NONE },
        children,
      })],
    })],
  });
}

const p = (opts) => new Paragraph(opts);
const run  = (text, o = {}) => new TextRun({ text, font: T.font.body, ...o });
const uRun = (text, o = {}) => new TextRun({ text, font: T.font.ui, ...o });
const dRun = (text, o = {}) => new TextRun({ text, font: T.font.display, ...o });

function rule(color = T.color.rule, size = 4, before = 120, after = 200) {
  return p({ spacing: { before, after }, border: { bottom: { style: BorderStyle.SINGLE, size, color, space: 1 } }, children: [run('')] });
}

function pageBreak() { return p({ children: [new PageBreak()] }); }

function label(text, color = T.color.graphite) {
  return p({
    spacing: { before: 0, after: 220 },
    children: [uRun(text.toUpperCase(), { size: T.size.micro, bold: true, characterSpacing: 60, color })],
  });
}

function body(text, o = {}) {
  return p({ style: 'BodyText', ...o, children: MD.inline(text) });
}

// ── styles ────────────────────────────────────────────────────────────────
function styles() {
  const heading = (id, name, size, color, before, after, opts = {}) => ({
    id, name, basedOn: 'Normal', next: 'BodyText', quickFormat: true,
    run: { font: opts.font || T.font.display, size, bold: opts.bold !== false, color, ...opts.run },
    paragraph: {
      spacing: { before, after, line: opts.line || 260 },
      outlineLevel: opts.outlineLevel,
      keepNext: true,
      ...opts.paragraph,
    },
  });

  return {
    default: {
      document: { run: { font: T.font.body, size: T.size.body, color: T.color.ink }, paragraph: { spacing: { line: 288 } } },
      heading1: { run: { font: T.font.display } },
    },
    paragraphStyles: [
      { id: 'Normal', name: 'Normal', run: { font: T.font.body, size: T.size.body, color: T.color.ink }, paragraph: { spacing: { line: 288, after: 0 } } },
      { id: 'BodyText', name: 'Body Text', basedOn: 'Normal', next: 'BodyText',
        run: { font: T.font.body, size: T.size.body, color: T.color.ink },
        paragraph: { spacing: { before: 0, after: 170, line: 290 }, alignment: AlignmentType.JUSTIFIED } },

      heading('Heading1', 'Heading 1', T.size.volumeTitle, T.color.paper, 0, 200, { outlineLevel: 0, line: 240 }),
      heading('Heading2', 'Heading 2', T.size.h1, T.color.depth, 0, 260, { outlineLevel: 1, line: 250 }),
      heading('Heading3', 'Heading 3', T.size.h2, T.color.depth, 360, 150, { outlineLevel: 2 }),
      heading('Heading4', 'Heading 4', T.size.h3, T.color.ink, 300, 110, { outlineLevel: 3, font: T.font.ui }),
      heading('Heading5', 'Heading 5', T.size.h4, T.color.ink2, 240, 90, { outlineLevel: 4, font: T.font.ui }),

      { id: 'Caption', name: 'Caption', basedOn: 'Normal', next: 'BodyText',
        run: { font: T.font.ui, size: T.size.caption, color: T.color.graphite, italics: false },
        paragraph: { spacing: { before: 90, after: 260 }, alignment: AlignmentType.LEFT } },

      { id: 'PullQuote', name: 'Pull Quote', basedOn: 'Normal', next: 'BodyText',
        run: { font: T.font.display, size: 22, color: T.color.depth },
        paragraph: {
          spacing: { before: 220, after: 240, line: 300 },
          indent: { left: 340, right: 200 },
          border: { left: { style: BorderStyle.SINGLE, size: 16, color: T.color.accent, space: 14 } },
        } },

      { id: 'EditorialNote', name: 'Editorial Note', basedOn: 'Normal', next: 'BodyText',
        run: { font: T.font.body, size: T.size.small, color: T.color.graphite, italics: true },
        paragraph: { spacing: { before: 60, after: 200, line: 280 } } },

      { id: 'CodeBlock', name: 'Code Block', basedOn: 'Normal', next: 'BodyText',
        run: { font: T.font.mono, size: 15, color: T.color.ink2 },
        paragraph: { spacing: { before: 0, after: 0, line: 230 }, indent: { left: 260 }, alignment: AlignmentType.LEFT } },

      { id: 'ExecSummary', name: 'Executive Summary', basedOn: 'Normal', next: 'BodyText',
        run: { font: T.font.body, size: 20, color: T.color.ink2 },
        paragraph: { spacing: { before: 0, after: 200, line: 300 }, alignment: AlignmentType.JUSTIFIED } },

      { id: 'FrontProse', name: 'Front Prose', basedOn: 'Normal', next: 'FrontProse',
        run: { font: T.font.body, size: 20, color: T.color.ink },
        paragraph: { spacing: { before: 0, after: 200, line: 310 }, alignment: AlignmentType.JUSTIFIED } },
    ],
    characterStyles: [
      { id: 'Hyperlink', name: 'Hyperlink', basedOn: 'DefaultParagraphFont', run: { color: T.color.depth, underline: {} } },
    ],
  };
}

const numbering = {
  config: [
    { reference: 'bible-ul', levels: [0, 1, 2].map(l => ({
        level: l, format: LevelFormat.BULLET, text: ['—', '·', '–'][l], alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 340 + l * 300, hanging: 220 } }, run: { color: T.color.accent, font: T.font.body } },
      })) },
    { reference: 'bible-ol', levels: [0, 1, 2].map(l => ({
        level: l, format: [LevelFormat.DECIMAL, LevelFormat.LOWER_LETTER, LevelFormat.LOWER_ROMAN][l],
        text: ['%1.', '%2.', '%3.'][l], alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 380 + l * 300, hanging: 260 } }, run: { color: T.color.depth, bold: true, font: T.font.body } },
      })) },
  ],
};

// ── source preparation ────────────────────────────────────────────────────
function prepare(md) {
  let s = md;
  s = s.replace(/^#\s+VOLUME[^\n]*\n/m, '');                       // volume h1 (divider carries it)
  s = s.replace(/^###\s+[^\n]*\n/m, '');                            // subtitle
  s = s.replace(/^\*Edition II[^\n]*\*\s*$/m, '');                  // edition note
  s = s.replace(/\n##\s+Contents[\s\S]*?(?=\n---\s*\n)/, '\n');     // per-volume TOC
  s = s.replace(/\n\*Volume [IVX]+ ends\.[\s\S]*$/, '\n');          // trailing nav
  s = s.replace(/\n\*Review due:[^\n]*\*\s*/g, '\n');
  s = s.replace(/^---\s*$\n+(?=#)/gm, '');                          // rules immediately before headings
  return s.trim();
}

const INDEX_TERMS = E.GLOSSARY.map(g => g[0]).concat([
  'Foundation', 'Race', 'Global Scale', 'SpaceTalk', 'StromeX Cloud', 'StromeX Pay',
  'StromeX Identity', 'StromeX Labs', 'Reference Implementation', 'Pricing Council',
  'free tier', 'verification', 'credential', 'federation', 'net revenue retention',
]);

// ── front matter ──────────────────────────────────────────────────────────
function bookCover(v) {
  return [panel({
    fill: T.color.obsidian,
    width: T.page.width,
    height: T.page.height,
    margins: { top: 1900, bottom: 1500, left: 1580, right: 1400 },
    children: [
      p({ spacing: { after: 0 }, children: [uRun('STROMEX', { size: 26, bold: true, characterSpacing: 240, color: 'FFFFFF' })] }),
      p({ spacing: { before: 120, after: 240 }, children: [uRun('EXECUTIVE KNOWLEDGE SYSTEM', { size: 14, bold: true, characterSpacing: 200, color: T.color.accent })] }),
      p({ spacing: { after: 60 }, children: [uRun('BOOK ' + v.roman, { size: 15, bold: true, characterSpacing: 220, color: '7C8794' })] }),
      p({ spacing: { after: 700, line: T.lead(150, 0.9) }, children: [dRun(v.roman, { size: 150, bold: true, color: 'FFFFFF' })] }),
      p({ spacing: { after: 200, line: T.lead(62, 1.06) }, children: [dRun(v.title, { size: 62, bold: true, color: T.color.accent })] }),
      p({ spacing: { after: 140 }, border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: T.color.accent, space: 12 } }, children: [run('')] }),
      p({ spacing: { after: 90 }, children: [run(v.sub, { size: 23, color: 'D9DEE5' })] }),
      p({ spacing: { after: 1200 }, children: [run('The StromeX Editorial Bible  ·  ' + E.EDITION, { size: 19, color: '7C8794' })] }),
      p({ spacing: { after: 40 }, children: [uRun('AUTHORITY — ' + v.authority.toUpperCase(), { size: 13, bold: true, characterSpacing: 40, color: '9AA5B1' })] }),
      p({ children: [uRun(E.DATE.toUpperCase() + '  ·  VERSION ' + E.VERSION, { size: 13, characterSpacing: 40, color: '7C8794' })] }),
    ],
  })];
}

function bookTitlePage(v) {
  return [
    p({ spacing: { before: 1400, after: 0 }, children: [uRun('STROMEX GROUP  ·  EXECUTIVE KNOWLEDGE SYSTEM', { size: 15, bold: true, characterSpacing: 160, color: T.color.accent })] }),
    rule(T.color.rule, 4, 200, 640),
    p({ spacing: { after: 0 }, children: [uRun('BOOK ' + v.roman, { size: 16, bold: true, characterSpacing: 200, color: T.color.graphite })] }),
    p({ spacing: { before: 160, after: 220, line: T.lead(56, 1.06) }, children: [dRun(v.title, { size: 56, bold: true, color: T.color.ink })] }),
    p({ spacing: { after: 700 }, children: [run(v.sub, { size: 22, color: T.color.ink2 })] }),
    p({ spacing: { after: 140 }, children: [uRun('EXECUTIVE SUMMARY', { size: 13, bold: true, characterSpacing: 110, color: T.color.accent })] }),
    p({ style: 'ExecSummary', children: MD.inline(v.summary) }),
    rule(T.color.rule, 4, 500, 200),
    p({ children: [run('One book of ten. The corpus index and the other nine are at docs/library/.', { size: 16, color: T.color.graphite })] }),
    pageBreak(),
  ];
}

function bookDocumentControl(v) {
  return [
    label('Document control'),
    p({ spacing: { after: 260 }, children: [dRun('Document Control', { size: 40, bold: true, color: T.color.depth })] }),
    twoColRows([
      ['Book', `Book ${v.roman} — ${v.title}`],
      ['Series', 'The StromeX Editorial Bible — Executive Knowledge System'],
      ['Edition', E.EDITION],
      ['Version', E.VERSION],
      ['Status', v.status || 'Ratified'],
      ['Classification', 'Confidential — internal and authorised parties'],
      ['Authority tier', v.authority],
      ['Owner', v.owner || 'Office of the Founder, StromeX Group Holdings'],
      ['Review cycle', v.review || 'Annually'],
      ['Amendment protocol', 'Book I, Chapter 9. Four tiers: Entrenched, Constitutional, Strategic, Operational.'],
      ['Precedence', 'Book I governs. Where this book conflicts with Book I, Book I wins until formally amended.'],
      ['Master source', 'The DOCX edition of this book. The PDF is generated from it and is content-identical.'],
      ['Source of record', `docs/bible/${v.file}, under version control.`],
      ['Issued', E.DATE],
    ]),
    pageBreak(),
  ];
}

function cover() {
  const inner = [
    p({ spacing: { after: 0 }, children: [uRun('STROMEX', { size: 30, bold: true, characterSpacing: 260, color: 'FFFFFF' })] }),
    p({ spacing: { before: 130, after: 1000 }, children: [uRun('GROUP', { size: 17, bold: true, characterSpacing: 300, color: T.color.accent })] }),

    p({ spacing: { after: 0, line: T.lead(66, 1.02) }, children: [dRun('The', { size: 66, color: 'FFFFFF', bold: true })] }),
    p({ spacing: { after: 0, line: T.lead(T.size.coverTitle, 1.02) }, children: [dRun('StromeX', { size: T.size.coverTitle, color: 'FFFFFF', bold: true })] }),
    p({ spacing: { after: 520, line: T.lead(T.size.coverTitle, 1.02) }, children: [dRun('Editorial Bible', { size: T.size.coverTitle, color: T.color.accent, bold: true })] }),

    p({ spacing: { after: 140 }, border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: T.color.accent, space: 12 } }, children: [run('')] }),

    p({ spacing: { after: 90 }, children: [run('The Constitution, Operating Manual and Strategic Corpus', { size: T.size.coverSub, color: 'D9DEE5' })] }),
    p({ spacing: { after: 1400 }, children: [run('Ten Volumes  ·  ' + E.EDITION, { size: T.size.coverSub, color: '7C8794' })] }),

    p({ spacing: { after: 40 }, children: [uRun('RATIFIED AS THE GOVERNING CORPUS OF THE STROMEX GROUP', { size: 13, bold: true, characterSpacing: 40, color: '9AA5B1' })] }),
    p({ children: [uRun(E.DATE.toUpperCase() + '  ·  VERSION ' + E.VERSION, { size: 13, characterSpacing: 40, color: '7C8794' })] }),
  ];
  return [panel({
    fill: T.color.obsidian,
    width: T.page.width,
    height: T.page.height,
    margins: { top: 1900, bottom: 1500, left: 1580, right: 1400 },
    children: inner,
  })];
}

function halfTitle() {
  return [
    p({ spacing: { before: 3600, after: 0 }, alignment: AlignmentType.CENTER,
        children: [dRun('The StromeX Editorial Bible', { size: 44, bold: true, color: T.color.depth })] }),
    p({ spacing: { before: 200 }, alignment: AlignmentType.CENTER,
        children: [run(E.EDITION.toUpperCase(), { size: 15, characterSpacing: 200, color: T.color.graphite })] }),
    pageBreak(),
  ];
}

function titlePage() {
  return [
    p({ spacing: { before: 1400, after: 0 }, children: [run('STROMEX GROUP', { size: 16, bold: true, characterSpacing: 240, color: T.color.accent })] }),
    rule(T.color.rule, 4, 200, 700),
    p({ spacing: { after: 0, line: T.lead(58, 1.04) }, children: [dRun('The StromeX', { size: 58, bold: true, color: T.color.ink })] }),
    p({ spacing: { after: 300, line: T.lead(58, 1.04) }, children: [dRun('Editorial Bible', { size: 58, bold: true, color: T.color.depth })] }),
    p({ spacing: { after: 120 }, children: [run('The Constitution, Operating Manual and Strategic Corpus of StromeX', { size: 23, color: T.color.ink2 })] }),
    p({ spacing: { after: 900 }, children: [run(E.EDITION + '  ·  Supersedes Edition I', { size: 19, color: T.color.graphite })] }),

    ...[
      ['Volume I', 'The Constitution'],
      ['Volume II', 'Market Strategy & Competitive Positioning'],
      ['Volume III', 'The Catalogue'],
      ['Volume IV', 'Engineering, AI Architecture, Cloud & Security'],
      ['Volume V', 'Go-to-Market'],
      ['Volume VI', 'The Creative Division'],
      ['Volume VII', 'Industry Ecosystems'],
      ['Volume VIII', 'Expansion, Finance & the Roadmap'],
      ['Volume IX', 'The Institution'],
      ['Volume X', 'SpaceTalk'],
    ].map(([v, t]) => p({
      spacing: { after: 60 },
      tabStops: [{ type: TabStopType.LEFT, position: 1500 }],
      children: [run(v, { size: 16, bold: true, color: T.color.accent }), run('\t' + t, { size: 17, color: T.color.ink2 })],
    })),

    rule(T.color.rule, 4, 700, 200),
    p({ children: [run('Lagos  ·  London  ·  New York', { size: 16, characterSpacing: 60, color: T.color.graphite })] }),
    pageBreak(),
  ];
}

function copyrightPage() {
  const lines = [
    `The StromeX Editorial Bible, ${E.EDITION}.`,
    `Version ${E.VERSION}. Published ${E.DATE}.`,
    '',
    '© 2026–2027 StromeX Group Holdings. All rights reserved.',
    '',
    'This corpus is the confidential and proprietary property of StromeX Group Holdings. It is issued to directors, officers, employees, certified partners and such external parties as the Executive may authorise in writing. It may not be reproduced, redistributed, published or disclosed, in whole or in part, without prior written authorisation.',
    '',
    'The StromeX name, the StromeX mark and the sub-brand names recorded in Volume I, Chapter 10 are trademarks of StromeX Group Holdings. Third-party names appearing in this corpus are the trademarks of their respective owners and are used for identification and comparison only.',
    '',
    'This document contains forward-looking statements, including the financial scenarios in Volume VIII. Those scenarios are estimates constructed from stated assumptions. They are not forecasts of record, projections of guaranteed outcome, or a representation that any particular result will be achieved. Actual outcomes will differ, and may differ materially. Nothing in this corpus constitutes an offer of securities, investment advice, or a solicitation of any kind.',
    '',
    'External data cited in this corpus is attributed at the point of use and listed in the Bibliography. Figures describing the group’s own delivered work are drawn from the sources recorded in Internal Sources.',
    '',
    'Composed for A4. The text is set in a serif book face with a companion sans for tabular and navigational matter, following the typographic roles defined in Volume I, Chapter 10; the StromeX brand faces Archivo and Fraunces are shipped alongside this edition and are selected by the build when they are present in the rendering environment. The press-quality PDF edition is generated from this master and the two are content-identical.',
  ];
  return [
    p({ spacing: { before: 2600, after: 300 } , children: [run('')] }),
    ...lines.map(l => l === ''
      ? p({ spacing: { after: 130 }, children: [run('')] })
      : p({ spacing: { after: 0, line: 270 }, alignment: AlignmentType.LEFT, children: [run(l, { size: 16, color: T.color.ink2 })] })),
    pageBreak(),
  ];
}

function twoColRows(pairs, keyWidth = 2600) {
  return new Table({
    columnWidths: [keyWidth, CW - keyWidth],
    width: { size: CW, type: WidthType.DXA },
    layout: 'fixed',
    borders: noBorders,
    rows: pairs.map(([k, v], i) => new TableRow({
      children: [
        new TableCell({
          width: { size: keyWidth, type: WidthType.DXA },
          margins: { top: 90, bottom: 90, left: 0, right: 200 },
          borders: { top: NONE, bottom: { style: BorderStyle.SINGLE, size: 2, color: T.color.ruleSoft }, left: NONE, right: NONE },
          children: [p({ spacing: { after: 0 }, children: [uRun(k.toUpperCase(), { size: 14, bold: true, characterSpacing: 40, color: T.color.graphite })] })],
        }),
        new TableCell({
          width: { size: CW - keyWidth, type: WidthType.DXA },
          margins: { top: 90, bottom: 90, left: 0, right: 0 },
          borders: { top: NONE, bottom: { style: BorderStyle.SINGLE, size: 2, color: T.color.ruleSoft }, left: NONE, right: NONE },
          children: [p({ spacing: { after: 0, line: 270 }, children: MD.inline(v, { size: 17 }) })],
        }),
      ],
    })),
  });
}

function documentControl() {
  return [
    label('Document control'),
    p({ spacing: { after: 260 }, children: [dRun('Document Control', { size: 40, bold: true, color: T.color.depth })] }),
    twoColRows([
      ['Title', 'The StromeX Editorial Bible'],
      ['Edition', E.EDITION],
      ['Version', E.VERSION],
      ['Status', 'Ratified — governing corpus'],
      ['Classification', 'Confidential — internal and authorised parties'],
      ['Owner', 'Office of the Founder, StromeX Group Holdings'],
      ['Custodian', 'Executive; Pricing Council for Volume III'],
      ['Supersedes', 'The StromeX Editorial Bible, Edition I (Version 1.0)'],
      ['Authority', 'Supreme. Where any roadmap, contract, pricing sheet, presentation or line of code conflicts with this corpus, the corpus governs until formally amended.'],
      ['Amendment protocol', 'Volume I, Chapter 9. Four tiers: Entrenched (board supermajority, published rationale, 30 days’ notice), Constitutional, Strategic, Operational.'],
      ['Review cycle', 'Volume III quarterly (Pricing Council). Volume II risk register quarterly. All other volumes annually.'],
      ['Master source', 'This DOCX. The press-quality PDF edition is generated from it and is content-identical.'],
      ['Corpus location', 'docs/bible/ in the StromeX repository, under version control.'],
      ['Issued', E.DATE],
    ]),
    pageBreak(),
  ];
}

function revisionHistory() {
  const rows = [
    ['Version', 'Date', 'Author / Authority', 'Summary of change'],
    ['1.0', 'August 2026', 'Office of the Founder', 'Edition I ratified. Established the vision, product, user and intelligence philosophy, editorial standards, design philosophy, AI architecture philosophy, and the trust, safety and scalability constitutions for StromeX as an AI operating system for knowledge work.'],
    ['2.0', E.DATE, 'Office of the Founder', 'Edition II ratified; supersedes Edition I in full. Reframes StromeX from a product to a group. Adds the doctrine of ecosystems, the Free and Commercial Constitutions, the Ethics Constitution, the amendment protocol, the brand system and logo decision (Volume I); market positioning, the six competitor classes and the moat assessment (II); the seventeen-division catalogue with published module-level pricing (III); the Security Bible and credential architecture (IV); the Customer Success Playbook and partner economics (V); the craft standard and print coordination (VI); the industry ecosystems by wave (VII); the three-phase roadmap, phase gates and three financial scenarios (VIII); the innovation laboratory, research institute, talent system and 100-Year Plan (IX); and SpaceTalk (X).'],
    ['2.0-p', E.DATE, 'Office of the Founder', 'Flagship publication edition. Adds front matter, executive summaries, apparatus, appendices, glossary, bibliography and index. Content-identical to the corpus of record.'],
  ];
  return [
    label('Revision history'),
    p({ spacing: { after: 260 }, children: [dRun('Revision History', { size: 40, bold: true, color: T.color.depth })] }),
    MD.buildTable(rows, [AlignmentType.LEFT, AlignmentType.LEFT, AlignmentType.LEFT, AlignmentType.LEFT],
      { columnWidths: [900, 1350, 1900, CW - 900 - 1350 - 1900] }),
    p({ style: 'EditorialNote', spacing: { before: 200 }, children: MD.inline('Superseded text is struck through and dated for one edition, then archived — never silently deleted. The record of what the group used to believe is part of the corpus (Volume I §9.2).') }),
    pageBreak(),
  ];
}

function proseSection(labelText, title, text, opts = {}) {
  const paras = text.split(/\n{2,}/).map(s => s.trim()).filter(Boolean);
  const out = [
    label(labelText),
    p({ spacing: { after: opts.lede ? 200 : 320 }, children: [dRun(title, { size: 40, bold: true, color: T.color.depth })] }),
  ];
  paras.forEach((t, i) => {
    out.push(p({
      style: 'FrontProse',
      spacing: { after: 200, line: 310 },
      children: MD.inline(t, i === 0 && opts.leadIn ? { size: 22, color: T.color.ink } : {}),
    }));
  });
  if (opts.signature) {
    out.push(rule(T.color.rule, 4, 300, 200));
    out.push(p({ spacing: { after: 20 }, children: [dRun(opts.signature[0], { size: 24, bold: true, color: T.color.ink })] }));
    out.push(p({ children: [run(opts.signature[1], { size: 16, color: T.color.graphite })] }));
  }
  out.push(pageBreak());
  return out;
}

function visionMission() {
  const block = (kind, text, fill, ink, accent) => panel({
    fill,
    margins: { top: 520, bottom: 520, left: 480, right: 480 },
    children: [
      p({ spacing: { after: 220 }, children: [uRun(kind.toUpperCase(), { size: 15, bold: true, characterSpacing: 110, color: accent })] }),
      p({ spacing: { after: 0, line: T.lead(30, 1.34) }, children: [dRun(text, { size: 30, bold: true, color: ink })] }),
    ],
  });
  return [
    label('Vision and mission'),
    p({ spacing: { after: 340 }, children: [dRun('Vision & Mission', { size: 40, bold: true, color: T.color.depth })] }),
    block('The Vision — Volume IX §9.1', E.VISION, T.color.obsidian, 'FFFFFF', T.color.accent),
    p({ spacing: { after: 260 }, children: [run('')] }),
    block('The Mission — Volume I §1.2', E.MISSION, T.color.sunk, T.color.depth, T.color.accent),
    p({ style: 'EditorialNote', spacing: { before: 340 }, children: MD.inline('Three clauses of the mission are load-bearing. *Every sector we can serve competently* — breadth is the strategy, competence is the gate. *Transform* — the deliverable is the institution working better, measured in the institution’s own units. *A price the institution can plan around* — pricing opacity is the primary mechanism by which institutions in emerging markets are overcharged, and removing it is both an ethical position and the group’s sharpest competitive weapon.') }),
    pageBreak(),
  ];
}

function leaderLine(left, page, opts = {}) {
  return p({
    spacing: { before: 0, after: opts.tight ? 20 : 40, line: 260 },
    indent: { left: opts.indent || 0, right: 200, hanging: 0 },
    tabStops: [{ type: TabStopType.RIGHT, position: CW - 60, leader: 'dot' }],
    children: [
      ...MD.inline(left, { size: 17 }),
      uRun('\t' + page, { size: 16, color: T.color.depth }),
    ],
  });
}

function listOf(kind, entries) {
  if (!entries || !entries.length) {
    return [p({ style: 'EditorialNote', children: MD.inline('This list is generated by the build. Rebuild the publication to populate it.') })];
  }
  const out = [];
  let lastVol = null;
  entries.forEach((e) => {
    if (e.vol && e.vol !== lastVol) {
      lastVol = e.vol;
      out.push(p({
        spacing: { before: out.length ? 220 : 0, after: 90 },
        children: [uRun(e.vol.toUpperCase(), { size: 13, bold: true, characterSpacing: 90, color: T.color.accent })],
      }));
    }
    out.push(leaderLine(`**${kind} ${e.n}**  ${e.cap}`, String(e.page), { tight: true }));
  });
  return out;
}

function indexPages(entries) {
  if (!entries || !entries.length) {
    return [p({ style: 'EditorialNote', children: MD.inline('This index is generated by the build. Rebuild the publication to populate it.') })];
  }
  const out = [];
  let letter = null;
  entries.forEach((e) => {
    const L = e.term.charAt(0).toUpperCase();
    if (L !== letter) {
      letter = L;
      out.push(p({
        spacing: { before: out.length ? 240 : 0, after: 100 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 3, color: T.color.rule, space: 4 } },
        children: [dRun(letter, { size: 22, bold: true, color: T.color.accent })],
      }));
    }
    out.push(p({
      spacing: { before: 0, after: 30, line: 250 },
      indent: { left: 240, hanging: 240 },
      children: [
        ...MD.inline(e.term, { size: 17 }),
        uRun('  ' + e.pages.join(', '), { size: 16, color: T.color.graphite }),
      ],
    }));
  });
  return out;
}

function contentsPages() {
  return [
    label('Navigation'),
    p({ spacing: { after: 200 }, children: [dRun('Contents', { size: 40, bold: true, color: T.color.depth })] }),
    p({ style: 'EditorialNote', spacing: { after: 300 }, children: MD.inline('A live Word field. In Microsoft Word press Ctrl+A then F9 (⌘A then fn+F9 on macOS) to repaginate it, or right-click and choose Update Field; every entry is an internal hyperlink. The lists of tables and figures and the index that follow are generated by the build and already carry final page numbers.') }),
    new TableOfContents('Contents', { hyperlinks: true, headingStyleRange: '1-3', captionLabelIncludingNumbers: false }),
    pageBreak(),
    label('Apparatus'),
    p({ spacing: { after: 300 }, children: [dRun('List of Tables', { size: 40, bold: true, color: T.color.depth })] }),
    p({ style: 'EditorialNote', spacing: { after: 260 }, children: MD.inline('Generated by the build from the corpus. Every table in the ten volumes is listed in order of appearance, grouped by volume.') }),
    ...listOf('Table', APPARATUS && APPARATUS.tables),
    pageBreak(),
    label('Apparatus'),
    p({ spacing: { after: 300 }, children: [dRun('List of Figures', { size: 40, bold: true, color: T.color.depth })] }),
    p({ style: 'EditorialNote', spacing: { after: 260 }, children: MD.inline('Generated by the build from the corpus. Architecture, stack and process figures in order of appearance.') }),
    ...listOf('Figure', APPARATUS && APPARATUS.figures),
    pageBreak(),
  ];
}

// ── volume divider + body ─────────────────────────────────────────────────
function volumeDivider(v) {
  return [
    panel({
      fill: T.color.obsidian,
      height: 8100,
      margins: { top: 900, bottom: 900, left: 620, right: 620 },
      children: [
        p({ spacing: { after: 120 }, children: [uRun('VOLUME', { size: 16, bold: true, characterSpacing: 180, color: T.color.accent })] }),
        p({ spacing: { after: 240, line: T.lead(T.size.volumeNumeral, 0.92) }, children: [dRun(v.roman, { size: T.size.volumeNumeral, bold: true, color: 'FFFFFF' })] }),
        p({
          heading: HeadingLevel.HEADING_1,
          spacing: { before: 0, after: 160, line: T.lead(T.size.volumeTitle, 1.08) },
          children: [dRun(v.title, { size: T.size.volumeTitle, bold: true, color: 'FFFFFF' })],
        }),
        p({ spacing: { after: 0 }, children: [run(v.sub, { size: 21, color: '8C97A4' })] }),
      ],
    }),
    p({ spacing: { before: 320, after: 60 }, children: [uRun('AUTHORITY', { size: 13, bold: true, characterSpacing: 110, color: T.color.graphite })] }),
    p({ spacing: { after: 300 }, children: [run(v.authority, { size: 18, color: T.color.ink })] }),
    rule(T.color.rule, 4, 0, 240),
    p({ spacing: { after: 140 }, children: [uRun('EXECUTIVE SUMMARY', { size: 14, bold: true, characterSpacing: 110, color: T.color.accent })] }),
    p({ style: 'ExecSummary', children: MD.inline(v.summary) }),
  ];
}

// ── back matter ───────────────────────────────────────────────────────────
function appendix(letter, title, intro, blocks) {
  const out = [
    p({ heading: HeadingLevel.HEADING_2, pageBreakBefore: true,
        children: [dRun(`Appendix ${letter} — ${title}`, { size: T.size.h1, bold: true, color: T.color.depth })] }),
  ];
  if (intro) out.push(p({ style: 'EditorialNote', spacing: { after: 240 }, children: MD.inline(intro) }));
  out.push(...blocks);
  return out;
}

function checklistTable(title, rows) {
  return [
    p({ heading: HeadingLevel.HEADING_3, children: [dRun(title, { size: T.size.h2, bold: true, color: T.color.depth })] }),
    MD.buildTable(rows, rows[0].map(() => AlignmentType.LEFT),
      { columnWidths: [700, CW - 700 - 2000, 2000] }),
    MD.caption('Table', title),
  ];
}

function glossary() {
  const rows = [['Term', 'Definition']].concat(E.GLOSSARY);
  return [
    p({ heading: HeadingLevel.HEADING_2, pageBreakBefore: true,
        children: [dRun('Glossary', { size: T.size.h1, bold: true, color: T.color.depth })] }),
    p({ style: 'EditorialNote', spacing: { after: 240 },
        children: MD.inline('Terms are defined as this corpus uses them. Where a term also has a general industry meaning, the definition here governs internally and the cross-reference points to the chapter in which the term is established.') }),
    MD.buildTable(rows, [AlignmentType.LEFT, AlignmentType.LEFT], { columnWidths: [2200, CW - 2200] }),
    MD.caption('Table', 'Glossary of terms'),
  ];
}

function bibliography() {
  const out = [
    p({ heading: HeadingLevel.HEADING_2, pageBreakBefore: true,
        children: [dRun('References & Bibliography', { size: T.size.h1, bold: true, color: T.color.depth })] }),
    p({ style: 'EditorialNote', spacing: { after: 260 },
        children: MD.inline('Every external figure in this corpus is attributed at the point of use. This list consolidates those sources and records what each was used for. Sources were consulted in August 2026; where a source reports a market figure that moves, the figure is dated in the text.') }),
    p({ heading: HeadingLevel.HEADING_3, children: [dRun('External sources', { size: T.size.h2, bold: true, color: T.color.depth })] }),
  ];
  E.BIBLIOGRAPHY.forEach(([author, work, url, use], i) => {
    out.push(p({
      spacing: { before: 0, after: 40, line: 275 },
      indent: { left: 420, hanging: 420 },
      children: [
        run(`[${i + 1}]  `, { size: 16, bold: true, color: T.color.accent }),
        run(author + '. ', { size: 17, bold: true }),
        run(work + ' ', { size: 17, italics: true }),
        new ExternalHyperlink({ link: url, children: [new TextRun({ text: url, size: 14, font: T.font.body, style: 'Hyperlink' })] }),
      ],
    }));
    out.push(p({ spacing: { after: 170 }, indent: { left: 420 }, children: [run(use, { size: 15, color: T.color.graphite })] }));
  });

  out.push(p({ heading: HeadingLevel.HEADING_3, children: [dRun('Internal sources', { size: T.size.h2, bold: true, color: T.color.depth })] }));
  out.push(p({ style: 'EditorialNote', spacing: { after: 200 },
      children: MD.inline('Claims in this corpus about what the group has built trace to these. Catalogue lines in Volume III are marked built, partial or specified-not-built on this basis.') }));
  E.INTERNAL_SOURCES.forEach(([name, loc, desc]) => {
    out.push(p({ spacing: { before: 0, after: 30 }, children: [run(name, { size: 17, bold: true }), run('  ·  ' + loc, { size: 15, color: T.color.accent })] }));
    out.push(p({ spacing: { after: 170, line: 275 }, indent: { left: 300 }, children: [run(desc, { size: 16, color: T.color.ink2 })] }));
  });
  return out;
}

function indexPage() {
  return [
    p({ heading: HeadingLevel.HEADING_2, pageBreakBefore: true,
        children: [dRun('Index', { size: T.size.h1, bold: true, color: T.color.depth })] }),
    p({ style: 'EditorialNote', spacing: { after: 300 },
        children: MD.inline('Generated by the build. Page references point to where each concept is established or substantively discussed; passing mentions are not indexed. Word index markers are also embedded throughout the corpus, so a live index can be built in Word if preferred.') }),
    ...indexPages(APPARATUS && APPARATUS.index),
  ];
}

function colophon() {
  return [
    p({ pageBreakBefore: true, spacing: { before: 2400, after: 260 },
        children: [dRun('Colophon', { size: 34, bold: true, color: T.color.depth })] }),
    p({ style: 'FrontProse', children: MD.inline('This edition is composed for A4 at 210 × 297 mm. Display matter is set in a serif book face and running text in a companion serif, with a sans for tables, captions and navigation and a monospaced face for code and architecture figures — the four typographic roles defined in Volume I, Chapter 10. The StromeX brand faces, **Archivo** and **Fraunces**, ship with this edition in `docs/bible/publication/fonts/`; the build selects them automatically wherever they are installed in the rendering environment, so the corpus can be reissued in full brand typography without editing a line of it.') }),
    p({ style: 'FrontProse', children: MD.inline('The rules, tables and figures follow the design laws in Volume I, Chapter 12: typography carries the interface, space is a component, colour carries meaning, and structural devices encode something true about the content rather than decorating it. Tables use horizontal rules only; the vertical grid is carried by alignment, as it is in every well-set financial document.') }),
    p({ style: 'FrontProse', children: MD.inline('This DOCX is the authoritative master. The press-quality PDF edition is generated from it and is content-identical. Both are produced from the markdown corpus of record under version control at `docs/bible/`, by the build recorded at `docs/bible/publication/`, so that the publication can be regenerated exactly whenever the corpus is amended.') }),
    rule(T.color.rule, 4, 400, 240),
    p({ children: [run('THE STROMEX EDITORIAL BIBLE  ·  ' + E.EDITION + '  ·  VERSION ' + E.VERSION, { size: 13, bold: true, characterSpacing: 100, color: T.color.graphite })] }),
    p({ spacing: { before: 40 }, children: [run('© 2026–2027 StromeX Group Holdings. Confidential.', { size: 13, color: T.color.graphite })] }),
  ];
}

// ── assembly ──────────────────────────────────────────────────────────────
function bodyHeader() {
  return new Header({
    children: [new Paragraph({
      spacing: { after: 0 },
      tabStops: [{ type: TabStopType.RIGHT, position: CW }],
      border: { bottom: { style: BorderStyle.SINGLE, size: 3, color: T.color.rule, space: 6 } },
      children: [
        uRun('THE STROMEX EDITORIAL BIBLE', { size: 13, bold: true, characterSpacing: 90, color: T.color.graphite }),
        run('\t', { size: 12 }),
        new SimpleField('STYLEREF "Heading 1" \\* MERGEFORMAT', 'Volume'),
      ],
    })],
  });
}

function pageFooter(withRule) {
  return new Footer({
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: withRule ? 60 : 0 },
      children: [
        uRun('· ', { size: 15, color: T.color.graphite }),
        new TextRun({ children: [PageNumber.CURRENT], font: T.font.ui, size: 15, color: T.color.graphite }),
        uRun(' ·', { size: 15, color: T.color.graphite }),
      ],
    })],
  });
}

function composeBook(v) {
  const stats = { chapters: 0 };
  const raw = fs.readFileSync(path.join(SRC, v.file), 'utf8');
  const bodyChildren = [
    ...volumeDivider(v),
    ...MD.parse(prepare(raw), {
      headingOffset: 1, chapterLevel: 2, indexTerms: INDEX_TERMS,
      tableCaption: (ctx) => ctx || v.title,
      figureCaption: (ctx) => ctx || v.title,
      onHeading: (lvl) => { if (lvl === 2) stats.chapters++; },
    }),
    ...glossary(), ...bibliography(), ...indexPage(), ...colophon(),
  ];

  return new Document({
    creator: 'StromeX Group Holdings',
    title: `Book ${v.roman} — ${v.title} · The StromeX Editorial Bible`,
    description: v.sub,
    subject: 'StromeX Executive Knowledge System',
    lastModifiedBy: 'StromeX Group Holdings',
    styles: styles(), numbering, features: { updateFields: true },
    sections: [
      { properties: { page: { size: { width: T.page.width, height: T.page.height },
          margin: { top: 0, bottom: 0, left: 0, right: 0, header: 0, footer: 0 } } },
        children: bookCover(v) },
      { properties: { page: { size: { width: T.page.width, height: T.page.height },
          margin: T.page.margin,
          pageNumbers: { start: 1, formatType: NumberFormat.LOWER_ROMAN } } },
        footers: { default: pageFooter(false) },
        children: [...bookTitlePage(v), ...copyrightPage(), ...bookDocumentControl(v), ...contentsPages()] },
      { properties: { page: { size: { width: T.page.width, height: T.page.height },
          margin: T.page.margin,
          pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL } } },
        headers: { default: bodyHeader() },
        footers: { default: pageFooter(true) },
        children: bodyChildren },
    ],
  });
}

function main() {
  if (BOOK) {
    const v = E.VOLUMES.find(x => x.roman === BOOK);
    if (!v) throw new Error('unknown book ' + BOOK);
    return Packer.toBuffer(composeBook(v)).then((buf) => {
      fs.writeFileSync(OUT, buf);
      console.log('wrote', path.basename(OUT), (buf.length / 1048576).toFixed(2) + ' MB');
    });
  }

  const stats = { tables: 0, figures: 0, chapters: 0 };

  // ---- body: volumes
  const bodyChildren = [];
  E.VOLUMES.forEach((v) => {
    const raw = fs.readFileSync(path.join(SRC, v.file), 'utf8');
    bodyChildren.push(...volumeDivider(v));
    const els = MD.parse(prepare(raw), {
      headingOffset: 1,          // chapters become Heading 2; volume title is Heading 1
      chapterLevel: 2,
      indexTerms: INDEX_TERMS,
      tableCaption: (ctx) => ctx || v.title,
      figureCaption: (ctx) => ctx || v.title,
      onHeading: (lvl) => { if (lvl === 2) stats.chapters++; },
      onTable: () => stats.tables++,
      onFigure: () => stats.figures++,
    });
    bodyChildren.push(...els);
  });

  // ---- back matter
  const gateI = [
    ['#', 'Criterion', 'Threshold'],
    ['1', 'Paying institutions', '≥ 250'],
    ['2', 'Net revenue retention', '≥ 105%'],
    ['3', 'Gross revenue retention', '≥ 92%'],
    ['4', 'Recurring share of revenue', '≥ 55%'],
    ['5', 'Blended gross margin', '≥ 60%'],
    ['6', 'CAC payback', '≤ 15 months'],
    ['7', 'Referral share of new customers', '≥ 35%'],
    ['8', 'Certified delivery partners', '≥ 15'],
    ['9', 'Reference customers willing to take calls', '≥ 10'],
    ['10', 'Executive layer operating without the founder for 60 days', 'Demonstrated by absence'],
    ['11', 'Independent penetration test passed, no unresolved high findings', 'Yes'],
    ['12', 'Free-tier monthly active institutions', '≥ 5,000'],
  ];
  const gateII = [
    ['#', 'Criterion', 'Threshold'],
    ['1', 'Revenue', '≥ growth-scenario floor'],
    ['2', 'Recurring share of revenue', '≥ 65%'],
    ['3', 'Net revenue retention', '≥ 115%'],
    ['4', 'Countries with local leadership', '≥ 3'],
    ['5', 'Ecosystems beyond education at depth', '≥ 2'],
    ['6', 'Partner-delivered revenue', '≥ 30%'],
    ['7', 'Board with independent directors', 'Functioning'],
    ['8', 'Accounts', 'Audited'],
    ['9', 'Rule of 40', '≥ 30'],
  ];

  const backChildren = [
    p({ pageBreakBefore: true, spacing: { before: 1800, after: 200 },
        children: [run('APPENDICES', { size: 15, bold: true, characterSpacing: 240, color: T.color.accent })] }),
    p({ heading: HeadingLevel.HEADING_1, spacing: { before: 0, after: 260 },
        children: [dRun('Apparatus & Appendices', { size: 46, bold: true, color: T.color.depth })] }),
    p({ style: 'FrontProse', children: MD.inline('The appendices extract the operational instruments of the corpus — the gates, checklists and definitions a reader must be able to find without navigating a volume. They are summaries of, and subordinate to, the chapters they draw from. Where an appendix and its source chapter differ, the chapter governs.') }),

    ...appendix('A', 'Phase Gate Checklists',
      'From Volume VIII, Chapter 2. A phase ends when its gate is passed, not when its years elapse. Running Phase I into 2032 because the gate was not met is a correct decision; entering Phase II with the gate unmet is not.',
      [...checklistTable('Gate I → II — assessed from 2030', gateI),
       ...checklistTable('Gate II → III — assessed from 2035', gateII),
       p({ style: 'EditorialNote', children: MD.inline('Criterion 10 of Gate I is the one most likely to be quietly skipped and the one that matters most. It is assessed by the founder actually being absent for sixty days.') })]),

    ...appendix('B', 'Market-Entry Checklist',
      'From Volume VIII, Chapter 10. Every item must be complete and signed off before the first customer contract in a new country.',
      [
        ...checklistTable('Legal & regulatory', [
          ['#', 'Item', 'Status'],
          ['B1', 'Entity incorporated', '☐'], ['B2', 'Tax registration', '☐'],
          ['B3', 'Employment compliance reviewed', '☐'], ['B4', 'Data protection regime mapped and implemented', '☐'],
          ['B5', 'Sector regulator requirements documented', '☐'], ['B6', 'Trademark filed', '☐'],
          ['B7', 'Contracts localised by local counsel', '☐'], ['B8', 'Sanctions and export-control screening', '☐'],
          ['B9', 'Anti-corruption exposure assessed', '☐'],
        ]),
        ...checklistTable('Commercial', [
          ['#', 'Item', 'Status'],
          ['B10', 'Market sized by the Volume II §2.2 method with dated inputs', '☐'],
          ['B11', 'Price band assigned', '☐'], ['B12', 'Competitors mapped', '☐'],
          ['B13', 'Three reference prospects identified', '☐'], ['B14', 'Partner or acquisition target assessed', '☐'],
          ['B15', 'Payment rails live', '☐'], ['B16', 'Local currency handling', '☐'], ['B17', 'Collection risk assessed', '☐'],
        ]),
        ...checklistTable('Product, operational & financial', [
          ['#', 'Item', 'Status'],
          ['B18', 'Language complete; curriculum and sector standards mapped', '☐'],
          ['B19', 'Local integrations built (payments, examination boards, regulators)', '☐'],
          ['B20', 'Data residency in place if required', '☐'],
          ['B21', 'Offline and low-bandwidth verified on local networks', '☐'],
          ['B22', 'Local leader hired, with authority', '☐'],
          ['B23', 'Support hours covered; delivery capacity confirmed in writing', '☐'],
          ['B24', 'Entry budget approved; break-even modelled with stated assumptions', '☐'],
          ['B25', 'FX exposure hedged or accepted explicitly', '☐'],
          ['B26', 'Exit criteria defined — what would make us withdraw, and by when', '☐'],
        ]),
        p({ style: 'EditorialNote', children: MD.inline('Item B26 is the one most often omitted and the most valuable. A market entry with no pre-agreed failure condition will be defended indefinitely by the people who championed it.') }),
      ]),

    ...appendix('C', 'Metric Definitions',
      'From Volume IX, Chapter 4. Every metric carries its denominator, its period and its trend. A metric definition may not be changed without restating history and saying that it was changed.',
      [MD.buildTable([
        ['Metric', 'Definition', 'Target'],
        ['Net revenue retention', 'Recurring revenue from the cohort of customers present twelve months ago, including expansion and contraction, divided by that cohort’s recurring revenue then.', '105–112% Phase I; ≥115% Phase II'],
        ['Gross revenue retention', 'As above, excluding expansion. Isolates churn.', '≥ 92%'],
        ['CAC payback', 'Loaded acquisition cost per customer divided by monthly gross profit per customer.', '< 12 months low-touch; < 18 consultative'],
        ['Time to first value', 'Days from contract signature until the customer uses something real in production.', '< 14 days'],
        ['Adoption rate', 'Active users by role divided by licensed users, measured at 90 days.', 'Reported beside every bookings figure'],
        ['Referral share', 'New customers originating from an existing customer or their network, divided by all new customers.', '≥ 35% by end of Phase I'],
        ['Rule of 40', 'Revenue growth percentage plus operating margin percentage.', '≥ 30 at Gate II; ≥ 40 from 2034'],
        ['Blended gross margin', 'Group gross profit divided by group revenue, across all eleven revenue engines.', '60% (2030) → 76% (2040)'],
        ['Unused-module count', 'Modules purchased and unused for 60 days. Triggers intervention or proactive removal.', 'Driven to zero'],
        ['Cancellation friction', 'Clicks to cancel divided by clicks to subscribe.', '< 1, measured and reported'],
      ], [AlignmentType.LEFT, AlignmentType.LEFT, AlignmentType.LEFT],
        { columnWidths: [1900, CW - 1900 - 2200, 2200] }),
       MD.caption('Table', 'Metric definitions and targets')]),

    ...glossary(),
    ...bibliography(),
    ...indexPage(),
    ...colophon(),
  ];

  const doc = new Document({
    creator: 'StromeX Group Holdings',
    title: 'The StromeX Editorial Bible — ' + E.EDITION,
    description: 'The Constitution, Operating Manual and Strategic Corpus of StromeX. Ten volumes.',
    subject: 'Corporate constitution, strategy, product catalogue, engineering standards and 20-year roadmap',
    keywords: 'StromeX; editorial bible; constitution; strategy; pricing; governance; roadmap',
    lastModifiedBy: 'StromeX Group Holdings',
    styles: styles(),
    numbering,
    features: { updateFields: true },
    sections: [
      // 1 — cover, full bleed
      {
        properties: {
          page: {
            size: { width: T.page.width, height: T.page.height },
            margin: { top: 0, bottom: 0, left: 0, right: 0, header: 0, footer: 0 },
          },
          titlePage: false,
        },
        children: cover(),
      },
      // 2 — front matter, roman numerals
      {
        properties: {
          page: {
            size: { width: T.page.width, height: T.page.height },
            margin: T.page.margin,
            pageNumbers: { start: 1, formatType: NumberFormat.LOWER_ROMAN },
          },
        },
        footers: { default: pageFooter(false) },
        children: [
          ...halfTitle(),
          ...titlePage(),
          ...copyrightPage(),
          ...documentControl(),
          ...revisionHistory(),
          ...proseSection('Executive foreword', 'Foreword', E.FOREWORD, { leadIn: true }),
          ...proseSection('From the founder', 'A Message from the Founder', E.FOUNDER,
            { leadIn: true, signature: ['Ahmad Sulaimiy', 'Founder, StromeX Group Holdings'] }),
          ...visionMission(),
          ...proseSection('Orientation', 'How to Read This Corpus', E.HOWTOREAD),
          ...contentsPages(),
        ],
      },
      // 3 — body + back matter, arabic restarting at 1
      {
        properties: {
          page: {
            size: { width: T.page.width, height: T.page.height },
            margin: T.page.margin,
            pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL },
          },
        },
        headers: { default: bodyHeader() },
        footers: { default: pageFooter(true) },
        children: [...bodyChildren, ...backChildren],
      },
    ],
  });

  return Packer.toBuffer(doc).then((buf) => {
    fs.writeFileSync(OUT, buf);
    console.log('wrote', OUT, (buf.length / 1048576).toFixed(2) + ' MB');
    console.log('chapters:', stats.chapters);
  });
}

main().catch(e => { console.error(e); process.exit(1); });
