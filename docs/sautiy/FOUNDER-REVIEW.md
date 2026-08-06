# SAUTIY™ — Founder Review

**Every release must pass this before it is accepted.**

Four questions. They are not about tests, presets or modules — they are about whether the person
whose name is on this product would put it in front of people.

Two of the four cannot be answered from a codebase, and this document says so rather than guessing.
A checklist that answers itself is not a gate.

---

## The four questions

| | Question | Answer | Who can answer it |
|---|---|---|---|
| 1 | Would I proudly use this app to record the entire Qur'an? | **Not yet** | Imam Ahmad Sulaimiy |
| 2 | Would I confidently use it for a public lecture? | **Not yet** | Imam Ahmad Sulaimiy |
| 3 | Would I recommend it over my current recording app? | **Unknown** | Imam Ahmad Sulaimiy |
| 4 | Would I be proud to demonstrate it on stage? | **Unknown** | Imam Ahmad Sulaimiy |

**No answer here is mine to give.** Questions 1 and 2 turn on whether the recording sounds good
enough to publish and whether the app can be trusted for ninety unattended minutes. Questions 3 and
4 turn on how it looks and feels in the hand. I cannot hear the output and cannot see the screen, so
what I can honestly supply is the evidence underneath each question and an explicit statement of what
is still missing.

---

## 1. Record the entire Qur'an

**What is verified.** Capture opens, frames arrive, and the file on disk is a complete playable WAV
after every flush — so a process kill loses at most the last flush interval, not the recording. A
ninety-minute take holds about 8 MB of peaks in memory rather than 500 MB of audio, so the length
that matters most is the length least likely to fail. 24 instrumented tests exercise this on a real
Android. Captured WAVs are write-once and never modified; every change lives in the timeline.

**What is not.** Nobody has recorded for ninety minutes on a real phone. The emulator has no
microphone, so what has been proven is that the *machinery* survives, not that a long recitation
comes out sounding like the room it was recorded in. Recitation is also the material with the least
tolerance for the one thing automatic processing can get wrong — flattening the delivery — and while
a test holds the loudest-to-quietest ratio at 2.5 or better through every recitation profile, a ratio
is not a judgement.

**Blocking:** one long recitation, recorded and listened to end to end.

---

## 2. A public lecture

**What is verified.** A `Lecture` outcome exists, is measurably distinct from the other nine, and is
audibly a hall rather than a name for one. Storage warns at two minutes remaining. Recording
guidance names the four things that ruin a take and stays silent when nothing is wrong.

**What is not.** A lecture is recorded once, cannot be repeated, and is usually the recording someone
cares about most. Confidence there needs a track record this app does not have: no crash across a
long unattended session, no interruption by a phone call, no loss on low battery. Two of those three
are untested.

**Blocking:** one real lecture, and an interruption test — phone call, low battery, screen off.

---

## 3. Better than the app they use now

**What is verified.** Record is one tap, play is one tap, and a finished take is cleaned up before it
is ever played — which is the thing most recorders do not do. MP3 export is validated by Android's
own decoder. Ten presets, each measurably distinct.

**What is not.** "Better" is comparative and no comparison has been run. The competitive benchmark
against Voloco and the rest exists as a directive, not as a result.

**Blocking:** the same passage recorded in SAUTIY and in the app currently used, compared by ear.

---

## 4. Demonstrate it on stage

**What is verified.** The APK builds, installs, launches with an empty crash buffer, and passes 24
device tests. Screenshots are captured automatically from the running application on every green run.

**What is not.** **I have never seen the app.** The screenshot artifact host is blocked by the same
network policy that blocks Google's Maven, so the pictures exist and are the user's to view but not
mine to review. Every claim in this project about layout, spacing, calm or beauty is a claim about
the code that produces them, not about what appears on a screen.

**Blocking:** somebody looking at the screenshots and saying what is wrong with them.

---

## What a release still owes

* A **VERIFIED** and an **IMPLEMENTED, AWAITING VERIFICATION** section, never mixed.
* A subtraction: at least one element removed or simplified.
* A refinement: at least one existing interaction improved.
* Nothing described as complete until it has compiled, installed, run, and produced screenshots.

## Standing gaps, listed so they cannot be forgotten

1. Nothing in this app has been heard by anyone.
2. Nothing in this app has been seen by me.
3. No recording longer than a test fixture has been made.
4. No interruption — call, battery, screen off — has been tested.
5. No comparison against another recorder has been run.

The first two are the ones that matter. Everything else is engineering.
