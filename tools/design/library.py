"""Proof the imported template library: render all fifteen, then measure them.

Two jobs. The first is to look at the work — every imported template rendered at
full size onto real paper geometry, plus a contact sheet, because a template
that reads acceptably alone and thin next to fourteen others has been judged
correctly. The second is to measure it, and that is the job the eye cannot do:
the same defect class — content leaving the field and landing on the border —
was found by eye four times in this project and never once by looking harder.

So every sheet goes through the collision audit before anything is reported as
finished, and the audit measures two things rather than one:

    content vs field   does the flow overflow the column it was given
    field vs sheet     does the field itself sit inside the ground's own
                       margin, or has it been tuned outward until it crosses
                       the innermost rule

Tuning those separately is how a masthead gets clipped and a verification code
gets cut in half while every individual measurement passes.

Run: ``python tools/design/library.py``
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "edtechx-api"))

from app.modules.documents.library import (
    FAMILIES,
    TEMPLATES,
    Template,
    fill,
)
from app.modules.documents.library_sheet import render, sheet_for

sys.path.insert(0, str(ROOT))
from tools.design.render import contact, shoot

OUT = ROOT / "docs" / "edtechx" / "design" / "library"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

#: A specimen institution. Every value is obviously a specimen — nobody should
#: be able to mistake a proof for an issued document, and "Meridian Institute"
#: on a sheet with a real-looking serial is exactly how that mistake happens.
SPECIMEN: dict[str, str] = {
    "institution": "Meridian Institute of Advanced Study",
    "institution_ar": "معهد ميريديان للدراسات العليا",
    "school": "School of Islamic and Arabic Studies",
    "school_ar": "كلية الدراسات الإسلامية والعربية",
    "recipient": "Fatimah Adenike Oyelaran-Balogun",
    "recipient_ar": "فاطمة أدينيكي أويلاران بالوغون",
    "student_id": "MIA-2026-004173",
    "session": "2025 – 2026",
    "issued_on": "14 March 2026",
    "issued_on_hijri": "٢٥ شعبان ١٤٤٧",
    "place": "Ikorodu, Lagos, Nigeria",
    "place_ar": "إكورودو، لاغوس، نيجيريا",
    "serial": "SPECIMEN/2026/000417",
    "document_id": "DID-2026-SPEC-0004173",
    "verification_code": "8FQ4-DRNM-7VZ2",
    "archive_reference": "ARCH/SPEC/2026/004173",
    "verify_url": "verify.example.edu",
    "principal_name": "Principal's Name",
    "chairman_name": "Chairman's Name",
    "head_name": "Head of School's Name",
    "registrar_name": "Registrar's Name",
    "graduate_id": "ALM-004173",
    "testimonial_text": (
        "She read Arabic and mathematics with equal seriousness, led the "
        "debating society for two years, and was trusted by younger pupils "
        "in a way that cannot be taught. She leaves with our confidence."
    ),
    "clearance_rows": (
        "Library|Cleared|A. Bello|3 January 2026\n"
        "Finance|Cleared|M. Idris|5 January 2026\n"
        "Boarding|N/A|—|—\n"
        "Academic Office|Cleared|R. Salawu|9 January 2026"
    ),
    "register_rows": (
        "1|Fatimah Adenike Oyelaran-Balogun|MIA-2026-004173|Secondary|SS 3A\n"
        "2|Abdulrahman Kolawole Shittu|MIA-2026-004174|Secondary|SS 3A\n"
        "3|Zainab Omotola Ajibade|MIA-2026-004175|Secondary|SS 3B\n"
        "4|Yusuf Oluwaseun Ogunleye|MIA-2026-004176|Secondary|SS 3B"
    ),
}

#: The hostile case. Not a stress test for its own sake: every one of these is
#: something a real registry produces, and a composition that only holds for the
#: specimen is a composition that fails in its second week.
HOSTILE: dict[str, str] = {
    **SPECIMEN,
    "institution": (
        "The Chartered Institute of Advanced Theological, Linguistic and "
        "Comparative Jurisprudential Studies"
    ),
    "recipient": "Muhammad-Awwal Oluwadamilare Adeyemi-Onaolapo",
    "recipient_ar": "محمد الأول أولوادميلاري أديمي أوناولابو",
    "session": "2025/2026 – 2026/2027",
    "student_id": "MIA-2026-000000000004173",
    "principal_name": "Prof. Abdul-Rahman Olanrewaju Bakare-Oyediran",
    "chairman_name": "Dr. Zakariyyah Olanrewaju Hanafi-Adeyinka",
    "head_name": "Dr. Zakariyyah Olanrewaju Hanafi-Adeyinka",
    "registrar_name": "Mrs. Mariam Tope Anofi-AbdulKareem",
}


def values_for(template: Template, source: dict[str, str]) -> dict[str, str]:
    """Only the slots this template actually has.

    `fill` refuses unknown keys on purpose — a caller passing `principal_name`
    to a template whose office is `head` has silently printed the default over
    the value they supplied — so the specimen is filtered rather than the
    refusal weakened.
    """
    return {k: v for k, v in source.items() if k in template.slot_keys}


def write_pages(source: dict[str, str], folder: str) -> list[pathlib.Path]:
    out = OUT / folder
    out.mkdir(parents=True, exist_ok=True)
    written: list[pathlib.Path] = []
    for key, template in TEMPLATES.items():
        filled = fill(template, values_for(template, source))
        page = out / f"{key}.html"
        page.write_text(render(filled), encoding="utf-8")
        written.append(page)
    return written


def audit(pages: list[pathlib.Path]) -> list[tuple[str, float, float]]:
    """Measure every sheet. Returns (key, content overflow mm, field bleed mm).

    Both numbers must be zero. `content` is the flow above the field's own
    height; `bleed` is the field's own box crossing the ground's innermost
    rule. A composition can pass the first and fail the second, which is the
    case that ships.
    """
    from playwright.sync_api import sync_playwright

    results: list[tuple[str, float, float]] = []
    with sync_playwright() as play:
        browser = play.chromium.launch(executable_path=CHROME)
        view = browser.new_context(viewport={"width": 1500, "height": 1100}).new_page()
        for page in pages:
            view.goto(page.resolve().as_uri())
            view.wait_for_timeout(650)
            measured = view.evaluate(
                "() => {"
                " const f = document.querySelector('.field');"
                " const s = document.querySelector('.sheet');"
                " if (!f || !s) return [0, 0];"
                " const fr = f.getBoundingClientRect();"
                " const sr = s.getBoundingClientRect();"
                " const bleed = Math.max(0,"
                "   sr.top - fr.top, sr.left - fr.left,"
                "   fr.bottom - sr.bottom, fr.right - sr.right);"
                " return [f.scrollHeight - f.clientHeight, bleed];"
                "}"
            )
            results.append((
                page.stem,
                max(0.0, measured[0]) * 25.4 / 96.0,
                max(0.0, measured[1]) * 25.4 / 96.0,
            ))
        browser.close()
    return results


def inventory() -> str:
    """The library, written out — what was imported and what is editable."""
    lines = [
        "# The imported template library",
        "",
        "Fifteen documents, brought across from the benchmark press and made",
        "editable. Every layout, every band position and every institutional",
        "sentence is transcribed; every name is a slot with a generic default.",
        "",
    ]
    for family_key, description in FAMILIES.items():
        members = [t for t in TEMPLATES.values() if t.family == family_key]
        lines += [f"## {family_key.title()} — {len(members)} templates", "",
                  description, ""]
        for template in members:
            built = sheet_for(fill(template, values_for(template, SPECIMEN)))
            lines += [
                f"### {template.name}",
                "",
                f"- **Key** `{template.key}`  ",
                f"- **Arabic title** {template.name_ar}  ",
                (f"- **Sheet** {template.sheet}, "
                 f"{built.width:g} × {built.height:g}mm  "),
                f"- **Ceremonial level** {template.level}  ",
                f"- **Language architecture** {template.language}  ",
                f"- **Metal scheme** {template.scheme}  ",
                f"- **Editable slots** {len(template.slots)}  ",
                f"- **Content field** {built.field.w:.1f} × {built.field.h:.1f}mm",
                "",
                f"{template.provenance}",
                "",
            ]
            if template.notes:
                lines += [f"> {template.notes}", ""]
            if template.security:
                lines += ["Security registers drawn on this sheet:", ""]
                lines += [f"- {item}" for item in template.security]
                lines += [""]
    return "\n".join(lines)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    specimen = write_pages(SPECIMEN, "specimen")
    hostile = write_pages(HOSTILE, "hostile")
    print(f"wrote {len(specimen)} specimen and {len(hostile)} hostile sheets")

    (OUT / "INVENTORY.md").write_text(inventory(), encoding="utf-8")

    failures: list[str] = []
    for label, pages in (("specimen", specimen), ("hostile", hostile)):
        print(f"\n{label}")
        for key, over, bleed in audit(pages):
            state = "fits" if over <= 0.05 and bleed <= 0.05 else "OVERFLOWS"
            if state != "fits":
                failures.append(f"{label}/{key}: {over:.2f}mm over, "
                                f"{bleed:.2f}mm outside the field")
            print(f"  {key:34s} {state:10s} "
                  f"content {over:5.2f}mm · field {bleed:5.2f}mm")

    shots = shoot(specimen, OUT / "shots")
    contact(shots, OUT / "contact-sheet.png", columns=3)
    print(f"\ncontact sheet → {OUT / 'contact-sheet.png'}")

    if failures:
        print("\nCOMPOSITIONS THAT DO NOT FIT:")
        for line in failures:
            print(f"  {line}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
