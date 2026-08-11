"""Audit the rendered journeys for accessibility, with a tool rather than by assertion.

The distinction this file exists to hold: EdirasX has *implemented*
accessibility semantics — landmarks, `aria-current`, `aria-pressed`, labelled
controls, a skip link, a `.ed-sr` class, focus rings tuned for contrast. None of
that is evidence. This runs axe-core over every rendered page at two widths and
walks the keyboard order in a real browser, and prints what it found rather than
what was intended.

Three things it does **not** establish, stated here rather than buried:

  * **It is not a screen-reader test.** No screen reader is installed in this
    environment and none can be driven headlessly here. axe checks the
    machine-readable side — names, roles, relationships, contrast — which is
    necessary and not sufficient. A NVDA/VoiceOver pass is still outstanding.
  * **Behaviour that needs JavaScript is unverifiable from these pages.** The
    journeys are static HTML rendered from the server: the drawer and the
    command palette are shown *open*, and there is no client script to trap
    focus, restore it on close, or wire Escape. The markup is there; the
    behaviour is not implemented yet, so this reports it as absent rather than
    as passing.
  * **axe finds roughly a third of real barriers.** It is a floor. A clean run
    means no machine-detectable violation, not an accessible product.

Usage:

    python tools/design/audit.py [--axe PATH_TO_axe.min.js]

axe-core is not vendored into this repository. Fetch it with
`npm pack axe-core@4.10.2 && tar xzf axe-core-4.10.2.tgz`, or point `--axe` /
`EDIRASX_AXE` at a copy. Without it the keyboard walk still runs and the report
says plainly that the automated checks did not.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DESIGN = ROOT / "docs" / "edtechx" / "design"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

WIDTHS = {"desktop": (1440, 1000), "mobile": (390, 844)}

#: WCAG 2.2 AA and the best-practice set. Best practice is included because
#: several of its rules — "heading-order", "region", "landmark-unique" — are the
#: ones that decide whether a page can be *navigated* rather than merely read,
#: and a product that ships them broken is inaccessible in practice whatever the
#: conformance table says.
TAGS = [
    "wcag2a",
    "wcag2aa",
    "wcag21a",
    "wcag21aa",
    "wcag22aa",
    "best-practice",
]

# The tab walk records what a keyboard user actually reaches, in order, and
# whether the browser paints something when they get there. A focus style that
# exists in the stylesheet and is overridden in situ is the failure mode this
# catches and a review by reading CSS does not.
TAB_SCRIPT = """
() => {
  const out = [];
  const seen = new Set();
  let node = document.activeElement;
  for (let i = 0; i < 200; i += 1) {
    const active = document.activeElement;
    if (!active || active === document.body) break;
    const path = [];
    let cursor = active;
    while (cursor && cursor !== document.body) {
      path.unshift(cursor.tagName.toLowerCase() +
        (cursor.className && typeof cursor.className === 'string'
          ? '.' + cursor.className.trim().split(/\\s+/).slice(0, 2).join('.')
          : ''));
      cursor = cursor.parentElement;
    }
    const style = getComputedStyle(active);
    const label = (active.getAttribute('aria-label') ||
                   active.textContent || '').trim().slice(0, 44);
    const key = path.join('>') + '|' + label;
    if (seen.has(key)) break;
    seen.add(key);
    const box = active.getBoundingClientRect();
    out.push({
      selector: path.slice(-2).join(' > '),
      label,
      outline: style.outlineStyle !== 'none' && style.outlineWidth !== '0px',
      shadow: style.boxShadow !== 'none',
      hidden: box.width === 0 && box.height === 0,
    });
    node = active;
  }
  return out;
}
"""


def _walk(page) -> list[dict]:
    """Tab through the document and record where focus lands, in order."""
    page.evaluate("() => document.body.focus()")
    found: list[dict] = []
    seen: set[str] = set()
    for _ in range(120):
        page.keyboard.press("Tab")
        entry = page.evaluate(
            """() => {
              const a = document.activeElement;
              if (!a || a === document.body) return null;
              const s = getComputedStyle(a);
              const box = a.getBoundingClientRect();
              return {
                tag: a.tagName.toLowerCase(),
                cls: (typeof a.className === 'string' ? a.className : '')
                       .trim().split(/\\s+/)[0] || '',
                label: (a.getAttribute('aria-label') || a.textContent || '')
                       .replace(/\\s+/g, ' ').trim().slice(0, 48),
                outline: s.outlineStyle !== 'none' && s.outlineWidth !== '0px',
                shadow: s.boxShadow !== 'none',
                offscreen: box.width === 0 || box.height === 0,
              };
            }"""
        )
        if entry is None:
            break
        key = f"{entry['tag']}.{entry['cls']}|{entry['label']}"
        if key in seen:
            break
        seen.add(key)
        found.append(entry)
    return found


def _axe(page, axe_source: str) -> dict:
    page.add_script_tag(content=axe_source)
    return page.evaluate(
        "async (tags) => await axe.run(document, {runOnly: {type: 'tag', values: tags}})",
        TAGS,
    )


def _static_checks(html: str) -> list[str]:
    """Two things axe cannot see in a static page, checked by reading the markup.

    Both are about *behaviour that is not there*. A `role="dialog"` with no
    script behind it is a promise the page cannot keep, and reporting it as a
    pass because the attribute is present is exactly the overclaim this whole
    exercise exists to prevent.
    """
    notes: list[str] = []
    if 'role="dialog"' in html and "<script" not in html:
        notes.append(
            "A dialog role is present and the page carries no script: focus is "
            "not trapped, Escape does not close, and focus is not restored on "
            "close. The markup is right; the behaviour is unimplemented."
        )
    if 'class="ed-palette' in html and "<script" not in html:
        notes.append(
            "The command palette is rendered open with no script: arrow-key "
            "navigation and type-ahead are unimplemented."
        )
    if 'class="ed-mobile-only"' in html and 'aria-expanded' not in html:
        notes.append(
            "The navigation toggle carries no `aria-expanded`, so a screen "
            "reader cannot tell whether the rail is open."
        )
    return notes


def audit(pages: dict[str, pathlib.Path], axe_source: str | None) -> dict:
    from playwright.sync_api import sync_playwright

    report: dict = {"axe_available": axe_source is not None, "pages": {}}
    with sync_playwright() as play:
        browser = play.chromium.launch(executable_path=CHROME)
        try:
            for label, (width, height) in WIDTHS.items():
                context = browser.new_context(viewport={"width": width, "height": height})
                page = context.new_page()
                for name, source in pages.items():
                    page.goto(source.resolve().as_uri())
                    page.wait_for_timeout(300)
                    entry = report["pages"].setdefault(name, {})
                    at = entry.setdefault(label, {})
                    if axe_source is not None:
                        results = _axe(page, axe_source)
                        at["violations"] = [
                            {
                                "id": v["id"],
                                "impact": v.get("impact"),
                                "help": v["help"],
                                "count": len(v["nodes"]),
                                "targets": [
                                    n["target"][0] for n in v["nodes"][:4]
                                ],
                            }
                            for v in results["violations"]
                        ]
                        at["passes"] = len(results["passes"])
                        at["incomplete"] = [i["id"] for i in results["incomplete"]]
                    at["tab_order"] = _walk(page)
                    if label == "desktop":
                        entry["notes"] = _static_checks(source.read_text("utf-8"))
                context.close()
        finally:
            browser.close()
    return report


def summarise(report: dict) -> str:
    lines: list[str] = []
    counts: collections.Counter = collections.Counter()
    for name, entry in sorted(report["pages"].items()):
        lines.append(f"\n{name}")
        for width in WIDTHS:
            at = entry.get(width, {})
            violations = at.get("violations")
            if violations is None:
                lines.append(f"  {width:8s} axe not run")
            elif not violations:
                lines.append(
                    f"  {width:8s} clean · {at.get('passes', 0)} checks passed"
                )
            else:
                for violation in violations:
                    counts[violation["id"]] += violation["count"]
                    lines.append(
                        f"  {width:8s} {violation['impact']:8s} "
                        f"{violation['id']} ×{violation['count']} — "
                        f"{violation['help']}"
                    )
                    for target in violation["targets"]:
                        lines.append(f"           {target}")
            order = at.get("tab_order", [])
            unfocusable = [s for s in order if not (s["outline"] or s["shadow"])]
            offscreen = [s for s in order if s["offscreen"]]
            lines.append(
                f"  {width:8s} keyboard: {len(order)} stops, "
                f"{len(unfocusable)} with no visible focus, "
                f"{len(offscreen)} not on screen"
            )
            for stop in unfocusable[:4]:
                lines.append(f"           no focus ring: {stop['tag']}.{stop['cls']} "
                             f"{stop['label']!r}")
            for stop in offscreen[:4]:
                lines.append(f"           zero-size: {stop['tag']}.{stop['cls']} "
                             f"{stop['label']!r}")
        for note in entry.get("notes", []):
            lines.append(f"  note      {note}")
    if counts:
        lines.append("\nBy rule:")
        for rule, total in counts.most_common():
            lines.append(f"  {rule:32s} {total}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--axe", default=os.environ.get("EDIRASX_AXE", ""))
    parser.add_argument("--json", default="")
    parser.add_argument("--only", default="")
    args = parser.parse_args()

    axe_source = None
    if args.axe:
        path = pathlib.Path(args.axe)
        if path.exists():
            axe_source = path.read_text("utf-8")
        else:
            print(f"axe not found at {path}; running the keyboard walk only.")
    else:
        print(
            "No axe-core supplied (--axe or EDIRASX_AXE). The automated checks "
            "will not run and this report must not be read as a pass."
        )

    pages = {p.stem: p for p in sorted(DESIGN.glob("*.html"))}
    if args.only:
        wanted = re.compile(args.only)
        pages = {k: v for k, v in pages.items() if wanted.search(k)}
    if not pages:
        print("Nothing to audit — run tools/design/journeys.py first.")
        return 1

    report = audit(pages, axe_source)
    print(summarise(report))
    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(report, indent=2), "utf-8")
    total = sum(
        v["count"]
        for entry in report["pages"].values()
        for width in WIDTHS
        for v in (entry.get(width, {}).get("violations") or [])
    )
    print(f"\n{len(pages)} pages · {total} axe violations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
