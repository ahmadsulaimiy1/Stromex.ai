# Chapter 5 — User Interface Design System

> A component is not a drawing. It is a decision, made once, that nobody has to make again.

---

## 5.1 The Grid

Everything is a multiple of **4 dp**. There are no exceptions and no "just this once" values.

| Token | dp | Use |
|---|---|---|
| `XXS` | 2 | Hairline separation only |
| `XS` | 4 | Icon-to-label |
| `S` | 8 | Inside a chip |
| `M` | 12 | Between related controls |
| `L` | 16 | Inside a card |
| `XL` | 20 | The page inset — every screen shares it, so edges align across the product |
| `XXL` | 24 | Between control groups |
| `H3`–`H6` | 32, 40, 48, 64 | Structural gaps |
| `SECTION_GAP` | 28 | Between unrelated sections |

A value off the grid is a defect, caught by `DesignSystemTest`.

## 5.2 Radii

| Token | dp | Applied to |
|---|---|---|
| `XS` | 4 | Meter fills, waveform selection edges |
| `S` | 8 | List rows, layer strip rows |
| `M` | 12 | Cards, preset cards |
| `L` | 16 | Large cards |
| `XL` | 24 | Prominent surfaces |
| `SHEET` | 28 | Panel top corners |
| `PILL` | full | Transport controls, chips, primary buttons |

## 5.3 Elevation

SAUTIY has **four planes** and no shadows on a dark surface — a shadow under a card on a near-black
canvas is a smudge, not a depth cue. Depth is carried by surface value.

| Plane | Dark | Light |
|---|---|---|
| Canvas | `ink900` | `paper050` |
| Surface | `ink850` | `paper000` |
| Raised | `ink800` | `paper100` |
| Overlay (panels) | `ink750` | `paper000` + border |

## 5.4 The Components

Each exists once, in `app/.../ui/`, and is used everywhere. A one-off variant is a bug.

| Component | Rules |
|---|---|
| **Transport control** | 52 dp secondary, 76 dp record. Never labelled — the five are universally understood (chapter 2.5 icon law 2). |
| **Context tool** | Icon over an 11 sp label, always. 48 dp minimum target. |
| **Preset card** | Name, one-sentence summary, and — only when applied — the real parameters. |
| **Panel** | One scaffold for all twelve: drag handle, title, close, insets. Content never draws chrome. |
| **List row** | 48 dp minimum, leading icon, title, secondary line, optional trailing state word. |
| **Primary action** | Pill, 52 dp tall, `commit` fill. **One per screen state** (chapter 3.2.2). |
| **Level meter** | Broadcast ballistics. Never a plain bar. |
| **Quality gauge** | Ring plus number plus a sentence. A score with no explanation is ignored. |
| **Empty state** | Title, one line of body, and no apology. |
| **Error in place** | Fact, consequence, one remedy. Never a modal unless data is at risk. |

## 5.5 What SAUTIY Does Not Have

Recorded so that future work does not add them by reflex:

- **No bottom navigation bar, drawer or tab bar.** Chapter 4.1.1.
- **No floating action button.** The record control is not floating; it is anchored, and a
  second floating primary would break the one-primary-action rule.
- **No snackbars.** A message that disappears while being read is not communication. State
  changes are shown where the thing changed.
- **No ripples.** A ripple spreading across a dark studio surface explains nothing. Press
  feedback is a 6% scale-down over 140 ms.
- **No dividers between list rows.** Space separates. A line is only used where two regions
  genuinely abut.
- **No badges, no dots, no counts.** Chapter 1.4 principle 4.

## 5.6 Density and Text Scaling

Every layout survives the user's font-size preference at **200%** without truncation or
overlap. Where a label cannot fit, the label wraps — it is never ellipsised, because a
truncated control name is a control the user cannot identify. Icons do not scale with text;
touch targets do.

---

### Implementation

`sautiy-core/.../design/SautiyMetrics.kt` (`Space`, `Radius`), `app/.../ui/theme/Theme.kt`
(`SautiyShapes`, `SautiySpace`), `app/.../ui/components/`, `app/.../ui/workspace/`.
Grid conformance is asserted by `DesignSystemTest`.
