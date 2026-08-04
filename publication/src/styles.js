/* Paragraph and character styles — the document's full typographic hierarchy. */
const { AlignmentType, LevelFormat, convertInchesToTwip } = require('/tmp/node_modules/docx');
const { C, F } = require('./theme');

const BODY_SIZE = 21;        // half-points → 10.5 pt
const BODY_LINE = 288;       // twips → 14.4 pt leading (1.37)

const paragraphStyles = [
  // ---------------------------------------------------------------- display
  { id: 'CoverTitle', name: 'Cover Title', basedOn: 'Normal', quickFormat: true,
    run: { font: F.display, size: 92, bold: true, color: C.void0 },
    paragraph: { spacing: { before: 0, after: 200, line: 960, lineRule: 'atLeast' } } },
  { id: 'CoverSub', name: 'Cover Subtitle', basedOn: 'Normal',
    run: { font: F.ui, size: 26, color: C.orbit200 },
    paragraph: { spacing: { before: 0, after: 120, line: 380, lineRule: 'atLeast' } } },
  { id: 'CoverMeta', name: 'Cover Meta', basedOn: 'Normal',
    run: { font: F.mono, size: 17, color: C.orbit300, characterSpacing: 24 },
    paragraph: { spacing: { before: 0, after: 90, line: 300, lineRule: 'atLeast' } } },
  { id: 'CoverRule', name: 'Cover Rule', basedOn: 'Normal',
    run: { size: 2 }, paragraph: { spacing: { before: 240, after: 240 },
      border: { bottom: { style: 'single', size: 12, color: C.orbit600, space: 1 } } } },

  { id: 'TitlePageTitle', name: 'Title Page Title', basedOn: 'Normal',
    run: { font: F.display, size: 64, bold: true, color: C.void900 },
    paragraph: { spacing: { before: 0, after: 160, line: 720, lineRule: 'atLeast' } } },
  { id: 'TitlePageSub', name: 'Title Page Subtitle', basedOn: 'Normal',
    run: { font: F.ui, size: 24, color: C.void600 },
    paragraph: { spacing: { before: 0, after: 120, line: 340, lineRule: 'atLeast' } } },

  // ---------------------------------------------------------------- chapter
  { id: 'ChapterKicker', name: 'Chapter Kicker', basedOn: 'Normal',
    run: { font: F.ui, size: 17, bold: true, color: C.orbit600, characterSpacing: 44 },
    paragraph: { spacing: { before: 0, after: 100 } } },
  { id: 'ChapterNumber', name: 'Chapter Number', basedOn: 'Normal',
    run: { font: F.display, size: 150, bold: true, color: C.orbit100 },
    paragraph: { spacing: { before: 0, after: 0, line: 1500, lineRule: 'atLeast' } } },
  { id: 'ChapterTitle', name: 'Chapter Title', basedOn: 'Normal', next: 'Body',
    quickFormat: true,
    run: { font: F.display, size: 56, bold: true, color: C.void900 },
    paragraph: { spacing: { before: 60, after: 140, line: 640, lineRule: 'atLeast' },
      keepNext: true, outlineLevel: 0 } },
  { id: 'ChapterLabel', name: 'Chapter Label', basedOn: 'Normal',
    run: { font: F.ui, size: 21, color: C.orbit700 },
    paragraph: { spacing: { before: 0, after: 260 },
      border: { bottom: { style: 'single', size: 8, color: C.orbit200, space: 8 } } } },
  { id: 'Standfirst', name: 'Standfirst', basedOn: 'Normal',
    run: { font: F.ui, size: 23, color: C.void600, italics: true },
    paragraph: { spacing: { before: 200, after: 200, line: 330, lineRule: 'atLeast' } } },
  { id: 'InThisPart', name: 'In This Part', basedOn: 'Normal',
    run: { font: F.ui, size: 19, color: C.void700 },
    paragraph: { spacing: { before: 0, after: 60, line: 260, lineRule: 'atLeast' },
      indent: { left: 260, hanging: 260 } } },

  // ---------------------------------------------------------------- headings
  { id: 'H1', name: 'Section Heading', basedOn: 'Normal', next: 'Body', quickFormat: true,
    run: { font: F.display, size: 30, bold: true, color: C.void900 },
    paragraph: { spacing: { before: 380, after: 130, line: 340, lineRule: 'atLeast' },
      keepNext: true, keepLines: true, outlineLevel: 1 } },
  { id: 'H2', name: 'Sub Heading', basedOn: 'Normal', next: 'Body', quickFormat: true,
    run: { font: F.ui, size: 23, bold: true, color: C.orbit700 },
    paragraph: { spacing: { before: 280, after: 90, line: 300, lineRule: 'atLeast' },
      keepNext: true, keepLines: true, outlineLevel: 2 } },
  { id: 'H3', name: 'Minor Heading', basedOn: 'Normal', next: 'Body',
    run: { font: F.ui, size: 21, bold: true, color: C.void700 },
    paragraph: { spacing: { before: 200, after: 70 }, keepNext: true, outlineLevel: 3 } },
  { id: 'FrontHeading', name: 'Front Matter Heading', basedOn: 'Normal', next: 'Body',
    run: { font: F.display, size: 40, bold: true, color: C.void900 },
    paragraph: { spacing: { before: 0, after: 220, line: 460, lineRule: 'atLeast' },
      keepNext: true, outlineLevel: 0 } },

  // ---------------------------------------------------------------- body
  { id: 'Body', name: 'Body', basedOn: 'Normal', next: 'Body', quickFormat: true,
    run: { font: F.ui, size: BODY_SIZE, color: C.void900 },
    paragraph: { spacing: { before: 0, after: 150, line: BODY_LINE, lineRule: 'atLeast' },
      alignment: AlignmentType.LEFT, widowControl: true } },
  { id: 'BodyTight', name: 'Body Tight', basedOn: 'Body',
    paragraph: { spacing: { before: 0, after: 60, line: BODY_LINE, lineRule: 'atLeast' }, widowControl: true } },
  { id: 'Bullet', name: 'Bullet', basedOn: 'Body',
    paragraph: { spacing: { before: 0, after: 80, line: BODY_LINE, lineRule: 'atLeast' },
      indent: { left: 340, hanging: 200 }, widowControl: true } },
  { id: 'Bullet2', name: 'Bullet Level 2', basedOn: 'Bullet',
    paragraph: { spacing: { before: 0, after: 70, line: BODY_LINE, lineRule: 'atLeast' },
      indent: { left: 660, hanging: 200 }, widowControl: true } },

  // ---------------------------------------------------------------- devices
  { id: 'Caption', name: 'Caption', basedOn: 'Normal', quickFormat: true,
    run: { font: F.ui, size: 17, color: C.void500 },
    paragraph: { spacing: { before: 100, after: 260, line: 240, lineRule: 'atLeast' }, keepLines: true } },
  { id: 'FigureImage', name: 'Figure Image', basedOn: 'Normal',
    paragraph: { spacing: { before: 200, after: 0 }, alignment: AlignmentType.LEFT,
      keepNext: true, keepLines: true } },
  { id: 'PullQuote', name: 'Pull Quote', basedOn: 'Normal',
    run: { font: F.display, size: 30, color: C.orbit800 },
    paragraph: { spacing: { before: 240, after: 240, line: 400, lineRule: 'atLeast' },
      indent: { left: 300 }, keepLines: true,
      border: { left: { style: 'single', size: 18, color: C.orbit500, space: 14 } } } },
  { id: 'CalloutTitle', name: 'Callout Title', basedOn: 'Normal',
    run: { font: F.ui, size: 20, bold: true, color: C.orbit700 },
    paragraph: { spacing: { before: 0, after: 70, line: 260, lineRule: 'atLeast' }, keepNext: true } },
  { id: 'CalloutBody', name: 'Callout Body', basedOn: 'Normal',
    run: { font: F.ui, size: 19, color: C.void800 },
    paragraph: { spacing: { before: 0, after: 0, line: 264, lineRule: 'atLeast' } } },
  { id: 'Code', name: 'Code Block', basedOn: 'Normal',
    run: { font: F.mono, size: 15, color: C.aurora300 },
    paragraph: { spacing: { before: 0, after: 0, line: 210, lineRule: 'atLeast' }, keepLines: true } },
  { id: 'Kicker', name: 'Kicker', basedOn: 'Normal',
    run: { font: F.ui, size: 15, bold: true, color: C.orbit600, characterSpacing: 34 },
    paragraph: { spacing: { before: 0, after: 90 } } },
  { id: 'Rule', name: 'Section Rule', basedOn: 'Normal',
    run: { size: 2 },
    paragraph: { spacing: { before: 130, after: 190 },
      border: { bottom: { style: 'single', size: 4, color: C.void200, space: 1 } } } },

  // ---------------------------------------------------------------- tables
  { id: 'TableHead', name: 'Table Head', basedOn: 'Normal',
    run: { font: F.ui, size: 17, bold: true, color: C.void0 },
    paragraph: { spacing: { before: 40, after: 40, line: 230, lineRule: 'atLeast' }, widowControl: true } },
  { id: 'TableCell', name: 'Table Cell', basedOn: 'Normal',
    run: { font: F.ui, size: 17, color: C.void800 },
    paragraph: { spacing: { before: 40, after: 40, line: 234, lineRule: 'atLeast' }, widowControl: true } },
  { id: 'TableCellTight', name: 'Table Cell Tight', basedOn: 'TableCell',
    paragraph: { spacing: { before: 30, after: 30, line: 226, lineRule: 'atLeast' } } },

  // ---------------------------------------------------------------- TOC
  { id: 'TocChapter', name: 'TOC Chapter', basedOn: 'Normal',
    run: { font: F.ui, size: 21, bold: true, color: C.void900 },
    paragraph: { spacing: { before: 170, after: 40, line: 260, lineRule: 'atLeast' } } },
  { id: 'TocSection', name: 'TOC Section', basedOn: 'Normal',
    run: { font: F.ui, size: 18, color: C.void600 },
    paragraph: { spacing: { before: 0, after: 20, line: 250, lineRule: 'atLeast' }, indent: { left: 300 } } },
  { id: 'TocFront', name: 'TOC Front', basedOn: 'Normal',
    run: { font: F.ui, size: 19, color: C.void700 },
    paragraph: { spacing: { before: 0, after: 40, line: 250, lineRule: 'atLeast' } } },
  { id: 'IndexEntry', name: 'Index Entry', basedOn: 'Normal',
    run: { font: F.ui, size: 17, color: C.void800 },
    paragraph: { spacing: { before: 0, after: 26, line: 236, lineRule: 'atLeast' },
      indent: { left: 240, hanging: 240 } } },
  { id: 'IndexLetter', name: 'Index Letter', basedOn: 'Normal',
    run: { font: F.display, size: 22, bold: true, color: C.orbit600 },
    paragraph: { spacing: { before: 180, after: 70 }, keepNext: true } },
];

const characterStyles = [
  { id: 'CodeChar', name: 'Code Char', run: { font: F.mono, size: 18, color: C.orbit800 } },
  { id: 'LinkChar', name: 'Link Char', run: { color: C.orbit600, underline: {} } },
  { id: 'XrefChar', name: 'Xref Char', run: { color: C.orbit600 } },
];

const numbering = {
  config: [
    { reference: 'st-bullet', levels: [
      { level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 340, hanging: 200 } },
          run: { color: C.orbit500, font: F.ui } } },
      { level: 1, format: LevelFormat.BULLET, text: '–', alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 660, hanging: 200 } },
          run: { color: C.void400, font: F.ui } } },
    ] },
    { reference: 'st-number', levels: [
      { level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 340, hanging: 240 } },
          run: { color: C.orbit600, bold: true, font: F.ui } } },
      { level: 1, format: LevelFormat.LOWER_LETTER, text: '%2.', alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 660, hanging: 240 } },
          run: { color: C.void500, font: F.ui } } },
    ] },
  ],
};

module.exports = {
  styles: {
    default: {
      document: { run: { font: F.ui, size: BODY_SIZE, color: C.void900 },
        paragraph: { spacing: { line: BODY_LINE, lineRule: 'atLeast' }, widowControl: true } },
    },
    paragraphStyles, characterStyles,
  },
  numbering,
};
