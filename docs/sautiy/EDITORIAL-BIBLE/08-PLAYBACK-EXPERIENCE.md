# Chapter 8 — Playback Experience

> Listening outranks everything.

---

## 8.1 The Priority Rule

**Playback never waits for analysis.** Not for waveform generation, not for loudness
measurement, not for transcription, not for enhancement. Audio starts; the picture fills in
behind it.

This is structural, not a matter of care: the playback state carries no reference to any
analysis result, so there is nothing for it to wait on even by accident.

| Promise | Standard |
|---|---|
| Tap to audible | ≤ 100 ms |
| Output buffer | 40 ms — small enough to keep the budget, large enough to survive a scheduler hiccup |
| Loading screens | none |
| Spinners before audio | none |

## 8.2 Rendering, Not Decoding

Playback renders **windows of the timeline** rather than decoding a file.

Three things follow, and all three are the point:

1. Playback starts instantly on a two-hour project, because only the block about to be played
   is rendered.
2. An edit is audible the moment it is made — there is no intermediate rendered file to
   invalidate.
3. What the user hears and what they export come from the same renderer, so the two cannot
   diverge.

## 8.3 Scrubbing

Dragging the playhead plays short grains (60 ms) at the finger's position. Long enough to have
pitch, short enough to track the finger.

Scrubbing exists because an edit point is found by **ear**, not by eye. A waveform shows where
a sound is; only listening shows where a word ends.

## 8.4 Speed

Six named steps — 0.5×, 0.75×, 1×, 1.25×, 1.5×, 2× — rather than a free slider. A slider
invites fiddling and no listener wants 1.37×. **1× is always one tap away.**

Speed change is band-limited resampling at preview quality: this is audio being heard once, at
speed, and spending thirty-two filter taps per sample to improve something nobody is
auditioning would be a waste of battery.

## 8.5 Markers And The Back Control

"Back" goes to the start of the segment the playhead is in — the marker just passed.

But if the playhead is already **within two seconds** of that marker, back goes to the one
*before* it. Without that grace window, pressing back while paused just after a marker returns
to the same marker, leaves the playhead there, and every subsequent press returns it again:
the control locks and the user can never walk backwards through their own markers.

## 8.6 Loop And Compare

- **Loop** is set by dragging a range on the waveform. It wraps seamlessly and carries the
  overshoot, so a loop does not stutter at its seam.
- **Compare** switches instantly between the processed and unprocessed versions of the same
  moment. It is always available (chapter 10.6), because a user who cannot A/B an effect cannot
  judge it.

## 8.7 Beyond The App

- Playback appears on the lock screen and in the media notification with the recording's name
  and real position.
- Output uses the **media** stream, so it respects the volume the user set for listening and
  ducks correctly against other apps.
- Output is 32-bit float, so the last conversion from the working format happens in the
  platform rather than costing a quantisation of SAUTIY's own.
- Playing while recording is refused. Playing from a **paused** recording is allowed, and is
  what makes review-in-place work: pause the take, listen back, resume, without leaving the
  workspace.

## 8.8 Seeking

Seeking never stops the transport. A transport that stops on seek makes scrubbing through a
recording impossible.

---

### Implementation

| Clause | Code |
|--------|------|
| 8.1 Priority, 8.4 speed, 8.5 markers | `sautiy-core/.../play/PlaybackSession.kt` |
| 8.1 Latency budget | `PlaybackPolicy` — checked against the constitutional budget at class init |
| 8.2 Rendering | `sautiy-core/.../edit/TimelineRenderer.kt`, `app/.../play/AudioPlayer.kt` |
| 8.3 Scrubbing | `PlaybackPolicy.SCRUB_GRAIN_MS`, `WaveformCanvas` gestures |

**Verified by test:** playback can begin from a paused recording; playing while recording is
refused; seeking never stops the transport; a loop wraps and carries its overshoot; back walks
past a marker it is already sitting on; the output buffer alone cannot exceed the tap-to-audible
budget.
