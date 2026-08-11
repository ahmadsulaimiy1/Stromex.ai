# M12 · EdirasX Signature — production specification

*one construction for frame and field: the lattice dissolving from trim to centre*

Generated from `tools/design/masterpiece.py`. Do not edit by hand: regenerate.

## 1 · Finished piece

| | |
|---|---|
| Trim | 297 × 210 mm (A4 landscape) |
| Bleed | 3 mm all round |
| Safe edge | 6 mm from trim — nothing is drawn inside it |
| Cutting tolerance | ±1.5 mm |
| Recommended edition | Royal or Flagship (see EDTECHX_PRODUCTION_SPEC.md §2) |

## 2 · Geometric family

This document's ornament is one family, appearing at six scales. A printer
replacing a damaged plate needs these six numbers, not a traced outline.

| | |
|---|---|
| Order | 10-fold |
| Star | {10/3} — inner/outer radius 0.7265 |
| Phase | 0.2094 rad off the sheet axis |
| Lathe | R=50, r=7, pen=8.4 |
| Lathe result | 50 lobes, closing after 7 turns |
| Interlace | 5 crossings per repeat |
| Derived from | The Meridian Institute for Advanced Study and Research · doctoral |

The lobe count is a whole multiple of the order
(50 = 5 × 10), which is why the lathe work and the
star work read as one hand. R and r are coprime, so the figure closes only
after 7 turns and cannot be approximated by a shorter one.

## 3 · Structural colour

| Role | Value |
|---|---|
| Ground | `#F7F2E6` |
| Ink | `#0A101C` |
| Accent | `#132038` |

Three structural colours, plus the metals. No fourth.

## 4 · Metals

| Role | Metal | Face | Process | Reference |
|---|---|---|---|---|
| Primary — ceremonial architecture | Royal gold | `#E3C169` | Hot-stamped gold foil on ivory stock | Kurz Luxor 220 / API 501 gold — vendor to match |
| Secondary — fine ornamental registers | Silver | `#CFD6DD` | Silver foil; cool shadow because silver reflects a cool room | Kurz Luxor 700 silver — vendor to match |
| Engraved — shadow and relief | Deep gold | `#C99B3C` | Deep gold foil or metallic ink; the highest-chroma register | Pantone 872 C metallic / deep gold foil |
| Security — fine ruling and text | Champagne gold | `#DCCBA6` | Pale champagne foil; reads as metal without reading as brass | API 220 champagne — vendor to match |
| Heritage — ornament | Antique gold | `#C0A059` | Oxidised gold foil, or gold ink over a warm grey underprint | Kurz Luxor 355 antique — vendor to match |

Two foil passes: primary and secondary. Everything else is process ink or a die.

## 5 · Separations supplied

| File suffix | Contents |
|---|---|
| substrate | Paper colour and deterministic fibre field |
| security | Guilloché registers, anti-copy ruling, ground figure |
| process | Structural colour — the CMYK plate |
| foil-primary | Foil plate 1: ceremonial architecture |
| foil-secondary | Foil plate 2: fine ornamental registers |
| emboss | Blind emboss die: seal and institutional mark |
| finetext | Fine text ring — serial-bearing, 0.58mm (see spec §6) |
| variable | Variable data: serial, verification code, issue date |

Each is a standalone SVG in millimetre user units at the trim size, in register.
The emboss and variable-data layers are emitted at *measured* positions read
back from the rendered page, because those elements are placed by the layout and
their coordinates are a result rather than an input.

## 6 · Linework

| Element | Weight |
|---|---|
| Fine text and micro-texture | 0.07–0.09 mm |
| Fine register | 0.09–0.20 mm |
| Engraved rule | three flat strokes, 0.28–0.72 mm overall |
| Frame register | 0.55–0.72 mm |

No opacity on any line, at any weight. Every pale tone is a flat pre-mixed ink.

## 7 · Fine text — measured, and not microprint

The serial-bearing ring is set at 0.58 mm, ≈0.41 mm cap height. Rasterised from
this artwork:

* **300 DPI** — 6.85 px per em. Illegible; the register reads as grey texture.
* **600 DPI** — 13.7 px per em. Legible; serial and verification code read back.

It is therefore **fine text, not microprint**. Security microprint means a cap
height at or below about 0.25 mm, chosen so a loupe resolves it and a copier
cannot; this is well above that and does not have that property. Any 300 DPI
edition must not describe this register as carrying readable data. No press test
has been run — see §9.

## 8 · Finishing

| Process | Where | Die |
|---|---|---|
| Hot foil, pass 1 | `--foil-primary.svg` | Yes |
| Hot foil, pass 2 | `--foil-secondary.svg` | Yes |
| Blind emboss | `--emboss.svg` — seal and institutional mark | Male/female pair |
| Serial numbering | `--variable.svg` | Numbering box |

## 9 · Not yet validated

Nothing here has been printed. This environment has no press, no paper and no
loupe, so the following are **unverified**: foil adhesion and register on cotton
stock; emboss depth and whether the die holds the 10-fold device at
seal scale; whether any press holds the 0.07 mm hairlines; whether the fine-text ring
survives a real 600 DPI output rather than a rasterised preview; how the metals
read under daylight, warm indoor light and raking light; and what the sheet
looks like from the back. Until a proof exists, every statement in §7 and §8 is
a specification, not a result.
