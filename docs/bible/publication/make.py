#!/usr/bin/env python3
"""Build the flagship edition.

The lists of tables and figures and the index carry real page numbers, and a
page number cannot be known until the document has been laid out. So the build
runs to convergence: compose, render, read the apparatus back off the rendered
pages, recompose with it, and repeat until the page numbers stop moving.
"""
import json, os, re, subprocess, sys, pathlib

HERE = pathlib.Path(__file__).parent
SRC = sys.argv[1] if len(sys.argv) > 1 else '/home/user/Stromex.ai/docs/bible'
DOCX = HERE / 'StromeX-Editorial-Bible.docx'
PDF = HERE / 'StromeX-Editorial-Bible.pdf'
APP = HERE / 'apparatus.json'

VOLUMES = [
    ('I', 'The Constitution'), ('II', 'Market Strategy & Competitive Positioning'),
    ('III', 'The Catalogue'), ('IV', 'Engineering, AI Architecture, Cloud & Security'),
    ('V', 'Go-to-Market'), ('VI', 'The Creative Division'),
    ('VII', 'Industry Ecosystems'), ('VIII', 'Expansion, Finance & the Roadmap'),
    ('IX', 'The Institution'), ('X', 'SpaceTalk'),
]
RUNNING = {t: f'Volume {r} — {t}' for r, t in VOLUMES}

INDEX_TERMS = [
    'ACV', 'Band A', 'Band B', 'Band C', 'CAC payback', 'Craft standard', 'Credential',
    'Degraded mode', 'Ecosystem', 'Entrenched provision', 'Federation', 'Foundation tier',
    'Free tier', 'Gate', 'GRR', 'Guilloche', 'Human-in-the-loop', 'LTV', 'No-fork rule',
    'NRR', 'Pricing Council', 'Reference Implementation', 'Rule of 40', 'Stakes ladder',
    'System of record', 'Value ledger', 'Verification', 'Verification token', 'Wave',
    'Net revenue retention', 'SpaceTalk', 'StromeX Cloud', 'StromeX Identity',
    'StromeX Pay', 'StromeX Labs', 'Smart campus', 'Data residency', 'Open source',
    'Marketplace', 'Partner network', 'Phase gate', 'Sustainability', 'Talent',
]


def run(cmd, **kw):
    r = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, **kw)
    if r.returncode:
        print(r.stdout[-2000:]); print(r.stderr[-2000:]); raise SystemExit(f'failed: {cmd}')
    return r.stdout


def compose():
    return run(['node', str(HERE / 'build.js'), SRC, str(DOCX)], cwd=HERE)


def render():
    if PDF.exists():
        PDF.unlink()
    return run(['python3', str(HERE / 'topdf.py'), str(DOCX), str(PDF)], cwd=HERE)


def harvest():
    """Read captions, running heads and index terms off the rendered pages."""
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(PDF))
    pages = []
    for i in range(len(doc)):
        pages.append(doc[i].get_textpage().get_text_range())

    # the printed folio, so references match what a reader sees
    def folio(i):
        m = re.search(r'·\s*(\d+)\s*·\s*$', pages[i].strip())
        return int(m.group(1)) if m else None

    tables, figures, seen = [], [], set()
    current_vol = None
    # the running head carries the volume title (a STYLEREF of Heading 1),
    # so the first line of each page tells us which volume a caption sits in
    titles = sorted(RUNNING, key=len, reverse=True)
    for i, txt in enumerate(pages):
        head = txt.split('\n', 1)[0]
        for title in titles:
            h = head.rstrip()
            if h.endswith(title) or (len(title) > 24 and h.endswith(title[:24])):
                current_vol = RUNNING[title]
                break
        f = folio(i)
        if f is None:
            continue
        for m in re.finditer(r'(Table|Figure)\s+(\d+)\s*—\s*([^\r\n]{1,90})', txt):
            kind, n = m.group(1), int(m.group(2))
            cap = re.sub(r'[\u2705\u25D0\u25CB\u2713\u2714]|\uFE0F', '', m.group(3)).strip(' .·—-')
            key = (kind, n)
            if key in seen:
                continue
            seen.add(key)
            (tables if kind == 'Table' else figures).append(
                {'n': n, 'cap': cap, 'page': f, 'vol': current_vol or ''})

    idx = []
    for term in sorted(INDEX_TERMS, key=str.lower):
        hits, pat = [], re.compile(re.escape(term), re.I)
        for i, txt in enumerate(pages):
            f = folio(i)
            if f is None or f in hits:
                continue
            n = len(pat.findall(txt))
            # a passing mention is not an index entry
            if n >= 2 or (n == 1 and pat.search(txt[:600])):
                hits.append(f)
        if hits:
            idx.append({'term': term, 'pages': hits[:14]})

    return {'tables': sorted(tables, key=lambda e: e['n']),
            'figures': sorted(figures, key=lambda e: e['n']),
            'index': idx}


def signature(app):
    return json.dumps([[e['n'], e['page']] for e in app['tables']] +
                      [[e['n'], e['page']] for e in app['figures']] +
                      [[e['term'], e['pages']] for e in app['index']], sort_keys=True)


def main():
    if APP.exists():
        APP.unlink()
    prev = None
    for attempt in range(1, 6):
        print(f'pass {attempt}: composing…')
        compose()
        print(f'pass {attempt}: rendering…')
        render()
        app = harvest()
        sig = signature(app)
        print(f'  {len(app["tables"])} tables, {len(app["figures"])} figures, '
              f'{len(app["index"])} index terms')
        if sig == prev:
            print(f'converged after {attempt} passes')
            break
        prev = sig
        APP.write_text(json.dumps(app, indent=1))
    else:
        print('did not fully converge; last pass written')

    import pypdfium2 as pdfium
    print('final pages:', len(pdfium.PdfDocument(str(PDF))))


if __name__ == '__main__':
    main()
