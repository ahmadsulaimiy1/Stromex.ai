# THE SPACETALK VISUAL DESIGN SYSTEM

### Part 2 — Colour, Type, Space, Surface

*Governed by `00-EDITORIAL-BIBLE.md` and `01-BRAND-BIBLE.md`. Every colour below states its HEX value, its job, and why it exists. Every contrast ratio quoted was computed against the WCAG 2.x relative-luminance formula and is accurate to two decimal places.*

**Naming.** Palette families are named for what they do, not for what they look like: **Orbit** (the brand action colour), **Aurora** (the intelligence colour), **Void** (the neutral scale). These names are internal tokens only — see `01-BRAND-BIBLE.md` §1.1 for the ban on cosmic *imagery*; a token name is not imagery.

---

## 2.1 — Colour Doctrine

Four rules that determine every colour decision:

1. **Colour encodes meaning, never mood.** If a colour is not communicating identity, state, or hierarchy, it should be a neutral.
2. **The interface is 90 % neutral.** Brand colour appears on roughly one element per screen. A screen with three coloured things has one too many.
3. **Human content and machine content never wear the same colour.** Orbit is the user's colour. Aurora belongs exclusively to the assistant. A user must be able to tell, at a glance and without reading, whether a person or a model produced something. This is a trust mechanism, not a decoration scheme.
4. **Contrast is verified, not eyeballed.** Every token pair used for text ships with a measured ratio. Anything below 4.5:1 is barred from body text, no exceptions for "it looks fine."

---

## 2.2 — Primary Palette: Orbit

A blue with a slight violet cast (hue ≈ 231°). Pure blue at this saturation reads corporate and is the single most-used hue in software; the violet lean keeps it distinct from iOS system blue (`#007AFF`), Telegram (`#2AABEE`), and Meta blue (`#0866FF`) at a glance, without drifting into the purple that AI products have colonised.

| Token | HEX | Why it exists |
|---|---|---|
| `orbit-50` | `#EEF2FF` | Tint background for selected rows and information banners in light mode. |
| `orbit-100` | `#DDE4FF` | **Outgoing message bubble, light mode.** Light enough to carry `void-900` text at **14.33:1** — the highest-traffic surface in the product had to be the most readable. |
| `orbit-200` | `#BCC9FF` | Hover/pressed state of `orbit-100`; disabled primary button fill. |
| `orbit-300` | `#92A7FF` | **Primary action text and icons in dark mode** — **7.93:1** on `void-900`. |
| `orbit-400` | `#6681FB` | Secondary emphasis in dark mode; **5.26:1** on `void-900`. Links inside dark bubbles. |
| `orbit-500` | `#3F5EF0` | **The brand colour.** Primary button fill and focus ring in light mode. White text on it: **5.16:1**. |
| `orbit-600` | `#2E48D8` | Pressed state of `orbit-500`; primary *text* colour on white where 5.16 is too tight (**6.92:1**). |
| `orbit-700` | `#2438AE` | Link text on light tinted surfaces — **8.34:1** on `orbit-50`. |
| `orbit-800` | `#1E2F8A` | **Outgoing message bubble, dark mode.** `void-50` text on it: **10.61:1**. |
| `orbit-900` | `#1A2769` | Deep accent for pressed dark-mode bubbles and large brand fields. |
| `orbit-950` | `#10173F` | Rare — the darkest brand field, used behind full-bleed onboarding art only. |

**Why one accent and not two.** Every additional brand hue doubles the number of decisions a designer makes per screen and halves the meaning each hue carries. One action colour makes "what is the primary action here?" answerable without thought.

---

## 2.3 — Secondary Palette: Aurora (the intelligence colour)

A green-cyan (hue ≈ 170°). Deliberately far from Orbit on the wheel so the two never read as variants of each other, and deliberately *not* the purple/magenta that the industry has made synonymous with generative AI — we are signalling *useful and calm*, not *magical*.

Aurora may only be used on assistant output, assistant affordances, and translation/transcription indicators. Using Aurora anywhere else is a design defect.

| Token | HEX | Why it exists |
|---|---|---|
| `aurora-300` | `#5FE3CE` | Assistant text/icons in dark mode — **11.53:1** on `void-900`. |
| `aurora-400` | `#2ACFB6` | Assistant icon fills, dark mode (**9.23:1**). |
| `aurora-500` | `#12B39B` | **Fill only** — assistant avatar, indicator dots. **2.64:1** on white, so it is barred from text and from any icon that carries meaning alone. |
| `aurora-700` | `#0A7466` | **Assistant text and icons in light mode** — **5.67:1** on white, **5.24:1** on `void-50`. |
| `aurora-800` | `#08594E` | Assistant text on tinted light surfaces (**8.24:1** on white). |
| `aurora-050` | `#E6FAF6` | Assistant response background in light mode; keeps AI content visually separable without a border. |
| `aurora-950` | `#062F2A` | Assistant response background in dark mode. |

---

## 2.4 — Semantic Colours

Each has a light-mode value (on white) and a dark-mode value (on `void-900`). Every value listed for text meets 4.5:1 minimum; fill-only values are labelled.

### Success

| Token | HEX | Ratio | Use |
|---|---|---|---|
| `success-fill` | `#12A150` | 3.37:1 on white — **non-text only** | Delivered/read ticks, connection-restored dot, toggle-on fill. |
| `success-text` | `#08602F` | **7.71:1** on white | "Sent," "Verified," success banner text. White on it: **7.71:1**; on `void-50`: **7.12:1**. |
| `success-dark` | `#35D07F` | **9.04:1** on `void-900` | Both text and fill in dark mode. |
| `success-surface` | `#E8F7EE` / `#0B2C1B` | — | Banner backgrounds, light / dark. |

*Why a separate fill and text value:* the green that reads correctly as a status dot is too light to read as text. Rather than compromise both, we specify both.

### Warning

| Token | HEX | Ratio | Use |
|---|---|---|---|
| `warning-text` | `#B45309` | **5.02:1** on white; white on it **5.02:1** | "Message not delivered," storage nearly full, unverified device. |
| `warning-dark` | `#FFC46B` | **11.53:1** on `void-900` | Dark-mode equivalent. `void-950` on it: **12.37:1**; on `void-850`: **10.50:1**. |
| `warning-surface` | `#FEF4E6` / `#301F05` | — | Banner backgrounds. |

*Amber rather than yellow:* true yellow cannot reach 4.5:1 on white at any saturation worth having, and warning states must be readable, not merely visible.

### Danger

| Token | HEX | Ratio | Use |
|---|---|---|---|
| `danger` | `#D92D20` | **4.83:1** on white; white on it **4.83:1** | Destructive buttons, failed-send state, block/report. |
| `danger-text` | `#C0271B` | **5.92:1** on white | Danger text at small sizes, where 4.83 is uncomfortably tight. |
| `danger-dark` | `#FF6B60` | **6.49:1** on `void-900` | Dark-mode equivalent. |
| `danger-surface` | `#FDECEA` / `#38120F` | — | Banner backgrounds. |

Danger is the *only* colour permitted on a destructive confirmation. It never appears as decoration, and never as an unread badge.

### Information

Information reuses **Orbit** rather than introducing a fifth hue. Informational banners use `orbit-50` / `orbit-950` surfaces with `orbit-700` / `orbit-300` text. A dedicated "info blue" would be a colour whose only job is to be a slightly different blue — Part 0.9 rule 1 deletes it.

### Security states (a semantic family, not decoration)

| State | Light | Dark | Meaning |
|---|---|---|---|
| Encrypted (normal) | `void-500` `#676F80` | `void-400` `#8B94A6` | Baseline. Shown once at conversation start, never as a persistent badge — E2EE is the default, and defaults are not announced repeatedly. |
| Verified contact | `success-text` | `success-dark` | Safety number confirmed by both parties. |
| Safety number changed | `warning-text` | `warning-dark` | The contact's keys changed. Requires user acknowledgement. |
| Unverified linked device | `warning-text` | `warning-dark` | A new device joined the account. |
| Suspected fraud | `danger` | `danger-dark` | Anti-scam signal fired (`04-AI-PHILOSOPHY.md` §4.7). |

---

## 2.5 — Neutrals: Void

Cool-tinted greys (a slight blue cast, hue ≈ 220°) so neutrals sit harmoniously with Orbit rather than fighting it. Warm greys against a violet-blue accent produce a muddy interference that is very hard to unsee once noticed.

| Token | HEX | Light-mode job | Dark-mode job |
|---|---|---|---|
| `void-0` | `#FFFFFF` | Primary surface (cards, sheets, bubbles) | Primary text on dark (`18.12:1` inverse) |
| `void-25` | `#FAFBFD` | App background beneath cards | — |
| `void-50` | `#F4F6FA` | Conversation list background; incoming bubble alt | Primary text on dark — **17.97:1** on `void-950` |
| `void-100` | `#E9EDF4` | **Incoming message bubble, light mode** — `void-900` text at **15.43:1** | Secondary text on dark — **15.43:1** on `void-900` |
| `void-200` | `#D7DDE8` | Dividers, input borders, skeleton base | — |
| `void-300` | `#B4BCCB` | Disabled text/icon (light); placeholder | Body text on dark — **9.49:1** on `void-900` |
| `void-400` | `#8B94A6` | **Non-text only** on white (3.05:1) — decorative icons, inactive tab glyphs paired with a label | Secondary text on dark — **5.94:1** on `void-900` |
| `void-500` | `#676F80` | Secondary text — **5.05:1** on white, **4.66:1** on `void-50` | Tertiary/disabled text on dark |
| `void-600` | `#4C5464` | Body text where full black is too heavy — **7.61:1** | — |
| `void-700` | `#363D4B` | Strong body text — **10.90:1** | Dark-mode divider / border |
| `void-800` | `#232935` | Headings on light | **Incoming bubble, dark mode** — `void-50` at **13.48:1** |
| `void-850` | `#1A1F29` | — | Elevated surface (sheets, cards, composer) |
| `void-900` | `#12161E` | Primary text — **18.12:1** on white | **Primary dark surface** |
| `void-950` | `#0A0D13` | — | App background beneath dark cards; OLED-friendly |

**Why `void-900` and not `#000000` for text**, and not for the dark background either: pure black on pure white is a contrast overshoot that causes halation for many readers, and pure-black OLED backgrounds produce visible smearing during scroll on most panels. `#12161E` costs almost nothing in measured contrast (18.12:1 vs 21:1) and reads materially calmer.

---

## 2.6 — Light Mode and Dark Mode

Both modes are designed independently against the same tokens. Dark mode is not a computed inversion.

| Role | Light | Dark |
|---|---|---|
| App background | `void-25` `#FAFBFD` | `void-950` `#0A0D13` |
| Primary surface | `void-0` `#FFFFFF` | `void-900` `#12161E` |
| Elevated surface (sheet, menu, dialog) | `void-0` + shadow | `void-850` `#1A1F29` + shadow |
| Primary text | `void-900` | `void-50` |
| Secondary text | `void-500` | `void-400` |
| Tertiary / timestamp | `void-400` (with ≥16 px or paired label) | `void-500` |
| Divider | `void-200` | `void-700` |
| Incoming bubble | `void-100` | `void-800` |
| Outgoing bubble | `orbit-100` | `orbit-800` |
| Assistant surface | `aurora-050` | `aurora-950` |
| Primary action | `orbit-500` fill, white label | `orbit-300` label on transparent, or `orbit-500` fill |

**Elevation in dark mode is expressed by lightness, not shadow.** Shadows are nearly invisible on dark surfaces; each elevation step raises the surface lightness instead (`void-950` → `void-900` → `void-850`). Shadows still ship in dark mode but only as a subtle ambient occlusion to separate overlapping surfaces.

**Mode switching is instant and stateless.** No cross-fade, no reload, no flash of the wrong theme at cold start (theme is read synchronously before the first frame — see `08-PERFORMANCE-STANDARDS.md` §8.2).

---

## 2.7 — Gradients

Gradients are permitted in exactly three places. Everywhere else they are banned, because a gradient is a decorative element pretending to be a functional one.

1. **The assistant's activity indicator** — `aurora-500` → `aurora-300`, animated at ≤0.5 Hz, only while the assistant is actively working. It is the one place in the product where "something is thinking" needs a non-textual signal.
2. **Media scrims** — a black gradient from `rgba(10,13,19,0.72)` to `transparent` over photos and video, so white controls remain legible over unknown content. Functional, not decorative.
3. **Onboarding and marketing full-bleed fields** — `orbit-950` → `orbit-800`, linear, ≤35° from vertical. Never behind interface controls.

Banned: multi-stop rainbow gradients, gradient text, gradient borders, gradients on buttons, "AI shimmer" on anything that is not the assistant indicator.

---

## 2.8 — Shadows and Elevation

Six levels. Shadows use a cool tint (`rgba(18, 22, 30, α)`) rather than neutral black, so they sit correctly on the Void scale.

| Level | Use | Light mode | Dark mode |
|---|---|---|---|
| `e0` | Flat content, message bubbles | none | none |
| `e1` | Cards, list rows on tinted backgrounds | `0 1px 2px rgba(18,22,30,0.06)` | surface `void-900` |
| `e2` | Composer bar, sticky headers | `0 2px 8px rgba(18,22,30,0.08)` | surface `void-850`, `0 2px 8px rgba(0,0,0,0.40)` |
| `e3` | Bottom sheets, popover menus | `0 8px 24px rgba(18,22,30,0.12)` | surface `void-850`, `0 8px 24px rgba(0,0,0,0.48)` |
| `e4` | Dialogs, floating action controls | `0 16px 40px rgba(18,22,30,0.16)` | surface `void-850`, `0 16px 40px rgba(0,0,0,0.56)` |
| `e5` | Incoming-call full-screen overlay | `0 24px 64px rgba(18,22,30,0.24)` | as `e4` + scrim |

**Message bubbles cast no shadow.** They are content, not objects. A chat transcript with 200 shadowed bubbles is 200 unnecessary composited layers and a visibly noisier screen.

---

## 2.9 — Glass (translucency)

Translucent blur is expensive on the GPU and unreadable over arbitrary content. It is permitted in exactly two places, both of which sit over scrolling content the user needs to keep tracking:

1. **The conversation header** while a transcript scrolls beneath it.
2. **The composer bar** while a transcript scrolls beneath it.

Specification: 24 px backdrop blur, 180 % saturation, over `rgba(255,255,255,0.72)` (light) / `rgba(18,22,30,0.72)` (dark). A 1 px `void-200` / `void-700` hairline is drawn on the content-facing edge so the boundary is unambiguous.

**Mandatory fallbacks.** Blur is disabled and replaced with the opaque surface colour when: the device is in a low-power state, the app has dropped below the frame-rate floor in the last 5 seconds, the platform reports reduced-transparency accessibility settings, or the device is below the Tier-B hardware baseline (`08-PERFORMANCE-STANDARDS.md` §8.7). Blur is a garnish; it is never load-bearing for legibility.

Banned everywhere else: glass cards, glass sheets, glass tab bars over static backgrounds, frosted modals.

---

## 2.10 — Corner Radius

A single geometric family, so the whole product feels cut from one material. Radii use *continuous* (squircle) curvature where the platform supports it, matching the logo construction.

| Token | Value | Applied to |
|---|---|---|
| `radius-xs` | 4 px | Tags, inline code, small checkboxes |
| `radius-sm` | 8 px | Input fields, small buttons, menu items |
| `radius-md` | 12 px | Cards, media thumbnails, attachment tiles |
| `radius-lg` | 18 px | **Message bubbles** |
| `radius-xl` | 24 px | Bottom sheets, dialogs (top corners) |
| `radius-full` | 999 px | Avatars, pills, FAB, primary CTA in onboarding |

**The bubble rule.** Bubbles are `radius-lg` on three corners and `radius-xs` on the corner nearest the sender's edge — but *only on the last message in a run*. Consecutive messages from the same sender within 60 seconds keep all four large corners and tighten to 2 px vertical spacing, so a burst of messages reads as one utterance. This is the single most important detail in the transcript's visual rhythm.

**Nesting rule.** An inner radius equals the outer radius minus the padding between them, never the same value. A 12 px card with 8 px padding contains 4 px children.

---

## 2.11 — Spacing

A 4 px base unit. All spacing is a token; arbitrary values are a lint failure.

| Token | Value | Typical use |
|---|---|---|
| `space-1` | 4 px | Icon-to-label, tightest internal padding |
| `space-2` | 8 px | Between related inline elements |
| `space-3` | 12 px | Inside bubbles (vertical), list row internal padding |
| `space-4` | 16 px | **Screen edge margin**; between bubbles from different senders |
| `space-5` | 20 px | Between distinct list rows with avatars |
| `space-6` | 24 px | Between content groups |
| `space-8` | 32 px | Section separation |
| `space-10` | 40 px | Above a screen's primary heading |
| `space-12` | 48 px | Empty-state vertical rhythm |
| `space-16` | 64 px | Onboarding vertical rhythm |

**Rule of proximity:** the space *inside* a group is always smaller than the space *around* it. If two elements are 12 px apart, the group they form must have more than 12 px around it. Most "cluttered" screens are proximity failures, not density failures.

---

## 2.12 — Grid

- **Mobile:** a single fluid column with a 16 px gutter. No multi-column layouts on phone portrait — the transcript is a column, and columns are what phones are for.
- **Tablet / foldable open / desktop:** a two-pane layout — conversation list (fixed 360 px, min 320 px, max 400 px) and conversation (fluid, content capped at 720 px and centred within the pane). A third pane (profile, thread, files) slides over the second below 1280 px and sits alongside it above.
- **Content max width:** 720 px. Beyond that, line length exceeds comfortable reading measure and the transcript stops feeling like a conversation.
- **Baseline:** 4 px vertical rhythm; text blocks snap to it.
- **Safe areas:** honoured on every platform. Nothing interactive within 8 px of a display cutout or home indicator.

---

## 2.13 — Typography

**Typefaces.**

| Role | Face | Why |
|---|---|---|
| UI + body | **Inter** (variable) | Exceptional legibility at small sizes, huge glyph coverage, true optical sizing, open-licensed — no per-seat cost as we scale, and no legal exposure. |
| Arabic / Persian / Urdu | **IBM Plex Sans Arabic** | A genuine Arabic design, not a Latin face with Arabic bolted on; weights map cleanly to Inter's. |
| CJK | Platform default (SF / Noto Sans CJK) | Nothing we could bundle would beat the platform faces, and the file-size cost of shipping CJK is unjustifiable. |
| Numerals in timestamps, counters, call duration | Inter **tabular** figures | Non-tabular numerals cause visible jitter on any counter that updates. |
| Code / hashes / safety numbers | **JetBrains Mono** | Safety-number verification requires unambiguous 0/O and 1/l/I. |

**Scale.** A modest ratio (≈1.18) because a communication app has few hierarchy levels and needs none of the drama a 1.5 scale gives.

| Token | Size / line-height | Weight | Use |
|---|---|---|---|
| `display` | 32 / 38 | 600 | Onboarding headline only |
| `title-1` | 24 / 30 | 600 | Screen titles |
| `title-2` | 20 / 26 | 600 | Section headings, dialog titles |
| `title-3` | 17 / 22 | 600 | Conversation name in list rows, contact name |
| `body` | 16 / 22 | 400 | **Message text** — the most-read type in the product |
| `body-strong` | 16 / 22 | 600 | Emphasis within body |
| `callout` | 15 / 20 | 400 | Message preview in list, sheet body copy |
| `subhead` | 14 / 19 | 400 | Secondary metadata, group member counts |
| `footnote` | 13 / 17 | 400 | Timestamps, "delivered," helper text |
| `caption` | 11 / 14 | 500 | Badges, overline labels, media duration |

**Rules.**
- **Body messages are never smaller than 16 px.** Not for density, not for "more content on screen," not on tablets.
- **Maximum three type sizes per screen.** A screen needing four has too many jobs.
- **Never set body text below 400 weight or above 600** — Inter's lighter and heavier weights fail at small sizes on low-DPI displays.
- **Dynamic Type / font scale is honoured up to 200 %.** Every layout is tested at 200 %; nothing may clip, truncate a critical label, or overlap. Layouts reflow vertically rather than shrinking type.
- **Line length target 45–75 characters.** Enforced by the 720 px content cap.
- **Emoji-only messages render at 32 px** for up to three emoji, then drop to inline size — a rare, deliberate exception to the "three sizes" rule, because it is a real communication signal.

**Bidirectional text.** The full interface mirrors for RTL locales, including message-bubble corner geometry, back-navigation direction, and progress-bar fill. Mixed-direction runs inside one message use the Unicode Bidirectional Algorithm with explicit isolates around embedded LTR fragments (URLs, @mentions, numbers) — the most common bidi bug is an unisolated URL flipping the punctuation at the end of an Arabic sentence, and it is a release blocker.

---

## 2.14 — Component Specifications (visual)

Interaction behaviour is in `03-UX-BIBLE.md`; the component API is in `07-DESIGN-SYSTEM.md`. Visual specs live here.

### Buttons

| Variant | Fill | Label | Height | Radius | Use |
|---|---|---|---|---|---|
| Primary | `orbit-500` / dark `orbit-500` | `void-0`, `body-strong` | 48 px | `radius-sm` | The one action that matters on the screen. Max one per screen. |
| Secondary | transparent, 1 px `void-200` / `void-700` | `void-900` / `void-50` | 48 px | `radius-sm` | Alternative actions. |
| Tertiary / text | none | `orbit-600` / `orbit-300` | 44 px | `radius-sm` | Low-emphasis, inline. |
| Destructive | `danger` | `void-0` | 48 px | `radius-sm` | Delete, block, leave. Requires confirmation. |
| Icon | none / `void-100` on press | inherits text colour | 44 × 44 px | `radius-full` | Toolbar actions; always has an accessibility label. |

States: **hover** −4 % lightness (pointer devices only) · **pressed** −8 % lightness plus a 0.97 scale over 80 ms · **disabled** 38 % opacity, no pointer events, never rendered as a colour a user could mistake for enabled · **focus** 2 px `orbit-500` ring at 2 px offset, always visible for keyboard users, never suppressed.

**Minimum touch target is 44 × 44 px** regardless of visual size — a 24 px icon has a 44 px hit area. This is not negotiable and is verified by an automated test.

### Cards

`void-0` / `void-900` surface, `radius-md`, `e1`, `space-4` internal padding. No border in light mode (shadow does the work); 1 px `void-700` border in dark mode where shadow cannot.

### Lists

Row height 72 px with avatar (48 px avatar, `space-4` gutter, two text lines), 56 px without. Dividers are inset to the text baseline, not full-bleed, and are `void-200` / `void-700` at 1 px. Pressed state fills the row with `void-50` / `void-850` — never a coloured highlight.

### Inputs

48 px height, `radius-sm`, 1 px `void-200` border, `void-0` fill, `space-3` horizontal padding. Focus: border becomes 2 px `orbit-500` (the extra pixel is drawn inward so the field does not shift). Error: 2 px `danger` border plus `footnote` `danger-text` message beneath — never a tooltip, never colour alone. Placeholder is `void-400` and never substitutes for a label.

**The composer** is the exception: it grows from 48 px to a maximum of 5 lines (140 px) then scrolls internally, keeping the send control pinned to the bottom-right and the transcript's last message visible.

### Navigation

- **Bottom bar, 4 destinations maximum:** Chats · Calls · Stories · Settings. 56 px + safe area. Active item uses a filled icon and `orbit-600` / `orbit-300`; inactive uses outline and `void-500` / `void-400`. Labels are always shown (icon-only bars fail comprehension tests and screen readers alike).
- **Channels** live inside Chats as a filter, not as a fifth destination — see `05-FEATURE-BIBLE.md` §5.6.
- **Top bar** is 56 px, carries at most a title, a back affordance, and two actions.

---

## 2.15 — Accessibility Requirements

Non-negotiable per Part 0.6 clause 9.

| Requirement | Standard |
|---|---|
| Text contrast | ≥4.5:1 body, ≥3:1 for ≥24 px or ≥19 px bold. Every token pair in this document is measured. |
| Non-text contrast | ≥3:1 for interface component boundaries, focus indicators, and meaningful icons. |
| Touch targets | ≥44 × 44 px, ≥8 px separation between adjacent targets. |
| Colour independence | No information conveyed by colour alone. Delivery state has distinct *glyphs*, not just colours. Unread state uses a dot **and** a weight change. |
| Screen readers | Every interactive element has a label, role, and state. The transcript is navigable message-by-message. Announcements for incoming messages are polite, not assertive. |
| Dynamic type | Layouts hold to 200 % scale without clipping or overlap. |
| Reduced motion | Honoured product-wide (`01-BRAND-BIBLE.md` §1.9 rule 7). |
| Reduced transparency | Blur replaced with opaque surfaces (§2.9). |
| Keyboard | Full operation on desktop/web: tab order matches visual order, focus is always visible, Escape closes, no keyboard traps. |
| Captions | Auto-transcription available for every voice note and, from Phase 2, live captions in calls. |
| Colour-blind safety | See the note below — lightness separation is maximised where possible but is **not** sufficient on its own, so distinct glyphs are mandatory. |

**A measured note on colour-blind safety, recorded honestly.** We wanted to claim that the semantic trio is distinguishable in greyscale. It is not fully, and the constraint is physical: in light mode every semantic *text* colour must clear 4.5:1 on white, which caps it at roughly CIE L\* 48. Green, amber, and red all land in a narrow band there. Measured values: `success-text #08602F` L\* 35.2 · `danger-text #C0271B` L\* 42.4 · `warning-text #B45309` L\* 46.9. Success is comfortably separable; warning and danger differ by ~4.5 L\* — visible side by side, unreliable in isolation. Dark mode is better because the ceiling lifts: `danger-dark #FF6B60` L\* 63.9 · `success-dark #35D07F` L\* 74.4 · `warning-dark #FFC46B` L\* 82.8.

The design consequence is a hard rule, not a caveat: **every semantic state ships a distinct glyph and, wherever space allows, a word.** A failed message is a filled circle with an exclamation *and* the word "Not sent." Delivery states use distinct tick geometry, not tick colour. Any surface where the only difference between "warning" and "error" is the hue is rejected in design review.

**Testing.** Automated checks (contrast, target size, missing labels) run in CI on every component. Manual screen-reader passes (VoiceOver + TalkBack) are a release gate for any changed surface. See `06-TECHNICAL-BIBLE.md` §6.12.
