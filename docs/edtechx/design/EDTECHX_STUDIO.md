# The institution's design studio

An institution onboarding to EdirasX designs its own document family: chooses a
ground, chooses a metal scheme, places its arms in the heraldic bays, uploads its
device and gets a struck golden seal built round it, and asks an assistant for
suggestions when it does not know what it wants.

## The studio edits a brief; the engine renders it

Nothing in the studio draws. A **`Brief`** is about a dozen values — ground key,
ground strength, gilding scheme, ceremonial level, language arrangement, three
structural colours, whether it buys a second foil pass, references to the
institution's own assets, an optional motif order. The deterministic plate engine
turns that into artwork.

That separation is the whole design:

* a brief is small enough to store, diff, review and approve;
* two renders of one brief are the same plate, forever;
* the artwork stays vector, press-legal and exact at 2400 DPI;
* and no sequence of studio actions can produce a sheet that breaks the press
  rules, because the studio never touches the artwork.

Six starting points ship — Royal Palace, Imperial Islamic, Crimson Imperial,
Scholarly Ijāzah (Arabic-only), Executive, Completion (Level I) — and every field
of each is editable.

## What an assistant may and may not do

**May: propose a brief.** "A deep green ground with antique gold, twelve-fold
geometry, Arabic-primary, ceremonial level III" is a design opinion. It is
checkable, a human approves it, and `AssistPort` is that contract — it returns a
reviewed `Brief` or raises `AssistUnavailable`. Provider-agnostic by design:
Claude, GPT, a rules engine or nothing at all satisfies it, and the studio works
when it is unimplemented.

**May not: produce artwork that lands on a certificate.** Not the ground, not
the frame, not the seal, and above all not the security layer. Three reasons,
none aesthetic:

*It would be a raster.* Over a 297mm sheet a 1024-pixel image is 87 DPI. This
codebase has already measured what that costs.

*It would be unaccountable.* A certificate is a legal instrument. "A model
produced it" is not a provenance an embassy can act on.

*It would be unrepeatable.* Two runs of a generative model are not the same
plate, and a reissued document must be identical to the original or the
verification argument collapses.

The signature is the enforcement: `propose()` returns a `Brief`, so there is
nowhere to put artwork. And the credential layer is **not in a brief** —
identifiers, the verification panel, the barcode and the seal's authority come
from `documents.authority` and `design.credential`, and a test asserts none of
those field names can appear.

## Uploaded logos are mounted, never generated

EdirasX constructs the gold — turned field, engraved rim, legend ring carrying
the document's serial, blind emboss, star ring — and the institution's device
sits in a stated clear circle at 46 % of the radius. The metal is ours and it is
vector; the device is theirs and it is theirs.

Supply nothing and the motif's own rosette takes that position, which EdirasX
may legitimately draw because it is our construction and not a claim to be
anybody's arms.

**A mounted device is not an approved seal.** The studio can mount a logo and
show what it looks like. Whether that device may seal an issued document is
governed by `documents.authority` — approval, validity period, revocation — which
refuses to issue rather than substitute. Appearance and authority are separate on
purpose; conflating them is how a system ends up sealing documents with a logo
somebody uploaded on a Tuesday.

## Heraldic bays — the register, never the emblems

Every benchmark sheet carries devices EdirasX must not draw: a national coat of
arms, a state's arms, the institution's crest. So `heraldry.py` builds the
**bays** — a reserved area, an enforced clear zone (14 % each side, so one
institution's tightly-cropped crest does not sit twice as large as another's),
and a caption naming the authority.

An unsupplied bay draws a fine dashed keyline and the words `DEVICE NOT
SUPPLIED`, so a sheet designed before the arms arrive still composes correctly
and visibly says what is missing. A placeholder emblem would not be honest.

## Bitmaps: allowed, with the cost stated

An institution's device may only exist as a bitmap. That is fine — it is their
mark, not our artwork — but the requirement is stated at upload rather than
discovered at the printer. A 22mm device needs **260 pixels** across for 300 DPI
and **520** for 600. Vector has no such limit and the studio should say so.

## Two rules the gate got wrong, and what fixed them

The review gate is deliberately narrow and it has been wrong twice already —
both times caught by testing it against EdirasX's own designs.

**It demanded three distinct structural colours** and immediately refused the
Imperial Islamic plate, where the text and the border mass are deliberately one
midnight. A two-colour scheme is a decision, not a missing register. The rule now
says only what it can defend: type may not be set in the colour of the paper.

**It inferred the second foil pass from the scheme** and consequently refused
every Level I and II design, because every gilding scheme names five metal roles.
Whether a plate is separated onto one foil or two is a decision with a price at
the printer, so it is now an explicit `second_metal` field, checked against the
level.
