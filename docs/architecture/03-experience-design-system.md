# TASMIM Experience Design System

> Defines how TASMIM *feels* to use, not just what it can do. This is the interaction contract every surface (web, desktop, mobile) must honor.

**North star:** a first-time user creates a professional design within **30 seconds** of arriving. A professional designer never hits a wall the software put there on purpose.

These two goals are usually treated as opposites (simple *or* powerful). TASMIM treats them as a sequencing problem, not a trade-off — solved by six interlocking philosophies below.

---

## 1. Navigation Philosophy

**Principle: the canvas is the app. Everything else is a temporary overlay.**

- No permanent multi-level sidebar tree (the pattern that makes Adobe Express and legacy Adobe apps feel dense). Navigation is a **command palette** (⌘K, Linear/Arc-inspired) plus a slim, auto-hiding contextual dock.
- A single omnipresent entry point — **"Ask TASMIM"** — sits where a search bar would, but accepts natural language for *anything*: find a file, generate a layout, explain a tool, fix a contrast issue. It's navigation and AI unified into one affordance, not two competing systems.
- Breadcrumbs over hierarchy: users always know where they are (Workspace → Project → Document) without a permanent tree view consuming screen space.
- Mode switching (Beginner/Professional/Studio/Enterprise) is a single, always-reachable control — never a settings-menu decision buried three levels deep.

---

## 2. Workspace Philosophy

**Principle: zero-clutter by default, infinite depth on demand.**

- **Canvas-first layout.** On load, the canvas occupies effectively the entire viewport. Panels are docked but collapsed until a relevant object is selected or a tool is invoked — directly implementing the Editorial Bible's "Zero-Clutter Workspace" standard.
- **Contextual toolbars.** Selecting text surfaces typography controls; selecting a shape surfaces geometry and fill controls. Nothing is shown that isn't actionable for the current selection.
- **Adaptive Interface modes** change *density*, not the underlying document or engine:
  - **Beginner Mode** — templates, guided prompts, one-click AI generation, minimal manual controls.
  - **Professional Mode** — full manual tools exposed, still contextual.
  - **Studio Mode** — multi-artboard, advanced typography/vector controls, plugin panel, print/CMYK tools.
  - **Enterprise Mode** — adds brand-lock controls, approval workflow rail, team asset governance.
- A user can move up a mode the moment they reach for a tool that isn't visible — TASMIM suggests the upgrade ("This looks like precision work — switch to Professional Mode?") rather than gatekeeping it.

---

## 3. Interaction Philosophy

**Principle: direct manipulation first, AI-assisted second, dialogs last.**

- Every property (position, color, size, spacing) is editable by dragging, nudging, or typing directly on-canvas — modal dialogs are treated as a last resort, reserved for genuinely complex configuration (e.g., export settings).
- **Inline AI suggestion** (ghost-preview pattern, like code-completion but for design): as a user drags a text box, TASMIM shows a faint preview of AI-suggested alignment, spacing, or a better type pairing; accept with Tab, ignore by continuing to drag. AI never interrupts the manual gesture — it rides alongside it.
- **Keyboard-first for professionals:** every action has a shortcut, and the command palette teaches the shortcut by echoing it next to the action it just ran, matching Linear's habit-forming approach to power-user fluency.
- **Touch-first, not touch-adapted, on mobile:** gestures are designed for fingers from the ground up (pinch/rotate/two-finger duplicate, palm-rejected calligraphy input) rather than a shrunk mouse-driven UI. See Master Architecture §4.

---

## 4. Animation Philosophy

**Principle: motion communicates state; it never decorates.**

- Every transition answers a question: where did this element come from, where is it going, is this action reversible. No motion exists purely for polish.
- Spring-physics-based easing (not fixed-duration eases) so interrupted animations (e.g., a panel closing mid-open because the user changed their mind) feel physically continuous rather than snapping.
- Target: 120fps on capable displays, never below 60fps — matching the "Zero lag" standard in the Editorial Bible. Enforced as a CI performance budget (see Master Architecture §3 rendering core), not an aspiration.
- AI-generated content **arrives**, it doesn't **appear** — layouts build in with staggered, structure-revealing motion (grid lines resolve into a template) so the user's mental model of "AI just did work for me" is reinforced by what they see, building trust in the automation.

---

## 5. Accessibility Philosophy

**Principle: accessibility is a property of both the tool and its output.**

- **The tool itself:** full keyboard navigability, screen-reader labeling for every control (not just WCAG-minimum contrast), resizable UI text independent of canvas zoom, and a reduced-motion mode that disables non-essential animation without disabling functional motion cues.
- **What the tool produces:** the Smart Design Coach (§8 of the Editorial Bible, expanded in [`04-creative-intelligence-engine.md`](./04-creative-intelligence-engine.md)) actively flags contrast failures, missing alt text, unreadable type sizes, and poor reading-order in *every design a user makes* — turning accessibility from a specialist's checklist into an ambient, continuous check available to every user regardless of expertise.
- Target compliance: WCAG 2.2 AA for the application shell at minimum, with an AAA-track for core creation flows.

---

## 6. AI-First Philosophy

**Principle: AI is ambient infrastructure, not a mode you enter.**

- There is no separate "AI panel" a user must discover — every surface (canvas, layers, typography controls, the command palette) has an AI affordance available at the point of need.
- **Transparency by default:** any AI-generated or AI-modified element carries a subtle provenance indicator, and a single click explains *why* the AI suggested it ("This heading uses your brand's secondary typeface, sized for 4.5:1 contrast against the background") — matching the Master Architecture's provenance/safety layer (§6) and building the trust that ambient automation requires.
- **Override is always one action away.** AI never locks a user out of manual control; every AI action is a normal, fully-editable operation in the undo history, not a black box.
- **AI learns the user, not just the prompt.** Because every agent reads/writes the shared Creative Context Graph (Master Architecture §6), suggestions get more relevant the more a person uses TASMIM — the practical expression of "Intelligence Over Complexity" from the Editorial Bible.

---

## The 30-Second Path (Beginner Mode, first session)

1. **0–5s:** Landing surface asks one open question — "What are you creating?" — accepting free text, a template category tap, or a photo/logo drop.
2. **5–15s:** AI Designer (see Creative Intelligence Engine) proposes three complete directions in parallel — not three color variants of one layout, three genuinely different structures — rendered live, not as static thumbnails.
3. **15–25s:** User taps one, and it opens already populated with their content (if provided) or smart placeholder content matched to their stated intent, immediately editable.
4. **25–30s:** A single, unobtrusive prompt — "Export" or "Keep editing" — is visible without hunting; export requires no additional dialog for the common case (web-ready PNG at the artboard's native size).

## The No-Ceiling Path (Professional/Studio Mode)

A professional never encounters a "this feature is for beginners" wall because there isn't a separate beginner product — Studio Mode exposes the same document to point-precise vector tools, CMYK export, multi-artboard publishing layouts, and the full AI agent roster as direct, addressable collaborators rather than a single "magic button." The ceiling is the rendering engine's actual technical limits (Master Architecture §3), not a product-tier decision.
