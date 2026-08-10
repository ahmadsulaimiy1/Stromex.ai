# EdirasX publisher

Builds the flagship Editorial Bible in PDF and Word from the canonical Markdown.

```bash
python publish.py   # build both artefacts
python verify.py    # re-check the finished files
```

Both must pass before a publication is released (`EDTECHX_DECISIONS.md` ADR-018).

## Why it works this way

One document model, rendered twice. Content parity between the PDF and the Word
file is therefore a property of the build rather than a claim made afterwards —
and `verify.py` re-extracts text from the *finished files* and checks it anyway,
because a shared model is a good reason to expect parity, not evidence of it.

```
EDTECHX_EDITORIAL_BIBLE.md   canonical, editable, the only place to make changes
        │
     bible.py                parse + publication apparatus (parts, callouts, figures)
        │
     model.py                Document → Chapter → Block → Run
        ├── render_pdf.py    HTML + print CSS → WeasyPrint
        └── render_docx.py   python-docx, real outline levels, TOC field
        │
     verify.py               re-extracts from the built files and checks
```

## Files

| File | Role |
|---|---|
| `model.py` | Document model, Markdown parsing, typographic quotes |
| `bible.py` | Builds the model; adds front matter, parts, callouts, diagrams |
| `render_pdf.py` | Print rendering, cover, running heads, contents |
| `render_docx.py` | Word rendering |
| `diagrams.py` | The two SVG figures (vector in PDF, rasterised for Word) |
| `verify.py` | Independent verification |
| `assets/style.css` | Print stylesheet |
| `assets/fonts/` | Source Serif 4, Inter, IBM Plex Mono, Amiri — all open-licence |

## What the verifier checks

- Every chapter present in both formats
- Every substantial line of source prose present in both
- Every document sentence present in both
- No unintended font fallback in the PDF
- No blank pages, correct metadata, Word outline levels for navigation
- The Arabic in Chapter 1 and the note on the name is actually set
- Named non-negotiables ("cross-tenant data access path", WCAG 2.2 AA, …) survived

It is deliberately hard to satisfy by accident. Dropping a chapter fails the
build before verification even runs.

## Two things that are easy to get wrong

**Text comparison must be whitespace- and hyphen-insensitive.** A justified line
break inside a hyphenated word extracts from a PDF as `school man agement` —
hyphen *and* space. Any comparison preserving either reports false misses.

**Bidirectional text extracts out of order.** `الدراسة (al-dirāsa` comes back as
`( الدراسةal-dirāsa`. The page is correct; only the extraction order differs.
Arabic characters and surrounding brackets are stripped before comparison, and
the Arabic is verified separately by exact match.
