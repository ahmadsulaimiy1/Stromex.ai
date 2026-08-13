'use strict';
/* Markdown → docx element conversion for the StromeX Editorial Bible.
   Deliberately supports only the subset the corpus actually uses. */

const {
  Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  BorderStyle, HeadingLevel, AlignmentType, ExternalHyperlink, SimpleField,
  VerticalAlign,
} = require('docx');

const T = require('./tokens');

// ── inline ────────────────────────────────────────────────────────────────
// Handles **bold**, *italic*, `code`, [text](url), and bare entities.
function inline(text, base = {}) {
  const runs = [];
  // Tokenise on link | code | bold | italic, in that precedence order.
  const re = /(\[([^\]]+)\]\(([^)]+)\))|(`([^`]+)`)|(\*\*([^*]+)\*\*)|(\*([^*]+)\*)/g;
  let last = 0, m;
  const push = (t, opt) => { if (t) runs.push(new TextRun({ text: t, ...base, ...opt })); };

  while ((m = re.exec(text)) !== null) {
    push(clean(text.slice(last, m.index)));
    if (m[1]) {
      const label = clean(m[2]), url = m[3];
      if (/^https?:/i.test(url)) {
        runs.push(new ExternalHyperlink({
          link: url,
          children: [new TextRun({ text: label, ...base, style: 'Hyperlink' })],
        }));
      } else {
        push(label); // internal .md links become plain text in print
      }
    } else if (m[4]) {
      push(clean(m[5]), { font: T.font.mono, size: base.size ? base.size - 2 : 17, color: T.color.depth });
    } else if (m[6]) {
      push(clean(m[7]), { bold: true });
    } else if (m[8]) {
      push(clean(m[9]), { italics: true });
    }
    last = re.lastIndex;
  }
  push(clean(text.slice(last)));
  return runs.length ? runs : [new TextRun({ text: '', ...base })];
}

function titleCase(s) {
  if (s !== s.toUpperCase()) return s;
  const small = new Set(['a','an','and','the','of','for','to','in','on','at','by','or','vs','with']);
  return s.toLowerCase().split(/(\s+|[—–-])/).map((w, i) => {
    if (!/[a-z]/.test(w)) return w;
    if (i > 0 && small.has(w)) return w;
    return w.charAt(0).toUpperCase() + w.slice(1);
  }).join('');
}

function clean(s) {
  return s
    .replace(/&mdash;/g, '—').replace(/&ndash;/g, '–')
    .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&')
    .replace(/&rsquo;/g, '’').replace(/&lsquo;/g, '‘')
    .replace(/&ldquo;/g, '“').replace(/&rdquo;/g, '”')
    .replace(/&times;/g, '×').replace(/&hellip;/g, '…')
    .replace(/\\([\\`*_{}[\]()#+\-.!])/g, '$1')
    // typographic quotes: publication standard, applied last so markup is gone
    .replace(/(^|[\s([{<\u2014\u2013\/])"/g, '$1\u201C')
    .replace(/"/g, '\u201D')
    .replace(/(^|[\s([{<\u2014\u2013])'/g, '$1\u2018')
    .replace(/(\d)'/g, '$1\u2032')
    .replace(/'/g, '\u2019');
}

// ── table ─────────────────────────────────────────────────────────────────
function splitRow(line) {
  return line.replace(/^\s*\|/, '').replace(/\|\s*$/, '').split('|').map(c => c.trim());
}

function alignOf(spec) {
  const s = spec.trim();
  if (s.startsWith(':') && s.endsWith(':')) return AlignmentType.CENTER;
  if (s.endsWith(':')) return AlignmentType.RIGHT;
  return AlignmentType.LEFT;
}

function buildTable(rows, aligns, opts = {}) {
  const width = opts.width || T.page.contentWidth;
  const n = rows[0].length;

  // Column widths: first column gets more room when the table is a definition
  // list (2 cols) or a keyed matrix; otherwise distribute evenly.
  let cols;
  if (opts.columnWidths) {
    cols = opts.columnWidths;
  } else if (n === 2) {
    cols = [Math.round(width * 0.34), width - Math.round(width * 0.34)];
  } else if (n === 3) {
    cols = [Math.round(width * 0.26), Math.round(width * 0.37), 0];
    cols[2] = width - cols[0] - cols[1];
  } else {
    const each = Math.floor(width / n);
    cols = Array(n).fill(each);
    cols[n - 1] = width - each * (n - 1);
  }

  const hair = { style: BorderStyle.SINGLE, size: 2, color: T.color.rule };
  const none = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
  const head = { style: BorderStyle.SINGLE, size: 8, color: T.color.depth };

  const mkCell = (txt, i, isHead, zebra) => {
    const align = aligns[i] || AlignmentType.LEFT;
    const runs = inline(txt, {
      font: T.font.ui,
      size: isHead ? 15 : 16,
      color: isHead ? 'FFFFFF' : T.color.ink,
      bold: isHead || undefined,
      allCaps: isHead || undefined,
    });
    return new TableCell({
      width: { size: cols[i], type: WidthType.DXA },
      margins: { top: isHead ? 90 : 80, bottom: isHead ? 90 : 80, left: 110, right: 110 },
      shading: isHead
        ? { type: ShadingType.CLEAR, fill: T.color.depth, color: 'auto' }
        : { type: ShadingType.CLEAR, fill: zebra ? T.color.zebra : 'FFFFFF', color: 'auto' },
      borders: { top: isHead ? none : hair, bottom: isHead ? head : hair, left: none, right: none },
      verticalAlign: VerticalAlign.TOP,
      children: [new Paragraph({
        alignment: align,
        spacing: { before: 0, after: 0, line: 250 },
        children: runs,
      })],
    });
  };

  const trs = rows.map((cells, r) => new TableRow({
    tableHeader: r === 0,
    cantSplit: false,
    children: Array.from({ length: n }, (_, i) =>
      mkCell(cells[i] === undefined ? '' : cells[i], i, r === 0, r > 0 && r % 2 === 0)),
  }));

  return new Table({
    columnWidths: cols,
    width: { size: width, type: WidthType.DXA },
    layout: 'fixed',
    rows: trs,
  });
}

// ── caption ───────────────────────────────────────────────────────────────
function caption(kind, text) {
  return new Paragraph({
    style: 'Caption',
    keepNext: kind === 'Figure' ? false : false,
    children: [
      new TextRun({ text: `${kind} `, bold: true, color: T.color.depth }),
      new SimpleField(`SEQ ${kind} \\* ARABIC`),
      new TextRun({ text: ` — `, color: T.color.depth }),
      ...inline(text, { size: 15, color: T.color.graphite }),
    ],
  });
}

// ── diagram (fenced code that is really an ASCII figure) ──────────────────
function diagramBlock(lines, cap) {
  const body = new Table({
    columnWidths: [T.page.contentWidth],
    width: { size: T.page.contentWidth, type: WidthType.DXA },
    layout: 'fixed',
    rows: [new TableRow({
      children: [new TableCell({
        width: { size: T.page.contentWidth, type: WidthType.DXA },
        margins: { top: 160, bottom: 160, left: 180, right: 140 },
        shading: { type: ShadingType.CLEAR, fill: T.color.sunk, color: 'auto' },
        borders: {
          top: { style: BorderStyle.SINGLE, size: 2, color: T.color.rule },
          bottom: { style: BorderStyle.SINGLE, size: 2, color: T.color.rule },
          left: { style: BorderStyle.SINGLE, size: 12, color: T.color.accent },
          right: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' },
        },
        children: lines.map(l => new Paragraph({
          spacing: { before: 0, after: 0, line: 230 },
          children: [new TextRun({ text: l.replace(/\t/g, '  ') || ' ', font: T.font.mono, size: 14, color: T.color.ink })],
        })),
      })],
    })],
  });
  return cap ? [body, caption('Figure', cap)] : [body];
}

// ── code (real code / config) ─────────────────────────────────────────────
function codeBlock(lines) {
  return lines.map((l, i) => new Paragraph({
    style: 'CodeBlock',
    spacing: { before: i === 0 ? 120 : 0, after: i === lines.length - 1 ? 160 : 0, line: 230 },
    children: [new TextRun({ text: l || ' ', font: T.font.mono, size: 15 })],
  }));
}

// ── index markers ─────────────────────────────────────────────────────────
// Emits Word XE fields so the INDEX field in the back matter resolves. A term
// is marked once per chapter, at the heading where it is discussed — an index
// that points at every mention is an index nobody uses.
function indexFields(text, opts, marked) {
  if (!opts.indexTerms || !opts.indexTerms.length) return [];
  const fields = [];
  const hay = text.toLowerCase();
  for (const term of opts.indexTerms) {
    if (marked.has(term)) continue;
    const t = term.toLowerCase();
    if (hay.length > 120) continue;
    if (!hay.includes(t)) continue;
    marked.add(term);
    fields.push(new SimpleField(`XE "${term.replace(/"/g, '')}"`));
    if (fields.length >= 3) break;
  }
  return fields;
}

// ── block parser ──────────────────────────────────────────────────────────
// opts: { headingOffset, chapterLevel, indexTerms, tableCaption(fn),
//         figureCaption(fn), onHeading(fn), onTable(fn), onFigure(fn) }
function parse(md, opts = {}) {
  const out = [];
  const lines = md.split('\n');
  let i = 0;
  let ctx = opts.startContext || '';
  let sectionCtx = '';
  const capCtx = () => sectionCtx || ctx;
  const marked = new Set();

  const H = [HeadingLevel.HEADING_1, HeadingLevel.HEADING_2, HeadingLevel.HEADING_3,
             HeadingLevel.HEADING_4, HeadingLevel.HEADING_5];

  while (i < lines.length) {
    let line = lines[i];

    // blank
    if (!line.trim()) { i++; continue; }

    // horizontal rule → a hairline, not a page break
    if (/^\s*---+\s*$/.test(line) || /^\s*\*\*\*+\s*$/.test(line)) {
      out.push(new Paragraph({
        spacing: { before: 160, after: 200 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: T.color.rule, space: 1 } },
        children: [new TextRun('')],
      }));
      i++; continue;
    }

    // heading
    const h = line.match(/^(#{1,6})\s+(.*)$/);
    if (h) {
      const depth = h[1].length;
      let txt = h[2].trim().replace(/\s*\{#.*\}$/, '');
      const lvl = Math.min(depth + (opts.headingOffset || 0), 5);
      const chapterLevel = opts.chapterLevel || 1;
      const isChapter = lvl === chapterLevel;
      if (isChapter) {
        ctx = titleCase(txt.replace(/^(CHAPTER|DIVISION)\s+[\dIVX]+\s*[—-]\s*/i, ''));
        sectionCtx = ''; marked.clear();
      } else if (lvl === chapterLevel + 1) {
        sectionCtx = txt.replace(/^[\d.]+\s+/, '').replace(/\*\*/g, '');
      }
      if (opts.onHeading) opts.onHeading(lvl, txt);
      out.push(new Paragraph({
        heading: H[lvl - 1],
        pageBreakBefore: isChapter && opts.chapterBreaks !== false,
        children: inline(txt).concat(indexFields(txt, opts, marked)),
      }));
      i++; continue;
    }

    // fenced block
    if (/^\s*```/.test(line)) {
      const buf = [];
      i++;
      while (i < lines.length && !/^\s*```/.test(lines[i])) { buf.push(lines[i]); i++; }
      i++;
      while (buf.length && !buf[0].trim()) buf.shift();
      while (buf.length && !buf[buf.length - 1].trim()) buf.pop();
      const looksDiagram = buf.some(l => /[│┌└├─┐┘┬┴┼┤↓→←↑]/.test(l)) || buf.some(l => /^\s*\d+\s*│/.test(l));
      if (looksDiagram) {
        if (opts.onFigure) opts.onFigure();
        out.push(...diagramBlock(buf, opts.figureCaption ? opts.figureCaption(capCtx()) : capCtx()));
      } else out.push(...codeBlock(buf));
      continue;
    }

    // table
    if (/^\s*\|/.test(line) && i + 1 < lines.length && /^\s*\|[\s:|-]+\|?\s*$/.test(lines[i + 1])) {
      const header = splitRow(line);
      const aligns = splitRow(lines[i + 1]).map(alignOf);
      const rows = [header];
      i += 2;
      while (i < lines.length && /^\s*\|/.test(lines[i])) { rows.push(splitRow(lines[i])); i++; }
      if (opts.onTable) opts.onTable();
      out.push(buildTable(rows, aligns));
      out.push(caption('Table', opts.tableCaption ? opts.tableCaption(capCtx()) : capCtx()));
      continue;
    }

    // blockquote (may span lines)
    if (/^\s*>/.test(line)) {
      const buf = [];
      while (i < lines.length && /^\s*>/.test(lines[i])) {
        buf.push(lines[i].replace(/^\s*>\s?/, '')); i++;
      }
      const text = buf.join('\n').split(/\n{2,}/).filter(s => s.trim());
      text.forEach((para, k) => {
        const t = para.replace(/\n/g, ' ').trim();
        const hh = t.match(/^(#{1,6})\s+(.*)$/);
        out.push(new Paragraph({
          style: 'PullQuote',
          spacing: { before: k === 0 ? 200 : 60, after: k === text.length - 1 ? 220 : 60 },
          children: inline(hh ? hh[2] : t, hh ? { bold: true } : {}),
        }));
      });
      continue;
    }

    // list
    const li = line.match(/^(\s*)([-*+]|\d+\.)\s+(.*)$/);
    if (li) {
      while (i < lines.length) {
        const m2 = lines[i].match(/^(\s*)([-*+]|\d+\.)\s+(.*)$/);
        if (!m2) {
          // lazy continuation
          if (lines[i].trim() && !/^\s*(#{1,6}\s|\||```|>)/.test(lines[i]) && out.length) {
            const prev = out[out.length - 1];
            if (prev && prev.__isListItem) { prev.__extra = (prev.__extra || '') + ' ' + lines[i].trim(); i++; continue; }
          }
          break;
        }
        const indent = Math.min(Math.floor(m2[1].length / 2), 2);
        const ordered = /\d/.test(m2[2]);
        const p = new Paragraph({
          numbering: { reference: ordered ? 'bible-ol' : 'bible-ul', level: indent },
          spacing: { before: 40, after: 40, line: 276 },
          children: inline(m2[3]),
        });
        p.__isListItem = true;
        out.push(p);
        i++;
      }
      continue;
    }

    // paragraph (gather until blank / block start)
    const buf = [];
    while (i < lines.length && lines[i].trim() &&
           !/^\s*(#{1,6}\s|\||```|>|---+\s*$)/.test(lines[i]) &&
           !/^(\s*)([-*+]|\d+\.)\s+/.test(lines[i])) {
      buf.push(lines[i].trim()); i++;
    }
    if (buf.length) {
      const text = buf.join(' ');
      // a paragraph that is entirely italic reads as an editorial note
      const noteM = text.match(/^\*([^*].*[^*])\*$/);
      out.push(new Paragraph({
        style: noteM ? 'EditorialNote' : 'BodyText',
        children: inline(noteM ? noteM[1] : text),
      }));
    }
  }
  return out;
}

module.exports = { parse, inline, buildTable, caption, diagramBlock, clean };
