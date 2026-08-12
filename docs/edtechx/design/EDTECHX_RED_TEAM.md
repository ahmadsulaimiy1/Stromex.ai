# Red team: what is wrong with these plates

Written adversarially and before release, against the benchmark. Nothing here is
a plan; it is a list of things a hostile reviewer would say about the current
sheets, with my own verdict on each.

## Confirmed defects — still present

**1 · The number cartouche is a box with a number in it.** Its guilloché fill
is passed but renders at a strength that does not read, so a panel meant to
balance the seal reads as an empty rectangle. The benchmark's equivalent is
visibly turned. *Not fixed.*

**2 · The QR bay reads as an unfinished form.** Three square outlines and the
words `QR RESERVED` look like empty checkboxes on a draft. Reserving the bay is
right; drawing it as three boxes is not. It should be a filled, obviously
*blank* plate — a solid tint panel with the caption — so it reads as "nothing
here yet" rather than as "form to complete". *Not fixed.*

**3 · The allover wave-lathe ground is invisible at 0.024.** It is doing none of
the work it was added for. The benchmark's ground reads clearly at arm's length
as a turned field. Either the strength is wrong or `wave_lathe` at scale 1.5 has
too long a period for a 297mm sheet. *Not fixed — needs a strength sweep looked
at, not guessed.*

**4 · The embossed crest is a smudge, not a device.** Twice reduced and still
reading as a stain rather than as relief, because a rosette is the wrong figure
for a watermark — the benchmark's is a *shield with internal structure*, which
holds an emboss. A rosette's radial symmetry gives the emboss nothing to catch.
*Not fixed; the figure is wrong, not the strength.*

**5 · No heraldic register.** The benchmark carries three devices across the
head with their authorities named. EdirasX has one mark in the lockup. The bays
were specified in the teardown and not built. *Not built.*

**6 · No signature assets.** The authority chain stores signature images; the
plates draw a rule and a name. Every benchmark sheet has a real signature above
the rule, and its absence is why the execution band still reads as a form.
*Not built.*

**7 · No woven border band.** The benchmark's top and bottom edges are a braided
band over a coloured ribbon. EdirasX uses a tessellation, which is flatter.
*Not built.*

**8 · The ceremonial field lost its border weight.** Recorded two passes ago and
still true: the panels opened to hold the interior and took the room from the
frame. M11's crimson band is thinner than it was.

## Claims a reviewer would challenge, and whether they hold

**"The barcode is real."** Holds. Code 128-C with the specification's modulo-103
check character, verified against the worked example, 11 modules per symbol and
13 for the stop, drawn in pure black at a stated module floor of 0.33mm. A
scanner is still the only proof that matters and there is none here.

**"Five identifiers."** Holds — document ID, verification code, archive
reference, identity number, certificate number, all labelled, four in the panel
and one in its own cartouche.

**"The QR is deliberately not drawn."** Holds, and should stay that way until
there is an encoder that has been checked against a decoder.

**"Fine text, not microprint."** Holds. Measured: illegible at 300 DPI, legible
at 600, ≈0.41mm cap height against microprint's ≤0.25mm. Renamed accordingly.

**"Nothing has been printed."** Holds, and is the largest outstanding gap in the
whole programme. Every statement about foil, emboss, hairline hold and substrate
is a specification.

## The honest summary

The officiality gap is now roughly half closed. The sheets carry a real
verification architecture where they carried none, and that is the single
biggest step towards the benchmark taken so far. The *craft* gap is not closed:
four of the eight defects above are things the benchmark does and EdirasX
still does not, and two more are elements that were added this pass and do not
yet read.

These plates are better than the last set and are not yet at the standard.
