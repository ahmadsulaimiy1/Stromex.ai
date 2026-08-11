# The luxury concept board — twelve doctoral plates, ranked

**Status: a design review, not a decision.** Twelve directions, one hostile
record, rendered at 300 DPI and looked at. The contact sheet is
`concepts/contact-sheet.png`; each plate is `concepts/NN-name.png` at full size.

**The correction this board answers.** The previous flagship work interpreted
"restraint" as the primary design principle and produced plates that were
technically exact and visually inexpensive — sparse, corporate, and not worth
framing. That reading has been withdrawn. The target is royal institutional
luxury: richness and order together, ornament that has been designed rather
than applied, and a document whose grandeur reads at a metre and whose
craftsmanship reads at five centimetres.

---

## The record every concept was judged on

Nothing here was designed against a short name. The hostile record is the same
in all twelve, and it is the record that has broken certificate compositions:

| Field | Value |
|---|---|
| Institution | The Meridian Institute for Advanced Study and Research (53 characters) |
| Institution (Arabic) | معهد مريديان للدراسات العليا والبحث العلمي |
| Recipient | Muhammad Abdulrahman Ibrahim Abdulwahid Al-Sulaimiy (50 characters) |
| Recipient (Arabic) | محمد عبد الرحمن إبراهيم عبد الواحد السليمي |
| Qualification | Doctor of Philosophy / درجة الدكتوراه في الفلسفة |
| Field of study | Educational Leadership and Institutional Development |
| Signatories | three, each with office and appointment authority |
| Seal | present, struck and blind-embossed |
| Verification | serial `PHD/2031/0007`, code `BFJ7-DRNM-8VZ9`, issued 14 March 2031 |

---

## What was built to make the board possible

Three new modules, because the old vocabulary could not express the target.

**`design/gilding.py` — gold as a material.** Eight metals, each four inks:
a lit crest, a broad reflecting face, a body colour, and a wall the light does
not reach. That ramp is what the eye recognises as metal; a single hex value is
what it recognises as yellow. Royal, antique, champagne, pale, deep, brushed,
copper and silver are genuinely different materials, not lightness variations —
antique is browner in the face than in the core because that is what oxidation
does, and silver's shadow is blue because silver reflects a cool room. Every
metal names the physical process it stands for and a foil reference a vendor can
order against.

**`design/architecture.py` — the frame as a built thing.** Corner blocks with a
mitred elbow and an inset lathe medallion; register stacks where each band has a
stated job; a real octagon-and-square tiling (regular octagons meet flat-to-flat
when the lattice pitch is twice the apothem, and the residual gaps are squares
on the diagonal); strapwork drawn as ribbon rather than as line; a two-centred
arch that can be struck to a *stated rise*, so a mihrab on a landscape sheet is
a canopy rather than a balloon; cresting, spreader rules with lozenge stops,
vertical spines, mandalas, medallions, radiant fields.

**`design/ceremony.py`, rewritten.** Levels I–IV now mean elegant → clearly
luxurious → richly ornamented → exceptional, and what rises with the level is
architecture, ornament and material. Two constraints survive, and neither is
asceticism: `content_ink` caps how much ink may sit *behind the words* (a
legibility guarantee — outside the content field a Level IV plate is routinely
dense), and `peak_ratio` keeps one dominant moment. **The whitespace floor has
been deleted.** Encoding air as a fraction of the sheet produced empty documents
that passed, and air is a judgement made by eye against a rendered plate.

---

## The ranking

Judged on the six questions that matter: does it look expensive, royal,
prestigious, professionally manufactured, frame-worthy — and could it compete
with the best institutional certificates in the world.

### The strongest three

**1 · 02 Imperial Islamic.** The most convincingly expensive plate on the board
and the most unmistakably itself. A midnight border of real strapwork — the
octagon tiling at 11mm pitch in royal gold, a champagne girih band inside it —
with an ivory field cut into it on chamfered corners and a khatam medallion at
each of the field's four angles. The masthead is a genuine peer band: English
left, Arabic right, and the qualification is set bilingually on one line. It
earns its richness by construction rather than by quantity: one tiling, one
band, one field, all from the same geometry.

**2 · 11 Crimson Imperial.** The frankest expression of imperial weight. Crimson
mass on all four sides at 8.6mm tiling pitch, mitred corner brackets in a deeper
crimson carrying gold medallions, vertical spines down the left and right
registers, a filled gold palmette cresting the inner frame, and one bright
ceremonial centre — an ivory cartouche carrying the recipient's name. The colour
does most of the work and the architecture keeps it from shouting.

**3 · 01 Royal Palace.** The most complete *architecture* of the twelve: a navy
field register, a micro-tessellation register, a stepped ceremonial architrave
with shouldered corners, mitred corner blocks, a crest medallion on the axis
with spreader rules running left and right, and a cresting above. Ivory, navy
and royal gold. It reads as a doorcase, which is exactly the ambition.

### The rest, honestly

**4 · 12 EdirasX Signature** — strategically the most important and not yet the
best executed. One construction for frame and field: the khatam lattice
dissolving from a 7mm cell at the trim to a 26mm cell at the centre, so the
frame does not end, it thins. Two metals, and the credential band designed as a
visible architectural register rather than a footnote. *The dissolve does not
yet read* — the four density bands are too close in value, and at arm's length
it looks like one even lattice. This is the one to fix, because it is the one
that could become unmistakably EdirasX.

**5 · 08 Heritage Manuscript** — genuinely beautiful and the only plate where
Arabic is the text and the Latin is the gloss. Parchment ground, an illuminated
border of tiling plus a copper girih band, a shamsa medallion in each outer
margin. Slightly monotone: the border wants a second value.

**6 · 03 Ottoman Academic** — burgundy and antique gold, arabesque and mid-edge
medallions, and the qualification mounted on a shaped cartouche rather than
written on the page. Strong; the plaque now sits correctly after a viewBox
defect was fixed.

**7 · 05 Royal University** — elegant, Latin-forward, an almost empty
double-rule frame with everything spent on the crest, the type and the execution
row. Excellent of its kind and deliberately the least ornamented; it stays on
the board as the sovereign-warrant pole, not as a flagship.

**8 · 10 Midnight Royal** — the inversion, and the idea is right: gold behaving
as light on a midnight ground with an ivory plaque mounted on it. The radiant
field now reads (it was being overpainted). Still too much unworked ground below
the plaque.

**9 · 04 Arabian Royal** — deep green and deep gold with a two-centred canopy as
the architecture. The balloon defect is fixed; the canopy silhouette is still
not resolved and the composition floats high in it.

**10 · 07 Guilloché Palace** — the security-instrument aesthetic, and currently
the closest to the withdrawn sparse direction. The lathe registers are correct
and the plate is not yet luxurious.

**11 · 09 Modern Royal** — Archivo at monumental scale against a dense gold
wall. The wall now reads, but it looks applied to the sheet rather than part of
it, and the left two-thirds is plain.

**12 · 06 Grand Medallion** — the document as a struck medal. The radiant field
reads as a starburst rather than as a turned ground, which is the one failure
mode this direction had to avoid.

---

## Defects found by looking, and fixed

Every one of these was invisible in the code and obvious in the render.

| What | Where | Fix |
|---|---|---|
| The peak broke at the hyphen — `Al-` / `Sulaimiy` — in eleven of twelve | all | A non-breaking hyphen at render time plus `text-wrap: balance`. The stored name is untouched; only what the line-breaker is permitted to do has changed. |
| The verification line fell on the midnight border: dark ink on a dark ground, unreadable | 02 | The field now ends where the ivory panel ends. |
| The seal legend read `INSMERIDIAN INSTITUTE` — the repeat seam | all with a seal | `legend_ring()` fits a whole number of repeats to the exact circumference with `textLength`. |
| The corner bracket's double step read as a mis-registered plate | 01, 11, 12 | One 45° mitre at the elbow, which is what a die leaves. |
| The cartouche was drawn into a viewBox twice its box and squashed to a pill across the qualification | 03 | The plaque is drawn at its own size in its own box. |
| A mihrab struck at its natural proportion is 131mm tall over a 237mm opening | 04 | `arch_niche_path(rise=…)` inverts the construction: state the rise, and `d = (rise² − a²)/2a` follows. |
| The ray field was painted over with a 72%-opacity ground and vanished | 10 | `geo.blend()` — on a dark plate a pale tone must be mixed towards the *ground*, not the paper. |
| The crest read as a circus tent | 01, 10, 11 | A filled palmette at 26 × 11mm rather than a stroked outline at 42 × 7mm. |
| Microtext sat 2.6mm from the trim, inside the knife | most | Moved to 8.4mm, outside the ±1.5mm cutting tolerance with margin. |
| The ground mandala was legible as a figure at arm's length | all | Held at 2.5% above the paper. A field is noticed on the second look. |

---

## What is verified, and what is not

**Verified.** The twelve plates render; the constructions are checked by 27 new
tests in `app/tests/test_architecture.py` — the octagon lattice is a real tiling,
a stated arch rise is the rise produced, all four corner brackets are one shape
rotated, no metal treatment emits an opacity on a line, every metal's ramp
actually descends, the legend ring fills its circumference exactly, and the
ceremonial levels increase in registers, permits and peak ratio together. The
full suite is green.

**Implemented but not yet verified.** Nothing here has been printed. Foil,
emboss and raised type are visual simulations and are named as such in
`gilding.SIMULATION` and in the production specification. Microtext is real
vector text at 0.56–0.62mm carrying the live serial; whether a given press holds
it is a question about that press and has not been measured. Greyscale
behaviour, 200% inspection and the A4-portrait and Letter compositions have not
been done for any of the twelve.

---

## Next

1. Refine the strongest three to flagship standard, and fix 12's dissolve
   because it is the house identity.
2. Portrait and Letter compositions for those three — designed, not scaled.
3. The 300 DPI microprint proof, or an explicit statement that the environment
   cannot produce one.
4. Then, and only then, the remaining fourteen documents and the transcripts.
