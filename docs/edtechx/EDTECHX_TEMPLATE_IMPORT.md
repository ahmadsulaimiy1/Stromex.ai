# Importing the benchmark press: fifteen documents, made editable

**What was asked.** Bring the benchmark institution's certificates and
examination documents into EdirasX *exactly*, so that an institution can edit
one quickly. All of them. They must support verification. The names may be
generic, but everything else — the layout, the background — should be what is
there.

**What was delivered.** Fifteen templates in three families, each an editable
`Template` in `app/modules/documents/library.py`, each rendering through the
EdirasX engine onto a resolution-free heritage ground, each wired to the one
verification architecture EdirasX already had. All fifteen render against
specimen and hostile data with zero collision on the machine audit.

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

### Record — six sheets, A4 portrait

| Key | Document | Level |
|---|---|---|
| `record-alumni-registration` | Alumni Registration Certificate | II |
| `record-testimonial` | Official Testimonial | II |
| `record-character` | Character Certificate | II |
| `record-clearance` | Graduation Clearance Certificate | I |
| `record-graduation` | Graduation Certificate | III |
| `record-graduation-register` | Graduation Register | I |

Full field-by-field inventory: `docs/edtechx/design/library/INVENTORY.md`.
Rendered proofs: `docs/edtechx/design/library/specimen/`, `…/hostile/`,
`…/shots/`, `…/contact-sheet.png`.

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

Current state: **thirty sheets, thirty passes, zero millimetres over.**

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
