# Red team: what is wrong with these plates

Written adversarially and re-run after each pass. Nothing here is a plan; it is
what a hostile reviewer would say, with my own verdict.

## Fixed in this pass

**The watermark was a smudge — because a rosette is the wrong figure.** Twice
reduced and still reading as a stain. Relief needs flat areas separated by edges
that change direction, and radial symmetry gives light nothing to catch. Rebuilt
as a constructed heater shield — chief, cross quartering, the motif's star at the
honour point, a charge in each quarter — at the heater's own proportions
(width 5/6 of height, flanks straight for the top two fifths, the point struck as
two arcs). It now reads as relief.

**The security ground was invisible at 0.024.** Its own library says a wave lathe
belongs near 0.050, and a sheet-scale field wants a longer period than a swatch.
Corrected, and the powdered stars with it — which then read as confetti over the
text at 0.26 and came back to 0.13.

**The number cartouche was a box with a number in it.** Its lathe fill was a
small rosette in the middle of a wide panel. Now a figure wider than the panel,
clipped by it, with a knockout behind the number so the turning does not run
through it.

**The QR bay read as three empty checkboxes** — a form somebody forgot to fill
in. Now one quiet tinted panel with a diagonal and a single line: `QR BAY
RESERVED`.

**No heraldic register.** Three bays across the head, each captioned with its
authority. EdirasX draws the bays and never the emblems.

## Found *by* this pass, and fixed

**A device escaped its bay and painted a shield across half a certificate.** The
mount was a nested `<svg>` with a viewBox and `overflow`. Rendered in isolation
the same fragment behaved; only in place, inside a plate whose root carries
`preserveAspectRatio="none"`, did the nested viewport go unhonoured. Replaced
with an explicit `translate`/`scale` transform and a `clipPath`, which has no
such ambiguity — and a test now asserts a device drawing far outside its own
space is cropped.

**`DEVICE NOT SUPPLIED` printed on a finished certificate.** The dashed keyline
and that text are a studio affordance telling a designer what is missing;
printing them would put those words across the head of somebody's doctorate.
Empty bays now draw nothing unless `show_empty` is set.

**One plate's administrative band rendered at the top of the sheet**, over the
masthead — a single line that had not been converted with the other three and
was still being handed the content field, whose origin is the top.

**A synthesised signature, removed after one look.** Seeded from each officer's
name it produced three near-identical wavy scribbles across the execution band:
artificial in exactly the way this project exists to avoid. A signature is the
one mark on a certificate that is *about a person's hand*, and inventing it is
not a smaller lie than inventing a coat of arms. The rule is now the bays' rule —
mount what was supplied, draw nothing otherwise.

## Still open

**No woven border band.** The benchmark's top and bottom edges are a braided
band over a coloured ribbon; EdirasX uses a tessellation, which is flatter.

**The ceremonial field still carries less border weight than it did** before the
interior pass. The room should come back from the content, not the frame.

**The heraldic bay caption sits close to the lockup mark** on some plates. The
head needs its own zone rather than sharing the masthead's.

**Nothing has been printed.** No press, no paper, no foil, no loupe. Every
statement about foil, emboss, hairline hold and substrate remains a
specification, and that is still the largest gap in the programme.

## Claims a reviewer would challenge, and whether they hold

**"The barcode is real."** Holds — Code 128-C with the specification's
modulo-103 check character, verified by arithmetic, 11 modules per symbol and 13
for the stop, pure black at a 0.33mm module floor. A scanner is still the only
proof that matters and there is none here.

**"The QR is deliberately not drawn."** Holds, and should until there is an
encoder checked against a decoder.

**"Fine text, not microprint."** Holds — measured illegible at 300 DPI, legible
at 600, ≈0.41mm against microprint's ≤0.25mm.

**"Premium only."** Holds structurally: every term in the prompt vocabulary
lands on a premium construction because there are no others in it, and the tests
check every term and every pair.

**"An assistant cannot produce artwork."** Holds by signature — `propose()`
returns a `Brief`, so there is nowhere to put artwork.
