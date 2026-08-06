# Chapter 6 — Interaction Design

> Motion exists to explain. If an animation is not carrying information, it is costing time.

---

## 6.1 The Motion Tiers

Five durations. Nothing in SAUTIY animates outside them.

| Tier | ms | For |
|---|---|---|
| `INSTANT` | 90 | A change the user must not perceive as animation |
| `FAST` | 140 | Press feedback, toggles, context-bar cross-fade, meter settle |
| `STANDARD` | 220 | The default: reveals, list changes, panel open |
| `EMPHASISED` | 320 | A panel arriving with content that must be read |
| `LARGE` | 480 | Large surface transitions. **The ceiling.** |

**Easing:** standard `(0.20, 0, 0, 1)`, emphasised `(0.05, 0.70, 0.10, 1)`, exit `(0.30, 0, 1, 1)`.

**Overshoot is capped at 3%.** SAUTIY moves like a well-damped mechanism, not a bouncing toy.
No elastic easing, no rotation for effect, no confetti, no spring that visibly settles.

## 6.2 What Is Allowed To Move

| Moves | Why |
|---|---|
| The waveform | It is the audio |
| The level meter | It is the signal |
| The playhead | It is time |
| A panel arriving or leaving | It explains where the panel came from |
| The record control's breath | It signals capture from across a room |
| A press | 6% scale-down: confirms the touch landed |

Everything else is still. A workspace that drifts, pulses or shimmers while the user is
listening is competing with the thing they came to do.

## 6.3 Gestures

| Gesture | On the canvas | Elsewhere |
|---|---|---|
| Tap | Move the playhead | Activate |
| Double tap | Select the clip under the finger | — |
| Drag | Select a range | Scroll |
| Drag an edge | Adjust the selection | — |
| Pinch | Zoom, anchored between the fingers | — |
| Two-finger drag | Pan without changing the selection | — |
| Long press | Pick up a clip | Reveal the history panel (from undo) |
| Drag down on a panel | Dismiss | — |

**Gesture law:** every gesture has a non-gesture equivalent. A user who cannot perform a
two-finger drag can still pan, and a user who cannot pinch can still zoom. A capability
reachable only by gesture is a capability some people do not have.

## 6.4 Haptics

Haptics are used **six times** in the entire product, and nowhere else:

1. Recording starts — a single firm tick, so the user knows without looking.
2. Recording stops — the same tick.
3. A marker is dropped — a light tick, confirming a control pressed without looking.
4. A selection edge snaps to a zero crossing or a marker — a light tick.
5. A destructive action completes — a double tick.
6. The input clips — a light tick, once, not repeatedly.

Haptics respect the system setting absolutely. A phone in a mosque or a lecture hall must be
silent and still, so all six are suppressed while a recording is in progress **except** the
clip warning, which is the one the user needs and cannot otherwise perceive.

## 6.5 Sound Feedback

**There is none.** SAUTIY never makes a sound. It is a recording application; a UI chime is a
chime in somebody's recording. The notification channel is created silent for the same reason.

## 6.6 Micro-interactions

| Moment | Behaviour |
|---|---|
| Record pressed | Control morphs disc → rounded square over `STANDARD`; waveform colour becomes ember |
| Clipping | The meter's peak line turns `critical` and holds; the status rail adds the word "Clipped" |
| Selection made | Context bar cross-fades to the editing tools over `FAST`, with no height change |
| Edit applied | The affected waveform region flashes `signal` at 30% for `FAST` — the only flash in the product, and it exists because an undo the user cannot see is an undo they do not trust |
| Panel opened | Slides from the bottom over `EMPHASISED`, interactive on the first frame |
| Storage critical | The remaining-time figure changes to `caution`. Nothing moves. |

## 6.7 Undo And Redo

- **Every action is undoable.** There are no exceptions and no confirmation dialogs standing in
  for undo. A dialog asks the user to predict the future; undo lets them look at it.
- Undo is a **tier-1 control** whenever audio exists.
- A **long press on undo** opens the history panel, where any step can be travelled to directly.
- An action that changes nothing does not become a history step, because an undo that appears
  to do nothing reads as a broken undo.
- History survives panel opens, closes and configuration changes for the life of the session.

## 6.8 Interruption And Focus

- Losing the microphone pauses; it never stops.
- An incoming call pauses recording and resumes it on the user's next tap, never automatically —
  resuming into a call would record the call.
- Rotation, split screen and font-scale changes never interrupt capture and never lose selection,
  zoom or playhead.

---

### Implementation

`sautiy-core/.../design/SautiyMetrics.kt` (`Motion`), `app/.../ui/theme/Theme.kt`
(`SautiyMotion`), gesture handling in `app/.../ui/workspace/WaveformCanvas.kt`, press feedback
in `app/.../ui/workspace/TransportDock.kt`. The duration ceiling, the tier ordering and the
no-overshoot rule are asserted by `DesignSystemTest`.
