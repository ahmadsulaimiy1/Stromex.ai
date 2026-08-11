"""Render plates and compose a contact sheet, so the work can be looked at.

Two jobs, and the second is the one that matters. Rendering a certificate proves
the HTML parses; putting twelve of them side by side at the same size is what
makes a direction's weakness visible — a plate that looks acceptable alone and
inexpensive next to eleven others has been judged correctly.

The element is captured rather than the page, at a device scale factor of 2, so
a 297mm sheet comes back at roughly 300 DPI and the fine linework can be read at
100% instead of guessed at.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"


def shoot(pages: list[pathlib.Path], out: pathlib.Path, *,
          selector: str = ".sheet", scale: int = 2) -> list[pathlib.Path]:
    from playwright.sync_api import sync_playwright

    out.mkdir(parents=True, exist_ok=True)
    written: list[pathlib.Path] = []
    with sync_playwright() as play:
        browser = play.chromium.launch(executable_path=CHROME)
        context = browser.new_context(viewport={"width": 1400, "height": 1000},
                                      device_scale_factor=scale)
        page = context.new_page()
        for source in pages:
            page.goto(source.resolve().as_uri())
            page.wait_for_timeout(700)
            target = out / f"{source.stem}.png"
            page.locator(selector).first.screenshot(path=str(target))
            written.append(target)
        browser.close()
    return written


def contact(shots: list[pathlib.Path], target: pathlib.Path, *,
            columns: int = 3, width: int = 760, gap: int = 22,
            label_h: int = 30) -> pathlib.Path:
    """A contact sheet: every plate at the same width, labelled, on one image."""
    from PIL import Image, ImageDraw, ImageFont

    try:
        font = ImageFont.truetype(
            str(ROOT / "tools" / "publisher" / "assets" / "fonts" / "Inter-600.ttf"), 19)
    except OSError:  # pragma: no cover - only if the face moves
        font = ImageFont.load_default()

    tiles = []
    for path in shots:
        image = Image.open(path).convert("RGB")
        height = round(image.height * width / image.width)
        tiles.append((path.stem, image.resize((width, height), Image.LANCZOS)))

    rows = (len(tiles) + columns - 1) // columns
    cell_h = max(t.height for _, t in tiles) + label_h
    sheet = Image.new(
        "RGB",
        (columns * width + (columns + 1) * gap, rows * cell_h + (rows + 1) * gap),
        (26, 24, 22),
    )
    draw = ImageDraw.Draw(sheet)
    for index, (name, tile) in enumerate(tiles):
        row, column = divmod(index, columns)
        x = gap + column * (width + gap)
        y = gap + row * (cell_h + gap)
        draw.text((x + 2, y + 4), name.replace("-", " "), font=font,
                  fill=(226, 214, 190))
        sheet.paste(tile, (x, y + label_h))
    sheet.save(target)
    return target


def main() -> int:
    which = sys.argv[1] if len(sys.argv) > 1 else "concepts"
    source = ROOT / "docs" / "edtechx" / "design" / which
    pages = sorted(source.glob("*.html"))
    if not pages:
        print(f"No pages in {source}")
        return 1
    shots = shoot(pages, source)
    print(f"{len(shots)} plates rendered")
    sheet = contact(shots, source / "contact-sheet.png")
    print(f"contact sheet → {sheet.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
