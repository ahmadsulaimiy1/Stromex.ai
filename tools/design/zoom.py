"""Look at one plate properly: named zones, at 100%, 200% and 400%.

(Named `zoom.py` rather than `inspect.py`: a module called `inspect` on the
path shadows the standard library's, and Playwright imports it.)

A contact sheet answers one question — *does this hold its own beside the
others* — and it is the wrong instrument for every other question. Craftsmanship
lives at magnifications a six-up thumbnail cannot show, and the defects found in
this project by looking were all found at full size or closer: a legend seam, a
mitre that read as mis-registration, a cartouche squashed by a viewBox, a
lattice running through an authority line.

So this renders one finalist at 300 DPI and cuts it into the zones a document is
actually judged in — ceremonial centre, border, corners, seal, signatures,
serial, fine text, security field — each at three magnifications, on one sheet
per zone. It is a review instrument, not a test: nothing here passes or fails.
It exists so the looking is systematic rather than wherever the eye happened to
land.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

W_MM, H_MM = 297.0, 210.0

#: Zones as fractions of the sheet, so they survive a change of trim size.
#: Chosen from where a document is actually examined rather than from a grid:
#: the ceremonial centre is what a recipient looks at, the seal and signatures
#: are what a registrar looks at, and the fine text and security field are what
#: somebody deciding whether to believe it looks at.
ZONES: dict[str, tuple[float, float, float, float]] = {
    "ceremonial-centre": (0.22, 0.26, 0.56, 0.34),
    "title-register": (0.28, 0.17, 0.44, 0.13),
    "border-top": (0.30, 0.00, 0.40, 0.13),
    "corner-top-left": (0.00, 0.00, 0.18, 0.25),
    "corner-bottom-right": (0.82, 0.75, 0.18, 0.25),
    "seal": (0.06, 0.68, 0.20, 0.28),
    "signatures": (0.24, 0.72, 0.48, 0.24),
    "serial-verification": (0.72, 0.70, 0.26, 0.26),
    "fine-text-edge": (0.20, 0.955, 0.60, 0.045),
    "security-field": (0.36, 0.40, 0.28, 0.20),
}

MAGNIFICATIONS: tuple[int, ...] = (100, 200, 400)


def render(source: pathlib.Path, out: pathlib.Path, *, dpi: int = 300) -> pathlib.Path:
    """One plate at a stated DPI. 300 is the press floor, not a screen choice."""
    from playwright.sync_api import sync_playwright

    out.mkdir(parents=True, exist_ok=True)
    target = out / f"{source.stem}--{dpi}dpi.png"
    with sync_playwright() as play:
        browser = play.chromium.launch(executable_path=CHROME)
        context = browser.new_context(viewport={"width": 1400, "height": 1000},
                                      device_scale_factor=dpi / 96.0)
        page = context.new_page()
        page.goto(source.resolve().as_uri())
        page.wait_for_timeout(900)
        page.locator(".sheet").first.screenshot(path=str(target))
        browser.close()
    return target


def zone_sheet(plate_png: pathlib.Path, zone: str, out: pathlib.Path) -> pathlib.Path:
    """One zone at three magnifications, stacked, labelled.

    100% is the zone as printed. 200% is where engraving and foil register
    become legible. 400% is where the lathe petals, the construction lines and
    the fine text either resolve or turn out not to be there.
    """
    from PIL import Image, ImageDraw, ImageFont

    fx, fy, fw, fh = ZONES[zone]
    image = Image.open(plate_png).convert("RGB")
    box = (round(fx * image.width), round(fy * image.height),
           round((fx + fw) * image.width), round((fy + fh) * image.height))
    crop = image.crop(box)

    try:
        font = ImageFont.truetype(
            str(ROOT / "tools" / "publisher" / "assets" / "fonts" / "Inter-600.ttf"), 20)
    except OSError:  # pragma: no cover
        font = ImageFont.load_default()

    width = 1500
    label_h, gap = 30, 14
    panels: list[tuple[str, Image.Image]] = []
    for magnification in MAGNIFICATIONS:
        # 100% means "the zone, fitted to the review width". Higher
        # magnifications show a proportionally smaller slice at the same width,
        # taken from the zone's centre, which is where the interest is.
        span = 100 / magnification
        sub = crop.crop((
            round(crop.width * (1 - span) / 2), round(crop.height * (1 - span) / 2),
            round(crop.width * (1 + span) / 2), round(crop.height * (1 + span) / 2),
        ))
        height = round(sub.height * width / sub.width)
        panels.append((f"{zone} · {magnification}%",
                       sub.resize((width, height), Image.LANCZOS)))

    total = sum(p.height + label_h + gap for _, p in panels) + gap
    sheet = Image.new("RGB", (width + gap * 2, total), (24, 22, 20))
    draw = ImageDraw.Draw(sheet)
    y = gap
    for caption, panel in panels:
        draw.text((gap + 2, y + 4), caption, font=font, fill=(228, 216, 192))
        sheet.paste(panel, (gap, y + label_h))
        y += panel.height + label_h + gap
    out.mkdir(parents=True, exist_ok=True)
    target = out / f"{plate_png.stem.split('--')[0]}--zone-{zone}.png"
    sheet.save(target)
    return target


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: zoom.py <plate.html> [zone ...]")
        return 1
    source = pathlib.Path(sys.argv[1])
    zones = sys.argv[2:] or list(ZONES)
    out = source.parent / "inspect"
    plate = render(source, out)
    print(f"{plate.name} at 300 DPI")
    for zone in zones:
        print("  " + zone_sheet(plate, zone, out).name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
