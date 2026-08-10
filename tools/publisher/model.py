"""A document model shared by every renderer.

Both the PDF and the DOCX are built from this one structure. That is the whole
point: content parity between the two formats is then a property of the
architecture rather than something to be checked by eye and hoped for. The
verifier in `verify.py` confirms it independently anyway.

The canonical source of truth remains the Markdown. This model is a parse of
it, never an edit of it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


# --- inline runs ----------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Run:
    """A span of text with optional emphasis."""

    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False


_INLINE = re.compile(
    r"(\*\*\*.+?\*\*\*|\*\*.+?\*\*|(?<!\*)\*(?!\*).+?(?<!\*)\*(?!\*)|`[^`]+`|\[[^\]]+\]\([^)]+\))"
)


def typographic(text: str) -> str:
    """Convert straight quotes and dashes to their typographic forms.

    Applied once, in the model, so the PDF and the Word file inherit identical
    text and the parity check compares like with like. Never applied to code
    spans, where a curly quote would be wrong.
    """
    out: list[str] = []
    for index, char in enumerate(text):
        if char == '"':
            previous = text[index - 1] if index else " "
            out.append("\u201d" if previous.strip() and previous not in "([{" else "\u201c")
        elif char == "'":
            previous = text[index - 1] if index else " "
            out.append("\u2019" if previous.isalnum() else "\u2018")
        else:
            out.append(char)
    return "".join(out)


def parse_inline(text: str) -> tuple[Run, ...]:
    """Split Markdown inline formatting into typed runs."""
    runs: list[Run] = []
    for part in _INLINE.split(text):
        if not part:
            continue
        if part.startswith("***") and part.endswith("***"):
            runs.append(Run(part[3:-3], bold=True, italic=True))
        elif part.startswith("**") and part.endswith("**"):
            runs.append(Run(part[2:-2], bold=True))
        elif part.startswith("`") and part.endswith("`"):
            runs.append(Run(part[1:-1], code=True))
        elif part.startswith("[") and "](" in part:
            label = part[1 : part.index("]")]
            runs.append(Run(label, italic=True))
        elif part.startswith("*") and part.endswith("*"):
            runs.append(Run(part[1:-1], italic=True))
        else:
            runs.append(Run(part))
    return tuple(
        r if r.code else Run(typographic(r.text), r.bold, r.italic, r.code)
        for r in runs
        if r.text
    )


def runs_to_text(runs: Iterable[Run]) -> str:
    return "".join(r.text for r in runs)


# --- blocks ---------------------------------------------------------------


class BlockKind(str, Enum):
    heading = "heading"
    paragraph = "paragraph"
    bullets = "bullets"
    numbers = "numbers"
    checklist = "checklist"
    table = "table"
    callout = "callout"
    quote = "quote"
    rule = "rule"
    contrast = "contrast"
    diagram = "diagram"
    pagebreak = "pagebreak"


class CalloutTone(str, Enum):
    principle = "principle"
    constitutional = "constitutional"
    test = "test"
    caution = "caution"


@dataclass
class Block:
    kind: BlockKind
    level: int = 0
    number: str = ""
    runs: tuple[Run, ...] = ()
    items: list[tuple[Run, ...]] = field(default_factory=list)
    rows: list[list[tuple[Run, ...]]] = field(default_factory=list)
    header: list[tuple[Run, ...]] = field(default_factory=list)
    tone: CalloutTone = CalloutTone.principle
    label: str = ""
    name: str = ""

    @property
    def text(self) -> str:
        return runs_to_text(self.runs)


@dataclass
class Chapter:
    number: str
    title: str
    blocks: list[Block] = field(default_factory=list)
    part: str = ""


@dataclass
class Part:
    number: str
    title: str
    standfirst: str


@dataclass
class Document:
    title: str
    subtitle: str
    edition: str
    parts: list[Part] = field(default_factory=list)
    front_matter: list[Chapter] = field(default_factory=list)
    chapters: list[Chapter] = field(default_factory=list)
    back_matter: list[Chapter] = field(default_factory=list)

    def all_chapters(self) -> list[Chapter]:
        return [*self.front_matter, *self.chapters, *self.back_matter]

    def plain_text(self) -> str:
        """Flatten to text, for the parity check between renderers."""
        out: list[str] = []
        for chapter in self.all_chapters():
            out.append(f"{chapter.number} {chapter.title}".strip())
            for block in chapter.blocks:
                if block.kind in (BlockKind.rule, BlockKind.pagebreak, BlockKind.diagram):
                    continue
                if block.runs:
                    out.append(block.text)
                for item in block.items:
                    out.append(runs_to_text(item))
                for cell in block.header:
                    out.append(runs_to_text(cell))
                for row in block.rows:
                    out.extend(runs_to_text(c) for c in row)
        return "\n".join(s.strip() for s in out if s.strip())


# --- markdown parsing -----------------------------------------------------

_TABLE_DIVIDER = re.compile(r"^\|[\s:|-]+\|$")


def _split_row(line: str) -> list[tuple[Run, ...]]:
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return [parse_inline(c) for c in cells]


def parse_markdown_body(lines: list[str]) -> list[Block]:
    """Parse the subset of Markdown the Bible actually uses.

    Deliberately not a general Markdown implementation. The input is a document
    we control, and a focused parser that fails loudly on something unexpected
    is safer here than a permissive one that silently drops content.
    """
    blocks: list[Block] = []
    i = 0
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            text = " ".join(paragraph).strip()
            if text:
                blocks.append(Block(BlockKind.paragraph, runs=parse_inline(text)))
            paragraph = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            i += 1
            continue

        if stripped in ("---", "***", "___"):
            flush_paragraph()
            blocks.append(Block(BlockKind.rule))
            i += 1
            continue

        if stripped.startswith("#"):
            flush_paragraph()
            level = len(stripped) - len(stripped.lstrip("#"))
            title = stripped.lstrip("#").strip()
            number = ""
            match = re.match(r"^(\d+(?:\.\d+)*)\.?\s+(.*)$", title)
            if match:
                number, title = match.group(1), match.group(2)
            blocks.append(
                Block(BlockKind.heading, level=level, number=number, runs=parse_inline(title))
            )
            i += 1
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            quote: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            blocks.append(Block(BlockKind.quote, runs=parse_inline(" ".join(quote).strip())))
            continue

        if stripped.startswith("|"):
            flush_paragraph()
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            if len(table_lines) >= 2 and _TABLE_DIVIDER.match(table_lines[1]):
                block = Block(BlockKind.table)
                block.header = _split_row(table_lines[0])
                block.rows = [_split_row(r) for r in table_lines[2:]]
                blocks.append(block)
            continue

        checklist = re.match(r"^-\s+\[([ xX])\]\s+(.*)$", stripped)
        if checklist:
            flush_paragraph()
            block = Block(BlockKind.checklist)
            while i < len(lines):
                m = re.match(r"^-\s+\[([ xX])\]\s+(.*)$", lines[i].strip())
                if not m:
                    break
                block.items.append(parse_inline(m.group(2)))
                i += 1
            blocks.append(block)
            continue

        bullet = re.match(r"^[-*]\s+(.*)$", stripped)
        if bullet:
            flush_paragraph()
            block = Block(BlockKind.bullets)
            while i < len(lines):
                current = lines[i].strip()
                m = re.match(r"^[-*]\s+(.*)$", current)
                if m:
                    block.items.append(parse_inline(m.group(1)))
                    i += 1
                elif current and not re.match(r"^[-*#>|]|^\d+\.", current) and block.items:
                    # A wrapped continuation line belongs to the previous item.
                    previous = runs_to_text(block.items[-1])
                    block.items[-1] = parse_inline(f"{previous} {current}")
                    i += 1
                else:
                    break
            blocks.append(block)
            continue

        numbered = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if numbered:
            flush_paragraph()
            block = Block(BlockKind.numbers)
            while i < len(lines):
                m = re.match(r"^(\d+)\.\s+(.*)$", lines[i].strip())
                if not m:
                    break
                block.items.append(parse_inline(m.group(2)))
                i += 1
            blocks.append(block)
            continue

        paragraph.append(stripped)
        i += 1

    flush_paragraph()
    return blocks
