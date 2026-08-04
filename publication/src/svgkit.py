"""A tiny vector-diagram toolkit, constrained to the SpaceTalk brand.

Rules encoded here so no diagram can drift off-brand:
  * only palette colours from 02-VISUAL-DESIGN-SYSTEM.md
  * 1.5 px strokes, rounded joins, radius family 4/8/12/18
  * Inter for all labels, JetBrains Mono for code/values
  * no gradients, no shadows, no decoration
"""

# ---- palette (verbatim from 02-VISUAL-DESIGN-SYSTEM.md)
ORBIT = {50: "#EEF2FF", 100: "#DDE4FF", 200: "#BCC9FF", 300: "#92A7FF", 400: "#6681FB",
         500: "#3F5EF0", 600: "#2E48D8", 700: "#2438AE", 800: "#1E2F8A", 900: "#1A2769",
         950: "#10173F"}
AURORA = {"050": "#E6FAF6", 300: "#5FE3CE", 400: "#2ACFB6", 500: "#12B39B",
          700: "#0A7466", 800: "#08594E", 950: "#062F2A"}
VOID = {0: "#FFFFFF", 25: "#FAFBFD", 50: "#F4F6FA", 100: "#E9EDF4", 200: "#D7DDE8",
        300: "#B4BCCB", 400: "#8B94A6", 500: "#676F80", 600: "#4C5464", 700: "#363D4B",
        800: "#232935", 850: "#1A1F29", 900: "#12161E", 950: "#0A0D13"}
SUCCESS, SUCCESS_S = "#08602F", "#E8F7EE"
WARNING, WARNING_S = "#B45309", "#FEF4E6"
DANGER, DANGER_S = "#C0271B", "#FDECEA"

UI = "Inter, 'Inter Display', sans-serif"
MONO = "'JetBrains Mono', monospace"


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class Svg:
    def __init__(self, w, h, bg=None):
        self.w, self.h = w, h
        self.parts = []
        if bg:
            self.parts.append(f'<rect width="{w}" height="{h}" fill="{bg}"/>')

    # ---------------------------------------------------------------- shapes
    def rect(self, x, y, w, h, r=12, fill="none", stroke=None, sw=1.5, dash=None, op=None):
        a = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" ry="{r}" fill="{fill}"'
        if stroke:
            a += f' stroke="{stroke}" stroke-width="{sw}"'
        if dash:
            a += f' stroke-dasharray="{dash}"'
        if op is not None:
            a += f' opacity="{op}"'
        self.parts.append(a + "/>")
        return self

    def rrect(self, x, y, w, h, tl, tr, br, bl, fill="none", stroke=None, sw=1.5):
        """Rounded rect with per-corner radii — needed to draw bubble run geometry."""
        d = (f"M{x + tl},{y} H{x + w - tr} A{tr},{tr} 0 0 1 {x + w},{y + tr} "
             f"V{y + h - br} A{br},{br} 0 0 1 {x + w - br},{y + h} "
             f"H{x + bl} A{bl},{bl} 0 0 1 {x},{y + h - bl} "
             f"V{y + tl} A{tl},{tl} 0 0 1 {x + tl},{y} Z")
        a = f'<path d="{d}" fill="{fill}"'
        if stroke:
            a += f' stroke="{stroke}" stroke-width="{sw}"'
        self.parts.append(a + "/>")
        return self

    def heart(self, cx, cy, r, fill):
        d = (f"M{cx},{cy + r * 0.75} C{cx - r * 1.3},{cy - r * 0.25} {cx - r * 0.55},{cy - r * 1.15} "
             f"{cx},{cy - r * 0.35} C{cx + r * 0.55},{cy - r * 1.15} {cx + r * 1.3},{cy - r * 0.25} "
             f"{cx},{cy + r * 0.75} Z")
        self.parts.append(f'<path d="{d}" fill="{fill}"/>')
        return self

    def circle(self, cx, cy, r, fill="none", stroke=None, sw=1.5):
        a = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"'
        if stroke:
            a += f' stroke="{stroke}" stroke-width="{sw}"'
        self.parts.append(a + "/>")
        return self

    def line(self, x1, y1, x2, y2, stroke=VOID[300], sw=1.5, dash=None, cap="round"):
        a = (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
             f'stroke-width="{sw}" stroke-linecap="{cap}"')
        if dash:
            a += f' stroke-dasharray="{dash}"'
        self.parts.append(a + "/>")
        return self

    def path(self, d, stroke=VOID[300], sw=1.5, fill="none", dash=None, marker=False):
        a = (f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
             f'stroke-linecap="round" stroke-linejoin="round"')
        if dash:
            a += f' stroke-dasharray="{dash}"'
        if marker:
            a += ' marker-end="url(#arw)"'
        self.parts.append(a + "/>")
        return self

    # ---------------------------------------------------------------- text
    def text(self, x, y, s, size=12, fill=VOID[900], anchor="start", weight=400,
             font=UI, ls=0, op=None):
        a = (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" '
             f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}"')
        if ls:
            a += f' letter-spacing="{ls}"'
        if op is not None:
            a += f' opacity="{op}"'
        self.parts.append(a + f">{esc(s)}</text>")
        return self

    def lines(self, x, y, rows, size=12, lh=15, **kw):
        for i, r in enumerate(rows):
            self.text(x, y + i * lh, r, size=size, **kw)
        return self

    # ---------------------------------------------------------------- combos
    def box(self, x, y, w, h, title, sub=None, fill=VOID[0], stroke=VOID[200],
            tcol=VOID[900], scol=VOID[500], r=12, tsize=12.5, ssize=10.5, sw=1.5,
            dash=None, mono=False):
        """A labelled box; title centred, optional sub-label lines beneath."""
        self.rect(x, y, w, h, r=r, fill=fill, stroke=stroke, sw=sw, dash=dash)
        cx = x + w / 2
        subs = [] if sub is None else ([sub] if isinstance(sub, str) else list(sub))
        block = tsize + (len(subs) * (ssize + 3.5))
        ty = y + h / 2 - block / 2 + tsize * 0.86
        self.text(cx, ty, title, size=tsize, anchor="middle", weight=600, fill=tcol,
                  font=MONO if mono else UI)
        for i, s in enumerate(subs):
            self.text(cx, ty + (i + 1) * (ssize + 3.5) + 1.5, s, size=ssize,
                      anchor="middle", fill=scol)
        return self

    def arrow(self, x1, y1, x2, y2, stroke=VOID[400], sw=1.5, dash=None):
        self.path(f"M{x1},{y1} L{x2},{y2}", stroke=stroke, sw=sw, dash=dash, marker=True)
        return self

    def elbow(self, x1, y1, x2, y2, stroke=VOID[400], sw=1.5, dash=None, mid=None):
        """Orthogonal connector: vertical then horizontal then vertical."""
        m = mid if mid is not None else (y1 + y2) / 2
        self.path(f"M{x1},{y1} L{x1},{m} L{x2},{m} L{x2},{y2}",
                  stroke=stroke, sw=sw, dash=dash, marker=True)
        return self

    def chip(self, x, y, s, fill=ORBIT[50], tcol=ORBIT[700], size=9.5, pad=8, h=19):
        w = len(s) * size * 0.58 + pad * 2
        self.rect(x, y, w, h, r=h / 2, fill=fill)
        self.text(x + w / 2, y + h / 2 + size * 0.35, s, size=size, anchor="middle",
                  weight=600, fill=tcol)
        return w

    def caption(self, x, y, s, size=10, fill=VOID[500], anchor="start"):
        self.text(x, y, s, size=size, fill=fill, anchor=anchor)
        return self

    def kicker(self, x, y, s, fill=VOID[400], size=9):
        self.text(x, y, s.upper(), size=size, fill=fill, weight=600, ls=1.1)
        return self

    # ---------------------------------------------------------------- output
    def render(self):
        defs = (
            '<defs>'
            '<marker id="arw" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
            'markerHeight="6" orient="auto-start-reverse">'
            f'<path d="M0,1.6 L9,5 L0,8.4 z" fill="{VOID[400]}"/></marker>'
            '<marker id="arwb" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
            'markerHeight="6" orient="auto-start-reverse">'
            f'<path d="M0,1.6 L9,5 L0,8.4 z" fill="{ORBIT[600]}"/></marker>'
            '</defs>'
        )
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
                f'height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
                + defs + "".join(self.parts) + "</svg>")

    def save(self, path):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.render())
        return path
