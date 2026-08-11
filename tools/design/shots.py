"""Render pages at three widths and look at them.

A page can pass every test and still look terrible. This is the part of the
review that no assertion replaces: open it, at the widths people actually use,
and read what comes back.

The widths are chosen from what schools have rather than from a breakpoint
table: 1440 is an administrator's laptop, 834 is an iPad a teacher carries round
a classroom, and 390 is the phone a parent reads a report card on in a car park.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

VIEWPORTS: dict[str, tuple[int, int]] = {
    "desktop": (1440, 1000),
    "tablet": (834, 1112),
    "mobile": (390, 844),
}


def capture(pages: dict[str, pathlib.Path], out: pathlib.Path,
            widths: tuple[str, ...] = ("desktop", "tablet", "mobile"),
            full: bool = True) -> list[pathlib.Path]:
    from playwright.sync_api import sync_playwright

    out.mkdir(parents=True, exist_ok=True)
    written: list[pathlib.Path] = []
    with sync_playwright() as play:
        browser = play.chromium.launch(executable_path=CHROME)
        try:
            for label, width in ((w, VIEWPORTS[w]) for w in widths):
                context = browser.new_context(
                    viewport={"width": width[0], "height": width[1]},
                    device_scale_factor=2,
                )
                page = context.new_page()
                for name, source in pages.items():
                    page.goto(source.resolve().as_uri())
                    page.wait_for_timeout(450)
                    target = out / f"{name}--{label}.png"
                    page.screenshot(path=str(target), full_page=full)
                    written.append(target)
                context.close()
        finally:
            browser.close()
    return written


def main() -> int:
    design = ROOT / "docs" / "edtechx" / "design"
    pages = {path.stem: path for path in sorted(design.glob("*.html"))}
    if not pages:
        print("Nothing to capture.")
        return 1
    shots = capture(pages, design / "shots")
    for shot in shots:
        size = shot.stat().st_size / 1024
        print(f"{shot.relative_to(ROOT)}  {size:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
