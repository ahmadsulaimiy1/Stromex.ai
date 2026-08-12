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


---

# Simple prompts — and no route to a cheap design

An institution types *"royal, midnight blue and gold, Arabic first, for our
PhD"* and gets a finished premium design. `design/prompt.py` is the vocabulary
that makes that work, and it is deliberately **not a model**: a table of terms a
real registrar would type, each mapping to a patch on a brief, resolved
deterministically.

Three reasons a table rather than a model, and the third is the one that matters:

*It works offline.* No key, no network, no per-request cost. An institution
onboarding at 2am gets the same studio as one onboarding in a demo.

*It is repeatable.* The same words give the same brief, forever. A model gives a
different design on Tuesday, and an institution that approved one on Monday
would not recognise it.

*It cannot fail downward.* **Every term in the table lands on a premium
construction, because there are no others in it.** A person can type "simple",
"clean", "minimal", "plain" or "modern" and what they get is the most
*restrained premium* register — laid paper, one metal, engraved rules, real
typography. Never a flat sheet, because a flat sheet is not in the vocabulary
and no code path reaches one. The product rule is structural rather than
advisory: **the cheap option does not exist to be chosen.**

An assistant sits on top of this and does the same job better for unusual
requests, but it is an accelerator, never a dependency, and it returns the same
`Brief`.

## Six axes

`character` (royal, imperial, crimson, heritage, emerald, midnight, executive,
scholarly) · `metal` · `ground` · `language` · `level` · `geometry`. One term per
axis wins — **the last one typed**, so "midnight blue, actually crimson" does
what a person means.

The **purpose decides the level** when the words do not: a certificate asked for
in crimson is a Level III document in crimson, not a doctorate in crimson. A
stated level beats the purpose. And Level I never carries ink behind the words,
whatever ground a character term chose.

Unrecognised design words are **reported, not swallowed** — an institution that
typed "letterpress" is told it was ignored — while stopwords are filtered so the
real finding is visible.

Guarded by tests that check *every term* and *every pair of terms* renders, and
that asking for "simple" still returns level ≥ II with a real metal and a real
ground.

## Signature preparation

`design/signature_asset.py` lifts an officer's ink off the paper it was
photographed on. A phone capture is dark strokes on a field that is not white —
a shadow down one side, a colour cast, JPEG noise — and dropping that onto an
ivory certificate puts a grey rectangle on it.

The method is deliberately explainable, because a registrar has to look at the
result and agree with it: estimate the paper from a high percentile; measure
each pixel's distance *below* the paper rather than its absolute darkness, so a
signature on grey card and one on white both work; ramp the alpha across a band
rather than stepping, so the pen's antialiasing survives and the stroke stays a
stroke; recolour to the document's ink, because a blue biro on a midnight-set
certificate is wrong twice over; and trim to the strokes, so a signature
photographed in the middle of an A4 sheet does not render at 4mm in a 60mm box.

`assess()` refuses a bad capture **at upload, while the officer is still there**,
and every problem is phrased as something to do: "sign again in black on white
paper", "photograph it again in brighter light", "crop closer to the strokes",
"the capture is 300px wide and needs 710px for 300 DPI".

Stated plainly: it does not vectorise, it does not repair a bad capture, and it
does not authenticate anything. Whether the officer holding that pen was in
office on the day is the authority chain's question.

## Two implementation bugs the tests caught

**"The last term wins" was false.** The resolver iterated the vocabulary table
and overwrote per axis, so the last row *in the file* won rather than the last
word *typed* — "midnight blue, actually crimson" produced midnight, the opposite
of the documented behaviour.

**The signature softness parameter was inverted against its own docstring.**
`spread × (1 − softness)` meant asking for a hard edge produced the softest
possible ramp. The width is now `softness × spread`.
