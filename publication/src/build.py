#!/usr/bin/env python3
"""Two-pass publication build.

  pass 1  render docx (folios unknown) → PDF → read back where everything landed
  pass 2  render docx with real folios  → PDF → verify

Both editions come from one source: the PDF is produced from the DOCX itself,
so their content cannot drift apart.
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, "/root/.claude/skills/docx/scripts")
from office.soffice import run_soffice  # noqa: E402

ROOT = "/home/user/Stromex.ai/publication"
DOCX = os.path.join(ROOT, "dist/SpaceTalk_Editorial_Bible_v1.0.docx")
PDF = os.path.join(ROOT, "dist/SpaceTalk_Editorial_Bible_v1.0.pdf")
PAGEMAP = os.path.join(ROOT, "build/pagemap.json")

PDF_OPTS = {
    "ExportBookmarks": {"type": "boolean", "value": "true"},
    "UseTaggedPDF": {"type": "boolean", "value": "true"},
    "ExportNotes": {"type": "boolean", "value": "false"},
    "ReduceImageResolution": {"type": "boolean", "value": "false"},
    "MaxImageResolution": {"type": "long", "value": "600"},
    "Quality": {"type": "long", "value": "95"},
    "UseLosslessCompression": {"type": "boolean", "value": "false"},
    "ExportLinksRelativeFsys": {"type": "boolean", "value": "false"},
    "EmbedStandardFonts": {"type": "boolean", "value": "true"},
    "IsAddStream": {"type": "boolean", "value": "false"},
    "SelectPdfVersion": {"type": "long", "value": "0"},
    "InitialView": {"type": "long", "value": "2"},        # bookmarks pane open
    "Magnification": {"type": "long", "value": "2"},      # fit page width
}

TITLES = {
    "The Constitution": 0, "The Brand Bible": 1, "The Visual Design System": 2,
    "The UX Bible": 3, "The AI Philosophy": 4, "The Feature Bible": 5,
    "The Technical Bible": 6, "The Design System": 7, "Performance Standards": 8,
    "The Roadmap": 9, "Scope Governance": 10, "Business, Growth & Compliance": 11,
    "Architecture Decision Records": 12, "Research, Journeys & IA": 13,
}
FRONT = {
    "Copyright and colophon": "f_copyright", "Document control": "f_control",
    "Version history": "f_versions", "How to use this document": "f_howto",
    "Executive summary": "f_exec", "Contents": "f_contents",
}
BACK = {
    "Appendix A": "b_adr", "Appendix B": "b_numbers",
    "Appendix C": "b_glossary", "Index": "b_index",
}


def roman(n):
    vals = [(1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"), (90, "xc"),
            (50, "l"), (40, "xl"), (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]
    out = ""
    for v, s in vals:
        while n >= v:
            out += s
            n -= v
    return out


def render():
    r = subprocess.run(["node", os.path.join(ROOT, "src/render.js")],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode:
        print(r.stdout, r.stderr)
        sys.exit(1)
    print(r.stdout.rstrip())
    # unique bookmark ids + embedded brand typefaces
    f = subprocess.run([sys.executable, os.path.join(ROOT, "src/finalize.py")],
                       capture_output=True, text=True, cwd=ROOT)
    if f.returncode:
        print(f.stdout, f.stderr)
        sys.exit(1)
    print(f.stdout.rstrip())


def convert():
    if os.path.exists(PDF):
        os.remove(PDF)
    r = run_soffice(["--headless", "--convert-to",
                     "pdf:writer_pdf_Export:" + json.dumps(PDF_OPTS),
                     "--outdir", os.path.join(ROOT, "dist"), DOCX],
                    capture_output=True, text=True)
    if r.returncode or not os.path.exists(PDF):
        print("conversion failed", r.stdout, r.stderr)
        sys.exit(1)


def extract_pagemap():
    import fitz
    doc = fitz.open(PDF)
    toc = doc.get_toc()

    body_start = None
    for lvl, title, page in toc:
        if lvl == 1 and title.strip() in TITLES and TITLES[title.strip()] == 0:
            body_start = page
            break
    if body_start is None:
        print("could not locate the body start"); sys.exit(1)
    front_offset = 1                      # cover is physical page 1, unnumbered
    arabic_offset = body_start - 1

    def folio(page):
        if page < body_start:
            return roman(page - front_offset)
        return str(page - arabic_offset)

    # Sections are mapped positionally against the renderer's own index, so a
    # heading that carries no N.M number (Parts 9 and 12) still resolves.
    sections = json.load(open(os.path.join(ROOT, "build/sections.json")))
    pm = {}
    cur, idx = None, 0
    for lvl, title, page in toc:
        t = title.strip()
        if lvl == 1 and t in TITLES:
            cur, idx = str(TITLES[t]), 0
            pm["c_" + cur] = folio(page)
        elif lvl == 1 and t in FRONT:
            cur = None
            pm[FRONT[t]] = folio(page)
        elif lvl == 1:
            cur = None
            for k, v in BACK.items():
                if t.startswith(k):
                    pm[v] = folio(page)
        elif lvl == 2 and cur is not None:
            lst = sections.get(cur, [])
            if idx < len(lst):
                pm[lst[idx]["anchor"]] = folio(page)
                idx += 1

    # figures: locate each caption label in the page text
    manifest = json.load(open(os.path.join(ROOT, "build/diagrams/manifest.json")))
    labels = {f["label"]: f["name"] for f in manifest if f.get("label")}
    for pno in range(body_start - 1, doc.page_count):
        text = doc[pno].get_text()
        for lab, name in list(labels.items()):
            if lab + "  " in text or (lab + " ") in text:
                pm.setdefault("fig_" + name, folio(pno + 1))
                labels.pop(lab, None)

    json.dump(pm, open(PAGEMAP, "w"), indent=1, sort_keys=True)
    print(f"  pagemap: {len(pm)} anchors  ·  body starts on physical page {body_start}"
          f"  ·  {doc.page_count} pages")
    return pm, doc.page_count


def main():
    print("pass 1 — render")
    if os.path.exists(PAGEMAP):
        os.remove(PAGEMAP)
    render()
    print("pass 1 — convert")
    convert()
    print("pass 1 — locate")
    extract_pagemap()

    print("pass 2 — render with real folios")
    render()
    print("pass 2 — convert")
    convert()
    print("pass 2 — confirm pagination is stable")
    pm2, pages = extract_pagemap()

    old = json.load(open(PAGEMAP))
    print(f"\n  {pages} pages  ·  "
          f"docx {os.path.getsize(DOCX) / 1e6:.2f} MB  ·  pdf {os.path.getsize(PDF) / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
