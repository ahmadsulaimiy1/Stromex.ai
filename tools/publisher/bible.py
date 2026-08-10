"""Build the flagship publication model from the canonical Editorial Bible.

The numbered chapters are a faithful parse of `EDTECHX_EDITORIAL_BIBLE.md`.
Front matter, part dividers, callout promotion, and diagrams are *publication
apparatus*: they change how the document is presented, never what it says. The
colophon states this so a reader knows which is which, and `verify.py` asserts
that every chapter's substantive text survives into both output formats.
"""

from __future__ import annotations

import pathlib
import re

from model import (
    Block,
    BlockKind,
    CalloutTone,
    Chapter,
    Document,
    Part,
    parse_inline,
    parse_markdown_body,
    runs_to_text,
)

REPO = pathlib.Path(__file__).resolve().parents[2]
SOURCE = REPO / "docs" / "edtechx" / "EDTECHX_EDITORIAL_BIBLE.md"

EDITION = "Official Edition · Version 1.0"

# Chapter number -> the part it belongs to.
PARTS: list[tuple[Part, set[str]]] = [
    (
        Part(
            "I",
            "Foundation",
            "What EdirasX is, what it believes, and the consequences those "
            "beliefs have for the engineering.",
        ),
        {"0", "1", "2"},
    ),
    (
        Part(
            "II",
            "Experience",
            "How the product behaves, how it looks, and for whom — the six "
            "people whose working lives it touches.",
        ),
        {"3", "4", "5", "6"},
    ),
    (
        Part(
            "III",
            "Constitutions",
            "Three commitments that bind every future decision: about "
            "intelligence, about flexibility, and about culture.",
        ),
        {"7", "8", "9"},
    ),
    (
        Part(
            "IV",
            "Standards",
            "The lines that are not crossed, the bar that must be met, and "
            "how this document itself is changed.",
        ),
        {"10", "11", "12"},
    ),
]


def part_for(number: str) -> Part | None:
    root = number.split(".")[0]
    for part, members in PARTS:
        if root in members:
            return part
    return None


# --- publication apparatus ------------------------------------------------

COLOPHON = """
## About this document

This is the official publication edition of the EdirasX Editorial Bible.

The canonical, editable source is `docs/edtechx/EDTECHX_EDITORIAL_BIBLE.md` in
the EdirasX repository. This edition is generated from that file by
`tools/publisher`, which builds one document model and renders it to both PDF
and Word. Content parity between the two formats is therefore a property of how
they are produced, not a claim made after the fact — and it is verified
independently on every build.

**What is faithful to the source.** Every numbered chapter. Every principle,
requirement, constraint, table, and acceptance criterion.

**What is publication apparatus.** This colophon, the note on the name, the
executive statement, the part dividers and their standfirsts, the table of
contents, running heads, page numbers, the promotion of certain paragraphs into
callout boxes, two explanatory diagrams, and the closing declaration. These
change how the document is presented. They do not change what it says.

**Amendment.** Amending this Bible means amending the Markdown source and
recording the change in `EDTECHX_DECISIONS.md`. Editing this PDF or Word file
amends nothing. Silent divergence between this document and the product is a
defect — in the product or in this document — never an acceptable steady state.
"""

NOTE_ON_THE_NAME = """
## A note on the name

This document is published under the name **EdirasX**.

The name derives from the Arabic root of study and learning — الدراسة
(*al-dirāsa*, "study") and ادرس (*idrus*, "study!") — with the X carrying the
meaning it has always carried in this product: the variable each school fills
in with its own identity. The platform was developed under the working name
EdirasX, which named a category rather than a company; EdirasX names what the
product is for.

**One inconsistency, stated rather than hidden.** The repository, package
names, documentation filenames, configuration prefix, and database roles still
use the earlier `edtechx` namespace. That migration is scheduled separately and
deliberately: renaming those identifiers touches the database roles and grants
that tenant isolation depends on, and that work belongs in its own change, with
the isolation suite as its gate — not folded into a branding commit whose
review attention is on wording.

Product-facing text uses EdirasX without exception. The decision, its
reasoning, and the migration it still owes are recorded in
`EDTECHX_DECISIONS.md` as ADR-017, which is authoritative wherever the two
names appear together.
"""

EXECUTIVE_STATEMENT = """
## Executive statement

Schools do not lack software. They lack software that feels like theirs.

The market has settled into two disappointing shapes. On one side, learning
platforms with genuine depth and an interface no institution would present with
pride. On the other, school-management systems that run the operation
competently and leave teaching to a second, disconnected product. Between them
sits a seam that every school reconciles by hand, every term, forever.

EdirasX is built on a single conviction: **the education platform should become
your school's own platform.** Not a system a school adopts, but the environment
in which a school becomes itself. Its mark, its colours, its vocabulary, its
academic structure, its documents, its address. EdirasX is the engine
underneath; the school owns the experience.

That conviction is not a marketing position. It is an architectural
constraint, and it decides things. It is why every visual value is a
tenant-resolvable token rather than a constant. It is why a class may be called
a form and a grade a year, and why no domain noun is ever a literal in the
interface. It is why terms, levels, grading scales, attendance codes, and
promotion rules are data rather than code — and why the test of that claim is
four genuinely different institutions configured without a single line changed.

Three further commitments shape everything that follows.

**Isolation is structural.** A school's data must be unreachable from another
school, and that guarantee cannot rest on a developer remembering a condition.
It is enforced in the database itself, and proven by a test suite generated from
the schema so that new tables are covered by existing rather than by diligence.

**Intelligence assists; it does not decide.** No artificial intelligence in
EdirasX writes to a grade, an attendance mark, an invoice, or a published
result without a persisted proposal and an attributed human approval. This is
enforced in code, with a test that attempts the bypass and must fail. The moment
a school cannot trust that its records were changed by a person, the product is
finished, and no amount of accuracy recovers it.

**Prestige is precision, not decoration.** It is typography, proportion,
restraint, and alignment — not gradients, shadows, and motion. The standard is
that a prestigious institution would project a screen in a board meeting, and a
teacher would be content to use it every day for a year. Both halves must hold.

What follows is the constitution of the product. It is written to be used, not
admired: every principle is stated so that it can be applied as a test, and any
principle that cannot be used to reject something does not belong in this
document.
"""

CREDITS = """
## Credits and custody

**Imam Ahmad Sulaimiy** — Senior Developer, and the expert behind the
development of EdirasX. The product\u2019s architecture, its engineering
standards, and the principles set out in this Bible are held to his direction.

**Custodian of this document.** Amendments to the EdirasX Editorial Bible are
made under his authority, by the procedure in Chapter 12: an amendment to the
canonical Markdown source, accompanied by an entry in the decision record
stating the principle changed, the reason, and the consequences.

**How this edition was produced.** Rendered from
`docs/edtechx/EDTECHX_EDITORIAL_BIBLE.md` by `tools/publisher`, which builds a
single document model and renders it to both PDF and Word. Content parity
between the two formats is a property of that build rather than a claim made
after the fact, and it is re-verified against the finished files on every
release: every chapter, every substantial line of source prose, and every
sentence of the document is confirmed present in both.

**Typeset in** Source Serif 4 and Inter, with IBM Plex Mono for identifiers and
Amiri for Arabic. All four are open-licence.
"""

CLOSING_DECLARATION = """
## Closing declaration

This Bible is the supreme governing authority of the EdirasX product.

Where any specification, design, roadmap, or line of code conflicts with what
is written here, this document wins — until it is formally amended by the
procedure in Chapter 12.

It exists because the alternative is worse. A product built without a
constitution accumulates decisions nobody made deliberately: a colour chosen
because it was to hand, a hard-coded term because one school used it, an
authorization check placed where it was convenient. Those decisions do not
announce themselves. They surface years later as the reason a school cannot be
served, an audit cannot be passed, or a rewrite cannot be avoided.

Every principle here has therefore been written so that it can be used to say
no. That is the test of a principle, and it is why this document is shorter and
more specific than it could have been.

Three obligations follow for anyone building on it.

**Read it before deciding, not after.** When the specification is silent, the
answer is derived here — from the principles, not from preference. That is what
makes a distributed team, over years, produce a coherent product rather than an
assortment of reasonable choices.

**Amend it rather than diverge from it.** A principle that no longer serves the
product should be changed openly, with its reasoning and its cost recorded.
Quietly building against it is how a constitution becomes decoration.

**Hold the standard when it is inconvenient.** The non-negotiables in Chapter 10
and the definition of done in Chapter 11 are worth precisely what they cost on
the day they are expensive. Every one of them exists because the alternative was
tried somewhere and failed.

EdirasX is built for institutions that will hold it to a standard, on behalf of
students who did not choose it, in places where the connection is poor and the
device is old and the stakes are somebody's education.

Build it as though responsible for its reputation for the next ten years.
Because someone will be.
"""


# --- callout and diagram promotion ---------------------------------------

CALLOUT_TRIGGERS: dict[str, tuple[CalloutTone, str]] = {
    "The Terminology Rule": (CalloutTone.principle, "Rule"),
    "The test:": (CalloutTone.test, "The test"),
    "The Four Schools test": (CalloutTone.test, "Acceptance test"),
    "The standard": (CalloutTone.principle, "The standard"),
    "The tone floor": (CalloutTone.principle, "Tone floor"),
}


def promote_callouts(blocks: list[Block]) -> list[Block]:
    """Lift certain paragraphs into callout boxes.

    Presentation only: the text is unchanged, and the parity check treats a
    callout as ordinary prose.
    """
    promoted: list[Block] = []
    for block in blocks:
        if block.kind is BlockKind.paragraph:
            text = block.text
            for trigger, (tone, label) in CALLOUT_TRIGGERS.items():
                if text.startswith(trigger):
                    block = Block(
                        BlockKind.callout, runs=block.runs, tone=tone, label=label
                    )
                    break
        promoted.append(block)
    return promoted


def _positive_terms(blocks: list[Block]) -> list[str]:
    """Collect the bold lead-in of each paragraph in "Prestige is"."""
    terms: list[str] = []
    for block in blocks:
        if block.kind is BlockKind.heading and block.text.strip().startswith("The standard"):
            break
        if block.kind is BlockKind.paragraph and block.runs and block.runs[0].bold:
            terms.append(block.runs[0].text.rstrip("."))
    return terms


def build_contrast(blocks: list[Block]) -> list[Block]:
    """Render chapter 4's "prestige is not / prestige is" as a paired panel.

    The contrast is the argument of the chapter; setting the two lists side by
    side makes it legible at a glance instead of two pages apart.
    """
    out: list[Block] = []
    i = 0
    while i < len(blocks):
        block = blocks[i]
        is_negative_heading = (
            block.kind is BlockKind.heading and block.text.strip() == "Prestige is not"
        )
        if is_negative_heading and i + 1 < len(blocks) and blocks[i + 1].kind is BlockKind.bullets:
            contrast = Block(BlockKind.contrast, name="prestige")
            contrast.items = list(blocks[i + 1].items)
            # The positive column is the set of bold lead-ins from the section
            # that follows, read out of the source so the panel cannot drift
            # from the chapter it summarises.
            contrast.rows = [[parse_inline(term)] for term in _positive_terms(blocks[i + 2 :])]
            out.append(block)
            out.append(contrast)
            i += 2
            continue
        out.append(block)
        i += 1
    return out


def insert_diagrams(chapter: Chapter) -> None:
    """Place the two diagrams that materially aid comprehension.

    Deliberately only two. A diagram that restates a list adds pages and
    subtracts attention.
    """
    if chapter.number == "7":
        for index, block in enumerate(chapter.blocks):
            if block.kind is BlockKind.numbers:
                chapter.blocks.insert(
                    index + 1,
                    Block(
                        BlockKind.diagram,
                        name="approval-gate",
                        label="Figure 7.1 — The approval gate, as it applies to every assistant in the product.",
                    ),
                )
                break
    if chapter.number == "5":
        chapter.blocks.insert(
            1,
            Block(
                BlockKind.diagram,
                name="six-humans",
                label="Figure 5.1 — Six people, six information architectures, "
                "one domain model.",
            ),
        )


# --- assembly -------------------------------------------------------------


def _preamble_chapter(raw: str) -> Chapter:
    """Carry the source's own status block into the publication verbatim.

    It contains the supremacy clause, which is substantive: front matter
    presents the document, but it must not quietly replace what the document
    says about its own authority.
    """
    body = raw.split("\n## ", 1)[0]
    lines = [ln for ln in body.splitlines() if not ln.startswith("# ")]
    blocks = [b for b in parse_markdown_body(lines) if b.kind is not BlockKind.rule]
    return Chapter(number="", title="Status and authority", blocks=blocks)


def _front_chapter(markdown: str) -> Chapter:
    lines = markdown.strip().splitlines()
    blocks = parse_markdown_body(lines)
    heading = blocks[0]
    return Chapter(number="", title=heading.text, blocks=blocks[1:])


def build_document() -> Document:
    raw = SOURCE.read_text(encoding="utf-8")

    document = Document(
        title="The EdirasX Editorial Bible",
        subtitle="The constitution of the EdirasX education platform",
        edition=EDITION,
        parts=[part for part, _ in PARTS],
    )

    document.front_matter = [
        _front_chapter(EXECUTIVE_STATEMENT),
        _front_chapter(NOTE_ON_THE_NAME),
        _front_chapter(COLOPHON),
        _preamble_chapter(raw),
    ]
    document.back_matter = [
        _front_chapter(CLOSING_DECLARATION),
        _front_chapter(CREDITS),
    ]

    # Split the source at level-2 headings; everything before the first one is
    # the source's own preamble, which the front matter supersedes.
    sections = re.split(r"^## ", raw, flags=re.MULTILINE)[1:]
    for section in sections:
        lines = section.splitlines()
        head = lines[0].strip()
        match = re.match(r"^(\d+)\.?\s+(.*)$", head)
        number, title = (match.group(1), match.group(2)) if match else ("", head)

        blocks = parse_markdown_body(lines[1:])
        blocks = [b for b in blocks if b.kind is not BlockKind.rule]
        blocks = promote_callouts(blocks)
        blocks = build_contrast(blocks)

        chapter = Chapter(number=number, title=title, blocks=blocks)
        part = part_for(number)
        chapter.part = part.number if part else ""
        insert_diagrams(chapter)
        document.chapters.append(chapter)

    _assert_source_covered(raw, document)
    return document


def _assert_source_covered(raw: str, document: Document) -> None:
    """Fail the build if the parse dropped a source heading.

    A publication that silently omits a chapter is the one failure mode that
    would be both easy to produce and hard to notice.
    """
    source_headings = [
        re.sub(r"^\d+\.?\s+", "", h.strip())
        for h in re.findall(r"^## (.+)$", raw, flags=re.MULTILINE)
    ]
    produced = [c.title for c in document.chapters]
    missing = [h for h in source_headings if h not in produced]
    if missing:
        raise RuntimeError(f"Publication dropped source chapters: {missing}")

    # Every substantial line of source prose should survive into the model.
    # List markers are stripped first: the model stores an item's text, not the
    # bullet or ordinal that introduced it.
    model_text = document.plain_text()
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.startswith(("#", "|", ">", "`")):
            continue
        stripped = re.sub(r"^(?:[-*]\s+(?:\[[ xX]\]\s+)?|\d+\.\s+)", "", stripped)
        if len(stripped) < 40:
            continue
        probe = runs_to_text(parse_inline(stripped))[:60]
        if probe and probe not in model_text:
            raise RuntimeError(f"Publication dropped source prose: {probe!r}")


__all__ = ["build_document", "SOURCE", "EDITION"]
