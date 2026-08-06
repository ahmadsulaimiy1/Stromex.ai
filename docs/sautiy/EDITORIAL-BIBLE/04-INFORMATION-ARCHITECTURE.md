# Chapter 4 — Information Architecture

> **SAUTIY is not an application with screens. It is one intelligent studio.**
>
> This chapter is the strictest in the Bible. It is enforced by a test that fails the build.

---

## 4.1 The One-Canvas Law

**SAUTIY has exactly one navigation destination: the Workspace.**

There is no Record screen, no Enhance screen, no Master screen, no Effects screen, no
Waveform screen, no Projects screen, no Library screen, no Mixer screen, no Assistant
screen. Those are not pages. They are **panels** that arrive over the workspace, and the
workspace never goes away underneath them.

The user must never feel they have moved between applications. They are in a studio; things
are brought to them.

### 4.1.1 What this forbids

| Forbidden | Because |
|---|---|
| A bottom navigation bar | It advertises that the product is fragmented |
| A navigation drawer | It hides the product behind a hamburger |
| A tab bar of workflows | Record/Edit/Export are phases of one task, not places |
| Any full-screen destination that replaces the canvas | Context loss |
| A back stack more than one panel deep | Chapter 3.2.3 caps nesting at two, and panels do not stack |

### 4.1.2 The one legitimate exception

**Settings** and **About** are full destinations, because they are genuinely outside the
work: the user is not making audio while reading a licence. They are reached from the status
rail, they cover the canvas completely, and returning from them restores the workspace
exactly as it was — same selection, same zoom, same playhead, same open panel.

Everything else — the library included — is a panel.

## 4.2 The Anatomy of the Canvas

Four fixed regions. Their positions never change, so the user's hands learn them once.

```
┌───────────────────────────────────────────────────┐
│  STATUS RAIL            (Far zone — no controls)  │  ← project · time · input · battery · storage
├───────────────────────────────────────────────────┤
│                                                   │
│                                                   │
│                  C A N V A S                      │  ← waveform / timeline / meters / spectrogram
│              (the application itself)             │
│                                                   │
│                                                   │
├───────────────────────────────────────────────────┤
│  LAYER STRIP           (Stretch zone)             │  ← layers, add layer, playhead ruler
├───────────────────────────────────────────────────┤
│  CONTEXT BAR           (Stretch/Natural)          │  ← changes with what is selected
├───────────────────────────────────────────────────┤
│  TRANSPORT DOCK        (Natural zone)             │  ← monitor · back · RECORD · play · commit
└───────────────────────────────────────────────────┘
```

| Region | Job | Contents change? |
|---|---|---|
| **Status rail** | Tell the truth about the session | Values change; controls never appear |
| **Canvas** | The audio itself | Representation changes (waveform / spectrogram / meters) |
| **Layer strip** | Which material exists | Grows with layers |
| **Context bar** | The tools for what is selected **right now** | **Yes — this is the adaptive element** |
| **Transport dock** | Move through time and capture | **Never.** Anchored. Always the same five positions. |

**The Transport Dock is immovable.** Its five slots hold the same functions for the life of
the product. A user who has learned that the red circle is under their thumb is never made
wrong.

## 4.3 The Adaptive Context Bar

The context bar is the entire navigation model of SAUTIY. It answers "what can I do with
this?" without the user asking.

| Workspace context | Context bar shows |
|---|---|
| **Idle**, nothing recorded | Input source · Quality · Library · Projects |
| **Armed / Recording** | Marker · Layer · Monitor level · Noise readout — *and nothing that could destroy the take* |
| **Recording paused** | Marker · Resume hint · Discard take |
| **Recorded, nothing selected** | Undo · Redo · Enhance · Trim · Export |
| **Range selected on the waveform** | Cut · Split · Fade · Silence · Gain · Deselect |
| **Layer selected** | Rename · Mute · Solo · Gain · Duplicate · Delete layer |
| **Marker selected** | Rename · Jump · Delete marker |
| **Playing** | Speed · Loop · Marker · A/B compare |

**Transition law:** the bar cross-fades over `Motion.FAST_MS` (140 ms) with no layout jump —
tools that persist between two contexts keep their exact position, so the eye tracks them.
The bar never changes height.

**Safety law:** while `RECORDING`, no destructive action may appear anywhere in the
workspace. Not greyed out — *absent*. A cut control that cannot be pressed is still a control
the eye must process.

## 4.4 Panels

A panel is a surface that arrives over the canvas without removing it.

### 4.4.1 Panel law

1. **At most one panel is open at a time.** Opening a second closes the first. There is no
   stacking, so there is no "where am I".
2. **A panel never covers the transport dock.** Recording and playback remain reachable with
   any panel open. This is what makes them panels and not pages.
3. **A panel never covers more than 62% of the canvas height.** The waveform stays visible,
   because the waveform is the context.
4. **Every panel is dismissed four ways:** the close affordance, a downward drag, a tap on
   the canvas above it, and the system back gesture. All four do the same thing.
5. **A panel opens in ≤ 220 ms and is interactive on its first frame.** No spinner. Content
   that needs computing renders progressively into a laid-out shell.
6. **Panel state survives.** Reopening a panel restores its scroll position and its
   sub-selection for the life of the session.
7. **A panel may not open another panel.** Chapter 3.2.3, tier 3, is the floor.

### 4.4.2 The panel set

| Panel | Opened from | Contains |
|---|---|---|
| `STUDIO` | Enhance | The preset cards — Studio, Broadcast, Podcast, Lecture, Recitation, Natural, Warm, Deep, Bright |
| `EQUALISER` | Studio panel → a preset's Adjust | Parametric bands, curve, spectrum behind it |
| `DYNAMICS` | Studio panel → Adjust | Compressor, limiter, de-esser, gate |
| `SPACE` | Studio panel → Adjust | Echo and reverb, with a decay graph |
| `ANALYSIS` | Canvas tap on the quality gauge | Loudness, noise floor, clipping, spectrum, quality score |
| `LAYERS` | Layer strip | Layer list, gain, mute, solo, order |
| `MARKERS` | Marker count in status rail | Marker list with times and labels |
| `HISTORY` | Long-press undo | The full edit stack, tap any point to travel |
| `TRANSCRIPT` | Analysis panel | On-device transcript, tap a word to seek |
| `LIBRARY` | Status rail project name | Recordings, search, favourites, collections, trash |
| `PROJECT` | Status rail project name → long-press | Project metadata, takes, Qur'an tracking |
| `EXPORT` | Commit control | Format, quality, destination, metadata |

Twelve panels, one canvas, zero pages.

## 4.5 The Journey

The user is never routed. The workspace simply becomes what the moment needs.

```
        ┌──────────────────────────────────────────────────┐
        │                   WORKSPACE                      │
        │                                                  │
   →    │  RECORD  ──→  REVIEW  ──→  EDIT  ──→  ENHANCE    │
        │     ▲            │           │          │        │
        │     └────────────┴───────────┴──────────┘        │
        │              (all reversible, in place)          │
        │                        │                         │
        │                        ▼                         │
        │                     EXPORT ──→ ARCHIVE           │
        └──────────────────────────────────────────────────┘
```

Not a route. A **state**. The user moves through the chain without a single navigation
event, and can move backwards through it at any point without losing anything.

**The three-tap export guarantee (chapter 1.6):**
`Commit` → choose format → `Export`. Three taps from a finished recording to a file, with
the last-used format pre-selected so the common case is two.

## 4.6 Search

One search field, in the Library panel. It searches, in this priority order:

1. Recording title
2. Tags and collection names
3. Marker labels
4. Transcript content (when a transcript exists)
5. Spoken-date phrases — "last Tuesday", "Ramadan", "this morning"

Results are grouped by source with the matched text shown in context. Search is incremental,
runs off the main thread, and never blocks typing. There is no search screen; there is a
search field in a panel.

## 4.7 What the User Is Told, Always

The status rail answers chapter 1.9's three questions permanently, so no screen has to:

| Question | Answered by |
|---|---|
| What am I looking at? | Project name and take, left of the rail |
| What is the primary action? | The largest object in the Natural zone — record, or the pulsing stop while recording |
| What happens next? | The commit control, right of the transport dock, whose label states the next step: `Export` |

---

### Implementation

| Clause | Code |
|--------|------|
| 4.1 One-canvas law | `sautiy-core/.../workspace/WorkspaceArchitecture.kt` — `destinations` is a closed set; `WorkspaceLawTest` fails if it grows |
| 4.2 Regions | `Region` enum; every action declares its region and inherits that region's `ReachZone` |
| 4.3 Context bar | `WorkspaceContext.contextActions()` — a pure function from state to tools, exhaustively tested |
| 4.3 Safety law | `WorkspaceLawTest` asserts no `destructive` action is reachable while recording |
| 4.4 Panel law | `Panel` enum + `PanelLaw`; single-open, coverage ceiling and dismissal count asserted |
| 4.5 Journey | `WorkspacePhase` derived from state, never navigated to |
| 4.6 Search | `LibraryQuery` with the five ranked matchers |
