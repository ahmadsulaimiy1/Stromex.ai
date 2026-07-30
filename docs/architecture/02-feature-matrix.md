# TASMIM Feature Matrix — Competitive Analysis

> Legend: ● Strong / native capability &nbsp;&nbsp; ◐ Partial, limited, or paid-tier-only &nbsp;&nbsp; ○ Absent or not a focus
> TASMIM column reflects **target capability at full roadmap maturity** (see [`07-super-app-roadmap.md`](./07-super-app-roadmap.md) for phasing), not day-one MVP scope.

Scope note: Adobe Creative Cloud broadly (Photoshop/Illustrator/InDesign/Premiere), VistaCreate, PicsArt, CapCut, Notion, Linear, and Arc Browser are referenced qualitatively throughout as pattern sources (Notion/Linear/Arc for interface philosophy, PicsArt/CapCut for mobile-native creation, VistaCreate for template-commerce) even where they aren't given their own matrix column, to keep the table readable.

---

## A. Core Design & Editing

| Feature | Canva | Figma | Adobe Express | PixelLab | Affinity | CorelDRAW | Pinterest | **TASMIM** |
|---|---|---|---|---|---|---|---|---|
| Vector precision editing | ◐ | ● | ◐ | ○ | ● | ● | ○ | ● |
| Non-destructive raster editing | ◐ | ○ | ◐ | ◐ | ● | ● | ○ | ● |
| Advanced typography control (kerning, OpenType features) | ◐ | ◐ | ◐ | ○ | ● | ● | ○ | ● |
| Template library depth | ● | ○ | ● | ● | ○ | ◐ | ○ | ● |
| Brand kit / consistency enforcement | ◐ | ◐ | ◐ | ○ | ○ | ○ | ○ | ● |
| CMYK / print-fidelity export | ○ | ○ | ○ | ○ | ● | ● | ○ | ● |

**Gap analysis.** The market is split into two camps that never merge: *accessible-but-shallow* (Canva, Adobe Express, PixelLab — huge template libraries, weak precision tools) and *precise-but-intimidating* (Figma, Affinity, CorelDRAW — professional-grade editing, steep learning curves, minimal template/AI assistance). No competitor spans both ends of that spectrum in one product.

**TASMIM advantage.** The Adaptive Interface (Beginner → Professional → Studio → Enterprise, see Editorial Bible §4) is architected specifically to collapse this split: the same document and rendering engine powers a one-click template flow *and* pixel/point-precise vector and CMYK-accurate editing, with the UI complexity gated by mode rather than by a separate product.

---

## B. AI Capabilities

| Feature | Canva | Figma | Adobe Express | PixelLab | Affinity | CorelDRAW | Pinterest | **TASMIM** |
|---|---|---|---|---|---|---|---|---|
| Text-to-design generation | ◐ | ○ | ◐ | ◐ | ○ | ○ | ○ | ● |
| AI image generation | ◐ | ○ | ◐ | ◐ | ○ | ○ | ○ | ● |
| AI auto-layout / composition | ◐ | ◐ (auto-layout for UI) | ◐ | ○ | ○ | ○ | ○ | ● |
| Brand-aware generation (uses *your* brand kit) | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ● |
| Design critique / accessibility AI | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ● |
| Multi-agent specialist AI (typography, art direction, copy, etc.) | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ● |

**Gap analysis.** Every competitor's "AI" today is a single bolt-on feature (an image generator, a "magic" background remover, a one-shot template suggester). None run AI *continuously* against the user's actual brand context, and none critique a design the way a creative director would.

**TASMIM advantage.** The Creative Intelligence Engine (§4, [`04-creative-intelligence-engine.md`](./04-creative-intelligence-engine.md)) is a standing council of ten specialist agents sharing one Creative Context Graph — brand-aware by construction, not by prompt engineering. The Smart Design Coach (Editorial Bible §8) is a category competitors have not built at all: ambient, continuous, Grammarly-style critique of layout, contrast, hierarchy, and accessibility.

---

## C. Collaboration & Workflow

| Feature | Canva | Figma | Adobe Express | PixelLab | Affinity | CorelDRAW | Pinterest | **TASMIM** |
|---|---|---|---|---|---|---|---|---|
| Real-time multiplayer editing | ◐ | ● | ○ | ○ | ○ | ○ | ○ | ● |
| Comments & review threads | ● | ● | ◐ | ○ | ○ | ○ | ● (pins) | ● |
| Full version history | ◐ | ● | ○ | ○ | ◐ | ◐ | ○ | ● |
| Team workspaces & roles | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● |
| Approval workflow (submit → review → publish) | ◐ | ◐ | ○ | ○ | ○ | ○ | ○ | ● |
| Enterprise SSO / governance | ● | ● | ◐ | ○ | ○ | ○ | ○ | ● |

**Gap analysis.** Figma set the bar for real-time multiplayer engineering; Canva matched it for simple documents but not for complex, asset-heavy files. None of the desktop-native precision tools (Affinity, CorelDRAW) have credible real-time collaboration — it is architecturally very hard to retrofit onto a non-CRDT document model, which is exactly why they haven't.

**TASMIM advantage.** Real-time collaboration is designed in at the document-model level from day one (CRDT core, §1/§5/§7 of the Master Architecture) rather than retrofitted, so TASMIM can offer Figma-grade multiplayer *on the same document* that also supports Affinity-grade precision and CMYK export — a combination no current competitor's architecture supports.

---

## D. Publishing & Media Breadth

| Feature | Canva | Figma | Adobe Express | PixelLab | Affinity | CorelDRAW | Pinterest | **TASMIM** |
|---|---|---|---|---|---|---|---|---|
| Multi-page / book layout | ◐ | ○ | ○ | ○ | ● (Publisher) | ● | ○ | ● |
| Presentation / deck tools | ● | ◐ | ◐ | ○ | ○ | ○ | ○ | ● |
| Animated / interactive slides | ◐ | ○ | ○ | ○ | ○ | ○ | ○ | ● |
| Video & motion graphics | ◐ | ○ | ◐ | ◐ | ○ | ○ | ○ | ● |
| Long-form publishing (journals, newspapers, research papers) | ○ | ○ | ○ | ○ | ◐ | ◐ | ○ | ● |

**Gap analysis.** Publishing-grade, long-document tooling (InDesign's historical territory) has no credible modern, AI-assisted, collaborative competitor — Affinity Publisher and CorelDRAW are capable but solo-desktop-era in workflow. Video/motion is fragmented across CapCut-style mobile-first tools and desktop NLEs with no bridge to the design layer.

**TASMIM advantage.** Publishing Studio and Video Studio (Editorial Bible §7) sit on the *same* document/asset/brand-kit substrate as the graphic design and presentation tools, so a brand system defined once flows into a book, a deck, a reel, and a poster without re-authoring — the "one document model" cross-cutting principle from the Master Architecture.

---

## E. Discovery & Community

| Feature | Canva | Figma | Adobe Express | PixelLab | Affinity | CorelDRAW | Pinterest | **TASMIM** |
|---|---|---|---|---|---|---|---|---|
| Inspiration boards / moodboards | ○ | ◐ (community files) | ○ | ○ | ○ | ○ | ● | ● |
| Trend discovery feed | ○ | ○ | ○ | ○ | ○ | ○ | ● | ● |
| Creator marketplace (templates/assets/fonts) | ● | ● (community) | ◐ | ◐ | ○ | ○ | ○ | ● |
| Social graph (follow creators/brands) | ○ | ◐ | ○ | ○ | ○ | ○ | ● | ● |
| Inspiration → editable design conversion | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ● |
| Plugin / developer ecosystem | ◐ | ● | ○ | ○ | ○ | ○ | ○ | ● |

**Gap analysis.** Pinterest owns discovery and taste but has no editor — saving a pin ends the workflow. Canva and Figma have marketplaces but no discovery layer that builds taste over time the way Pinterest's recommendation graph does. The "see something → make something" jump is manual and lossy everywhere today.

**TASMIM advantage.** TASMIM Boards ([`05-inspiration-ecosystem.md`](./05-inspiration-ecosystem.md)) is architected to close exactly that gap: inspiration and the editor share the same Creative Context Graph, so a saved board becomes usable style DNA (palette, type pairing, layout rhythm) rather than a dead-end screenshot. This is TASMIM's single clearest "no one else has built this" opportunity.

---

## F. Platform Reach & Access

| Feature | Canva | Figma | Adobe Express | PixelLab | Affinity | CorelDRAW | Pinterest | **TASMIM** |
|---|---|---|---|---|---|---|---|---|
| True offline mode | ○ | ◐ (desktop app, limited) | ○ | ◐ | ● | ● | ○ | ● |
| Full mobile/desktop feature parity | ○ | ○ | ○ | ◐ | ○ | ○ | ◐ | ● |
| Native RTL / Arabic typography engine | ◐ | ○ | ◐ | ○ | ◐ | ◐ | ○ | ● |
| In-app accessibility (screen reader, keyboard nav) | ◐ | ◐ | ◐ | ○ | ◐ | ◐ | ◐ | ● |
| Islamic/liturgical content tooling (Mushaf, calligraphy, Hijri) | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ● |

**Gap analysis.** Mobile is universally a "lite" experience across every competitor — none treat it as a first-class creation surface. Arabic/RTL support is bolted-on font rendering at best (correct glyph shaping, but no calligraphy, Mushaf, or tashkeel-aware tooling) across the entire market; the Islamic creative space is, as the Editorial Bible notes, genuinely unowned.

**TASMIM advantage.** Shared rendering core across mobile/desktop/web (Master Architecture §3–4) is a direct structural answer to the mobile-parity gap. The Islamic Creative Suite ([`06-islamic-creative-suite.md`](./06-islamic-creative-suite.md)) is not a localization checkbox but a purpose-built product line — the clearest whitespace in the entire competitive set and a defensible initial wedge (see roadmap risk notes).

---

## Summary: Where TASMIM's Real Advantage Comes From

It is *not* any single feature in the tables above — competitors can and will copy individual features quickly. TASMIM's durable advantage is structural:

1. **One document model** spanning precision editing, AI generation, publishing, video, and mobile — competitors are architecturally siloed across multiple products/formats.
2. **A standing multi-agent AI council with shared brand memory**, not a single bolt-on generator.
3. **Inspiration wired directly into the editor**, closing the "Pinterest saves but can't make" gap.
4. **The Islamic Creative Suite as a genuine, unowned category**, giving TASMIM a defensible beachhead market rather than a head-on assault on Canva's template scale or Adobe's enterprise entrenchment (see risk discussion in [`08-design-the-future-and-self-review.md`](./08-design-the-future-and-self-review.md)).
