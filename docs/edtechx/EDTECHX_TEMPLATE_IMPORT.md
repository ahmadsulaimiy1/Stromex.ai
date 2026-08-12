# Importing the benchmark press: twenty-four documents, at every honest size

**What was asked.** Bring the benchmark institution's certificates and
examination documents into EdirasX *exactly*, so that an institution can edit
one quickly. All of them. They must support verification. The names may be
generic, but everything else — the layout, the background — should be what is
there.

**What was delivered.** Twenty-four templates in five families, each an editable
`Template` in `app/modules/documents/library.py`, each rendering through the
EdirasX engine onto a resolution-free heritage ground, each wired to the one
verification architecture EdirasX already had, and each issuable on **twelve to
fourteen sheet sizes** — every ISO A and B stock and every North American stock
large enough to carry it, in both orientations.

Fifteen came from the benchmark's rendering code. **Nine more existed only in
its own master specification** — named, numbered, given a security class, and
never built. Those nine are the ones an institution needs most.

Plus the reissuance discipline the specification is most emphatic about and
nothing implemented: **Certified True Copy** and **Duplicate** editions, each
with its own reference number and a visible permanent overprint.

---

## The fifteen

### Stage — four sheets, A4 landscape, Level III

| Key | Award | Arabic |
|---|---|---|
| `stage-preparatory` | Certificate of Tamhīdiyyah | شهادة إتمام المرحلة التمهيدية |
| `stage-primary` | Certificate of Ibtidāʼiyyah | شهادة إتمام المرحلة الابتدائية |
| `stage-intermediate` | Certificate of Iʻdādiyyah | شهادة إتمام المرحلة الإعدادية |
| `stage-secondary` | Certificate of Thānawiyyah | شهادة إتمام المرحلة الثانوية |

### College — five sheets, A4 landscape

| Key | Award | Level |
|---|---|---|
| `college-junior-secondary` | Junior Secondary School Graduation Certificate | III |
| `college-senior-secondary` | Senior Secondary School Graduation Certificate | III |
| `college-primary` | Primary School Graduation Certificate | II |
| `college-memorisation-complete` | Completion of the Memorisation (Thirty Juzʼ) | IV |
| `college-memorisation-ten` | Memorisation of Ten Juzʼ | III |

### Record — seven sheets, portrait

| Key | Document | Code | Class | Level |
|---|---|---|---|---|
| `record-alumni-registration` | Alumni Registration Certificate | `ALUM` | C | II |
| `record-testimonial` | Official Testimonial | `TEST` | B | II |
| `record-character` | Character Certificate | `CHAR` | B | II |
| `record-clearance` | Graduation Clearance Certificate | `CLR` | B | I |
| `record-graduation` | Graduation Certificate | `CERT` | A | III |
| `record-graduation-register` | Graduation Register | `REG` | C | I |
| `record-provisional` | **Provisional Certificate** | `PROV` | A | III |

### Ledger — three sheets, portrait tabular *(all new)*

A ledger is not a certificate with a table on it. It has a holder block, a body
of rows that *is* the document, and a grading key on the same sheet — a
transcript read by somebody who has never seen this institution's conventions is
otherwise a page of letters to guess at. Every ledger closes with an **End of
record** rule, because unused space below the last row on a sealed transcript is
where a line gets added afterwards.

| Key | Document | Code | Class |
|---|---|---|---|
| `ledger-transcript` | Official Academic Transcript | `TRAN` | A |
| `ledger-supplement` | Diploma Supplement | `SUPP` | A |
| `ledger-statement` | Statement of Results | `SOR` | A |

### Award — four sheets, landscape ceremonial *(all new)*

One family parameterised by awarding authority and citation, not four that drift
apart. An award carries **no academic session**: an award for a piece of work is
not an award for a year. The citation is required — an award with a generic
citation is a certificate of attendance with a ribbon on it.

| Key | Document | Code | Class | Level |
|---|---|---|---|---|
| `award-general` | Award Certificate | `AWD` | B | III |
| `award-distinction` | Special Distinction | `DIST` | B | IV |
| `award-board` | Board Award | `BRD` | B | IV |
| `award-head-of-schools` | Head of Schools Award | `FCA` | B | IV |

And `college-islamiyyah` (`ISL`, class A) joins the college family — the level is
a slot, so one certificate names six levels rather than six templates drifting
apart at the third revision.

Full field-by-field inventory: `docs/edtechx/design/library/INVENTORY.md`.
Rendered proofs: `docs/edtechx/design/library/specimen/`, `…/hostile/`,
`…/shots/`, `…/contact-sheet.png`.

---

## Sheet sizes: a brief, not a scale factor

An institution asks for A3 and gets A3. What it never gets is an A4 composition
photographed onto a different rectangle — which is what produces 0.05mm
hairlines on an enlargement and an unscannable verification panel on a
reduction.

**Three things happen when the sheet changes, and only one is scaling.**

1. **The border is re-cut.** The seven band insets are proportions of the short
   side, so the border is *drawn* at the new size. A hairline stays a hairline.
2. **The type is re-solved**, on a square-root curve rather than linearly —
   doubling the field does not double the reading distance — and clamped so no
   sheet drives the peak below 4.2mm or the body below 1.8mm.
3. **The instruments do not move at all.** A Code 128 module floor of 0.33mm,
   a 27mm verification cartouche, an 18mm seal. These are facts about presses,
   scanners and eyes, and they are the same on A6 as on A3.

Point 3 is why the system can say **no**:

| Stock | Sizes | Carried by |
|---|---|---|
| A3, Tabloid, B4, Legal, A4, Letter | both orientations | every family |
| B5 | portrait / landscape by family | most |
| **A5, A6, Half Letter** | — | **refused, with the arithmetic** |

A refusal reads: *"The field is 99mm tall and this composition needs 123mm at
its type floors — 74mm of content above a 49mm foot that may not be shrunk. It
is 24mm short."* That is an answer an institution can act on. "Does not fit"
without a number is an opinion.

**Landscape and portrait are different compositions, including in the foot.** A
wide sheet sets the number cartouche, the signatures and the seal on one line; a
tall one has not got the width for that, so the cartouche takes its own line and
the signatures pair beneath it. Same rule that makes the citation run in columns
on one and stack on the other.

---

## Reissuance: never a second original

| Edition | Overprint | Names the original? |
|---|---|---|
| `original` | *nothing* | — |
| `certified_copy` | CERTIFIED TRUE COPY · نسخة طبق الأصل معتمدة | no |
| `duplicate` | DUPLICATE — ORIGINAL REFERENCE No. X | **required** |

The overprint is drawn **over** the ground and under nothing, at −16°, in
oxblood — a colour reserved in this library for exactly two things and spent
nowhere else, which is what makes it mean something when it appears. A copy
notice that content can obscure is a copy notice a forger can obscure.

An original renders **no stamp at all**. There is no faint "ORIGINAL" mark,
because a document that has to announce it is genuine has already conceded the
question.

A duplicate with no original reference number is **refused outright**: without
it the sheet is indistinguishable from a second original, and a holder with two
unmarked certificates can lend one and keep one while a verifier has no way to
tell which is which. A Class C registry document cannot be reissued as a copy at
all — it is regenerated from the register, and stamping a copy notice on it would
imply a chain of custody it does not have.

---

## Permanent banners, which are not editions

Two documents carry a banner *always*, set in the flow above the title where it
is read before the document is:

- **Statement of Results** — INTERIM — NOT A COMPLETION DOCUMENT. Without it the
  sheet reads as a final academic record. It is signed by Examinations and
  Records rather than by a principal, because the office that signs is itself a
  claim about what the document attests.
- **Provisional Certificate** — PROVISIONAL — FINAL CERTIFICATE IN PREPARATION.
  Without it the sheet reads as the certificate it is standing in for.

---

## What "exactly" means, stated precisely

Three categories, and the honesty of the import is in keeping them apart.

**Transcribed exactly.** The layout family. The sheet and orientation. The band
architecture of the ground and its seven measured insets. The zone order. The
ceremonial register. And the institutional sentences — character for character,
including the Arabic. "has satisfactorily completed … has met in full the
academic and conduct requirements of the institution, and is hereby graduated
and admitted to …" is not paraphrased, because its precision is why the
document means anything.

**Generic by design.** Every name. Personal names, institution names, schools,
places, signatories, offices — all slots with placeholder defaults. A real
principal's name and a real registrar's signature belong to the institution that
owns them; carrying them into a multi-tenant library would put a named person's
attestation on documents they never saw. The layout does not change by a
millimetre when the names change, which is what makes the import editable rather
than merely copied.

**Not carried at all: the raster.** The benchmark's master background is a
1080×772 image. Across a 297×210mm sheet that is 92 DPI — a quarter of the 300
a press needs, a seventh of the 600 an engraved register needs. There is nothing
to recover by enlarging it; an upscale would manufacture ornament that was never
in the file and print it on a permanent record.

So the background was **redrawn**, which is what a security printer does. The
benchmark's own repository had already done this work — a constructed vector
ground built precisely because the raster could not be enlarged — and
`app/modules/design/heritage.py` is that architecture rebuilt on EdirasX's
engine: epitrochoid lathe work, parametric rosettes, star polygons on an n-fold
rotation, engraved rules in three flat strokes, real text on a path. It has no
resolution. It is exact at 300 DPI, at 600 and at 2400, and it is re-cut for any
sheet size rather than scaled.

That is the honest answer to "including the background": the background is the
same architecture at a resolution the original never had.

---

## The band architecture

Outside → in, seven insets, stated as a proportion of the sheet's **short**
side so that a border measured for a landscape sheet does not put a 36mm margin
down a 210mm width:

| Band | Inset (of short side) | What it is |
|---|---|---|
| `hair` | 4.7 / 210 | outer gold hairline — where the paper ends |
| `band_outer` | 10.2 / 210 | ornamental band, outer engraved rule |
| `band_inner` | 14.0 / 210 | ...and its inner rule. Lathe strapwork between |
| `strip_outer` | 21.7 / 210 | iridescent security strip, outer edge |
| `strip_inner` | 28.1 / 210 | ...and inner edge |
| `rule_outer` | 32.7 / 210 | inner double rule closing the margin |
| `rule_inner` | 36.3 / 210 | the document's own perceived edge |

`Bands.for_sheet(w, h, weight=…)` narrows the whole border together. A register
that has to hold thirty rows cannot spend 36mm a side; it spends 28 and keeps
every proportion between the bands intact. Deleting two bands would not be the
same thing, and the parameter exists so nobody has to.

---

## Verification

Every template declares a `Verification` spec and every spec resolves against
`design.credential.Credential`. No second scheme was invented: an imported
certificate verifies by the same route, in the same five states, as one EdirasX
designed itself.

On the face of a ceremonial sheet:

- an engraved **number cartouche** carrying the certificate number, opposite the
  seal, guilloché-filled so it does not read as a box with a number in it;
- a **verification cartouche** — masthead, four labelled identifiers, a real
  Code 128 subset C symbol of the identity number at a 0.33mm module floor, and
  a footer carrying the verification URL and the void notice in both scripts;
- a **QR bay**, reserved and dimensioned rather than drawn. EdirasX does not
  mint the code here; the issuing service does. A plausible grid of squares that
  is not a valid QR is worse than no QR, because somebody will rely on it;
- **serial-bearing fine-text rails** through the border, so a sheet copied from
  another student's record contradicts itself in its own frame.

A document with no identity number — the register — carries **no barcode at
all**, rather than a symbol encoding nothing.

---

## What the machine audit found

`tools/design/library.py` renders all fifteen against a specimen institution and
against hostile data (a 92-character institution name, a 47-character recipient,
a doubled session string, a 24-digit identity number) and measures two things:
whether the content overflows its field, and whether the field itself has been
tuned outward across the ground's innermost rule.

It found, in order, and every one of these is now fixed:

1. **A 34mm overflow on every stage sheet and 54mm on every college sheet.** The
   field was being inset a second time on top of a border that already spends
   17 % of the short side. Nothing had been looked at yet.
2. **A verification panel printing its archive reference through its own void
   notice.** The panel was given 17mm and its internals need 25.6. This is the
   defect class a layout audit cannot see — a collision *inside* an SVG is
   invisible to anything that measures boxes — so the guard now lives in
   `verification_cartouche` itself, which refuses a rect too short for it.
3. **The college award set twice**, once as a masthead subtitle and once in the
   conferred-award register, at 7.8mm of a 132mm field to say the same words at
   two sizes.
4. **The register composed as though it were about a person** — one graduand's
   name at full peak size over a list of four, which reads as that student's
   certificate with three strangers appended. Templates now name their own peak;
   the register's is the session, and it carries no recipient slots at all.
5. **A barcode raised on a document with no identity number**, which crashed
   rather than silently encoding an empty payload — the right failure, in the
   wrong place. `Credential.barcode_digits` now returns nothing and the panel
   draws nothing.

**The second pass found three more**, and the third of them is the kind only a
rendering catches:

6. **An award printing the word AWARD over the holder's identity number.** The
   particulars band took its first label from `registers[-3]`, which is "Student
   ID" on a stage sheet and "Award" on an award sheet. A label derived from a
   position rather than named is a label that will eventually describe the wrong
   value; both are now stated explicitly.
7. **A transcript left open below its last row.** Blank space under a sealed
   record is where a line gets added afterwards. Closed with an End-of-record
   rule — and left *blank* rather than filled with ruled lines, because ruled
   lines invite an entry and a closing rule forbids one.
8. **A5 accepted for transcripts** on a height check alone. Five table columns
   below about 26mm each stop being readable long before the page runs out of
   height, so width is now its own constraint with its own reason per family.

**The third pass was the model itself.** The first size arithmetic accepted 320
compositions and the browser found 23 of them overflowing by 0.3 to 19.6mm. The
first correction over-swung and refused A4 landscape, the size the certificates
were designed at. So the estimates were thrown away and the constants
**measured**: every template rendered on every candidate sheet, with both data
sets, with its flexible spacers deleted and its natural height read back — 672
measurements — then fitted per family *and orientation* as `base + slope ×
type_scale`. Affine rather than proportional, because a content column is partly
type (which scales) and partly rules and fixed boxes (which do not).

Two traps that cost a full run each, and both are recorded in the source:

- **The measured stack already includes the foot.** Adding the foot floors on
  top double-counted 49mm and refused everything below A3.
- **The gate has to be open while measuring.** With the previous constants in
  place the renderer refused the small sheets, so those sheets were never
  measured and the fit came back describing only the sizes the old constants
  already allowed. Calibrating a limit against data the limit itself selected
  tells you nothing.

Four sizes still overflowed after that, all line-wrap discontinuities a linear
model cannot see — a citation that sets on one line at ×1.00 takes two at ×1.02
and the column jumps 7mm. They are recorded as `MEASURED_OVERFLOWS`, with the
millimetres, rather than absorbed into a constant that would then refuse A4.
**The model predicts; the proof wins.**

Current state: **48 sheets at design size (specimen and hostile), 44 reissued
editions, and 279 size compositions — every one measured, zero millimetres over,
and 201 sheet sizes honestly refused.**

---

## Editorial rules that came across with the layouts

Importing a sheet without its reasoning imports the sheet and loses the thing
that made it lawful. Three are carried in `Template.notes` and two are enforced
by tests:

- **A school award may not borrow a national examination board's name.** A
  national award is made by a board on its own examination; a school certificate
  calling itself one claims an authority the institution does not hold.
  `test_school_awards_do_not_borrow_a_national_examination_board_s_name` fails
  if the wording drifts.
- **The two memorisation awards are separate templates, not variants.** A
  completion sheet printed over a child who has memorised ten juzʼ overstates
  it; an achievement sheet printed over one who has completed the whole robs her
  of it. Neither may be reachable from the other by a default.
- **No invented numbers.** The primary citation says "the Primary School
  programme" and not "the six-year programme", because the published range is
  an age range and the year count would be manufactured. An invented number on a
  permanent record is exactly the error this library exists to avoid.
- **A testimonial's Arabic half is empty, not machine-translated.** A translated
  character reference is a reference the signatory did not give.
- **A character certificate's qualifier must state a recorded disciplinary
  action where one exists.** A certificate of good conduct that quietly drops
  the exception is a false one.

---

## What has *not* been established

- **Nothing has been printed.** No press, no paper, no foil, no loupe. Every
  statement about hairline survival, foil, emboss and the Code 128 module floor
  remains a specification.
- **The fine-text rails are fine text, not microprint.** At the size these
  plates use the cap height is around 0.41mm; security microprint means 0.25mm
  or below. The register is worth having and is not that.
- **The anti-copy screens are screens, not a latent image.** A latent image
  needs a coarse and a fine ruling at matched ink fraction with a shape defined
  between them, and neither ruling here is doing that.
- **The fibres are cosmetic.** A real security substrate's fibres are *in* the
  sheet and fluoresce; printed ones do neither.
- Only A4 has been composed. Letter and A3 will be re-cut, not scaled.
- The `zoned` and `integrated` language arrangements exist and no imported
  template opts into them yet.
