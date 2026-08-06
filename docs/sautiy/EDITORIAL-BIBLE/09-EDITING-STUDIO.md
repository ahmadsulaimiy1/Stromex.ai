# Chapter 9 — Editing Studio

> Editing happens on the canvas, with the fingers, on the waveform. Never in a menu.

---

## 9.1 The First Law of Editing

**No edit ever modifies a sample of recorded audio.**

A SAUTIY edit is a change to a *description* of the recording, not to the recording. The
captured audio file is written once, during capture, and is thereafter read-only for the life
of the project. Everything the user does — trimming, splitting, cutting, gain, fades, layer
order, the entire studio chain of chapter 10 — is a small, cheap, serialisable structure
describing how those samples should be assembled and processed at playback and export time.

This is what makes chapter 1.3.5's promise ("nothing is ever lost") mechanically true rather
than aspirational. Undo is not a repair operation that tries to put samples back; it is a
step backwards through a list of descriptions. Nothing was ever taken away to be restored.

## 9.2 The Model

Four types, and no others:

| Type | Is | Holds |
|---|---|---|
| **Source** | A captured or imported audio file | Immutable samples on disk |
| **Clip** | A window onto a source, placed in time | Source id, offset into the source, length, position on the timeline, gain, fades |
| **Layer** | An ordered lane of clips | Clips, name, gain, mute, solo |
| **Timeline** | The project | Sample rate, layers |

A clip never contains audio. A layer never contains audio. Only a source contains audio, and
sources are never written twice.

**Invariants**, enforced at construction and asserted by tests:

1. Clips within a layer never overlap and are always sorted by position.
2. A clip's window always lies inside its source.
3. Fades never exceed the clip that carries them, and a fade-in plus a fade-out never exceed
   the clip's length.
4. Every clip has non-zero length. A zero-length clip is deleted, not kept.
5. The timeline's length is the end of its last clip. There is no separate duration field
   that could disagree with the content.

## 9.3 The Operations

Every operation is a **pure function** from `Timeline` to `Timeline`, carrying a
human-readable label for the history panel.

| Operation | Effect | Label shown |
|---|---|---|
| `Split` | One clip becomes two at the playhead, sample-accurate | "Split" |
| `Trim` | Move a clip's start or end without moving its audio | "Trim" |
| `DeleteRange` | Remove a time range, closing the gap (ripple) | "Cut" |
| `SilenceRange` | Remove a time range, leaving the gap | "Silence" |
| `GainRange` | Apply gain to the clips covering a range | "Gain" |
| `FadeClip` | Set a clip's fade-in and fade-out | "Fade" |
| `MoveClip` | Slide a clip along its layer | "Move" |
| `AddLayer` / `DeleteLayer` / `RenameLayer` | Layer lifecycle | as named |
| `SetLayerGain` / `MuteLayer` / `SoloLayer` | Layer mix | as named |
| `MergeLayers` | Flatten two layers into one | "Merge" |
| `AppendRecording` | Add newly captured audio at a position | "Record" |
| `RemoveSilence` | Delete detected silent regions in one step | "Remove silence" |

**Ripple law.** `DeleteRange` closes the gap; `SilenceRange` does not. These are different
user intentions and SAUTIY never guesses which one was meant — cutting a cough out of a
sentence and muting a passage are not the same edit, and a product that conflates them makes
one of them impossible.

## 9.4 Fades

Three shapes, because the right curve depends on what the fade is for:

| Shape | Curve | Use |
|---|---|---|
| `LINEAR` | `t` | Short fades used to kill a click at an edit point |
| `EQUAL_POWER` | `sin(πt/2)` | Crossfades and joins between takes — holds constant perceived loudness through the transition, which linear does not |
| `SMOOTH` | `t²(3−2t)` | Long musical fades in and out |

**Edit-point law:** every cut, split and join automatically carries a 5 ms linear fade at the
seam unless the user overrides it. A sample-accurate splice across a non-zero crossing is a
step discontinuity, and a step discontinuity is a click. The user should never have to know
that; they should simply never hear one.

## 9.5 History

The edit history is a list of timeline states, not a list of inverse operations.

Because a timeline is metadata — a few hundred bytes per clip — a state costs nothing next to
the audio it describes, and storing states instead of inverses gives three things an inverse
stack cannot:

1. **Undo and redo are exact**, with no possibility of an inverse being subtly wrong.
2. **Time travel**: the history panel lists every step and the user taps any one to jump
   straight there (chapter 4.4.2).
3. **A new edit after undoing** truncates the future cleanly, with no orphaned inverses.

History depth is capped at 200 steps; beyond that the oldest state is dropped, and the
history panel says so rather than silently forgetting.

## 9.6 Gestures

Editing is tactile (chapter 6). On the canvas:

| Gesture | Does |
|---|---|
| Drag on the waveform | Select a range |
| Drag a selection edge | Adjust the selection, with the waveform zooming under the finger |
| Pinch | Zoom, anchored between the fingers |
| Drag with two fingers | Pan without changing the selection |
| Tap | Move the playhead |
| Double tap | Select the clip under the finger |
| Long press on a clip | Pick it up to move it |
| Drag a clip edge | Trim |

No modal dialogs. No numeric entry required for any edit — though a numeric readout is always
visible, because chapter 1.4 principle 5 requires the interface to tell the truth about what
the fingers just did.

## 9.7 Silence Removal

Detection is honest and adjustable, never magic:

- **Threshold** in dBFS, defaulting to 12 dB above the measured noise floor of the recording
  rather than to a fixed constant — a lecture hall and a padded room do not share a threshold.
- **Minimum duration**: a gap shorter than 350 ms is not silence, it is speech rhythm, and
  removing it is what makes edited audio sound frantic.
- **Padding**: 80 ms of the original is kept at each end of every removed region, so words
  are not clipped at their onsets.
- The user always sees what *would* be removed, highlighted on the waveform, before it is.

---

### Implementation

| Clause | Code |
|--------|------|
| 9.2 Model + invariants | `sautiy-core/.../edit/Timeline.kt` — invariants enforced in `init`, so an illegal timeline cannot be constructed |
| 9.3 Operations | `sautiy-core/.../edit/EditOperation.kt` |
| 9.4 Fades | `FadeShape`, applied in `TimelineRenderer` |
| 9.4 Edit-point law | `EditOperation.SEAM_FADE_MS`, applied by `Split`, `DeleteRange` and `MergeLayers` |
| 9.5 History | `sautiy-core/.../edit/EditHistory.kt` |
| 9.7 Silence removal | `sautiy-core/.../analysis/SilenceDetector.kt` |
| Rendering | `sautiy-core/.../edit/TimelineRenderer.kt` |
