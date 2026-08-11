# The masterpiece pass — four finalists, developed and separated

**What changed.** The twelve concepts were a design exploration. These four are
what a proposal becomes when somebody has to manufacture it: every ornament a
member of the document's own geometric family, every metal a role rather than a
colour, every millimetre placed against a named zone, and the artwork split into
the eight plates a printer actually receives.

Each finalist has a full-page preview, eight standalone separations, and a
production specification generated from the same plate as the artwork.

| | Preview | Separations | Specification |
|---|---|---|---|
| **M02 Imperial Islamic** | `masterpieces/m02-imperial-islamic.png` | 8 | `…--specification.md` |
| **M11 Crimson Imperial** | `masterpieces/m11-crimson-imperial.png` | 8 | `…--specification.md` |
| **M12 EdirasX Signature** | `masterpieces/m12-edirasx-signature.png` | 8 | `…--specification.md` |
| **M01 Royal Palace** | `masterpieces/m01-royal-palace.png` | 8 | `…--specification.md` |

---

## 1 · The ornament is now the document's own

The criticism was exact: the concepts read as *a beautiful Islamic pattern
placed around a certificate*. Correct geometry, applied rather than belonging.

`design/signature.py` replaces that with a **Motif** — a family derived from the
institution and the document type, appearing at six scales on one sheet:

| Where | Scale | Member of the family |
|---|---|---|
| Border field | 11.5 mm cell | rosette lattice |
| Corner medallion | 14 mm | rosette with kites |
| Seal device | 8 mm | rosette, blind-embossed |
| Institutional mark | 6–7 mm | star and construction polygram |
| Ground figure | 52–56 mm | rosette at 2.6% above the paper |
| Guilloché | full register | lathe whose lobe count is a multiple of the order |

For this institution's doctoral award the family is **{10/3}** — ten-fold, star
density 3, inner/outer radius 0.7265, lathe R=50 r=7 pen=8.4 giving **50 lobes
closing after 7 turns**. Fifty is five times ten, which is the point: the lathe
work and the star work are the same hand at different frequencies.

**Two generalisations made this possible.**

`geometry.INNER_RATIO` was √(2−√2), the khatam's inner radius, treated as a
constant. It is the (n,k) = (8,2) member of `cos(kπ/n) / cos((k−1)π/n)` — the
inner radius of the star polygon {n/k}. Writing the family down lets ten- and
twelve-fold documents be constructed with the same correctness rather than drawn
by eye. And `density_for` picks the k that holds *sharpness* constant as the
order changes (0.765 at n=8, 0.727 at n=10, 0.707 at n=12), so an eight-fold
plate and a twelve-fold plate are recognisably from one house instead of merely
both being geometric.

The lathe specification is **derived from the order** rather than picked from
the shared table. No row in `geometry.LATHE` has a lobe count divisible by 8, 10
or 12 — they are all primes and near-primes — so selecting from it produced a
guilloché with no relationship to the family at all.

**What varies per document, and what does not.** The motif belongs to an
institution and a document type: every doctoral award from one institution
carries one geometry, because that is what makes it an identity. What varies per
sheet is the security layer — the fine text carries this serial, the fibres are
seeded on it. Ornament identifies the institution; the security layer identifies
the sheet.

---

## 2 · Gold is a system, not a colour

`gilding.Scheme` gives five **roles**, and every drawing call names a role:

| Role | Job |
|---|---|
| Primary | ceremonial architecture — the only metal allowed to be large |
| Secondary | fine ornamental registers |
| Engraved | shadow and relief; never a face, only a wall |
| Security | the fine ruling and fine text; pale by requirement |
| Heritage | ornament wanting an older metal than the primary |

Four schemes, and each is a decision about how many foils a job buys:
**imperial** (royal / champagne / deep / pale / antique), **crimson** (deep
primary, because a royal gold cannot hold against a saturated ground),
**signature** (royal against *silver* — two metals that are not two golds, which
is what makes a two-pass job look like one), **palace** (royal / antique).

That is what stops the fine registers competing with the architecture: they are
*different metals*, not the same metal at a different weight.

---

## 3 · Depth is assigned, not hoped for

Each plate places elements at four viewing distances, and the code says which
register belongs to which:

| | |
|---|---|
| **1 m** | frame mass, ground colour, ceremonial centre |
| **50 cm** | hierarchy, corner architecture, medallion, metal |
| **20 cm** | interlace, engraved rules, kites, seal device |
| **5 cm** | lathe petals, fine text, construction polygram, fibres |

Something that reads at every distance is a poster. Something that reads at one
is a diagram.

---

## 4 · The separations

Eight per finalist, each a standalone SVG in millimetres at trim size:

`substrate` · `security` · `process` · `foil-primary` · `foil-secondary` ·
`emboss` · `finetext` · `variable`

The **emboss** and **variable** layers are emitted at *measured* positions: the
seal, the institutional mark and the verification panel are placed by the flow —
which is what keeps a fifty-character name from landing on them — so their sheet
coordinates are a result. The page is rendered, the boxes are read back at
96 px/inch, and the die geometry is written where it actually sits. A separation
drawn from guessed coordinates would be a separation of a different document.

---

## 5 · The fine text is not microprint — measured

The brief said: 300 DPI → physical size → raster inspection → print test →
measurement; and if it does not qualify, rename it. The first three steps have
been done.

The serial-bearing ring is set at 0.58 mm, ≈0.41 mm cap height:

* **300 DPI** — 6.85 px per em. **Illegible.** The raster breaks the strokes and
  the register reads as grey texture; nothing can be read back from it.
* **600 DPI** — 13.7 px per em. **Legible.** The serial and the verification code
  read off the crop.

Security microprint means a cap height at or below about 0.25 mm, chosen so a
loupe resolves it and a photocopier cannot. At 0.41 mm this is well above that
and does not have the property. **`microtext_ring` has been renamed
`fine_text_ring` throughout**, the ceremonial permit is now `finetext`, and every
document says so. Any 300 DPI edition must not describe this register as
carrying readable data, because at 300 DPI it does not.

---

## 6 · Defects found by looking

| What | Fix |
|---|---|
| **Every rosette on every plate was an unclosed, mis-specified curve.** `epitrochoid` derived its closure turn count by rounding the values it was passed, and both callers pre-multiplied the wheels by a scale — so a 50-lobe figure asked for at a tenth scale ran 3.6 turns instead of 7, drew half its petals and closed with a chord across the middle. | `scale=` keyword; turns and lobes derived from the integer specification, which is where they live |
| The lathe passes beat against the lobe period, laying a moiré lens across the rosette | rotate by a fraction of the *lobe* period, not of the order |
| `{10/2}` is two pentagons, `{8/2}` is a square traced twice — the star construction degenerated for every even order | draw the star as its outline (2n alternating vertices), and the polygram separately as `gcd(n,k)` circuits |
| The rosette's kites read as spikes — tip at 1.30 of the radius with a narrow waist is a gear, not a rosette | tip at 1.12, shoulders opened to most of the gap |
| Ornament ran through the signatories' authority lines | `Motif.field(keep_out=…)` — the content field is excluded by construction |
| The exclusion then made it *worse*: two even-odd subpaths overlapped and flipped the middle back to filled | nest two clip paths — outside the ring AND outside the field — which is the operation actually wanted |
| A two-line office pushed its engraved rule 4 mm out of line with the other two | fixed-height name box, so the three rules share one baseline |
| M11's execution band overflowed the ivory panel; the architrave cut through "Board of Examiners" | field height corrected; statement given a wider measure so it sets in two lines |
| The crest failed twice — stroked it was a tent, filled it was a traffic cone | rebuilt as a struck medallion straddling the frame rule with two low scroll wings |

---

## 7 · Not validated

**Nothing here has been printed.** This environment has no press, no paper, no
foil and no loupe, so the physical validation the brief asks for cannot be
performed here and is not claimed. Unverified: foil adhesion and register on
cotton stock; emboss depth and whether a die holds the ten-fold device at seal
scale; whether any press holds the 0.07 mm hairlines; whether the fine-text ring
survives real 600 DPI output rather than a rasterised preview; how the metals
read under daylight, warm indoor light and raking light; and what the back of
the sheet looks like.

Until a proof exists, every statement in the production specifications about
finishing and fine text is a specification, not a result. Getting a physical
proof made is the next real milestone, and it needs a vendor rather than more
code.

---

## 8 · Language architecture — Arabic + English is not the formula

A compulsory bilingual layout is exactly as templated as a compulsory ornament,
so the language arrangement is now a design decision recorded on the template
and resolved by `design/language.py`. **Every arrangement goes through one code
path. There is no `if arabic:` anywhere**, and there must never be one: the
moment one script is a branch and another is the default, the system has an
opinion it was not asked for.

Eight arrangements, none a special case: `latin-only`, `arabic-only`,
`arabic-primary`, `latin-primary`, `peer`, `zoned`, `integrated`, three-run.
The proof is `masterpieces/language/` — M02's plate under six of them, nothing
swapped but the architecture.

**Three things the module knows that a translation table does not.** Optical
size is not nominal size, so Amiri carries a 1.18 multiplier and "peer" means
*optically* equal. Direction is a property of the run, not of the page. And
absence is ordinary — an institution that never supplied an Arabic name gets a
composition that re-balances, not a gap where something used to be.

**Two composition rules came out of the hostile data.** Subordinate scripts
carry *identity, not prose*: the institution, the recipient and the
qualification appear in every script the document sets; a 250-character legal
paragraph appears once, in the lead script. And the plate responds to the
arrangement — the ceremonial panel opens as the typographic load rises, because
a sheet setting two scripts genuinely needs more field than one setting a
single script. Both replaced the alternative of shrinking the recipient's name
until two scripts fitted in one script's room.

**A stated limitation.** This models *scripts*, not languages. An English /
French / Arabic document is three languages in two scripts, and there is no way
yet to express two Latin runs that must not be collapsed. The arrangement is
named "three runs" rather than "trilingual" for that reason.

## 9 · Two instruments taken from the Sultan Hanafi press specification

**A collision audit on every sheet.** The reference runs one; this project had
found the same defect class — content leaving the ceremonial panel and landing
on the border — four times by eye and never by a test. `audit_overflow()` now
measures a field's overflow in millimetres on every build. Its first run
reported that **all four finalists overflowed**, three of them invisibly at
contact-sheet size: M11 by 31.8 mm, M12 by 16.4 mm, M01 by 7.7 mm. Eyes are the
right instrument for judging a composition and the wrong one for measuring
whether it fits.

**A counted stroke census, not an asserted floor.** The reference does not claim
a hairline minimum; it counts every stroke and tells the printer the
distribution. Doing the same here found **1,320 strokes at 0.050 mm** — all of
them *derived*, from sub-stroke multipliers compounding inside the rosette, all
below this package's own stated floor and below the 0.25 pt most litho
specifications quote. Nothing asked for 0.05 mm; arithmetic produced it. The
floor is now enforced where the multiplication happens (`signature.STROKE_FLOOR`),
and every specification carries the census.

**And three questions that block a press file**, added to each specification:
which ICC output profile, which PDF/X part (and specifically whether X-4 is
acceptable, because X-1a and X-3 force a flatten that turns every guilloché line
into a raster), and the TAC limit with whether pure black must stay 100 % K.

## 10 · The interior pass — first iteration

The language pass was approved; the artwork was not, and the diagnosis was
right: **the dark border was doing all the luxury work and the cream field was
a stack of centred prose on blank paper.** Everything built until now happened
at the perimeter, which is where a plate is easiest to make impressive.

`design/interior.py` is the inside of the frame. Five constructions, every one
gated on the ceremonial level so a completion certificate gets an elegant field
and a doctorate gets all of it:

* **`field_ground`** — a lathe field beneath the content at a fraction of the
  level's ink ceiling. The difference between cream paper and a security
  substrate that happens to be cream. Draws nothing at Level I.
* **`interior_corners`** — engraved brackets at the *content field's* own
  corners, struck from the same family as the corner blocks at the trim. The
  corner-to-centre relationship, made explicit.
* **`title_register`** — the band a conferral is set *into*. A letterspaced line
  on blank paper is a caption; the same words between two engraved rules with
  the family's rosette at each terminal is a register.
* **`name_cartouche_path`** — the peak, mounted rather than printed: cut panel,
  double rule in two metals, a member of the family at each cut.
* **`execution_rule`** — a spanning engraved rule with the family on its axis,
  so the signatures hang from an architecture instead of sitting above three
  short lines.

**A zone review instrument, because a contact sheet cannot judge this.**
`tools/design/zoom.py` renders one plate at 300 DPI and cuts it into the ten
zones a document is actually examined in — ceremonial centre, title register,
border, corners, seal, signatures, serial, fine text, security field — each at
100 %, 200 % and 400 %. It found, on its first run, that the Arabic run's
descenders crossed the cartouche's own bottom rule: invisible at a metre, a
printing fault at arm's length.

**What this iteration cost, stated plainly.** The panels had to open to hold the
new interior, and they opened at the border's expense: M11's crimson band is
noticeably narrower than it was, M12's dissolve is compressed, M01's navy
register is squeezed. The interior is right and the trade is not — the next move
is to take the room back from the *content* (the conferral statement is long,
and the field-of-study line is set twice in bilingual arrangements) rather than
from the frame. This is a first interior iteration, not a finished one.

**One instrument gap the same work exposed.** The overflow audit measures
whether content fits its field; it says nothing about whether the *field* fits
the panel. Tuning those two separately clipped a masthead against the border and
cut a verification code in half — and every individual measurement passed. The
field is now derived from the panel so one number moves, but the audit should
learn to check the containment too.

## 11 · Still to do

* The `zoned` and `integrated` arrangements are defined but no plate opts into
  them yet — integrated text is drawn rather than laid out, so it needs a plate
  built for it.
* A4 portrait and Letter compositions for the four finalists — designed, not scaled.
* Greyscale and photocopy behaviour.
* The remaining fourteen certificates and five transcripts.
* The verification log (privacy-preserving, internal-only) — still outstanding
  from Priority 2.
