# Chapter 12 — Qur'an Studio

> A practice instrument for reciters. Not a separate application — a project type inside the
> same workspace.

---

## 12.1 The Person

Ustadh Bilal (chapter 3.1.1) records the same passage six or seven times after ʿIshāʾ and keeps
the best. He needs takes that never overwrite, comparison that is instant, and Arabic that is
set properly. He must not be asked to name a file before he can record.

## 12.2 It Is Not A Separate Experience

Qur'an Studio is a **project type**, opened from the Project panel. The canvas, the transport,
the editing tools, the studio chain and the export path are all the same. What changes is what
the Project panel holds: a passage, a set of takes, and a record of progress.

Chapter 4.1 is not suspended for it. There is no Qur'an screen.

## 12.3 The Model

| Type | Is |
|---|---|
| **Project** | A surah, a juz, or a named passage |
| **Passage** | A contiguous ayah range within it |
| **Take** | One recording of one passage. Immutable. Never overwritten. |
| **Note** | A reciter's own remark against a take, or against a moment within it |

Recording a passage that already has takes **adds** a take. It never replaces one. This is the
single most important rule in the chapter: a reciter who loses a good take to a worse one loses
work that cannot be recreated.

## 12.4 Comparison

Takes of the same passage are compared **A/B, gap-free, from the same position**. Switching
between them does not restart either. That is the whole of the feature and it is the reason the
studio exists — a reciter cannot judge two takes they have to listen to separately.

Each take carries its measured numbers (chapter 10.4) so a judgement can be checked against
something: duration, loudness, noise floor, clipping.

## 12.5 Ayah Tracking

Markers can be **labelled with an ayah number**. Where they are, three things become possible:

- Jump to an ayah directly.
- See per-ayah duration, so an unusually fast or slow ayah is visible without listening.
- Export a single ayah as its own file.

Ayah numbering is entered by the reciter, not inferred. SAUTIY does not attempt to detect which
ayah is being recited: a wrong inference in this domain is not a minor annoyance, and a tool
that guesses at scripture has overstepped.

## 12.6 Progress

The Project panel shows what is genuinely known and nothing more:

- Passages recorded, of passages planned.
- Total recorded duration.
- Takes per passage.
- Date of the most recent take.

**There are no streaks, no badges, no targets and no encouragement.** Chapter 1.4 principle 4
and chapter 1.8's non-goals both apply, and they apply with particular force here: gamifying
recitation would be a category error about what the user is doing.

## 12.7 Arabic Typography

- Qur'anic text is set in **Amiri** at 26 sp with 48 sp of leading, regardless of the density
  of the surrounding interface (chapter 2.4.2 clause 5).
- It is **never truncated with an ellipsis**. It wraps, or it scrolls.
- It is never tracked, never condensed, and never set in a UI face.
- The interface mirrors fully in right-to-left, including the transport dock's ordering, the
  waveform's time direction remaining left-to-right (because time is not a language), and the
  layer strip.
- Non-Qur'anic Arabic interface text is set in **Cairo**.

## 12.8 Respect

- No audio of recitation is uploaded, analysed remotely, or used for any purpose but the
  reciter's own (chapter 1.3.7).
- No processing is applied to a recitation without being asked. The **Recitation** preset is
  deliberately the lightest compression of the nine (chapter 10.3), because recitation lives on
  its dynamics and flattening them is the one thing a reciter will not forgive.
- Deleting a take goes to the trash with a stated 30-day recovery window, like everything else.

---

### Implementation

The project model, take set and passage tracking are serialisable structures in
`sautiy-core/.../edit/` and the project store; comparison uses the same
`TimelineRenderer` path as ordinary playback, so a take comparison is not a special mode.
Amiri is bundled and its metrics are asserted by `DesignSystemTest`
(`quranic arabic is given generous leading`).
