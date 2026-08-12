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
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "edtechx-api"))

from app.modules.design.sheets import SHEETS, fits, sheet_for
from app.modules.documents.library import (
    EDITIONS,
    FAMILIES,
    MEASURED_OVERFLOWS,
    TEMPLATES,
    Template,
    fill,
)
from app.modules.documents.library_sheet import render, sheet_for_template

sys.path.insert(0, str(ROOT))
from tools.design.render import contact, shoot

OUT = ROOT / "docs" / "edtechx" / "design" / "library"

#: One CSS pixel, in millimetres. The measurement floor, and the tolerance.
#:
#: `scrollWidth` and `clientWidth` are integers in CSS pixels, so an element
#: whose width is fractional reports one pixel of overflow that does not exist.
#: Twenty-five compositions sat at exactly 0.26mm — 25.4/96 to two places — and
#: chasing it would have meant tuning a design against a rounding artefact.
#:
#: This is not a loosened standard. It is declining to assert a precision the
#: instrument does not have: below one pixel the browser cannot tell a real
#: overflow from a rounded one, so a claim either way would be invented. At
#: 600 DPI one CSS pixel is six device pixels of a 0.07mm hairline — visible if
#: it were real, and it is not.
_PIXEL = 25.4 / 96 + 0.005
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
    "programme": "Secondary Programme in Islamic and Arabic Studies",
    "rows": (
        "2025 – 2026|Arabic Language and Grammar|3|86|A\n"
        "2025 – 2026|Qurʼanic Studies and Tajwīd|3|91|A\n"
        "2025 – 2026|Islamic Jurisprudence|2|78|B\n"
        "2025 – 2026|Mathematics|3|74|B\n"
        "2025 – 2026|English Language|3|69|C\n"
        "2025 – 2026|History of the Islamic World|2|83|A"
    ),
    "examinations_name": "Examinations Officer's Name",
    "head_of_schools_name": "Head of Schools' Name",
    "award_title": "Prize for Excellence in Arabic Language",
    "award_title_ar": "جائزة التميّز في اللغة العربية",
    "citation": (
        "for sustained excellence in Arabic language and grammar across three "
        "sessions, and for teaching younger pupils without being asked to."
    ),
    "citation_ar": (
        "لتميّزها المستمر في اللغة العربية ونحوها على مدى ثلاثة أعوام، "
        "ولتعليمها من هم أصغر منها دون أن يُطلب منها ذلك."
    ),
    "islamiyyah_level": "Level Four",
    "islamiyyah_level_ar": "المستوى الرابع",
    "resolution": "RES-2026-014",
    "honorific": "Founder and Head of Schools",
    "original_reference": "CERT/2024/000188",
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


def write_pages(source: dict[str, str], folder: str, *,
                sheet: str | None = None,
                edition: str = "original") -> list[pathlib.Path]:
    out = OUT / folder
    out.mkdir(parents=True, exist_ok=True)
    written: list[pathlib.Path] = []
    for key, template in TEMPLATES.items():
        if edition != "original" and template.security_class == "C":
            continue  # a registry document is regenerated, never reissued
        filled = fill(template, values_for(template, source), edition=edition)
        page = out / f"{key}.html"
        page.write_text(render(filled, sheet=sheet), encoding="utf-8")
        written.append(page)
    return written


def size_matrix() -> tuple[list[pathlib.Path], list[str]]:
    """Every template on every sheet it claims to fit, rendered and recorded.

    A claim that a document supports A3 is worth nothing until an A3 of it has
    been composed and measured, so the matrix renders rather than asserts. What
    it writes out is one page per (template, sheet) pair for the sizes each
    template says it fits — and it records, rather than quietly skips, the
    sizes each one refuses.
    """
    # Written outside the repository: 320 pages with embedded fonts is 1.4GB,
    # and what is worth keeping is what the matrix established, not the pages
    # that established it. SIZES.md and the audit result are the deliverable.
    out = pathlib.Path(tempfile.gettempdir()) / "edirasx-size-matrix"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    written: list[pathlib.Path] = []
    refusals: list[str] = []
    for key, template in TEMPLATES.items():
        allowed = set(template.sheets())
        for sheet_key in SHEETS:
            verdict = fits(family=template.family, sheet=sheet_for(sheet_key),
                           border_weight=template.border_weight)
            if sheet_key not in allowed:
                # A size can be refused two ways: by the arithmetic, which
                # gives a reason, or by a recorded measurement, which gives a
                # millimetre count. Both are refusals and both belong in the
                # ledger; only the first has `verdict.reasons`.
                reason = (
                    verdict.reasons[0] if verdict.reasons
                    else "measured on a proof: "
                         + MEASURED_OVERFLOWS[(key, sheet_key)]
                         + " — the arithmetic accepts this size and the press "
                           "proof does not; the proof wins"
                )
                refusals.append(f"{key} × {sheet_key}: {reason}")
                continue
            filled = fill(template, values_for(template, SPECIMEN))
            page = out / f"{key}__{sheet_key}.html"
            page.write_text(render(filled, sheet=sheet_key), encoding="utf-8")
            written.append(page)
    return written, refusals


def audit(pages: list[pathlib.Path]) -> list[tuple[str, float, float]]:
    """Measure every sheet. Returns (key, content overflow mm, field bleed mm).

    Both numbers must be zero, and `content` is now the worse of two
    directions rather than just height. The vertical-only version passed a
    portrait certificate whose bilingual title ran 90mm past the inner rule and
    off the ceremonial field entirely: the column fitted, and the row inside it
    did not. Anything laid out as a row — a peer title, a two-column citation,
    a particulars band — can overflow sideways while the column it sits in
    reports no overflow at all.

    `bleed` is the field's own box crossing the ground's innermost rule. A
    composition can pass both content checks and fail this one, which is the
    case that ships.
    """
    from playwright.sync_api import sync_playwright

    results: list[tuple[str, float, float]] = []
    with sync_playwright() as play:
        browser = play.chromium.launch(executable_path=CHROME)
        view = browser.new_context(viewport={"width": 1500, "height": 1100}).new_page()
        for page in pages:
            view.goto(page.resolve().as_uri())
            view.wait_for_timeout(420)
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
                # HTML blocks only. An SVG child legitimately exceeds its
                # own viewBox — text does not clip to it — and walking into
                # the seal and the verification cartouche reported every sheet
                # in the library as 40–75mm over. What is being asked is
                # whether a *laid-out block* left the field, and an SVG is one
                # block however its internals are drawn.
                " let side = f.scrollWidth - f.clientWidth;"
                " for (const el of f.querySelectorAll('div, table, p, img')) {"
                "   if (el.closest('svg')) continue;"
                "   const r = el.getBoundingClientRect();"
                "   if (!r.width) continue;"
                "   side = Math.max(side, fr.left - r.left, r.right - fr.right);"
                " }"
                " return ["
                "   Math.max(f.scrollHeight - f.clientHeight, side), bleed];"
                "}"
            )
            results.append((
                page.stem,
                max(0.0, measured[0]) * 25.4 / 96.0,
                max(0.0, measured[1]) * 25.4 / 96.0,
            ))
        browser.close()
    return results


def size_ledger(refusals: list[str]) -> str:
    """The sizes each family carries and the ones it refuses, with the reason.

    Grouped by *family* rather than by template, because the refusal is a
    property of the composition and listing it once per template prints the
    same sentence twenty-four times. What varies per template is the border
    weight, and where that changes the answer it is called out.
    """
    lines = [
        "# Sheet sizes: what each family carries, and what it refuses",
        "",
        "A document is composed for a sheet, never scaled onto one. The border",
        "is re-cut from its proportions, the type is re-solved on a",
        "square-root curve, and the instruments — a 0.33mm Code 128 module, a",
        "27mm verification cartouche, an 18mm seal — do not move at all.",
        "",
        "Where the arithmetic says a sheet cannot carry a composition with an",
        "unshrunk verification panel, the size is **refused with the**",
        "**arithmetic** rather than squeezed. A refusal without a number is an",
        "opinion.",
        "",
    ]
    for family_key in FAMILIES:
        members = [t for t in TEMPLATES.values() if t.family == family_key]
        lines += [f"## {family_key.title()}", ""]
        offered: dict[str, list[str]] = {}
        for template in members:
            offered.setdefault(", ".join(template.sheets()),
                               []).append(template.key)
        for sizes, keys in offered.items():
            who = "all" if len(keys) == len(members) else ", ".join(f"`{k}`" for k in keys)
            lines += [f"**Issues on** ({who}): {sizes}", ""]
        reasons: dict[str, str] = {}
        for line in refusals:
            name, reason = line.split(":", 1)
            key, sheet_key = name.split(" × ")
            if TEMPLATES[key].family != family_key:
                continue
            reasons.setdefault(reason.strip(), sheet_key)
        lines += ["**Refuses**, and why:", ""]
        for reason, example in reasons.items():
            lines.append(f"- *(e.g. {example})* {reason}")
        lines.append("")
    return "\n".join(lines)


def inventory() -> str:
    """The library, written out — what was imported and what is editable."""
    lines = [
        "# The imported template library",
        "",
        (f"{len(TEMPLATES)} documents in {len(FAMILIES)} composition "
         "families, brought across from"),
        ("the benchmark press and made editable. Every layout, every band "
         "position and every"),
        ("institutional sentence is transcribed; every name is a slot with a "
         "generic default."),
        "",
        "## Reference-number families",
        "",
        "| Code | Documents | Class |",
        "|---|---|---|",
    ]
    by_code: dict[str, list] = {}
    for template in TEMPLATES.values():
        by_code.setdefault(template.code, []).append(template)
    for code in sorted(by_code):
        members = by_code[code]
        names = ", ".join(t.name for t in members)
        classes = "/".join(sorted({t.security_class for t in members}))
        lines.append(f"| `{code}` | {names} | {classes} |")
    lines.append("")
    for family_key, description in FAMILIES.items():
        members = [t for t in TEMPLATES.values() if t.family == family_key]
        lines += [f"## {family_key.title()} — {len(members)} templates", "",
                  description, ""]
        for template in members:
            built = sheet_for_template(fill(template, values_for(template, SPECIMEN)))
            lines += [
                f"### {template.name}",
                "",
                f"- **Key** `{template.key}`  ",
                f"- **Arabic title** {template.name_ar}  ",
                (f"- **Reference family** `{template.code}` · "
                 f"security class {template.security_class}  "),
                (f"- **Designed at** {template.sheet}, "
                 f"{built.width:g} × {built.height:g}mm  "),
                ("- **Also issues on** "
                 + ", ".join(k for k in template.sheets()
                             if k != template.sheet) + "  "),
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


def report(label: str, pages: list[pathlib.Path], failures: list[str], *,
           quiet: bool = False) -> None:
    if not quiet:
        print(f"\n{label}")
    for key, over, bleed in audit(pages):
        ok = over <= _PIXEL and bleed <= _PIXEL
        if not ok:
            failures.append(f"{label}/{key}: {over:.2f}mm over, "
                            f"{bleed:.2f}mm outside the field")
        if not quiet:
            print(f"  {key:36s} {'fits' if ok else 'OVERFLOWS':10s} "
                  f"content {over:5.2f}mm · field {bleed:5.2f}mm")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    specimen = write_pages(SPECIMEN, "specimen")
    hostile = write_pages(HOSTILE, "hostile")
    print(f"wrote {len(specimen)} specimen and {len(hostile)} hostile sheets")
    (OUT / "INVENTORY.md").write_text(inventory(), encoding="utf-8")

    report("specimen", specimen, failures)
    report("hostile", hostile, failures)

    # Reissuance. A copy notice that a composition cannot accommodate is a copy
    # notice somebody will be tempted to remove, so both editions are measured
    # rather than assumed to be free.
    print("\neditions")
    for key in EDITIONS:
        if key == "original":
            continue
        pages = write_pages(SPECIMEN, f"edition-{key}", edition=key)
        report(f"edition-{key}", pages, failures, quiet=True)
        print(f"  {key:20s} {len(pages)} sheets")

    # Every size each template claims. A claim is not a rendering.
    matrix, refusals = size_matrix()
    print(f"\nsizes: {len(matrix)} compositions rendered, "
          f"{len(refusals)} sheet sizes honestly refused")
    report("sizes", matrix, failures, quiet=True)
    (OUT / "SIZES.md").write_text(size_ledger(refusals), encoding="utf-8")

    shots = shoot(specimen, OUT / "shots")
    contact(shots, OUT / "contact-sheet.png", columns=4, width=540)
    print(f"\ncontact sheet → {OUT / 'contact-sheet.png'}")

    if failures:
        print(f"\nCOMPOSITIONS THAT DO NOT FIT ({len(failures)}):")
        for line in failures[:40]:
            print(f"  {line}")
        return 1
    print("\nEvery composition fits, at every size it claims, in every edition.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
