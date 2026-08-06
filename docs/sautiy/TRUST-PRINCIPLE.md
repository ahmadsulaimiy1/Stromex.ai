# The Trust Principle

**Permanent. Outranks every other requirement in this project, including sound quality.**

If users trust SAUTIY completely they will forgive small imperfections. If they stop trusting it,
excellent DSP will not keep them. Every other principle here is about making the product good; this
one is about making it believable, and a product nobody believes is not good.

---

## The five prohibitions

SAUTIY must never:

1. **Modify audio without telling the user.**
2. **Pretend an improvement happened when it did not.**
3. **Exaggerate quality.**
4. **Hide meaningful processing.**
5. **Make irreversible decisions automatically.**

Instead: **honest, reversible, clear.** In that order — an honest app that cannot undo is better than
a reversible one that lies about what it did.

---

## How each is currently kept

### 1. Never modify audio without telling the user

Automatic cleanup runs when a take ends. It is announced by the **Original / Enhanced** pair on the
canvas: both versions are always on screen, the one playing is the one lit. There is no state in
which processing is applied and the interface does not say so.

Captured WAVs are **write-once**. Nothing in the app reopens a take for writing; every change lives
in the timeline and is applied at playback and export. So "modify" is not even reachable for the
original file — a test asserts a take is a complete playable WAV after every flush, and the source
provider opens takes read-only.

### 2. Never pretend an improvement happened when it did not

When `Restraint` decides a recording needs almost nothing, the label reads **"Already clean"** rather
than "Enhanced". This is not cosmetic. A user who taps Original, hears no difference, and has been
told something was cleaned has caught the app in a lie, and will discount the next thing it says.

`Restraint.summary` on a transparent recording says *"This recording is already clean. Almost nothing
has been changed."* A test asserts that a clean recording comes out within **1 dB in every band** —
so the claim and the audio agree.

### 3. Never exaggerate quality

Every superlative in this project is either measured or absent:

* Preset distinctness is a measured decibel difference, not a claim.
* The signature sound is enforced as rules the build checks, and the document says outright that
  whether it is *recognisable* is a listening judgement and is not asserted.
* The implementation ledger separates verified from unproven and does not round up.
* The Founder Review answers two of its four questions "not yet" and two "unknown".

### 4. Never hide meaningful processing

The Studio panel shows what is applied. The preview says, in plain language, that the finished file
will be slightly cleaner and evener because some work can only be done on the whole recording. Every
outcome card reveals its actual parameters once applied, and its underlying acoustic in Advanced.

### 5. Never make irreversible decisions automatically

The only automatic change in the product is cleanup on stop, and it is reversible in one tap, forever,
because the original is on disk untouched. Nothing else — no space, no preset, no loudness target —
is ever applied without being asked for.

Voice DNA is written atomically with an `fsync` before the rename, and decodes tolerantly across
versions, so an update cannot silently destroy a sound somebody saved months ago.

---

## What this principle has already cost, deliberately

* **"Cleaned up" became "Already clean"** where that is the truth, giving up the nicer-sounding
  claim.
* **A single pill became two labelled halves**, which is more pixels and more layout for the same
  function — because one label cannot answer "was it changed, am I hearing it, how do I get back".
* **"Open location" was not added** to the export confirmation, despite being asked for, because it
  would have been new unverified plumbing and the system picker had already shown the user the folder.
  Trust includes not shipping things I cannot verify.
* **Auto Improve was nearly removed entirely** when this principle appeared to forbid it. It survives
  because it is announced, reversible and non-destructive — the three conditions that separate
  automation from presumption.

---

## The test

Before any release, for every automatic behaviour in the product:

1. Does the interface say it happened? *If no — say it or stop doing it.*
2. Can the user hear both versions? *If no — give them both or stop doing it.*
3. Is the original untouched on disk? *If no — do not ship it.*
4. Would the claim survive the user checking it? *If no — change the claim, not the audio.*

Four questions, and the acceptable answer to each is the same one.
