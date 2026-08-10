"""Turning a file somebody exported from something else into rows.

This is the least glamorous part of the import pipeline and the part that
decides whether it works. Real files from real schools are not clean: they
arrive with a byte-order mark, with semicolons because the exporting machine
was set to a European locale, with three blank rows above the header because
somebody typed a title, with `=1+1` in a cell, and with trailing spaces on
every column name.

Two rules govern everything here:

  **Nothing is interpreted.** Every value comes back as a string exactly as it
  was written, with only surrounding whitespace removed. A leading zero on an
  admission number is data, not a formatting accident, and a date is text until
  a field that knows its format says otherwise. Readers that helpfully parse
  are the reason imported records are subtly wrong in ways nobody notices for a
  term.

  **Line numbers are the file's, not the list's.** An error report that says
  "row 14" must mean the fourteenth line of the file the person is looking at,
  including the header and any blank rows above it. Off-by-one here turns a
  precise error report into a puzzle.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field

# A cell spreadsheet software would execute on open. Prefixing on *export* is
# the real defence against formula injection; flagging on import makes a
# malicious file visible rather than merely inert.
#
# Deliberately narrower than the usual advice, which names "+" and "-" outright.
# A great many real phone numbers begin with "+", and a great many real figures
# begin with "-": rejecting those would break ordinary imports across whole
# countries in the name of a risk that lives at export time. So a leading "+"
# or "-" counts only when what follows could start a function name.
FORMULA_PREFIXES = ("=", "@", "\t=", "\r=", "\t@", "\r@")

MAX_ROWS = 20_000
MAX_COLUMNS = 200
MAX_CELL_LENGTH = 4_000


class ImportFileError(ValueError):
    """The file cannot be read at all. Distinct from a row that fails validation."""


@dataclass(frozen=True, slots=True)
class SourceRow:
    """One line of the file, keyed by its header, with the line number kept."""

    line_number: int
    values: dict[str, str]

    def get(self, column: str) -> str:
        return self.values.get(column, "")


@dataclass(slots=True)
class SourceTable:
    columns: list[str]
    rows: list[SourceRow] = field(default_factory=list)
    # Columns whose header was blank or duplicated, and the substitute used.
    notes: list[str] = field(default_factory=list)

    @property
    def row_count(self) -> int:
        return len(self.rows)

    def sample(self, limit: int = 10) -> list[SourceRow]:
        return self.rows[:limit]


def _clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    # Excel writes a trailing ".0" onto every integer it thinks is a number, so
    # an admission number typed as 004512 comes back as "4512.0". Stripping the
    # decimal tail of an otherwise-integral float is the least-surprising
    # reading; the leading zeros are already gone by then, which is why the
    # duplicate check compares on the school's own reference rather than
    # assuming this reader recovered it perfectly.
    if text.endswith(".0") and text[:-2].lstrip("-").isdigit():
        text = text[:-2]
    return text.strip()[:MAX_CELL_LENGTH]


def _headers(raw: list[str]) -> tuple[list[str], list[str]]:
    """Normalise a header row, keeping every column addressable.

    A blank or duplicated header is not an error — exports produce both — but a
    column nobody can name cannot be mapped, so each gets a stable substitute
    and a note the person can see.
    """
    columns: list[str] = []
    notes: list[str] = []
    seen: dict[str, int] = {}
    for index, value in enumerate(raw):
        name = _clean(value)
        if not name:
            name = f"column_{index + 1}"
            notes.append(f"Column {index + 1} had no heading; it is shown as {name!r}.")
        if name in seen:
            seen[name] += 1
            replacement = f"{name} ({seen[name]})"
            notes.append(
                f"Column {index + 1} repeats the heading {name!r}; "
                f"shown as {replacement!r}."
            )
            name = replacement
        else:
            seen[name] = 1
        columns.append(name)
    return columns, notes


def _first_populated(rows: list[list[str]]) -> int:
    """The index of the header row, skipping blank lines above it.

    Files exported by hand routinely carry a title and an empty line before the
    real header. Refusing them would be defensible and would also mean every
    such school gives up at the first step.
    """
    for index, row in enumerate(rows):
        if any(_clean(cell) for cell in row):
            return index
    raise ImportFileError("The file contains no data.")


def _assemble(grid: list[list[str]]) -> SourceTable:
    if not grid:
        raise ImportFileError("The file contains no data.")
    header_index = _first_populated(grid)
    columns, notes = _headers(grid[header_index])
    if len(columns) > MAX_COLUMNS:
        raise ImportFileError(
            f"The file has {len(columns)} columns; the limit is {MAX_COLUMNS}."
        )

    rows: list[SourceRow] = []
    for offset, raw in enumerate(grid[header_index + 1 :], start=header_index + 2):
        values = {
            column: _clean(raw[index]) if index < len(raw) else ""
            for index, column in enumerate(columns)
        }
        if not any(values.values()):
            continue  # a wholly blank line is a separator, not a record
        rows.append(SourceRow(line_number=offset, values=values))
        if len(rows) > MAX_ROWS:
            raise ImportFileError(
                f"The file has more than {MAX_ROWS} rows. Split it and import in parts."
            )
    return SourceTable(columns=columns, rows=rows, notes=notes)


def read_csv(data: bytes) -> SourceTable:
    """Read comma-, semicolon-, or tab-separated text.

    The delimiter is sniffed rather than assumed: a school in a locale where
    the list separator is a semicolon exports semicolons, and telling them
    their file is malformed would be both wrong and unhelpful.
    """
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:  # pragma: no cover - latin-1 decodes any byte string
        raise ImportFileError("The file's text encoding could not be determined.")

    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel  # a single-column file sniffs as nothing; that is fine
    return _assemble([list(row) for row in csv.reader(io.StringIO(text), dialect)])


def read_xlsx(data: bytes) -> SourceTable:
    """Read the first worksheet of an XLSX file.

    `data_only=True` reads the *cached values* of formulas rather than their
    text, which is what the person looking at the spreadsheet sees. A file
    saved by a tool that stores no cached values yields blanks, and that shows
    up in the preview rather than silently importing formula source.
    """
    import openpyxl

    try:
        workbook = openpyxl.load_workbook(
            io.BytesIO(data), read_only=True, data_only=True
        )
    except Exception as exc:  # openpyxl raises a wide family for a bad file
        raise ImportFileError("The file could not be opened as a spreadsheet.") from exc
    try:
        sheet = workbook.worksheets[0]
        grid = [
            [_clean(cell) for cell in row]
            for row in sheet.iter_rows(values_only=True)
        ]
    finally:
        workbook.close()
    return _assemble(grid)


def read(data: bytes, *, filename: str) -> SourceTable:
    """Read a file by its extension, refusing anything else by name."""
    lowered = filename.lower()
    if lowered.endswith(".csv") or lowered.endswith(".txt"):
        return read_csv(data)
    if lowered.endswith(".xlsx"):
        return read_xlsx(data)
    raise ImportFileError(
        f"{filename!r} is not a supported file type. Upload a .csv or .xlsx file."
    )


def looks_like_a_formula(value: str) -> bool:
    """Whether a cell would be executed by spreadsheet software on open."""
    text = value.lstrip()
    if text.startswith(FORMULA_PREFIXES):
        return True
    # "+SUM(...)" and "-cmd|..." are formulas; "+2348012345678" and "-12.50"
    # are a telephone number and a credit note.
    return len(text) > 1 and text[0] in "+-" and (text[1].isalpha() or text[1] == "(")
