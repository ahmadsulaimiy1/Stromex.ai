# Chapter 17 — Accessibility

> An interface a blind reciter cannot use is not "less accessible". It is broken for him.

---

## 17.1 The Standing

Accessibility is not a checklist appended to a finished design. It is chapter 3 applied to a
person the designer did not imagine, and it carries the same weight as every other requirement
in this Bible. A screen that fails here does not ship, exactly as a screen that fails the design
review gate does not ship.

## 17.2 Screen Readers

- **Every** interactive element has a spoken description. No exceptions, and this is the one
  rule in the product with no permitted exception at all.
- Descriptions state the **action**, not the picture: "Start recording", not "red circle".
- The waveform is not a blank space. It announces position and duration: *"Waveform. 1:24.3 of
  6:10.0."*
- The level meter announces its value in decibels.
- The quality gauge announces its score **and its reason** — a number alone is not actionable.
- State is spoken as state: a muted layer announces "muted", not a colour.
- Live regions announce only what changes and matters: recording started, recording stopped,
  clipping detected, export finished. Not the timer — a timer announced every second is a
  screen reader rendered useless.

## 17.3 Focus Order

Follows the reading order of chapter 4.2's regions, top to bottom: status rail, canvas, layer
strip, context bar, transport dock. When a panel opens, focus moves into it; when it closes,
focus returns to the control that opened it.

The transport dock's order never changes, which matters more for a screen reader user than for
anyone else: it is the only part of the interface they can rely on by position.

## 17.4 Dynamic Type

- Every layout survives the system font scale at **200%** without truncation or overlap.
- A control label that cannot fit **wraps**. It is never ellipsised, because a truncated control
  name is a control the user cannot identify.
- Icons do not scale with text; **touch targets do**.
- Line heights are absolute, so vertical rhythm survives scaling.

## 17.5 Contrast

| Content | Floor |
|---|---|
| Body text | 4.5:1 |
| Large text, icons, meters, focus rings | 3:1 |
| Disabled text | 3:1 — SAUTIY holds disabled text to the non-text floor rather than exempting it |

Measured against the surface the content **actually sits on**, in both themes, for every role —
and asserted by `ContrastTest`, which fails the build below the floor. This is not reviewed by
eye at design time and hoped for at runtime.

**Opacity is not a colour.** Disabled states use `textDisabled`, not alpha on `textPrimary`, so
contrast stays predictable wherever the element lands.

## 17.6 Colour Independence

Every state carried by colour is also carried by something else:

| State | Colour | Also |
|---|---|---|
| Recording | ember | The control's shape changes disc → rounded square |
| Clipping | critical | The word "Clipped" in the status rail |
| Muted layer | dimmed | The word "Muted" |
| Applied preset | signal fill | The word "Applied" |
| Selected range | signal tint | Edge handles and a context bar that changed |
| Storage critical | caution | The number itself, in minutes |

## 17.7 Touch And Motor

- **48 dp minimum** for every interactive element, whatever the icon inside it.
- All tier-1 controls sit in the bottom 35% of the display (chapter 3.2.4).
- Every gesture has a non-gesture equivalent (chapter 6.3).
- No action requires a long press alone, a double tap alone, or two fingers alone.
- No time-limited interaction anywhere. Nothing must be done quickly.
- Panels are dismissed four ways, so no single motor capability is required to escape one.

## 17.8 Reduced Motion

When the system's reduce-motion preference is on, every transition drops to a cross-fade at
`INSTANT` (90 ms). The record control's breathing loop stops. Nothing else about the product
changes — no capability is withdrawn, because motion never carried a capability.

## 17.9 Right To Left

Full mirroring: layout, layer strip, context bar, panel, and the transport dock's ordering.

**The waveform's time direction stays left-to-right**, because time is not a language and a
mirrored timeline would put the future behind the playhead.

## 17.10 Hearing

The product is for making audio, so it cannot be made usable without hearing — but everything
*about* the audio is visible: level, clipping, noise floor, quality, loudness, duration, and the
waveform itself. A user with partial hearing can judge a recording's technical quality entirely
from the screen.

---

### Implementation

`ContrastTest` (build-failing), semantics in `app/.../ui/workspace/` and
`app/.../ui/components/`, `PerformanceBudget.MIN_TOUCH_TARGET_DP` applied through
`SautiySpace.minTouchTarget`, `strings.xml` (every content description, versioned with the
strings they describe).
