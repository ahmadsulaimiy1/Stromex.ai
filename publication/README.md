# SpaceTalk Editorial Bible — publication build

Typesets `docs/spacetalk/` into the two distributed editions:

- `dist/SpaceTalk_Editorial_Bible_v1.0.docx` — Microsoft Word, fonts embedded
- `dist/SpaceTalk_Editorial_Bible_v1.0.pdf` — tagged, bookmarked, print-ready

**The content of the two editions cannot diverge.** Both are produced from one
parse of the Markdown source, and the PDF is exported from the DOCX itself
rather than rendered separately.

## Build

```bash
python3 src/parse.py           # Markdown  → build/ir.json
python3 src/build_diagrams.py  # 20 figures → SVG + 430 dpi PNG
python3 src/brandmark.py       # the mark and lockup
python3 src/build.py           # two-pass render → DOCX → PDF
python3 src/verify.py          # 27 pre-flight checks
```

`build.py` runs twice on purpose. The first pass has no page numbers; it is
converted to PDF, the real position of every heading and figure is read back
out of that PDF, and the second pass bakes those folios into the contents, the
part openers and the index. The build asserts that pagination is identical
across the two passes, so the numbers it printed are the numbers it produced.

## Layout

| File | Role |
|---|---|
| `src/parse.py` | Markdown → intermediate representation. Typographer's quotes applied to prose runs only, never to code spans. |
| `src/svgkit.py` | Vector toolkit constrained to the brand — palette, 1.5 px strokes, the radius family, Inter and JetBrains Mono. |
| `src/diagrams_*.py` | The twenty figures. |
| `src/brandmark.py` | The mark, built to the construction rules in Part 1 §1.5. |
| `src/theme.js` · `styles.js` | Page geometry, colour, and the full paragraph/character style hierarchy. |
| `src/content.js` | Blocks, tables, callouts, code panels, and the cross-reference resolver. |
| `src/apparatus.js` · `backmatter.js` | Front matter, editorial devices, appendices, index. |
| `src/render.js` | Document assembly: cover, front matter, 14 parts, back matter. |
| `src/finalize.py` | Unique bookmark ids, embedded typefaces. |
| `src/build.py` | Two-pass orchestration and folio extraction. |
| `src/verify.py` | Pre-flight verification. |

## Cross-references

Source references such as `` `06-TECHNICAL-BIBLE.md` §6.8 ``, `ADR-003`,
`Part 0.6` and bare `§6.10` are rewritten at render time into live internal
links — “Part 6 §6.8” — anchored to a bookmark on the target heading. There are
200 bookmarks and 929 live links; `verify.py` fails the build if any link does
not resolve.

Parts 9 and 12 carry no `N.M` section numbers, so their headings receive stable
synthetic anchors. One shared section index drives the body, the contents, the
part openers and the folio extraction, so those four can never disagree.

## Verification

`verify.py` checks heading levels, folio correctness against the printed page,
link resolution, cross-reference rendering, figure placement and duplication,
table counts, section coverage, verbatim paragraph coverage against the source,
blank pages, PDF tagging and structure tree, bookmark count, font embedding,
text extractability, and widow/orphan control. The DOCX is separately validated
against the OOXML schema.

## Requirements

Node with `docx`; Python with `cairosvg`, `pymupdf`; LibreOffice **Writer**
(`libreoffice-core` alone cannot open a Writer document); Inter, Inter Display
and JetBrains Mono installed for the PDF export.
