/* SpaceTalk Editorial Bible — publication renderer.
   IR (build/ir.json) → SpaceTalk_Editorial_Bible_v1.0.docx
   Pass 1 emits the document with placeholder folios; pass 2 re-emits it with
   real page numbers read back out of the pass-1 PDF. */
const fs = require('fs');
const path = require('path');
const D = require('/tmp/node_modules/docx');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType,
  ShadingType, BorderStyle, AlignmentType, ImageRun, InternalHyperlink, Bookmark,
  Header, Footer, PageNumber, NumberFormat, PageBreak, Tab, TabStopType,
  HeightRule, VerticalAlign, PageOrientation, SectionType,
} = D;

const { C, F, PAGE } = require('./theme');
const { styles, numbering } = require('./styles');
const K = require('./content');
const APP = require('./apparatus');

const ROOT = path.resolve(__dirname, '..');
const ir = JSON.parse(fs.readFileSync(path.join(ROOT, 'build/ir.json'), 'utf8'));
const figures = JSON.parse(fs.readFileSync(path.join(ROOT, 'build/diagrams/manifest.json'), 'utf8'));
const pagemap = fs.existsSync(path.join(ROOT, 'build/pagemap.json'))
  ? JSON.parse(fs.readFileSync(path.join(ROOT, 'build/pagemap.json'), 'utf8')) : {};

const IMG = (n) => path.join(ROOT, 'build/diagrams', n);
const CONTENT_PX = 604;                    // 6.30 in at 96 dpi
const NONE = K.NONE;

// ------------------------------------------------------------------ helpers
const P = (opts) => new Paragraph(opts);
const T = (text, o = {}) => new TextRun({ text, ...o });
const spacer = (h = 160) => P({ children: [T('')], spacing: { before: 0, after: h } });
const pageBreak = () => P({ children: [new PageBreak()] });

function folio(key) {
  const v = pagemap[key];
  return v === undefined ? '—' : String(v);
}

function dotLeader(label, anchor, pageKey, style) {
  return P({
    style,
    tabStops: [{ type: TabStopType.RIGHT, position: PAGE.content, leader: 'dot' }],
    children: [
      new InternalHyperlink({ anchor, children: [T(label)] }),
      new TextRun({ children: [new Tab(), folio(pageKey)] }),
    ],
  });
}

function bookmarkHeading(anchor, style, children, extra = {}) {
  return P({ style, ...extra,
    children: [new Bookmark({ id: anchor, children })] });
}

// ------------------------------------------------------------ page furniture
function runningHeader(right) {
  return new Header({
    children: [P({
      tabStops: [{ type: TabStopType.RIGHT, position: PAGE.content }],
      spacing: { before: 0, after: 0, line: 240, lineRule: 'atLeast' },
      border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C.void200, space: 6 } },
      children: [
        T('SPACETALK EDITORIAL BIBLE', { font: F.ui, size: 13, color: C.void400,
          characterSpacing: 32, bold: true }),
        new TextRun({ children: [new Tab(), right],
          font: F.ui, size: 13, color: C.orbit600, characterSpacing: 32, bold: true }),
      ],
    })],
  });
}

function runningFooter() {
  return new Footer({
    children: [P({
      tabStops: [{ type: TabStopType.RIGHT, position: PAGE.content }],
      spacing: { before: 60, after: 0, line: 240, lineRule: 'atLeast' },
      children: [
        T('Version 1.0  ·  Internal reference', { font: F.ui, size: 14, color: C.void400 }),
        new TextRun({ children: [new Tab(), PageNumber.CURRENT],
          font: F.ui, size: 16, color: C.void700, bold: true }),
      ],
    })],
  });
}

const blankHeader = () => new Header({ children: [P({ children: [T('')] })] });

function sectionProps(opts = {}) {
  return {
    page: {
      size: { width: PAGE.w, height: PAGE.h },
      margin: {
        top: opts.top ?? PAGE.top, bottom: opts.bottom ?? PAGE.bottom,
        left: opts.left ?? PAGE.left, right: opts.right ?? PAGE.right,
        header: PAGE.header, footer: PAGE.footer, gutter: 0,
      },
      ...(opts.pageNumbers ? { pageNumbers: opts.pageNumbers } : {}),
    },
    titlePage: !!opts.titlePage,
  };
}

// ------------------------------------------------------------------ figures
// Numbered up front so the list of figures is correct on the first pass too.
(() => {
  const seen = {};
  figures.forEach((f) => {
    seen[f.chapter] = (seen[f.chapter] || 0) + 1;
    f.label = `Figure ${f.chapter}.${seen[f.chapter]}`;
  });
})();

function figureFor(chapter, key) {
  // Exact match on a section number; prefix match only for parts whose headings
  // carry no number (otherwise "6.1" would also claim 6.10 … 6.15).
  return figures.filter((f) => f.chapter === chapter && (f.after === key
    || (!/^\d+\.\d+$/.test(f.after) && key.startsWith(f.after))));
}

// -------------------------------------------------- section index (shared)
// One definition of "what are this part's sections and what are they called",
// used by the body, the contents, the part opener and the page-number pass.
// Parts 9 and 12 do not use N.M numbering, so unnumbered headings get a
// stable synthetic anchor rather than being dropped.
const SECTIONS = {};
for (const ch of ir.chapters) {
  const list = [];
  let n = 0;
  for (const b of ch.blocks) {
    if (b.k !== 'h' || b.level !== 2) continue;
    n += 1;
    const text = K.plain(b.runs);
    const num = text.match(/^(\d+\.\d+)\s*—\s*(.*)$/);
    const adr = text.match(/^(ADR-(\d{3}))\s*—\s*(.*)$/);
    if (num) list.push({ anchor: K.secAnchor(num[1]), num: num[1], title: num[2], key: num[1] });
    else if (adr) list.push({ anchor: K.adrAnchor(adr[2]), num: adr[1], title: adr[3], key: adr[1] });
    else {
      const m = text.match(/^(.*?)\s*—\s*(.*)$/);
      list.push({ anchor: `h_${ch.num}_${n}`, num: m ? m[1] : '', title: m ? m[2] : text, key: text });
    }
  }
  SECTIONS[ch.num] = list;
}
fs.writeFileSync(path.join(ROOT, 'build/sections.json'), JSON.stringify(SECTIONS, null, 1));

function renderFigure(f) {
  const h = Math.round(CONTENT_PX * (f.h / f.w));
  return [
    P({ style: 'FigureImage', children: [new ImageRun({
      type: 'png', data: fs.readFileSync(f.png),
      transformation: { width: CONTENT_PX, height: h },
      altText: { title: f.label, description: f.caption, name: f.name },
    })] }),
    P({ style: 'Caption', children: [new Bookmark({ id: 'fig_' + f.name, children: [
      T(`${f.label}  `, { bold: true, color: C.orbit600, size: 17 }),
      T(f.caption, { color: C.void500, size: 17 }),
    ] })] }),
  ];
}

// ------------------------------------------------------------------- blocks
let listInstance = 1;
function renderBlocks(blocks, ctx) {
  const out = [];
  let pending = [];
  for (let i = 0; i < blocks.length; i++) {
    const b = blocks[i];

    if (b.k === 'rule') {
      const nxt = blocks[i + 1];
      if (nxt && nxt.k === 'h') continue;            // heading brings its own space
      out.push(P({ style: 'Rule', children: [T('')] }));
      continue;
    }

    if (b.k === 'h') {
      if (b.level === 2) {
        const s = SECTIONS[ctx.chapter][ctx.i++];
        const kids = s.num
          ? [T(s.num + '  ', { color: C.orbit500, bold: true, font: F.display, size: 30 }),
            T(s.title, { color: C.void900, bold: true, font: F.display, size: 30 })]
          : [T(s.title, { color: C.void900, bold: true, font: F.display, size: 30 })];
        out.push(bookmarkHeading(s.anchor, 'H1', kids));
        pending = figureFor(ctx.chapter, s.key);
      } else {
        out.push(P({ style: 'H2', children: K.inlineRuns(b.runs,
          { base: { size: 23, bold: true, color: C.orbit700 } }) }));
      }
      continue;
    }

    if (b.k === 'p') {
      const co = APP.calloutFor(ctx.chapter, K.plain(b.runs));
      if (co) {
        out.push(K.calloutPanel(null, b.runs, co));
        out.push(spacer(150));
      } else {
        out.push(P({ style: 'Body', children: K.inlineRuns(b.runs) }));
      }
      if (pending.length) { pending.forEach((f) => out.push(...renderFigure(f))); pending = []; }
      continue;
    }

    if (b.k === 'list') {
      // Each ordered list needs its own numbering instance, or the counter
      // runs on across the whole document instead of restarting at 1.
      const instance = b.ordered ? listInstance++ : 0;
      b.items.forEach((it) => out.push(P({
        style: it.lvl ? 'Bullet2' : 'Bullet',
        numbering: { reference: b.ordered ? 'st-number' : 'st-bullet',
          level: it.lvl || 0, instance },
        children: K.inlineRuns(it.runs),
      })));
      out.push(spacer(60));
      if (pending.length) { pending.forEach((f) => out.push(...renderFigure(f))); pending = []; }
      continue;
    }

    if (b.k === 'table') {
      out.push(K.renderTable(b));
      out.push(spacer(210));
      if (pending.length) { pending.forEach((f) => out.push(...renderFigure(f))); pending = []; }
      continue;
    }

    if (b.k === 'code') { out.push(K.codeBlock(b.lines)); out.push(spacer(210)); continue; }

    if (b.k === 'quote') {
      out.push(P({ style: 'PullQuote', children: K.inlineRuns(b.runs,
        { base: { font: F.display, size: 30, color: C.orbit800 } }) }));
      continue;
    }
  }
  if (pending.length) pending.forEach((f) => out.push(...renderFigure(f)));
  return out;
}

// ------------------------------------------------------------------- cover
function coverSection() {
  const cell = (children) => new TableCell({
    width: { size: PAGE.w, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: C.orbit950, color: 'auto' },
    margins: { top: 2100, bottom: 1400, left: 1584, right: 1584 },
    borders: { top: NONE, bottom: NONE, left: NONE, right: NONE },
    verticalAlign: VerticalAlign.TOP,
    children,
  });

  const body = [
    P({ spacing: { after: 900 }, children: [new ImageRun({
      type: 'png', data: fs.readFileSync(IMG('mark-white.png')),
      transformation: { width: 92, height: 92 },
      altText: { title: 'SpaceTalk', description: 'The SpaceTalk mark', name: 'mark' },
    })] }),
    P({ style: 'CoverMeta', children: [T('THE EDITORIAL BIBLE', { font: F.ui, size: 18,
      color: C.orbit300, characterSpacing: 66, bold: true })] }),
    P({ style: 'CoverTitle', children: [T('SpaceTalk')] }),
    P({ style: 'CoverSub', children: [T('The constitution of the product — vision, brand, design,')] }),
    P({ style: 'CoverSub', children: [T('experience, intelligence, architecture and roadmap.')] }),
    P({ style: 'CoverRule', children: [T('')] }),
    P({ style: 'CoverMeta', children: [T('VERSION 1.0   ·   RATIFIED EDITION')] }),
    P({ style: 'CoverMeta', children: [T('FOURTEEN PARTS   ·   TWENTY FIGURES   ·   TWELVE DECISION RECORDS')] }),
    spacer(4500),
    P({ children: [T('Room to talk.', { font: F.display, size: 34, color: C.orbit200 })] }),
  ];

  return {
    properties: sectionProps({ top: 0, bottom: 0, left: 0, right: 0 }),
    children: [
      new Table({
        columnWidths: [PAGE.w],
        width: { size: PAGE.w, type: WidthType.DXA },
        borders: { top: NONE, bottom: NONE, left: NONE, right: NONE,
          insideHorizontal: NONE, insideVertical: NONE },
        rows: [new TableRow({
          height: { value: PAGE.h, rule: HeightRule.EXACT },
          cantSplit: true,
          children: [cell(body)],
        })],
      }),
    ],
  };
}

// ------------------------------------------------------------- front matter
function frontMatter() {
  const kids = [];

  // ---- title page
  kids.push(spacer(2200));
  kids.push(P({ spacing: { after: 620 }, children: [new ImageRun({
    type: 'png', data: fs.readFileSync(IMG('mark-dark.png')),
    transformation: { width: 62, height: 62 },
    altText: { title: 'SpaceTalk', description: 'The SpaceTalk mark', name: 'mark' },
  })] }));
  kids.push(P({ style: 'Kicker', children: [T('THE EDITORIAL BIBLE', { font: F.ui, size: 16,
    bold: true, color: C.orbit600, characterSpacing: 58 })] }));
  kids.push(P({ style: 'TitlePageTitle', children: [T('SpaceTalk')] }));
  kids.push(P({ style: 'TitlePageSub', children: [
    T('The constitution of the product. Every design, engineering, brand and business decision traces back to this document.')] }));
  kids.push(P({ style: 'Rule', children: [T('')] }));
  kids.push(P({ style: 'Body', children: [
    T('Version 1.0', { bold: true }), T('   ·   Ratified edition   ·   Fourteen parts')] }));
  kids.push(P({ style: 'Body', children: [T('Prepared for executives, investors, designers, engineers, and everyone who joins the project after us.', { color: C.void600 })] }));
  kids.push(pageBreak());

  // ---- copyright / colophon
  kids.push(...APP.copyrightPage());
  kids.push(pageBreak());

  // ---- document control
  kids.push(...APP.documentControl());
  kids.push(pageBreak());

  // ---- version history
  kids.push(...APP.versionHistory());
  kids.push(pageBreak());

  // ---- how to use
  kids.push(...APP.howToUse(ir));
  kids.push(pageBreak());

  // ---- executive summary
  kids.push(...APP.executiveSummary());
  kids.push(pageBreak());

  // ---- contents
  kids.push(bookmarkHeading('f_contents', 'FrontHeading', [T('Contents')]));
  kids.push(P({ style: 'Body', children: [T('Every entry is a live link. Section numbers match the source documents exactly, so a reference in one part resolves to the same number in another.', { color: C.void600 })] }));
  kids.push(spacer(180));

  kids.push(P({ style: 'Kicker', children: [T('FRONT MATTER')] }));
  for (const [label, anchor, key] of APP.FRONT_ENTRIES) {
    kids.push(dotLeader(label, anchor, key, 'TocFront'));
  }

  kids.push(spacer(200));
  kids.push(P({ style: 'Kicker', children: [T('THE FOURTEEN PARTS')] }));
  for (const ch of ir.chapters) {
    kids.push(dotLeader(`Part ${ch.num}  —  ${APP.chapterTitle(ch)}`, K.chapAnchor(ch.num),
      'c_' + ch.num, 'TocChapter'));
    for (const s of SECTIONS[ch.num]) {
      kids.push(dotLeader(s.num ? `${s.num}   ${s.title}` : s.title,
        s.anchor, s.anchor, 'TocSection'));
    }
  }

  kids.push(spacer(200));
  kids.push(P({ style: 'Kicker', children: [T('BACK MATTER')] }));
  for (const [label, anchor, key] of APP.BACK_ENTRIES) {
    kids.push(dotLeader(label, anchor, key, 'TocFront'));
  }

  kids.push(spacer(240));
  kids.push(P({ style: 'Kicker', children: [T('FIGURES')] }));
  figures.forEach((f) => {
    kids.push(dotLeader(`${f.label || 'Figure'}   ${f.caption.split('—')[0].trim()}`,
      'fig_' + f.name, 'fig_' + f.name, 'TocSection'));
  });

  return {
    properties: {
      ...sectionProps({ pageNumbers: { start: 1, formatType: NumberFormat.LOWER_ROMAN } }),
      titlePage: true,
    },
    headers: { default: runningHeader('FRONT MATTER'), first: blankHeader() },
    footers: { default: runningFooter(), first: runningFooter() },
    children: kids,
  };
}

// ---------------------------------------------------------------- chapters
function chapterSection(ch, isFirst) {
  const kids = [];

  // ---- opener
  kids.push(spacer(760));
  kids.push(P({ style: 'ChapterKicker', children: [T(`PART ${String(ch.num).padStart(2, '0')}`)] }));
  kids.push(P({ style: 'ChapterNumber', children: [T(String(ch.num).padStart(2, '0'))] }));
  kids.push(bookmarkHeading(K.chapAnchor(ch.num), 'ChapterTitle', [T(APP.chapterTitle(ch))]));
  const title = APP.chapterTitle(ch);
  const label = (ch.label || '').replace(new RegExp('\\s*—\\s*' + title + '$'), '');
  kids.push(P({ style: 'ChapterLabel', children: [T(label)] }));
  if (ch.standfirst) {
    kids.push(P({ style: 'Standfirst', children: K.inlineRuns(ch.standfirst,
      { base: { italics: true, color: C.void600, size: 23 } }) }));
  }
  const pq = APP.PULL_QUOTES[ch.num];
  if (pq) kids.push(P({ style: 'PullQuote', children: [T(pq)] }));

  kids.push(spacer(260));
  kids.push(P({ style: 'Kicker', children: [T('IN THIS PART')] }));
  for (const s of SECTIONS[ch.num]) {
    kids.push(P({ style: 'InThisPart',
      tabStops: [{ type: TabStopType.RIGHT, position: PAGE.content, leader: 'dot' }],
      children: [
        new InternalHyperlink({ anchor: s.anchor, children: [
          ...(s.num ? [T(s.num + '   ', { color: C.orbit600, bold: true })] : []),
          T(s.title, { color: C.void700 })] }),
        new TextRun({ children: [new Tab(), folio(s.anchor)], color: C.void400, size: 17 }),
      ] }));
  }
  kids.push(pageBreak());

  // ---- body
  kids.push(...renderBlocks(ch.blocks, { chapter: ch.num, i: 0 }));

  return {
    properties: {
      ...sectionProps(isFirst
        ? { pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL } } : {}),
      titlePage: true,
      type: SectionType.NEXT_PAGE,
    },
    headers: {
      default: runningHeader(`PART ${ch.num} — ${ch.short.toUpperCase()}`),
      first: blankHeader(),
    },
    footers: { default: runningFooter(), first: runningFooter() },
    children: kids,
  };
}

// -------------------------------------------------------------------- build
function build() {
  const sections = [coverSection(), frontMatter()];
  ir.chapters.forEach((ch, i) => sections.push(chapterSection(ch, i === 0)));
  sections.push({
    properties: { ...sectionProps(), titlePage: true, type: SectionType.NEXT_PAGE },
    headers: { default: runningHeader('BACK MATTER'), first: blankHeader() },
    footers: { default: runningFooter(), first: runningFooter() },
    children: APP.backMatter(ir, figures, folio),
  });

  const doc = new Document({
    creator: 'SpaceTalk',
    title: 'SpaceTalk Editorial Bible v1.0',
    description: 'The constitution of the SpaceTalk product: vision, brand, design system, '
      + 'user experience, AI philosophy, features, architecture, performance, roadmap, '
      + 'scope governance, business and decision records.',
    subject: 'Product constitution and design manual',
    keywords: 'SpaceTalk, editorial bible, design system, product, architecture',
    styles, numbering,
    features: { updateFields: false },
    sections,
  });

  return Packer.toBuffer(doc).then((buf) => {
    const out = path.join(ROOT, 'dist/SpaceTalk_Editorial_Bible_v1.0.docx');
    fs.writeFileSync(out, buf);
    // record figure labels for the pass-2 list of figures
    fs.writeFileSync(path.join(ROOT, 'build/diagrams/manifest.json'), JSON.stringify(figures, null, 1));
    console.log(`  docx written  ${(buf.length / 1024 / 1024).toFixed(2)} MB  ${sections.length} sections`);
  });
}

build().catch((e) => { console.error(e); process.exit(1); });
