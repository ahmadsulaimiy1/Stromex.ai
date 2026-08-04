#!/usr/bin/env python3
"""Parse the SpaceTalk Editorial Bible markdown into a structured IR.

The IR is the single source of truth for both the DOCX and the PDF, which is
how "the content in both documents must be identical" is guaranteed by
construction rather than by comparison.
"""
import json
import os
import re
import sys

SRC = "/home/user/Stromex.ai/docs/spacetalk"
OUT = "/home/user/Stromex.ai/publication/build/ir.json"

# Chapter order. README is handled separately as front matter.
CHAPTERS = [
    ("00-EDITORIAL-BIBLE.md", 0, "The Constitution"),
    ("01-BRAND-BIBLE.md", 1, "Brand"),
    ("02-VISUAL-DESIGN-SYSTEM.md", 2, "Visual Design System"),
    ("03-UX-BIBLE.md", 3, "User Experience"),
    ("04-AI-PHILOSOPHY.md", 4, "AI Philosophy"),
    ("05-FEATURE-BIBLE.md", 5, "The Feature Bible"),
    ("06-TECHNICAL-BIBLE.md", 6, "Technical Architecture"),
    ("07-DESIGN-SYSTEM.md", 7, "Design System"),
    ("08-PERFORMANCE-STANDARDS.md", 8, "Performance Standards"),
    ("09-ROADMAP.md", 9, "Roadmap"),
    ("10-SCOPE-GOVERNANCE.md", 10, "Scope Governance"),
    ("11-BUSINESS-AND-COMPLIANCE.md", 11, "Business & Compliance"),
    ("12-ADR.md", 12, "Architecture Decision Records"),
    ("13-UX-RESEARCH-AND-JOURNEYS.md", 13, "Research, Journeys & IA"),
]

# ---------------------------------------------------------------- inline text

INLINE_RE = re.compile(
    r"(\*\*.+?\*\*)"          # bold
    r"|(\*[^*\n]+?\*)"        # italic
    r"|(`[^`]+?`)"            # code
    r"|(\[[^\]]+?\]\([^)]+?\))"  # link
)


def parse_inline(text):
    """Return a list of runs: {t: text, b: bold, i: italic, c: code, href: url}."""
    runs = []
    pos = 0
    for m in INLINE_RE.finditer(text):
        if m.start() > pos:
            runs.append({"t": text[pos:m.start()]})
        tok = m.group(0)
        if m.group(1):
            inner = tok[2:-2]
            # bold may contain nested code or italic
            for r in parse_inline(inner):
                r["b"] = True
                runs.append(r)
        elif m.group(2):
            inner = tok[1:-1]
            for r in parse_inline(inner):
                r["i"] = True
                runs.append(r)
        elif m.group(3):
            runs.append({"t": tok[1:-1], "c": True})
        elif m.group(4):
            lm = re.match(r"\[([^\]]+?)\]\(([^)]+?)\)", tok)
            label, href = lm.group(1), lm.group(2)
            for r in parse_inline(label):
                r["href"] = href
                runs.append(r)
        pos = m.end()
    if pos < len(text):
        runs.append({"t": text[pos:]})
    runs = [r for r in runs if r.get("t")]
    for r in runs:
        if not r.get("c"):
            r["t"] = smart(r["t"])
    return runs


def norm(s):
    """Normalise source markdown text for print typography."""
    return s.replace("\u00a0", " ")


def smart(s):
    """Typographer's quotes. Applied to prose runs only — never to code spans,
    where a straight quote is the correct character."""
    out = []
    prev = ""
    for ch in s:
        if ch == '"':
            out.append("\u201c" if prev == "" or prev in " \t([{\u2014\u2013/" else "\u201d")
        elif ch == "'":
            out.append("\u2018" if prev == "" or prev in " \t([{\u2014\u2013/" else "\u2019")
        else:
            out.append(ch)
        prev = ch
    return "".join(out)


# ---------------------------------------------------------------- block parse

def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    # split on | not inside backticks
    cells, cur, tick = [], "", False
    for ch in line:
        if ch == "`":
            tick = not tick
        if ch == "|" and not tick:
            cells.append(cur)
            cur = ""
        else:
            cur += ch
    cells.append(cur)
    return [c.strip() for c in cells]


def parse_blocks(lines):
    blocks = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # code fence
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i].rstrip())
                i += 1
            i += 1
            blocks.append({"k": "code", "lang": lang, "lines": buf})
            continue

        # horizontal rule
        if re.fullmatch(r"-{3,}|\*{3,}", stripped):
            blocks.append({"k": "rule"})
            i += 1
            continue

        # heading
        hm = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if hm:
            level = len(hm.group(1))
            blocks.append({"k": "h", "level": level, "runs": parse_inline(norm(hm.group(2)))})
            i += 1
            continue

        # table
        if stripped.startswith("|") and i + 1 < n and re.match(r"^\|[\s:|-]+\|?\s*$", lines[i + 1].strip()):
            header = split_row(lines[i])
            align_cells = split_row(lines[i + 1])
            aligns = []
            for a in align_cells:
                if a.startswith(":") and a.endswith(":"):
                    aligns.append("center")
                elif a.endswith(":"):
                    aligns.append("right")
                else:
                    aligns.append("left")
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            blocks.append({
                "k": "table",
                "aligns": aligns,
                "header": [parse_inline(norm(c)) for c in header],
                "rows": [[parse_inline(norm(c)) for c in r] for r in rows],
            })
            continue

        # blockquote
        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            blocks.append({"k": "quote", "runs": parse_inline(norm(" ".join(buf)))})
            continue

        # list (bullet or ordered), possibly multi-line items
        lm = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
        if lm:
            ordered = bool(re.match(r"\d+\.", lm.group(2)))
            items = []
            while i < n:
                m2 = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", lines[i])
                if not m2:
                    if lines[i].strip() and lines[i].startswith(("  ", "\t")) and items:
                        items[-1]["text"] += " " + lines[i].strip()
                        i += 1
                        continue
                    break
                indent = len(m2.group(1))
                items.append({"lvl": 1 if indent >= 2 else 0, "text": m2.group(3)})
                i += 1
            blocks.append({
                "k": "list",
                "ordered": ordered,
                "items": [{"lvl": it["lvl"], "runs": parse_inline(norm(it["text"]))} for it in items],
            })
            continue

        # paragraph
        buf = [line.strip()]
        i += 1
        while i < n and lines[i].strip() and not re.match(
                r"^(#{1,6}\s|\||>|```|\s*([-*]|\d+\.)\s|-{3,}$)", lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        text = " ".join(buf)
        blocks.append({"k": "p", "runs": parse_inline(norm(text))})
    return blocks


def load(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read().split("\n")


def build():
    chapters = []
    for fname, num, short in CHAPTERS:
        blocks = parse_blocks(load(os.path.join(SRC, fname)))
        # first h1 is the chapter title; the following h3 is the part label;
        # the following italic paragraph is the standfirst.
        title = None
        label = None
        standfirst = None
        body = []
        for b in blocks:
            if title is None and b["k"] == "h" and b["level"] == 1:
                title = "".join(r["t"] for r in b["runs"])
                continue
            if label is None and b["k"] == "h" and b["level"] == 3:
                label = "".join(r["t"] for r in b["runs"])
                continue
            if standfirst is None and b["k"] == "p" and all(r.get("i") for r in b["runs"]):
                standfirst = b["runs"]
                continue
            body.append(b)
        # drop a leading rule right after the standfirst
        while body and body[0]["k"] == "rule":
            body.pop(0)
        chapters.append({
            "num": num,
            "file": fname,
            "short": short,
            "title": title,
            "label": label,
            "standfirst": standfirst,
            "blocks": body,
        })

    readme = parse_blocks(load(os.path.join(SRC, "README.md")))
    ir = {"chapters": chapters, "readme": readme}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(ir, fh, ensure_ascii=False, indent=1)

    # ---- report
    kinds = {}
    words = 0
    for c in chapters:
        for b in c["blocks"]:
            kinds[b["k"]] = kinds.get(b["k"], 0) + 1
            if b["k"] in ("p", "quote"):
                words += len(" ".join(r["t"] for r in b["runs"]).split())
    print(f"chapters: {len(chapters)}")
    print("blocks:", dict(sorted(kinds.items())))
    print("h-levels:", sorted({b['level'] for c in chapters for b in c['blocks'] if b['k'] == 'h'}))
    for c in chapters:
        h2 = sum(1 for b in c["blocks"] if b["k"] == "h" and b["level"] == 2)
        tb = sum(1 for b in c["blocks"] if b["k"] == "table")
        print(f"  Part {c['num']:>2}  {c['title'][:46]:<48} h2={h2:<3} tables={tb:<3} blocks={len(c['blocks'])}")


if __name__ == "__main__":
    build()
