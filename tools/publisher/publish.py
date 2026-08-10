"""Build the flagship Editorial Bible in both formats, then verify both."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from bible import build_document  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[2] / "docs" / "edtechx" / "publications"
PDF = OUT / "EDIRASX_Flagship_Editorial_Bible.pdf"
DOCX = OUT / "EDIRASX_Flagship_Editorial_Bible.docx"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    document = build_document()

    import render_pdf
    render_pdf.render(document, PDF)
    print(f"PDF   {PDF}  {PDF.stat().st_size/1024:.0f} KB")

    try:
        import render_docx
        render_docx.render(document, DOCX)
        print(f"DOCX  {DOCX}  {DOCX.stat().st_size/1024:.0f} KB")
    except ModuleNotFoundError:
        print("DOCX  (renderer not yet present)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
