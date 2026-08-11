"""Render the ground library as swatches, so it can be browsed rather than read."""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "edtechx-api"))

from app.modules.design import geometry as geo  # noqa: E402
from app.modules.design.grounds import GROUNDS  # noqa: E402

OUT = ROOT / "docs" / "edtechx" / "design" / "grounds"
SW, SH = 96.0, 62.0
INK, METAL = "#0A101C", "#B08D57"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cells = []
    for ground in GROUNDS.values():
        rect = geo.Rect(0, 0, SW, SH)
        for label, ink in (("ink", INK), ("metal", METAL)):
            body = ground.draw(rect, ink=ink, strength=ground.suggested * 3.2)
            cells.append(
                f'<figure><figcaption><b>{ground.name}</b>'
                f'<span>{ground.family} · {label} · suggested '
                f'{ground.suggested:.3f}</span></figcaption>'
                f'<svg viewBox="0 0 {SW:g} {SH:g}" width="{SW:g}mm"'
                f' height="{SH:g}mm">'
                f'<rect width="{SW:g}" height="{SH:g}" fill="#F7F2E6"/>'
                f'{body}</svg><p>{ground.note}</p></figure>'
            )
    html = (
        '<!doctype html><meta charset="utf-8"><title>EdirasX grounds</title>'
        "<style>body{margin:0;background:#211E1A;font-family:system-ui;"
        "color:#E6DCC8}#grid{display:grid;grid-template-columns:repeat(3,1fr);"
        "gap:10px;padding:12px}figure{margin:0;background:#F7F2E6;color:#2A2418}"
        "figcaption{background:#2E2A22;color:#EDE4D2;padding:5px 7px;"
        "font-size:11px;display:flex;justify-content:space-between;gap:6px}"
        "figcaption span{opacity:.75}svg{display:block;width:100%;height:auto}"
        "p{margin:0;padding:5px 7px;font-size:10.5px;color:#5A5140}</style>"
        f'<div id="grid">{"".join(cells)}</div>'
    )
    (OUT / "catalogue.html").write_text(html, encoding="utf-8")
    print(f"{len(GROUNDS)} grounds x 2 inks -> {OUT / 'catalogue.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
