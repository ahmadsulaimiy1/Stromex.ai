/* Block and inline rendering: IR → docx elements, with live cross-references. */
const D = require('/tmp/node_modules/docx');
const {
  Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  BorderStyle, AlignmentType, ImageRun, InternalHyperlink, ExternalHyperlink,
  HeightRule, VerticalAlign,
} = D;
const { C, F, PAGE } = require('./theme');

// ------------------------------------------------------------------ anchors
const secAnchor = (s) => 's_' + s.replace(/\./g, '_');
const adrAnchor = (n) => 'a_' + n;
const chapAnchor = (n) => 'c_' + n;

const NONE = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const hair = (color) => ({ style: BorderStyle.SINGLE, size: 2, color });

// ------------------------------------------------------------ cross-refs
// Rewrites the IR run list so that document references become real hyperlinks.
function resolveRefs(runs) {
  const out = [];
  for (let i = 0; i < runs.length; i++) {
    const r = runs[i];
    const next = runs[i + 1];

    // `NN-FILE.md` §N.M   |   `NN` §N.M   |   `NN-FILE.md` ADR-0NN
    if (r.c && /^(\d{2})(-[A-Z0-9-]+\.md)?$/.test(r.t)) {
      const part = r.t.slice(0, 2).replace(/^0/, '') || '0';
      const partNum = parseInt(r.t.slice(0, 2), 10);
      if (next && !next.c) {
        let m = next.t.match(/^\s*§(\d+\.\d+)/);
        if (m) {
          out.push({ xref: secAnchor(m[1]), t: `Part ${partNum} §${m[1]}`, b: r.b });
          const rest = next.t.slice(m[0].length);
          if (rest) out.push({ ...next, t: rest });
          i++;
          continue;
        }
        m = next.t.match(/^\s*(ADR-(\d{3}))/);
        if (m) {
          out.push({ xref: adrAnchor(m[2]), t: `Part ${partNum} ${m[1]}`, b: r.b });
          const rest = next.t.slice(m[0].length);
          if (rest) out.push({ ...next, t: rest });
          i++;
          continue;
        }
      }
      out.push({ xref: chapAnchor(partNum), t: `Part ${partNum}`, b: r.b });
      continue;
    }
    out.push(r);
  }

  // Plain-text patterns: ADR-0NN and "Part N.M"
  const out2 = [];
  for (const r of out) {
    if (r.c || r.href || r.xref) { out2.push(r); continue; }
    let text = r.t;
    const re = /(ADR-(\d{3}))|(Part (\d+\.\d+))|(§(\d+\.\d+))/g;
    let last = 0, m;
    while ((m = re.exec(text)) !== null) {
      if (m.index > last) out2.push({ ...r, t: text.slice(last, m.index) });
      if (m[2]) out2.push({ ...r, xref: adrAnchor(m[2]), t: m[1] });
      else if (m[4]) out2.push({ ...r, xref: secAnchor(m[4]), t: m[3] });
      else out2.push({ ...r, xref: secAnchor(m[6]), t: m[5] });
      last = m.index + m[0].length;
    }
    if (last < text.length) out2.push({ ...r, t: text.slice(last) });
  }
  return out2;
}

// ------------------------------------------------------------------ inline
function inlineRuns(runs, opts = {}) {
  const base = opts.base || {};
  const resolved = opts.raw ? runs : resolveRefs(runs);
  const els = [];
  for (const r of resolved) {
    const props = {
      text: r.t,
      font: r.c ? F.mono : (base.font || F.ui),
      size: r.c ? (base.size ? base.size - 3 : 18) : base.size,
      bold: !!r.b || base.bold,
      italics: !!r.i || base.italics,
      color: base.color,
    };
    if (r.c) props.color = opts.onDark ? C.aurora300 : C.orbit800;
    if (r.xref) {
      els.push(new InternalHyperlink({
        anchor: r.xref,
        children: [new TextRun({ ...props, color: C.orbit600 })],
      }));
    } else if (r.href && /^https?:/.test(r.href)) {
      els.push(new ExternalHyperlink({
        link: r.href,
        children: [new TextRun({ ...props, color: C.orbit600, underline: {} })],
      }));
    } else if (r.href) {
      els.push(new TextRun({ ...props, color: C.orbit600 }));
    } else {
      els.push(new TextRun(props));
    }
  }
  return els;
}

const plain = (runs) => runs.map((r) => r.t).join('');

// ------------------------------------------------------------------ tables
function columnWidths(block, total) {
  const n = block.header.length;
  const score = new Array(n).fill(0);
  const cells = [block.header.map(plain), ...block.rows.map((r) => r.map(plain))];
  for (const row of cells) {
    for (let i = 0; i < n; i++) {
      const len = (row[i] || '').length;
      score[i] = Math.max(score[i], Math.min(len, 130));
    }
  }
  // temper extremes so one long column cannot starve the others
  const w = score.map((s) => Math.pow(Math.max(s, 6), 0.72));
  const sum = w.reduce((a, b) => a + b, 0);
  let out = w.map((x) => Math.round((x / sum) * total));
  const min = Math.max(620, Math.floor(total / (n * 3.4)));
  for (let i = 0; i < n; i++) if (out[i] < min) out[i] = min;
  const s2 = out.reduce((a, b) => a + b, 0);
  out = out.map((x) => Math.round((x / s2) * total));
  const drift = total - out.reduce((a, b) => a + b, 0);
  out[out.findIndex((v) => v === Math.max(...out))] += drift;
  return out;
}

function renderTable(block) {
  const widths = columnWidths(block, PAGE.content);
  const align = (a) => (a === 'center' ? AlignmentType.CENTER
    : a === 'right' ? AlignmentType.RIGHT : AlignmentType.LEFT);
  const dense = block.rows.length > 9;

  const head = new TableRow({
    tableHeader: true,
    cantSplit: true,
    children: block.header.map((cell, i) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: C.orbit950, color: 'auto' },
      margins: { top: 90, bottom: 90, left: 130, right: 130 },
      verticalAlign: VerticalAlign.CENTER,
      borders: { top: NONE, bottom: NONE, left: NONE, right: NONE },
      children: [new Paragraph({
        style: 'TableHead',
        alignment: align(block.aligns[i]),
        children: inlineRuns(cell, { base: { color: C.void0, bold: true, size: 17 }, onDark: true }),
      })],
    })),
  });

  const rows = block.rows.map((row, ri) => new TableRow({
    cantSplit: true,
    children: row.map((cell, i) => new TableCell({
      width: { size: widths[i] || 900, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: ri % 2 ? C.void25 : C.void0, color: 'auto' },
      margins: { top: dense ? 70 : 90, bottom: dense ? 70 : 90, left: 130, right: 130 },
      verticalAlign: VerticalAlign.TOP,
      borders: { top: NONE, bottom: hair(C.void200), left: NONE, right: NONE },
      children: [new Paragraph({
        style: dense ? 'TableCellTight' : 'TableCell',
        alignment: align(block.aligns[i]),
        children: inlineRuns(cell),
      })],
    })),
  }));

  return new Table({
    columnWidths: widths,
    width: { size: PAGE.content, type: WidthType.DXA },
    borders: { top: NONE, bottom: NONE, left: NONE, right: NONE,
      insideHorizontal: NONE, insideVertical: NONE },
    rows: [head, ...rows],
  });
}

// ---------------------------------------------------------------- callouts
function calloutPanel(titleRuns, bodyRuns, tone = 'orbit') {
  const tones = {
    orbit: { fill: C.orbit50, bar: C.orbit500, title: C.orbit700 },
    warning: { fill: C.warningS, bar: C.warning, title: C.warning },
    danger: { fill: C.dangerS, bar: C.danger, title: C.danger },
    success: { fill: C.successS, bar: C.success, title: C.success },
    neutral: { fill: C.void50, bar: C.void400, title: C.void700 },
  };
  const t = tones[tone] || tones.orbit;
  const kids = [];
  if (titleRuns) {
    kids.push(new Paragraph({ style: 'CalloutTitle',
      children: inlineRuns(titleRuns, { base: { color: t.title, bold: true, size: 20 } }) }));
  }
  kids.push(new Paragraph({ style: 'CalloutBody', children: inlineRuns(bodyRuns) }));
  return new Table({
    columnWidths: [PAGE.content],
    width: { size: PAGE.content, type: WidthType.DXA },
    borders: { top: NONE, bottom: NONE, left: NONE, right: NONE,
      insideHorizontal: NONE, insideVertical: NONE },
    rows: [new TableRow({
      cantSplit: false,
      children: [new TableCell({
        width: { size: PAGE.content, type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, fill: t.fill, color: 'auto' },
        margins: { top: 190, bottom: 190, left: 240, right: 240 },
        borders: { top: NONE, bottom: NONE, right: NONE,
          left: { style: BorderStyle.SINGLE, size: 18, color: t.bar } },
        children: kids,
      })],
    })],
  });
}

function codeBlock(lines) {
  return new Table({
    columnWidths: [PAGE.content],
    width: { size: PAGE.content, type: WidthType.DXA },
    borders: { top: NONE, bottom: NONE, left: NONE, right: NONE,
      insideHorizontal: NONE, insideVertical: NONE },
    rows: [new TableRow({
      cantSplit: false,
      children: [new TableCell({
        width: { size: PAGE.content, type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, fill: C.void950, color: 'auto' },
        margins: { top: 190, bottom: 190, left: 230, right: 200 },
        borders: { top: NONE, bottom: NONE, left: NONE, right: NONE },
        children: lines.map((l) => new Paragraph({
          style: 'Code',
          children: [new TextRun({ text: l.length ? l : ' ', font: F.mono, size: 15,
            color: l.trim().startsWith('│') || l.trim().startsWith('├')
              || l.trim().startsWith('└') || l.includes('─') ? C.void400 : C.aurora300 })],
        })),
      })],
    })],
  });
}

module.exports = {
  inlineRuns, plain, renderTable, calloutPanel, codeBlock, resolveRefs,
  secAnchor, adrAnchor, chapAnchor, NONE, hair, columnWidths,
};
