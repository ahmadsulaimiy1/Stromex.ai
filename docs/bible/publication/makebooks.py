#!/usr/bin/env python3
"""Build the Executive Knowledge System: ten independently-issued books.

Each book is its own publication — its own cover, front matter, document
control, contents, apparatus, version and changelog — because a constitution
that changes once a decade and a price book that changes quarterly should not
share a version number. The omnibus edition remains available as a single-file
reference and is built by make.py.

Each book converges independently: its lists of tables and figures and its
index carry real page numbers, so the build renders, reads the apparatus back
off the rendered pages, recomposes, and repeats until the numbers settle.
"""
import json, re, subprocess, sys, pathlib, shutil

HERE = pathlib.Path(__file__).parent
SRC = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '/home/user/Stromex.ai/docs/bible')
OUTDIR = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else '/home/user/Stromex.ai/docs/library')
ONLY = sys.argv[3] if len(sys.argv) > 3 else None

sys.path.insert(0, str(HERE))
from make import INDEX_TERMS  # noqa: E402


def books():
    out = subprocess.run(
        ['node', '-e',
         "const E=require('./lib/editorial');process.stdout.write(JSON.stringify("
         "E.VOLUMES.map(v=>({roman:v.roman,title:v.title,sub:v.sub,slug:v.slug,"
         "file:v.file,owner:v.owner,review:v.review,status:v.status}))))"],
        cwd=HERE, capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=HERE, **kw)
    if r.returncode:
        print(r.stdout[-1500:]); print(r.stderr[-1500:])
        raise SystemExit(f'failed: {" ".join(map(str, cmd))}')
    return r.stdout


def harvest(pdf, roman):
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(pdf))
    pages = [doc[i].get_textpage().get_text_range() for i in range(len(doc))]

    def folio(i):
        m = re.search(r'·\s*(\d+)\s*·\s*$', pages[i].strip())
        return int(m.group(1)) if m else None

    tables, figures, seen = [], [], set()
    for i, txt in enumerate(pages):
        f = folio(i)
        if f is None:
            continue
        for m in re.finditer(r'(Table|Figure)\s+(\d+)\s*—\s*([^\r\n]{1,90})', txt):
            kind, n = m.group(1), int(m.group(2))
            cap = re.sub(r'[✅◐○✓✔]|️', '', m.group(3)).strip(' .·—-')
            if (kind, n) in seen:
                continue
            seen.add((kind, n))
            (tables if kind == 'Table' else figures).append({'n': n, 'cap': cap, 'page': f, 'vol': ''})

    idx = []
    for term in sorted(INDEX_TERMS, key=str.lower):
        hits, pat = [], re.compile(re.escape(term), re.I)
        for i, txt in enumerate(pages):
            f = folio(i)
            if f is None or f in hits:
                continue
            n = len(pat.findall(txt))
            if n >= 2 or (n == 1 and pat.search(txt[:600])):
                hits.append(f)
        if hits:
            idx.append({'term': term, 'pages': hits[:14]})
    return {'tables': tables, 'figures': figures, 'index': idx}, len(doc)


def sig(app):
    return json.dumps([[e['n'], e['page']] for e in app['tables']] +
                      [[e['n'], e['page']] for e in app['figures']] +
                      [[e['term'], e['pages']] for e in app['index']], sort_keys=True)


def build(v):
    roman, slug = v['roman'], v['slug']
    app_file = HERE / f'apparatus-{roman}.json'
    docx = HERE / f'{slug}.docx'
    pdf = HERE / f'{slug}.pdf'
    if app_file.exists():
        app_file.unlink()

    prev, pages = None, 0
    for attempt in range(1, 5):
        run(['node', str(HERE / 'build.js'), str(SRC), str(docx), roman])
        if pdf.exists():
            pdf.unlink()
        run(['python3', str(HERE / 'topdf.py'), str(docx), str(pdf)])
        app, pages = harvest(pdf, roman)
        s = sig(app)
        if s == prev:
            break
        prev = s
        app_file.write_text(json.dumps(app, indent=1))

    dest = OUTDIR / slug
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(docx, dest / f'{slug}.docx')
    shutil.copy(pdf, dest / f'{slug}.pdf')
    print(f'  Book {roman:<5} {v["title"][:46]:<46} {pages:>4} pp  '
          f'({len(app["tables"])}t/{len(app["figures"])}f/{len(app["index"])}i)')
    return {'roman': roman, 'title': v['title'], 'sub': v['sub'], 'slug': slug,
            'pages': pages, 'tables': len(app['tables']), 'figures': len(app['figures']),
            'owner': v['owner'], 'review': v['review'], 'status': v['status']}


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    result = []
    for v in books():
        if ONLY and v['roman'] != ONLY:
            continue
        result.append(build(v))
    (HERE / 'library-manifest.json').write_text(json.dumps(result, indent=1))
    print(f'\ntotal: {sum(r["pages"] for r in result)} pages across {len(result)} books')


if __name__ == '__main__':
    main()
