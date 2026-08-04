# Chapter 3 — Human Experience

> Never ask "what feature should I add?" Ask "what experience should the user have?"

---

## 3.1 The People

Five people. Every design decision is checked against all five; a change that helps one and
harms another is not shipped until it helps one and harms none.

### 3.1.1 The Reciter — Ustadh Bilal, 34

Records Qur'anic recitation nightly after ʿIshāʾ, in a quiet room, on a mid-range Android
phone with a lapel microphone. Records the same passage six or seven times and keeps the
best. Cannot tolerate a click, a room hum or a plosive. Needs to compare takes without
losing any of them. Arabic is his first reading language.

**What he needs:** takes that never overwrite, instant A/B comparison, honest noise
measurement, a trim that is sample-accurate, and Arabic that is set properly.
**What breaks him:** any workflow that requires naming a file before he can record.

### 3.1.2 The Lecturer — Dr Aisha, 47

Records a 90-minute lecture in a hall, from a bag, on battery. Presses record once and does
not look at the phone again. Discovers afterwards that the first eight minutes were quiet
and the last twenty had air-conditioning noise.

**What she needs:** capture that survives a 90-minute session, a screen-off recording that
does not die, level normalisation after the fact, noise reduction that does not sound
underwater, and an export she can email in under a minute.
**What breaks her:** a process kill at minute 84 that loses everything.

### 3.1.3 The Podcaster — Tunde, 29

Semi-professional. Knows what a limiter is. Wants −16 LUFS integrated for streaming, MP3 at
192 kbps, ID3 tags filled in. Will edit out three coughs and a doorbell.

**What he needs:** real loudness measurement to a published standard, a real compressor with
real ratio and knee, split/delete/merge on the waveform, and no surprise processing applied
without his consent.
**What breaks him:** a "magic enhance" button that he cannot inspect, defeat or measure.

### 3.1.4 The Journalist — Mariam, 26

Records interviews in the field, one-handed, often while walking, sometimes while holding a
notebook. Needs a marker dropped at the moment something important is said. Battery is
always at 14%.

**What she needs:** one-thumb operation, a marker control she can hit without looking, low
battery draw, and recording that starts before she has finished raising the phone.
**What breaks her:** anything that needs two hands, or a confirmation dialog.

### 3.1.5 The Beginner — Yusuf, 61

Recording his memoirs for his grandchildren. Has never used audio software. Opens the app,
sees a red circle, presses it, talks, presses it again. That is the entire product to him.

**What he needs:** the red circle, and for nothing else to be in the way.
**What breaks him:** a tutorial, a sign-up, a permission wall he does not understand, or a
screen with more than one obvious thing to do.

## 3.2 Experience Principles

### 3.2.1 Zero learning curve

A first-time user must begin recording **within three seconds of first launch**, with no
tutorial, no onboarding carousel, no account, and no exploration.

Consequences, all binding:
- The app opens directly into the workspace. There is no welcome screen.
- The record control is the largest, highest-contrast object on the display, positioned
  under the resting thumb.
- The microphone permission is requested **at the moment of the first record tap**, not on
  launch, with a one-line explanation in SAUTIY's own words before the system dialog.
- If permission is denied, recording is not simply blocked — the workspace explains what is
  unavailable and offers the single control that fixes it.

### 3.2.2 Cognitive load budget

Every state of the workspace is subject to a hard budget. The budget is stated per *cluster*
rather than as one screen-wide number, because the eye does not scan a screen — it scans
groups, and a group is what has a size limit.

| Measure | Ceiling |
|---|---|
| Controls in the **context bar** (the cluster that changes) | **6** |
| Controls in the **transport dock** | **exactly 5**, permanently, for the life of the product |
| Interactive elements in the **status rail** | **2** |
| Total interactive elements outside the canvas and layer strip | **13** |
| **Primary** actions per state | **1** |
| Decisions required before recording | **0** |
| Decisions required before export | **1** (the format) |
| Words in any control label | **3** |
| Nesting depth of any panel | **2** |

Six is the ceiling that matters. It is the point at which a changing cluster stops being
*seen* in one fixation and starts being *searched*. The transport dock is exempt from that
pressure precisely because it never changes: it is learned once and thereafter recognised by
position, not read.

### 3.2.3 Progressive disclosure — the three-tier rule

Every capability sits in exactly one tier, and the tier determines its distance from the user.

| Tier | Distance | Contents |
|---|---|---|
| **Tier 1 — Present** | Zero gestures. Always visible. | Record, play/pause, stop, timer, level, waveform, marker |
| **Tier 2 — One gesture** | One deliberate tap or drag | Trim, split, undo/redo, layers, presets, export, library |
| **Tier 3 — Two gestures** | Inside an opened panel | EQ bands, ratio/knee/attack/release, LUFS target, bit rate, sample rate, de-esser frequency |

**Binding limits:** nothing may be at tier 4. If a professional control cannot be reached in
two gestures, the panel containing it is badly organised. And nothing may be promoted to
tier 1 without something else being demoted, because tier 1 is capped at nine.

### 3.2.4 One-hand operation

SAUTIY is operated by a right or left thumb on a phone held in one hand, while standing.

The screen is divided into three reachability zones, measured from the bottom edge:

| Zone | Extent | Rule |
|---|---|---|
| **Natural** | bottom 0–35% | All tier-1 controls live here. The record control is centred in it. |
| **Stretch** | 35–65% | Contextual tools, layer strip. Reachable but not comfortable. |
| **Far** | top 65–100% | Status and information only. **No control that is required to complete a task may live here.** |

The Far zone may contain a control only if an equivalent control also exists in Natural or
Stretch. Closing a panel, for example, is available from the Far-zone close affordance *and*
from a downward drag anywhere on the panel *and* from the system back gesture.

### 3.2.5 Emotional design

The feeling SAUTIY produces, in order: **calm**, then **confidence**, then **satisfaction**.

- **Calm** comes from darkness, space, silence and stillness. The workspace does not move
  unless the user moved it or the audio moved it.
- **Confidence** comes from honesty. The meter is real. The dB number is real. The remaining
  storage is real, computed from the actual bitrate in use, and stated in minutes.
- **Satisfaction** comes from the waveform. Watching one's own voice draw itself is the
  single most rewarding moment in the product, and it is given the centre of the screen.

There is no celebration. Finishing a recording is not an achievement to be congratulated; it
is a normal thing a competent person did. SAUTIY says "Saved" and gets out of the way.

### 3.2.6 Error posture

An error is a state of the world, not a failure of the user.

Every error message has three parts, in this order:
1. **What is true.** "The microphone is in use by another app."
2. **What that means.** "Recording cannot start."
3. **What fixes it.** A single control: `Retry`, or `Open settings`, or `Use a different input`.

Errors never appear as modal dialogs unless the user is about to lose data. They appear in
the workspace, in place, where the affected thing is.

### 3.2.7 Interruption law

SAUTIY interrupts the user in exactly four situations, and no others:

1. Storage will run out within two minutes at the current bitrate.
2. The microphone was taken by another app or the audio route changed mid-recording.
3. A destructive action would discard audio that cannot be recovered from the trash.
4. An unrecovered recording from a previous crash exists, offered once on next launch.

No rating prompts. No feature tours. No tips. No newsletters. No badges.

### 3.2.8 Trust

- Recording is auto-saved from the **first sample**, before the user has named anything.
- The name is asked for **after** the recording exists, never before, and never blocks.
- Deletion goes to a trash that holds items for 30 days and states the date they will go.
- Processing is **non-destructive**: the original PCM is never modified in place; the
  effect chain is a recipe, and "revert to original" is always available.
- Nothing is uploaded. There is no network permission in the manifest for the core product.

## 3.3 Accessibility as Human Experience

Accessibility is specified in full in chapter 17. It is named here because it belongs to this
chapter: an interface that Ustadh Bilal cannot use when his sight fails is not "less
accessible", it is broken for him. The requirement is not a checklist item; it is the same
requirement as every other in this chapter, applied to a person the designer did not
imagine.

---

### Implementation

| Clause | Code |
|--------|------|
| 3.2.2 Cognitive load budget | `sautiy-core/.../workspace/WorkspaceLaw.kt`; asserted for **every reachable state** by `WorkspaceLawTest` |
| 3.2.3 Three-tier disclosure | `Tier` on every `WorkspaceAction`; depth asserted by test |
| 3.2.4 Reachability zones | `ReachZone` on every action; `WorkspaceLawTest` fails any required action in the Far zone |
| 3.2.6 Error posture | `SautiyError` — a sealed type that cannot be constructed without fact, consequence and remedy |
| 3.2.7 Interruption law | `Interruption` — a closed enum of exactly four permitted interruptions |
| 3.2.8 Trust | `RecordingSession` auto-commit; `Trash` 30-day retention; non-destructive `EffectChain` |
