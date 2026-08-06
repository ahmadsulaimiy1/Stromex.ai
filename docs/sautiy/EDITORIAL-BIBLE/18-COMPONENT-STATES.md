# Chapter 18 — Component States

> Every component has five states. Designing only the full one is how products come to feel
> unfinished at exactly the moments a user needs them most.

---

## 18.1 The Five

| State | Occurs when | Must do |
|---|---|---|
| **Empty** | There is nothing yet | Say what this is for, offer the one action, and not apologise |
| **Loading** | Something is genuinely being computed | Show the shell, fill it in progressively — never a spinner over a blank area |
| **Partial** | Some of it is ready | Show what is ready. Never withhold available content to preserve a tidy transition |
| **Error** | The world is in a state that prevents the task | Fact, consequence, remedy — in that order |
| **Success** | It worked | Say so once, briefly, and get out of the way |

## 18.2 Empty

An empty state is not an absence to be excused. It is the first thing a new user reads, and it
is the best chance the product has to explain itself in one line.

| Where | Title | Body |
|---|---|---|
| Workspace | "Ready" | "Press record to begin. Everything is saved from the first moment." |
| Library | "No recordings yet" | "Recordings appear here as soon as you make them." |
| Markers | "No markers" | "Drop a marker while recording to find a moment again later." |
| Transcript | "No transcript" | "Transcription runs on this device when a recording is finished. Nothing is uploaded." |
| Equaliser (preset shapes nothing) | "No equalisation" | "This preset shapes nothing. Choose another to see its bands." |

**Rules:** no illustration, no mascot, no "oops", no exclamation mark. The workspace's empty
state does **not** add a second record button — the real one is already under the thumb, and a
duplicate would create a choice where there was none.

## 18.3 Loading

SAUTIY shows a spinner in exactly **zero** places.

- A panel is interactive on its first frame; content that needs computing renders into a
  laid-out shell (chapter 4.4.1 clause 5).
- The waveform draws what has been built so far and extends as more arrives.
- Analysis fills its rows in as each measurement completes.
- Playback never has a loading state, because playback never waits (chapter 1.3.4).

The only determinate progress bar in the product is export, and it is driven by bytes actually
encoded — not by a timer, because a timer-driven bar is a lie with a smooth animation.

## 18.4 Error

Every error carries three parts, in this order, and the type that represents one cannot be
constructed without all three:

1. **What is true.** "The microphone is in use by another app."
2. **What that means.** "Recording cannot start."
3. **What fixes it.** One control: `Retry`.

Errors appear **in place**, next to the affected thing. A modal appears only when the user is
about to lose data, and in the whole product there is exactly one such case: storage exhausted
mid-recording.

Never: "Something went wrong." Never an error code alone. Never "Sorry". Never blame.

## 18.5 Success

- "Saved." Once. It fades after 2 seconds and takes no action from the user.
- Finishing a recording is **not** an achievement. It is a normal thing a competent person did.
  No confetti, no celebration, no rating prompt, no share nag (chapter 1.4 principle 4).
- The only success message with a control is export, which offers "Share" — because that is
  genuinely the likely next step, not because the moment needs decorating.

## 18.6 Degraded

Where a capability is genuinely unavailable on this device — no AAC encoder, no on-device
speech recogniser — SAUTIY does not show it disabled with an explanation. It **is not there**.

A control that cannot be pressed is still a control the eye must process, and an explanation of
why a feature is missing is a paragraph the user did not ask for. The panel simply offers what
works. Chapter 14's registry exists for exactly this reason.

## 18.7 Disabled

Reserved for the narrow case where a control is momentarily unavailable but will shortly not be
— export while a recording is in progress, for instance. Disabled uses `textDisabled`, a real
colour held to a 3:1 contrast floor, never alpha on the enabled colour.

---

### Implementation

`sautiy-core/.../workspace/SautiyError.kt` (fact/consequence/remedy enforced in `init`),
`app/.../ui/panels/PanelHost.kt` (`EmptyPanelState`),
`app/.../ui/workspace/SautiyWorkspace.kt` (`EmptyCanvas`),
`app/.../export/PlatformEncoders.kt` (conditional registration — the degraded state of 18.6).

**Verified by test:** an error with no fact cannot be constructed; an apologising error cannot
be constructed; modal presentation is reserved to the single data-loss case.
