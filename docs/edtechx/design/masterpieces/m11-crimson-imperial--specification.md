# M11 · Crimson Imperial — production specification

*crimson mass, gold architecture, one bright ceremonial centre*

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
| Ground | `#F7F1E4` |
| Ink | `#2A0E18` |
| Accent | `#5A1226` |

Three structural colours, plus the metals. No fourth.

## 4 · Metals

| Role | Metal | Face | Process | Reference |
|---|---|---|---|---|
| Primary — ceremonial architecture | Deep gold | `#C99B3C` | Deep gold foil or metallic ink; the highest-chroma register | Pantone 872 C metallic / deep gold foil |
| Secondary — fine ornamental registers | Royal gold | `#E3C169` | Hot-stamped gold foil on ivory stock | Kurz Luxor 220 / API 501 gold — vendor to match |
| Engraved — shadow and relief | Antique gold | `#C0A059` | Oxidised gold foil, or gold ink over a warm grey underprint | Kurz Luxor 355 antique — vendor to match |
| Security — fine ruling and text | Pale gold | `#EADFAE` | Pale gold foil on a dark ground; the low-contrast register | Kurz Luxor 380 pale — vendor to match |
| Heritage — ornament | Copper | `#D08E5F` | Copper foil; the warm counter-metal in a two-tone scheme | Kurz Luxor 440 copper — vendor to match |

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

## 6 · Linework — counted, not asserted

Every stroke in the supplied separations, by width:

| Width | Count |
|---|---|
| **0.048 mm** | 8 |
| **0.056 mm** | 8 |
| **0.061 mm** | 1 |
| **0.070 mm** | 885 |
| **0.072 mm** | 1 |
| **0.075 mm** | 1 |
| **0.080 mm** | 207 |
| **0.088 mm** | 13 |
| **0.090 mm** | 176 |
| **0.099 mm** | 40 |
| **0.100 mm** | 42 |
| **0.104 mm** | 8 |
| **0.110 mm** | 875 |
| **0.140 mm** | 10 |
| **0.143 mm** | 1 |
| **0.160 mm** | 10 |
| **0.165 mm** | 4 |
| **0.168 mm** | 1 |
| **0.180 mm** | 5 |
| **0.186 mm** | 40 |
| **0.200 mm** | 2 |
| **0.211 mm** | 4 |
| **0.220 mm** | 5 |
| **0.248 mm** | 4 |
| **0.260 mm** | 11 |
| **0.300 mm** | 6 |
| **0.340 mm** | 4 |
| **0.400 mm** | 1 |
| **0.420 mm** | 7 |
| **0.450 mm** | 4 |
| **0.620 mm** | 5 |
| **0.720 mm** | 1 |
| **0.836 mm** | 2 |
| **0.924 mm** | 6 |
| **0.988 mm** | 2 |
| **1.064 mm** | 1 |
| **1.092 mm** | 6 |
| **1.176 mm** | 3 |
| **1.216 mm** | 1 |
| **1.344 mm** | 3 |
| **1.672 mm** | 1 |
| **1.848 mm** | 3 |

**The floor in this artwork is 0.048 mm.** That is stated so you can act on
it: confirm your reproduction floor and anything underneath it will be raised,
rather than being left to drop out or fill in. Nothing here uses a "hairline"
keyword — every stroke is an explicit width in millimetres.

No opacity on any line, at any weight. Every pale tone is a flat pre-mixed ink,
because a stroke with an opacity separates into a screen percentage and a
screened hairline is the first thing to leave the sheet.

## 6a · Three questions, answers required in writing

Nothing further can be finished until these are answered. Each blocks a specific
step; none is a preference.

**Which ICC output profile?** A PDF/X file *is* a PDF plus an output intent, and
the output intent is your characterisation of your press, your paper and your
ink. There is no safe default and one will not be guessed — guessing ships a
file that states, in machine-readable form, a printing condition nobody agreed
to. It also blocks the RGB→CMYK separation, because the separation is *to* that
profile.

**Which PDF/X part — and will you accept PDF/X-4?** The artwork uses live
transparency in the emboss simulation. PDF/X-1a and PDF/X-3 forbid it and force
a flatten; PDF/X-4 permits it. This is not a metadata setting: a flatten turns
every rule, guilloché line and fine-text rail into a raster at the flattener's
resolution, and a certificate that has been rasterised is a photograph of a
certificate. If you require X-1a or X-3, say so and the transparency will be
removed by redrawing rather than by conversion.

**Your maximum total area coverage, and must pure black stay 100 % K?** The
plate carries large solid dark areas, so the separation has to be built to your
TAC limit rather than trimmed to it afterwards. And if a machine-readable mark
is added to this family later it will be drawn in pure black: separated into a
rich four-colour black it picks up registration spread and stops scanning.

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
