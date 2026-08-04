#!/usr/bin/env python3
"""The SpaceTalk mark, built to the construction rules in 01-BRAND-BIBLE.md §1.5.

Two overlapping soft-cornered forms whose intersection creates a lens-shaped
void at the centre. The void is the subject. Built on a 24-unit grid with all
radii multiples of 2, so it scales from a 16 px favicon to a 1024 px app icon
from one source. Monochrome-first: colour versions derive from this master.
"""
import os
import cairosvg

OUT = "/home/user/Stromex.ai/publication/build/diagrams"


def mark_svg(colour="#FFFFFF", size=240):
    """The mark: two rounded forms, even-odd fill leaves the lens void open."""
    u = size / 24.0                      # one grid unit
    # Two 16u rounded squares, radius 6u, overlapping by 8u horizontally.
    a_x, b_x, y, s, r = 0 * u, 8 * u, 4 * u, 16 * u, 6 * u

    def rr(x, y, s, r):
        return (f"M{x + r},{y} H{x + s - r} A{r},{r} 0 0 1 {x + s},{y + r} "
                f"V{y + s - r} A{r},{r} 0 0 1 {x + s - r},{y + s} "
                f"H{x + r} A{r},{r} 0 0 1 {x},{y + s - r} "
                f"V{y + r} A{r},{r} 0 0 1 {x + r},{y} Z")

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}">'
        f'<path fill-rule="evenodd" fill="{colour}" '
        f'd="{rr(a_x, y, s, r)} {rr(b_x, y, s, r)}"/>'
        f'</svg>'
    )


def lockup_svg(colour="#FFFFFF", sub=None, w=900, h=200):
    """Mark + wordmark, tracked −2 % per §1.5."""
    m = mark_svg(colour, 96)
    inner = m.split(">", 1)[1].rsplit("</svg>", 1)[0]
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">']
    s.append(f'<g transform="translate(0,{(h - 96) / 2})">{inner}</g>')
    s.append(f'<text x="120" y="{h / 2 + 16}" font-family="Inter Display, Inter, sans-serif" '
             f'font-size="52" font-weight="600" letter-spacing="-1" fill="{colour}">SpaceTalk</text>')
    if sub:
        s.append(f'<text x="122" y="{h / 2 + 44}" font-family="Inter, sans-serif" font-size="15" '
                 f'letter-spacing="3.4" fill="{colour}" opacity="0.72">{sub}</text>')
    s.append("</svg>")
    return "".join(s)


def write(name, svg, scale=4.0):
    p = os.path.join(OUT, name)
    with open(p + ".svg", "w") as fh:
        fh.write(svg)
    cairosvg.svg2png(url=p + ".svg", write_to=p + ".png", scale=scale)
    return p + ".png"


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for n, p in [
        ("mark-white", write("mark-white", mark_svg("#FFFFFF", 240))),
        ("mark-dark", write("mark-dark", mark_svg("#12161E", 240))),
        ("mark-orbit", write("mark-orbit", mark_svg("#3F5EF0", 240))),
        ("lockup-white", write("lockup-white", lockup_svg("#FFFFFF", "EDITORIAL BIBLE"))),
        ("lockup-dark", write("lockup-dark", lockup_svg("#12161E", None, 900, 160))),
    ]:
        print(f"  {n:<16} {os.path.getsize(p) // 1024} KB")
