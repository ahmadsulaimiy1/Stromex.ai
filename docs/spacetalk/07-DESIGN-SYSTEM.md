# THE SPACETALK DESIGN SYSTEM

### Part 7 — Tokens, Components, Patterns

*Governed by `02-VISUAL-DESIGN-SYSTEM.md` (what things look like) and `03-UX-BIBLE.md` (how they behave). This document is the buildable specification: the token contract, the component inventory, and the patterns that compose them.*

**The rule that makes a design system real:** a designer may not invent a value, and an engineer may not hard-code one. Every colour, space, radius, duration, and type style referenced in a screen must resolve to a token below. Anything else fails design review and CI lint.

---

## 7.1 — Token Architecture

Three tiers. Screens consume tier 3 only; tier 3 references tier 2; tier 2 references tier 1. A screen that reaches past tier 3 is a bug.

```
Tier 1 — Primitive     orbit-500, void-100, space-4, radius-lg, dur-medium
                       Raw values. Theme-independent. Never used in a screen.

Tier 2 — Semantic      color.surface.primary, color.text.secondary, color.action.primary
                       Meaning, resolved per theme. This is where light/dark diverge.

Tier 3 — Component     bubble.outgoing.background, composer.height, button.primary.label
                       Component-scoped. What screens actually reference.
```

**Distribution.** Tokens are authored once in JSON (W3C Design Tokens format) and generated into: Dart (`SpaceTokens`), the Figma variable set, and a CSS custom-property sheet for the web client. **Generation is one-directional and automated in CI** — hand-editing a generated file is a build failure. This is what keeps design and code from drifting, which is the failure mode of every design system that dies.

**Semantic token set** (abbreviated; the full set is in the token repository):

| Token | Light | Dark |
|---|---|---|
| `color.bg.app` | `void-25` | `void-950` |
| `color.surface.primary` | `void-0` | `void-900` |
| `color.surface.elevated` | `void-0` | `void-850` |
| `color.text.primary` | `void-900` | `void-50` |
| `color.text.secondary` | `void-500` | `void-400` |
| `color.text.tertiary` | `void-400` | `void-500` |
| `color.text.onAction` | `void-0` | `void-0` |
| `color.action.primary` | `orbit-500` | `orbit-500` |
| `color.action.primaryText` | `orbit-600` | `orbit-300` |
| `color.border.subtle` | `void-200` | `void-700` |
| `color.ai.text` | `aurora-700` | `aurora-300` |
| `color.ai.surface` | `aurora-050` | `aurora-950` |
| `color.status.danger` | `danger` | `danger-dark` |
| `color.status.warning` | `warning-text` | `warning-dark` |
| `color.status.success` | `success-text` | `success-dark` |

---

## 7.2 — Component Inventory

Every component is specified as: **props · states · variants · accessibility contract · when not to use it.** The last line is the one that keeps a system small.

### Foundational

| Component | Variants | Key states | Never use for |
|---|---|---|---|
| `Button` | primary, secondary, tertiary, destructive, icon | default, hover, pressed, disabled, loading, focus | Navigation — that's a link or a row |
| `Avatar` | 24 / 32 / 40 / 48 / 64 / 96 px | image, initials, group-stack, online dot | Decorative imagery |
| `Badge` | count, dot | — | Anything that isn't addressed to the user (`03` §3.9) |
| `Chip` | filter, input, suggestion | selected, unselected, disabled | Primary actions |
| `Divider` | inset, full | — | Creating hierarchy that spacing should create |
| `Icon` | 16 / 20 / 24 / 32 px | — | Conveying meaning without a label |
| `Spinner` | 16 / 24 / 32 px | — | List loading — use `Skeleton` |
| `Skeleton` | text, avatar, media, row | shimmer, static (reduced motion) | Anything under 300 ms |

### Content

| Component | Notes |
|---|---|
| `MessageBubble` | The most important component in the product. Variants: incoming, outgoing, system, deleted. Slots: reply-quote, content, attachments, reactions, meta (time + delivery glyph). Run-grouping and corner geometry per `02` §2.10. |
| `MediaTile` | Image, video, GIF. Always renders at known intrinsic dimensions so nothing shifts (`03` §3.4). |
| `VoiceNote` | Waveform, play/pause, speed, duration, transcript toggle. |
| `FileTile` | Type glyph, name, size, progress, download/open. |
| `LinkPreview` | Sender-generated (`05` §5.1). Title, description, image, domain. Collapsible. |
| `AiAnnotation` | The only component permitted to use `color.ai.*`. Slots: label, content, source-link, feedback. |
| `SystemMessage` | Centred, `footnote`, `color.text.secondary`. Group events, encryption notices, disappearing-message changes. |

### Navigation & containers

| Component | Notes |
|---|---|
| `AppBar` | 56 px. Title + back + max two actions. Translucent variant per `02` §2.9. |
| `BottomNav` | Exactly 4 items, labels always shown. |
| `ListRow` | 56 / 72 px. Leading, title, subtitle, trailing, swipe actions. Entire row is one touch target. |
| `Sheet` | Bottom sheet. Drag handle, snap points, dismissible. **Preferred over `Dialog` for anything non-blocking** (`03` §3.12). |
| `Dialog` | Blocking decisions only. Max two actions. |
| `Menu` | Long-press and overflow. Destructive items last, separated, in `danger`. |
| `Composer` | Text field, attach, mic, send. Fixed position, grows to 5 lines (`02` §2.14). |
| `Banner` | Persistent, dismissible, top of content. Offline, security warnings. |
| `Snackbar` | 4 s, one action, non-blocking. Undo lives here (`03` §3.2). |

### Input

`TextField` · `SearchField` · `Switch` · `Checkbox` · `Radio` · `Slider` · `Picker` · `OtpField` · `SafetyNumberDisplay` (monospaced, chunked, copyable, QR-linked).

**Components we deliberately do not have**, recorded so nobody adds them: carousel, accordion, tooltip on touch surfaces, breadcrumb, stepper, tab-within-tab, floating action button on the conversation screen (the composer *is* the action), and any "onboarding tour" component.

---

## 7.3 — Iconography

Specification in `01-BRAND-BIBLE.md` §1.8. Delivery:

- One source SVG set on a 24 × 24 grid, 1.5 px stroke, exported to a Flutter icon font and a web sprite by the same pipeline that builds tokens.
- Sizes: 16 (inline), 20 (dense), 24 (default), 32 (prominent).
- **Every icon ships with a required `semanticLabel`.** The Flutter wrapper makes the label a required parameter, so an unlabelled icon is a *compile error* rather than an audit finding. This is the cheapest accessibility enforcement in the entire system.
- Icons inherit `color.text.*` and never carry colour of their own, except status icons.

---

## 7.4 — Buttons (behavioural contract)

| Property | Rule |
|---|---|
| Count | **One primary button per screen.** Two primaries means the screen has two purposes. |
| Loading | The button keeps its width, swaps its label for a spinner, and remains disabled. Never collapses or jumps. |
| Disabled | Only when the action is genuinely impossible. Prefer an enabled button that explains what is missing on tap — a disabled button with no explanation is a dead end. |
| Destructive | Always paired with a confirmation or an undo, never both. |
| Touch target | ≥44 × 44 px regardless of visual size, verified by automated test. |
| Label | A verb. "Send," "Link device," "Delete chat." Never "OK," "Submit," or "Yes." |

---

## 7.5 — Cards and Lists

**Cards** are for grouped, self-contained content that can be acted on as a unit. If the content is a list of similar things, it is a list, not a stack of cards. Card-per-row is the most common way a clean list becomes a cluttered screen.

**Lists** are the product's primary structure. Rules: the whole row is the touch target; swipe actions match `03` §3.2 exactly, product-wide; dividers are inset to the text baseline; a list of one item is not a list, it is a row; and virtualisation is mandatory above 50 items — no exceptions, because the conversation list and the transcript are both unbounded.

---

## 7.6 — Dialogs, Sheets, and Menus

**Choosing between them** — this decision is made wrongly more often than any other in mobile design:

| Use | When |
|---|---|
| **Snackbar** | Something happened; the user may want to undo it |
| **Sheet** | The user needs to choose from options or fill something in, and can back out |
| **Dialog** | The user must decide before anything else can proceed, and the decision is hard to reverse |
| **Full screen** | The task has multiple steps or needs the whole viewport |

Dialogs have at most two actions, with the safe one on the right in LTR (per platform convention) and the destructive one clearly marked. Sheets support drag-to-dismiss, snap points, and a visible handle. Menus place destructive items last, after a separator, in `danger`.

**Nothing stacks.** A sheet may not open a dialog which may not open another sheet. If a flow needs that, it is a full screen.

---

## 7.7 — Motion Tokens

| Token | Duration | Curve (cubic-bézier) | Use |
|---|---|---|---|
| `dur-instant` | 80 ms | `standard` `(0.2, 0.0, 0.0, 1.0)` | Press feedback, ripples |
| `dur-fast` | 120 ms | `standard-decelerate` `(0.0, 0.0, 0.0, 1.0)` | Small fades, tooltips, chips |
| `dur-medium` | 200 ms | `emphasised-accelerate` `(0.3, 0.0, 0.8, 0.15)` | Sheet out, dismiss |
| `dur-default` | 240 ms | `emphasised-decelerate` `(0.05, 0.7, 0.1, 1.0)` | Sheet in, menu in |
| `dur-screen` | 280 ms | `emphasised` `(0.2, 0.0, 0.0, 1.0)` | Screen transitions |
| `dur-slow` | 400 ms | `standard` | Rare: full-screen media transitions |

**Rules.** Nothing exceeds 400 ms. Nothing springs or overshoots. Every animation is interruptible at any frame. Under `prefers-reduced-motion`, position and scale transitions become ≤100 ms cross-fades, and all looping motion stops (`01-BRAND-BIBLE.md` §1.9).

---

## 7.8 — Gestures

The complete, fixed set is in `03-UX-BIBLE.md` §3.2. System-level requirements:

- **Gesture conflicts are resolved in favour of the platform.** The iOS edge-back and Android back gestures always win; our swipe zones start beyond the system's.
- **Every gesture has a discoverable, non-gesture equivalent.**
- **Haptics are informational**: a light tick on long-press engage, a medium tick on send, a distinct pattern on error. Nothing celebratory. All haptics respect the system setting.
- **Drag operations show a drop target before release** — never a mystery drop.

---

## 7.9 — Transitions and Shared Elements

| From → To | Transition |
|---|---|
| Conversation list → conversation | Push with the avatar as a shared element |
| Conversation → profile | Push; avatar expands to header |
| Message media → full-screen viewer | Shared-element expansion from the tile's exact bounds |
| Composer → attachment tray | Tray rises; composer does not move (`03` §3.2) |
| Any screen → sheet | Sheet rises from the triggering control; scrim fades to 40 % |
| Tab → tab | Cross-fade only, 120 ms. No horizontal slide — tabs are peers, not a sequence. |

---

## 7.10 — Design Patterns

Repeatable solutions, defined once so they are not re-solved differently on each screen.

**Progressive disclosure.** Show the common case; put the rest behind one clearly-labelled control. Never behind two.

**Optimistic action.** Update the UI immediately, reconcile in the background, surface only real failures (`03` §3.2).

**Undo over confirm.** For anything recoverable, act and offer undo. Reserve confirmation for the irreversible.

**Inline over navigate.** Solve it where the user is. Translation appears under the message; it does not open a screen.

**Explain in place.** When something is unavailable, say why at the point of unavailability — not in a help centre.

**One question per screen.** Onboarding and settings flows ask one thing at a time.

**Honest state.** Never show a state that isn't true. No fake progress, no optimistic "delivered," no placeholder avatars that look like real people.

**The AI seam.** Anything a model produced sits in an `AiAnnotation` with Aurora colour, a label, and a feedback control. There is exactly one way for AI output to appear in this product, so a user learns it once.

---

## 7.11 — Contribution Rules

Adding to the system:

1. **Three uses before a component.** A pattern used twice is a copy; used three times it is a component. Premature components are as costly as duplicated code.
2. **Every component ships with:** the Flutter implementation, a Figma component with matched variants, golden tests for every state in both themes and both directions, an accessibility contract, and a "when not to use it" note.
3. **Every component is reviewed by design and engineering together.** A component approved by only one of them will be wrong in the other's dimension.
4. **Deprecation is scheduled, not implied.** A deprecated component gets a replacement, a migration note, and a removal date. Two components that do the same thing is how a design system stops being a system.
5. **A change to a tier-1 or tier-2 token requires CDO approval**, because it changes every screen at once.
