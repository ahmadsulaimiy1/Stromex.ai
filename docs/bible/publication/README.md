# The Flagship Edition — Build System

This directory produces the two published editions of the Editorial Bible from the markdown corpus in `docs/bible/`:

| Deliverable | Role |
|---|---|
| **`../StromeX-Editorial-Bible.docx`** | The authoritative master. |
| **`../StromeX-Editorial-Bible.pdf`** | The press-quality edition, generated from the master. Content-identical. |

Both are generated. **Neither is edited by hand** — the corpus is the source of truth, and a change made in the DOCX would be lost on the next build. To change the publication, change the corpus (or this build) and rebuild.

## Build

```bash
cd docs/bible/publication
npm install                 # docx (the only dependency)
python3 make.py ../         # composes, renders, converges, writes both editions
```

Requirements: Node 18+, Python 3.9+ with `pypdfium2`, and LibreOffice with **`libreoffice-writer`** installed (`libreoffice-core` alone cannot open a `.docx`).

## Why the build runs more than once

The lists of tables and figures and the index carry real page numbers, and a page number cannot be known until the document has been laid out. Adding a six-page list of tables also moves every page after it. So `make.py` runs to convergence: compose → render → read the apparatus back off the rendered pages → recompose with it → repeat until the page numbers stop moving. It typically settles in four passes and stops automatically.

## What each file does

| File | Role |
|---|---|
| `build.js` | Composes the DOCX: front matter, volume dividers, executive summaries, the parsed corpus, appendices, glossary, bibliography, index, colophon. |
| `lib/tokens.js` | The design tokens of the printed edition — page geometry, palette, type scale, leading. |
| `lib/md.js` | Markdown → docx. Headings, tables with captions, ASCII figures, lists, block quotes, inline markup, smart quotes, index markers. |
| `lib/editorial.js` | The written matter that exists only in the publication: foreword, founder's message, document control, revision history, per-volume executive summaries, glossary, bibliography. |
| `topdf.py` | Renders the PDF over UNO. `soffice --convert-to pdf` does **not** resolve field-driven apparatus, so the table of contents would export empty; this loads the document, updates every index and field, repaginates, and exports tagged PDF with bookmarks. |
| `make.py` | The convergence loop, and the harvester that reads captions, running heads and index terms off the rendered pages. |
| `apparatus.json` | The harvested apparatus from the last converged run. Committed so a single-pass rebuild reproduces the same page references. |
| `fonts/` | The StromeX brand faces, instanced as static Regular/Bold pairs from the variable originals in `apps/web/public/fonts/`. |

## Typography

The publication uses the four typographic roles defined in Volume I, Chapter 10: a display face, a text face, a sans for tables and navigation, and a monospace for code and architecture figures.

By default the build uses faces that render identically in every environment, so the DOCX and the PDF always agree. To compose in the true brand faces:

```bash
# install the brand faces first, then:
BRAND=1 python3 make.py ../
```

**Known environment issue.** The brand faces in `fonts/` are static instances cut from the variable originals. Some LibreOffice builds refuse instanced variable fonts and silently substitute a fallback — which is worse than a deliberate stand-in, because the substitution is invisible until you inspect the embedded font list. Verify after building:

```bash
python3 -c "import re;raw=open('../StromeX-Editorial-Bible.pdf','rb').read();\
print(sorted(set(n.decode() for n in re.findall(rb'/BaseFont\s*/([A-Za-z0-9+#\-,_]+)',raw))))"
```

If `Archivo` and `Fraunces` do not appear in that list, the fonts did not load and the default set should be used instead. Microsoft Word has no such difficulty: open the DOCX on a machine where the two families are installed and it composes in full brand typography.

## Editing the publication

- **Corpus text** → edit the volume markdown in `docs/bible/`, rebuild.
- **Front matter, executive summaries, glossary, bibliography** → `lib/editorial.js`.
- **Page geometry, palette, type scale** → `lib/tokens.js`.
- **Structure of the publication** (what appears, and in what order) → `build.js`.
- **How markdown becomes typeset matter** → `lib/md.js`.

## Verification

The DOCX is schema-validated on every change:

```bash
python3 /path/to/docx/scripts/office/validate.py ../StromeX-Editorial-Bible.docx
```

The last build validated clean, converged in four passes, and produced 299 pages with a single intentionally blank page — the verso facing the title.
