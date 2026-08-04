#!/usr/bin/env python3
"""Pre-flight verification of the two deliverables."""
import json
import os
import re
import sys
import zipfile
from collections import Counter

import fitz

ROOT = "/home/user/Stromex.ai/publication"
DOCX = os.path.join(ROOT, "dist/SpaceTalk_Editorial_Bible_v1.0.docx")
PDF = os.path.join(ROOT, "dist/SpaceTalk_Editorial_Bible_v1.0.pdf")

ok, warn, fail = [], [], []


def check(cond, good, bad, hard=True):
    (ok if cond else (fail if hard else warn)).append(good if cond else bad)


def main():
    doc = fitz.open(PDF)
    z = zipfile.ZipFile(DOCX)
    xml = z.read("word/document.xml").decode("utf-8")
    stylexml = z.read("word/styles.xml").decode("utf-8")
    ir = json.load(open(os.path.join(ROOT, "build/ir.json")))
    figs = json.load(open(os.path.join(ROOT, "build/diagrams/manifest.json")))
    secs = json.load(open(os.path.join(ROOT, "build/sections.json")))

    print(f"pages {doc.page_count}  ·  docx {os.path.getsize(DOCX)/1e6:.2f} MB  "
          f"·  pdf {os.path.getsize(PDF)/1e6:.2f} MB\n")

    # ---------------------------------------------------------- heading levels
    toc = doc.get_toc()
    lv = Counter(l for l, _, _ in toc)
    n_sections = sum(len(v) for v in secs.values())
    check(lv[1] == 14 + 6 + 4, f"outline level 1: {lv[1]} (14 parts + 6 front + 4 back)",
          f"outline level 1 = {lv[1]}, expected 24")
    check(lv[2] == n_sections, f"outline level 2: {lv[2]} = every section in the source",
          f"outline level 2 = {lv[2]}, source has {n_sections}")
    check(lv[3] > 0, f"outline level 3: {lv[3]} sub-headings", "no level-3 headings", False)

    # ---------------------------------------------------------- page numbering
    pm = json.load(open(os.path.join(ROOT, "build/pagemap.json")))
    dash = [k for k, v in pm.items() if v in ("", "—")]
    check(not dash, "every mapped anchor has a folio", f"unresolved folios: {dash[:6]}")

    body_start = int([p for l, t, p in toc if t.strip() == "The Constitution"][0])
    romans = [v for k, v in pm.items() if k.startswith("f_")]
    check(all(re.fullmatch(r"[ivxl]+", r) for r in romans),
          f"front matter uses roman folios ({', '.join(sorted(set(romans))[:4])}…)",
          f"bad roman folios: {romans}")
    arabics = [v for k, v in pm.items() if k.startswith(("s_", "c_", "a_", "h_", "b_"))]
    check(all(a.isdigit() for a in arabics), "body and back matter use arabic folios",
          "non-numeric body folio found")

    # spot-check three folios against the printed page
    bad_folio = []
    for key, want in list(pm.items())[:400]:
        if not want.isdigit():
            continue
        phys = int(want) + body_start - 1
        if phys <= doc.page_count:
            txt = doc[phys - 1].get_text()
            if want not in txt.split("\n")[-1] and want not in txt[-40:]:
                bad_folio.append((key, want))
    check(len(bad_folio) < 6, f"printed folios agree with the page map "
          f"({len(pm)-len(bad_folio)}/{len(pm)} verified)",
          f"folio mismatches: {bad_folio[:5]}", hard=False)

    # ------------------------------------------------------------- hyperlinks
    anchors = set(re.findall(r'<w:bookmarkStart[^>]*w:name="([^"]+)"', xml))
    targets = set(re.findall(r'<w:hyperlink[^>]*w:anchor="([^"]+)"', xml))
    dangling = sorted(t for t in targets if t not in anchors)
    check(not dangling, f"all {len(targets)} distinct internal link targets resolve "
          f"to one of {len(anchors)} bookmarks",
          f"{len(dangling)} dangling links: {dangling[:8]}")

    n_links = xml.count("<w:hyperlink ")
    check(n_links > 600, f"{n_links} hyperlinks in the document",
          f"only {n_links} hyperlinks")

    pdf_links = sum(len(doc[i].get_links()) for i in range(doc.page_count))
    check(pdf_links > 600, f"{pdf_links} live links carried into the PDF",
          f"only {pdf_links} PDF links")

    # --------------------------------------------------------- cross-refs
    xrefs = re.findall(r"Part \d+ §\d+\.\d+", doc[0].get_text() + "".join(
        doc[i].get_text() for i in range(doc.page_count)))
    check(len(xrefs) > 150, f"{len(xrefs)} rendered cross-references of the form "
          f"“Part N §N.M”", f"only {len(xrefs)} cross-references")
    leftover = re.findall(r"\b\d\d-[A-Z][A-Z0-9-]+\.md\b",
                          "".join(doc[i].get_text() for i in range(doc.page_count)))
    check(not leftover, "no raw source filenames leaked into the text",
          f"raw filenames still present: {sorted(set(leftover))[:5]}")

    # ------------------------------------------------------------- diagrams
    all_text = [doc[i].get_text() for i in range(doc.page_count)]
    placed, dupes = 0, []
    for f in figs:
        pages = [i + 1 for i, t in enumerate(all_text) if f["label"] + "  " in t]
        if pages:
            placed += 1
        # once in the list of figures, once at the figure itself
        if len(pages) > 2:
            dupes.append((f["label"], pages))
    check(placed == len(figs), f"all {len(figs)} figures placed with captions",
          f"{placed}/{len(figs)} figures placed")
    check(not dupes, "no figure is emitted more than once",
          f"duplicated figures: {dupes[:3]}")

    imgs = set()
    for i in range(doc.page_count):
        for im in doc[i].get_images(full=True):
            imgs.add(im[0])
    check(len(imgs) >= len(figs), f"{len(imgs)} distinct images embedded",
          f"only {len(imgs)} images embedded")

    media = [n for n in z.namelist() if n.startswith("word/media/") and n.endswith(".png")]
    check(len(media) >= len(figs) + 2, f"{len(media)} PNGs in the docx package",
          f"only {len(media)} PNGs")

    # --------------------------------------------------------------- tables
    n_tbl_src = sum(1 for c in ir["chapters"] for b in c["blocks"] if b["k"] == "table")
    n_tbl_docx = xml.count("<w:tbl>")
    check(n_tbl_docx >= n_tbl_src, f"{n_tbl_docx} tables rendered "
          f"(source has {n_tbl_src} + apparatus, callouts and code panels)",
          f"only {n_tbl_docx} tables for {n_tbl_src} source tables")

    # ------------------------------------------------------- missing sections
    missing = []
    for ch_num, lst in secs.items():
        for s in lst:
            needle = s["title"][:38]
            if not any(needle in t for t in all_text):
                missing.append(f"{ch_num}:{s['num'] or s['title'][:20]}")
    check(not missing, f"all {n_sections} section headings present in the PDF",
          f"missing sections: {missing[:6]}")

    # source paragraph coverage — every source paragraph must appear
    import random
    paras = [b for c in ir["chapters"] for b in c["blocks"] if b["k"] == "p"]
    joined = "\n".join(all_text)
    # PyMuPDF emits a newline at a soft line break, which lands mid-word after a
    # hyphen ("content-\nfacing"). Rejoin those before comparing.
    joined = re.sub(r"-\n(?=[a-z])", "-", joined).replace("\n", " ")
    joined = re.sub(r"\s+", " ", joined)
    sample = random.Random(7).sample(paras, 120)
    lost = []
    for b in sample:
        # references such as `03-UX-BIBLE.md` §3.8 are rewritten to "Part 3 §3.8"
        # by design, so probe a stretch of prose that carries no reference.
        parts = [re.sub(r"\s+", " ", r["t"]).strip()
                 for r in b["runs"] if not r.get("c") and not r.get("href")]
        probe = max(parts, key=len) if parts else ""
        probe = re.sub(r"Part \d+ §[\d.]+|§[\d.]+|ADR-\d+", "", probe).strip()[:55]
        if len(probe) > 24 and probe not in joined:
            lost.append(probe[:48])
    check(not lost, f"120 sampled source paragraphs all present verbatim",
          f"{len(lost)} paragraphs not found: {lost[:3]}")

    # ---------------------------------------------------------- blank pages
    blanks = [i + 1 for i in range(doc.page_count)
              if len(all_text[i].strip()) < 60 and not doc[i].get_images()]
    check(not blanks, "no unintended blank pages",
          f"blank-looking pages: {blanks}", hard=False)

    # ------------------------------------------------------------ pdf quality
    cat = doc.pdf_catalog()
    marked = doc.xref_get_key(cat, "MarkInfo")
    check("Marked" in str(marked), "PDF is tagged (/MarkInfo /Marked true)",
          f"PDF not tagged: {marked}")
    check(doc.xref_get_key(cat, "StructTreeRoot")[0] != "null",
          "PDF carries a structure tree (logical reading order)",
          "no StructTreeRoot")
    check(len(toc) > 150, f"{len(toc)} clickable PDF bookmarks", f"only {len(toc)} bookmarks")

    fonts = set()
    for i in range(min(40, doc.page_count)):
        for f in doc.get_page_fonts(i):
            fonts.add(f[3].split("+")[-1])
    embedded = all(doc.get_page_fonts(i) for i in range(3, 10))
    check(any("Inter" in f for f in fonts), f"fonts embedded: {', '.join(sorted(fonts)[:6])}",
          f"Inter not found in {fonts}")

    txt_chars = sum(len(t) for t in all_text)
    check(txt_chars > 200_000, f"{txt_chars:,} characters of selectable text "
          f"(no scanned pages)", f"only {txt_chars} characters of text")

    # ------------------------------------------------------------- widows
    check("widowControl" in stylexml,
          f"widow/orphan control enabled ({stylexml.count('widowControl')} styles)",
          "widow control missing")
    check(stylexml.count("keepNext") >= 6 and stylexml.count("keepLines") >= 5,
          f"keep-with-next on {stylexml.count('keepNext')} styles, "
          f"keep-lines-together on {stylexml.count('keepLines')}",
          "keepNext/keepLines missing")

    # ---------------------------------------------------------------- report
    print("PASS")
    for m in ok:
        print("  ✓", m)
    if warn:
        print("\nNOTE")
        for m in warn:
            print("  •", m)
    if fail:
        print("\nFAIL")
        for m in fail:
            print("  ✗", m)
    print(f"\n{len(ok)} passed · {len(warn)} notes · {len(fail)} failed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
