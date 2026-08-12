# Teardown: the Sultan Hanafi final-production certificates

Six issued sheets, read element by element. This is not a list of things that
look nice — it is the inventory of what makes those documents read as *official*
rather than merely ceremonial, and the gap analysis against what EdirasX
currently produces.

The distinction matters because it is where EdirasX is actually short. The
EdirasX plates are ceremonial: frame, cartouche, seal, engraving, typography.
They are **not yet official**: they carry one serial and one verification code in
a small right-hand panel, and that is all. The benchmark sheets carry an entire
administrative architecture, and it is the largest single reason they look like
instruments and the EdirasX plates look like artwork.

---

## 1 · The identifier set — five, not one

Every benchmark sheet carries five distinct identifiers, each labelled:

| Identifier | Example | Where |
|---|---|---|
| Document ID | `DID-2026-SS-0000063` | verification cartouche, top-left cell |
| Verification code | `46CD-2BD8-F771` | verification cartouche, top-right cell |
| Archive reference | `ARCH/SS/2026/000063` | verification cartouche, lower-left cell |
| Student identity no. | `712878764389035` | verification cartouche, lower-right cell **and** printed a second time directly beneath the recipient's name |
| Certificate number | `SHRS-CERT-SS-000063-46CD2` | its own guilloché-filled cartouche, separate from the verification panel |

EdirasX currently has two of these. The student identity number appearing
*twice* — once in the ceremonial field under the name, once in the
administrative panel — is deliberate: the ceremonial instance ties the person to
the record, the administrative instance ties the sheet to the archive.

## 2 · The verification cartouche is a designed panel

Not a footnote. A bordered box, roughly 62 × 26 mm, containing:

* a header rule with the institution's mark and the words `CERTIFICATE VERIFICATION`;
* a **2 × 2 grid** of label/value pairs, labels in fine letterspaced caps above
  values in a larger face;
* a **Code 128 barcode** spanning the full inner width;
* a footer rule carrying the verification URL and
  `VOID IF ALTERED, ERASED OR REPRODUCED`.

Two things follow. The panel has a *masthead of its own* — it is a document
within the document. And the void warning is on the sheet, in small caps, as a
legal statement rather than as decoration.

## 3 · Two machine-readable marks, in separate places

A **Code 128** barcode inside the verification cartouche, and a **QR** in its own
small panel captioned `VERIFY AUTHENTICITY / SCAN QR CODE`. They are separated
deliberately — a damaged corner does not take both.

## 4 · The labelled data register

A three-field row across the sheet, each field a label in fine caps over a value:

    ACADEMIC SESSION    DATE OF AWARD    PLACE OF ISSUE
    2025 – 2026         8 August 2026    Ikorodu, Lagos, Nigeria

On the bilingual sheets the same register runs with Arabic labels above the
English ones. This is what turns prose into a *record*: a reader looking for the
issue date finds a field, not a sentence.

## 5 · The heraldic register

Three devices across the head of the sheet — the Federal Republic of Nigeria
arms at the left, the institutional crest at the centre, the Lagos State arms at
the right — each with its authority named beneath in two lines of fine caps.

**EdirasX must not attempt this.** State emblems are official marks and
approximating one is not a thing to do quietly; the reference implementation says
the same in its own source. What EdirasX can build is the *register* — three
reserved bays with correct proportions, captions and clearances — into which an
institution places its own supplied, licensed devices.

## 6 · The title leader

The title is not centred alone. A horizontal rule runs in from each side and
terminates in a small arrowhead or lozenge pointing at the first and last
letters. It reads as a *plate* rather than as a heading, and it is the single
cheapest device on the sheet.

## 7 · The certificate-number cartouche

A separate shaped panel, guilloché-filled, with fine microtext rules above and
below and the number set in a mono or small-caps face. It sits opposite the seal,
balancing it.

## 8 · Vertical ornamental spines

A chain of small beads or cartouches running down the inside of the left and
right registers. EdirasX has this (`architecture.vertical_spine`) and had removed
it from M11 to recover space — the benchmark says put it back.

## 9 · Woven border bands

The top and bottom borders are a braided gold band over a coloured ribbon, with a
fine microtext rule outside it. Not a rule and not a tessellation — a *woven*
band, which reads as textile and is why the edge looks manufactured.

## 10 · Signature blocks carry the signature

A real signature image sits above the rule; the printed name below it; the office
in fine caps below that. EdirasX draws the rule and the name and has no
provision for the signature asset itself, which the authority chain already
stores.

## 11 · The bilingual sheets use a centre rule

On the peer-arrangement sheets, English occupies the left column and Arabic the
right, separated by a full-height vertical rule, with the ceremonial devices on
the axis between them. The two columns are *mirrored*, not stacked — every label
appears twice, once per column, at the same height.

---

## Gap analysis — what EdirasX is missing

| Benchmark element | EdirasX today | Action |
|---|---|---|
| Five labelled identifiers | Two, unlabelled | **Build** |
| Verification cartouche with its own masthead | Right-hand text panel | **Build** |
| Code 128 barcode | None | **Build** |
| QR | None | Build — but only a *correct* encoder |
| `VOID IF ALTERED…` legal footer | None | **Build** |
| Labelled data register | Prose only | **Build** |
| Heraldic register | None | Build the *bays*, never the emblems |
| Title leader rule | None | **Build** |
| Certificate-number cartouche | None | **Build** |
| Vertical spines | Have it; removed from M11 | Restore |
| Woven border band | Tessellation instead | Build |
| Signature asset on the rule | Rule only | Wire to the authority chain |

The first eight are what this pass builds.

---

# Second reading — the blank substrate and the transcripts

The most useful image in the second set is the one with no content on it: the
**unprinted Sultan Hanafi security plate**. It settles an argument this project
had been getting wrong.

## The ground runs edge to edge, and the frame sits on top of it

EdirasX had a worked perimeter and a cream field. The benchmark has the
opposite: an engine-turned wave field covers the entire sheet, a very large
crest is blind-embossed at the centre, small stars are powdered across it, and
the frame is drawn **over** that ground rather than containing it. That single
inversion is most of why the EdirasX interiors read as blank and the benchmark's
do not.

Also visible only on the blank plate: a holographic strip down the left edge, a
`GENUINE VERIFIED AUTHENTIC` patch at the right, a `SECURITY FIBER WINDOW` patch
at the lower right, and a microtext band running the whole perimeter. Three of
those four are *substrate* features bought from a paper mill, not artwork — a
distinction the production specification already draws and which this confirms.

## What the transcripts add

The IUN transcript carries a **twenty-item authentication checklist** — original
registrar's signature, senate seal, UV fluorescent fibres, invisible security
fibres, microtext printing, latent image technology, holographic strip,
anti-copy background, watermarked paper, chemical reactivity protection,
blockchain verification ID, SHA-256 document hash — printed as a ticked list.

**EdirasX must not copy that list.** More than half of those items are physical
substrate or chemical features that no renderer provides, and printing a tick
beside "UV Fluorescent Fibers" on a sheet that has none is the precise failure
this codebase refuses. What EdirasX can print is a checklist **generated from
what the edition actually bought** — the production specification already
separates cryptographically verifiable / genuine production feature / visual
simulation, and a per-edition checklist is that table, printed. A digital
edition's list would be short and true.

The transcripts also show structures EdirasX has not built at all: a
two-column `STUDENT INFORMATION` grid, per-semester course tables with credit
and grade-point columns, semester and annual summaries, a grade-interpretation
key, and a competencies list. Those are the transcript work, still outstanding.

## What was built from this reading

* An allover security ground — wave lathe edge to edge, powdered stars, a large
  blind-embossed crest on the axis — under the frame rather than inside it.
* The verification cartouche, matching the benchmark's structure: masthead,
  2 × 2 labelled identifiers, Code 128 barcode, footer with the verify URL and
  the void notice.
* Five identifiers where there were two.
* The labelled data register — session, date of award, place of issue.
* The certificate-number cartouche, separate from the verification panel.
* The title leader rule.
* A dimensioned, captioned QR **bay** — not a QR, because a mark that looks
  machine-readable and is not is worse than no mark.
