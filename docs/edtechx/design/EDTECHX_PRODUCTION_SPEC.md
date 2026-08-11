# Physical production specification — ceremonial documents

**What this is.** The artwork EdirasX generates is a blueprint for a physical
object. This file is what a print vendor, a foil stamper, an engraver or a
binder needs in order to manufacture that object, and what a purchaser needs in
order to know what they are buying.

**What this is not.** It is not a claim that any digital edition possesses the
properties described below. The distinction is the point of the document, and it
is drawn explicitly in §6.

---

## 1. Finished dimensions and tolerances

| | A4 landscape | A4 portrait | A3 landscape | Letter landscape |
|---|---|---|---|---|
| Trim | 297 × 210 mm | 210 × 297 mm | 420 × 297 mm | 279.4 × 215.9 mm |
| Bleed | 3 mm all round | 3 mm | 3 mm | 3 mm |
| Safe edge | 6 mm from trim | 6 mm | 6 mm | 6 mm |
| Cutting tolerance | ±1.5 mm | ±1.5 mm | ±1.5 mm | ±1.5 mm |

Nothing is drawn inside the safe edge. The 6mm figure is four times the cutting
tolerance, which is what stops a rule landing on the knife on some of the
copies rather than none of them.

**A3 is a designed size, not an enlargement.** A doctoral award is genuinely
framed at A3 in some institutions. Scaling an A4 plate by 141% ships hairlines
at 0.14mm, below several presses' minimum stroke, so the A3 composition is
composed rather than scaled.

## 2. Substrate

| Edition | Stock | Weight | Colour | Notes |
|---|---|---|---|---|
| Digital | — | — | — | PDF/A target; screen and archive only |
| Standard print | Uncoated wove | 170–200 gsm | Warm white | Digital or offset |
| Premium print | Uncoated laid or wove | 250–300 gsm | Ivory | Offset; metallic ink permitted |
| Royal edition | 100% cotton, mould-made | 300–350 gsm | Ivory / natural | Foil and emboss |
| Security edition | Cotton security paper with embedded fibres | 120–160 gsm | Natural | Fine-line printing, serialised |
| Flagship edition | 100% cotton, mould-made, watermarked | 350 gsm | Ivory | Every applicable process |

Never a gloss stock and never a laminate. Gloss reads as inexpensive whatever is
printed on it, and laminate flattens an emboss, which defeats the single most
effective low-cost physical anti-counterfeit feature available.

Clean-edge cut for all editions. A deckled edge reads as artisan stationery
rather than as a state instrument.

## 3. Inks and metals

The eight metals are defined in `app/modules/design/gilding.py`; each carries a
foil reference a vendor can order against, named honestly as a *reference* —
matching the exact shade is the vendor's job.

| Metal | Face | Process | Reference |
|---|---|---|---|
| Royal gold | `#E3C169` | Hot-stamped gold foil on ivory | Kurz Luxor 220 / API 501 |
| Antique gold | `#C0A059` | Oxidised foil, or gold ink over a warm grey underprint | Kurz Luxor 355 |
| Champagne | `#DCCBA6` | Pale champagne foil | API 220 |
| Pale gold | `#EADFAE` | Pale foil for a dark ground | Kurz Luxor 380 |
| Deep gold | `#C99B3C` | Deep foil or metallic ink | Pantone 872 C |
| Brushed gold | `#C6B489` | Satin foil — a diffuse face | Vendor to match |
| Copper | `#D08E5F` | Copper foil, the warm counter-metal | Kurz Luxor 440 |
| Silver | `#CFD6DD` | Silver foil, cool shadow | Kurz Luxor 700 |

**A second metal is a second pass on press.** It is granted by ceremonial level
(III and IV) rather than taken by a template, because it is a real cost.

**Structural colours are capped at three per document** — a ground, an ink and
one accent — plus the metals and one reserved alert colour used only for
DUPLICATE / CERTIFIED TRUE COPY / PROVISIONAL. What makes a rich plate look
cheap is rarely the ornament; it is the fourth colour.

## 4. Linework

| Element | Weight | Rule |
|---|---|---|
| Hairline / fine texture | 0.07–0.09 mm | Never below 0.07mm; never screened |
| Fine register | 0.10–0.20 mm | Flat ink only |
| Engraved rule | 0.30–0.75 mm | Three flat strokes: highlight, face, shadow |
| Frame register | 0.45–0.85 mm | Weights step *up* inwards |

**No opacity on a hairline, ever.** A 0.1mm stroke at 40% opacity becomes a
screen percentage at separation, and a screened hairline is the first thing to
drop off press — the line is simply not on the sheet. Every pale tone in the
artwork is pre-mixed flat against its ground by `geometry.tint()` (ivory grounds)
or `geometry.blend()` (dark grounds).

**A gradient is legal on an area and never on a line.** Foil simulations use
`gilding.foil_gradient()` on fills only.

## 5. Finishing

| Process | Where | Die required |
|---|---|---|
| Hot foil stamping | Frame registers, cresting, medallion rims, title | Yes — one per metal |
| Blind emboss | Institutional seal, central mark | Yes — male/female pair |
| Deboss | Cartouche panels, optional | Yes |
| Letterpress / intaglio | Recipient's name, optional flagship | Yes |
| Serial numbering | Verification band and fine-text ring | Numbering box |
| Die-cut | Not used | — |

The blind emboss is the recommendation to argue hardest for. It requires a die
most counterfeiters will not have made, it photocopies as a faint shadow rather
than disappearing — which itself becomes a verification cue — and its
cost-per-unit at volume is small.

## 6. What is real, what is a production feature, and what is simulation

This section is binding. Nothing may be described to an institution or a
credential-holder in terms stronger than these.

### Cryptographically verifiable — real in every edition, including digital

- HMAC content signature over the frozen payload, with key versioning
  (`documents/integrity.py`).
- Permanent credential serial and public verification code, resolving to a
  five-state public answer: VALID / REVOKED / SUPERSEDED / INVALID /
  UNVERIFIABLE. A system fault returns UNVERIFIABLE and never an accusation
  against the holder.
- Signatory and seal snapshots taken at issue, so a document stays valid after
  the officer who signed it leaves office.

### Genuine production features — real only in the physical editions that buy them

Foil, emboss, deboss, letterpress, cotton substrate, embedded fibres,
watermarked paper, UV-reactive ink. **A renderer cannot specify UV ink**: it is
a choice made at the vendor. What the artwork does is reserve an undisturbed
zone adjacent to the seal where a UV mark would sit.

### Visual simulation — appearance only, in every edition

Reproduced verbatim from `gilding.SIMULATION`:

| Treatment | What it is | What it is not |
|---|---|---|
| Foil gradient | A banded linear gradient standing in for a struck metallic foil. | Visual simulation only. It is ink on a screen or a flat press sheet; it has no metallic reflectance, no tactile relief, and no anti-copy property. Physical foil requires a hot-stamping die. |
| Engraved metal rule | Three flat strokes in the metal's highlight, face and shadow inks, reading as a line cut into the sheet. | Printable as specified in metallic or process ink. Becomes a genuine engraving only if produced by intaglio or die-stamping, which is a vendor process. |
| Emboss | A pale copy offset towards the light and an ink copy offset away, beneath the drawn figure. | Visual simulation. A true blind emboss is uninked relief and needs a die pair. |
| Raised type | Paired light and dark offsets on display type, standing in for raised foil or thermographic ink. | Visual simulation. Raised type is a physical process and cannot be produced by a renderer. |

### Named honestly as appearance, not protection

- **Paper fibres** (`geometry.fibres`) — deterministic, cosmetic. A fibre drawn
  in ink is not a fibre embedded in a substrate.
- **Anti-copy screen** (`geometry.line_screen`) — a single ruling set off a
  copier's screen angles. **Not a latent image**, which needs a coarse and a
  fine ruling at matched ink fraction with a shape defined between them.
- **Guilloché** — a genuine closed epitrochoid construction, expensive to
  reproduce without the generating parameters. It is a deterrent, not a
  guarantee.
- **Fine text** — real vector text at 0.58mm carrying the document's own serial.
  **Not microprint, and now measured rather than assumed.** Rasterised from the
  artwork: at 300 DPI it is 6.85 px per em (≈0.41mm cap height) and *illegible*
  — the register reads as grey texture; at 600 DPI it is 13.7 px per em and the
  serial and verification code read back. Security microprint means a cap height
  at or below about 0.25mm, chosen so a loupe resolves it and a copier cannot;
  this is well above that and does not have the property. The feature is named
  `fine_text_ring` throughout for that reason. No press test has been run, so
  whether paper holds it is still unknown. A 300 DPI edition must not be
  described as carrying readable data in this register.

## 7. Ceremonial level and edition

| Level | Documents | Recommended edition |
|---|---|---|
| I Elegant | Report cards, letters, statements of results | Digital / standard print |
| II Premium | Diplomas, professional certificates | Standard / premium print |
| III Ceremonial | Graduation, distinction, major awards | Premium / royal |
| IV Flagship | Doctorates, honorary and royal awards | Royal / flagship |

A level is recorded on the template *version*, so a document issued in 2027
keeps the level it was designed at when the institution raises the level of new
ones in 2029.

## 8. Per-document specification

Every flagship template ships with a companion sheet stating: finished size,
bleed and safe area, stock and weight, structural colours as process values,
each metal and the areas it covers, emboss and deboss areas with die outlines,
guilloché parameters (`R : r : pen`, pass count, amplitude), the security ruling
angle and pitch, microtext size and content, the serial format, the seal
specification, the signature block architecture, the verification block, and the
recommended press.

That sheet is generated from the same plate the artwork is generated from, so it
cannot drift from what is actually drawn.
