# TASMIM Feature Prioritization Framework

> Every feature from the Phase 2 architecture set, re-sorted through the wedge decision in [`03-wedge-strategy.md`](./03-wedge-strategy.md). The Phase 2 documents describe the full destination; this document decides what actually earns a place in the first real build, and — just as importantly — what should not be built at all.

**Tiering rule:** a feature earns Tier A only if it is required for the core 30-second loop *or* required to make the Islamic-design wedge real and differentiated on day one. Everything else is sequenced by how directly it compounds the wedge versus how much it merely sounds impressive.

---

## Tier A — Must Exist (Phase 1 MVP)

| Feature | Why it's Tier A |
|---|---|
| Core canvas: vector + basic raster editing | Without this there is no product. |
| AI Designer (basic text-to-design, 2–3 draft directions) | The entire 30-second-path promise depends on this working well, not broadly. |
| AI Layout Expert + AI Typography Expert (core versions) | Minimum viable intelligence behind the AI Designer's output quality. |
| **Arabic Typography Engine** (contextual shaping, kashida justification, basic diacritics) | The wedge is not real without this. Everything else in the Islamic Suite depends on it being correct first. |
| Curated Islamic event template set + **Hijri-aware calendar integration** | Cheap to build (calendar math + curated templates), immediately reinforces the wedge, no governance dependency unlike Mushaf tooling. |
| General template library (curated, not marketplace-scale) | Table stakes for the beginner path; does not need Canva's breadth to be useful, just enough to cover common formats. |
| Basic export (web-ready raster, single/multi-page PDF) | Non-negotiable minimum utility. |
| Accounts, auth, basic cloud storage | Infrastructure floor. |
| Web app only (no desktop, no mobile yet) | See "What Phase 1 deliberately excludes" below. |

**Explicitly excluded from Tier A despite being in the Phase 2 architecture:** real-time collaboration, offline mode, desktop/mobile apps, the full ten-agent Creative Intelligence roster, Mushaf tooling, and calligraphy tools. Each is addressed below with its actual tier and the reasoning for the delay.

---

## Tier B — Competitive Advantage (Phase 2–3)

| Feature | Why it's Tier B, not A or C |
|---|---|
| Real-time collaboration (CRDT sync) | Genuinely differentiating, but the highest engineering-risk item on the entire roadmap (Phase 2 self-review) — sequencing it *after* the core editor is proven, not before, protects Phase 1's timeline. |
| AI Design Critic / Smart Design Coach | A real differentiator against every competitor (Market Opportunity Report synthesis, gap #3), but depends on enough usage data from Tier A features to be trained meaningfully. |
| AI Brand Strategist + brand kits | Needed once TASMIM serves institutions and repeat organizational users (Islamic organizations, publishers) rather than one-off individual designs. |
| Calligraphy tools (Naskh, Thuluth, Diwani, Kufic vector brushes) | Core to the wedge's full promise, but secondary to getting the Arabic Typography Engine (Tier A) right first — calligraphy without solid underlying typography is building the differentiator on a weak foundation. |
| Islamic geometric pattern generator | High wedge relevance, moderate engineering cost (parametric tessellation), reasonable to follow shortly after Tier A ships. |
| Mosque branding kits, da'wah media templates (captioning, quote cards) | Low engineering cost, high wedge reinforcement — candidates to pull *earlier* into late Tier A if Phase 1 timeline allows, but not blocking for initial launch. |
| **Mushaf publishing tools** | Architecturally and strategically core to the wedge, but explicitly gated on the scholarly governance board (Islamic Creative Suite document) being established — a trust/partnership dependency, not an engineering one. Do not let commercial pressure compress this into Tier A; do not let it silently slip to Tier C either, since delaying it indefinitely undercuts the wedge's full promise. |
| CMYK/print-fidelity export, Studio Mode precision tools | Needed to credibly serve publishers and serious institutional users, not needed for the initial 30-second-path audience. |
| Presentation Studio + AI Presentation Designer | Broadly useful, moderately wedge-relevant (conference/da'wah event decks), reasonable Phase 2 addition. |
| Bilingual Arabic-English publishing engine | Directly extends the wedge into Universities and Publishers (User Research Blueprint) — a natural Phase 2–3 expansion once Publishing Studio exists. |
| Mobile app (full parity) | Architecturally important (Master Architecture §4) and important for reach, but the shared-rendering-core dependency means it should follow, not precede, a stable web core. |
| Offline mode (CRDT-based) | Valuable for TASMIM's target markets' connectivity realities, but depends on the same CRDT infrastructure as real-time collaboration — sequence together, not before either is proven. |
| Desktop app | Professional-precision audience matters less in Phase 1 (individual/community wedge users) than in Phase 2–3 (publishers, agencies). |

---

## Tier C — Future Expansion (Phase 4–5)

| Feature | Why it waits |
|---|---|
| TASMIM Boards / full Inspiration Ecosystem | The single most exciting gap identified in the Market Opportunity Report (Pinterest has no editor), but it is also the most infrastructure-heavy feature on the entire list (vector search, trend discovery, community/social graph) and depends on a large enough user base and content corpus to be good rather than empty — building it before Phase 1–3 traction exists risks an unpopulated discovery feed, which is worse than not having one. |
| Creative Marketplace (templates/fonts/assets economy) | Needs supply (creators) and demand (users) simultaneously — a classic two-sided marketplace cold-start problem best attempted after TASMIM already has a real user base to seed it with, not before. |
| Video Studio / motion graphics | Valuable (CapCut proves the demand) but unrelated to the wedge's core differentiation and technically separable — a clean Phase 4 addition once the core platform and wedge are proven. |
| Plugin/developer API ecosystem | Only valuable once there's a large enough user base to attract third-party developers — premature before Phase 3–4 scale. |
| AI Social Media Creator (trend-aware version) | Explicitly depends on the Inspiration Ecosystem's trend discovery infrastructure (Creative Intelligence Engine §8) — cannot be meaningfully differentiated before that exists. |
| AI Marketing Assistant (analytics-integrated) | Requires external ad-platform integrations and a large enough customer base generating meaningful performance data to be useful — a later-stage feature. |
| Enterprise SSO, full approval workflows, audit logging | Necessary for large institutional and government customers (User Research Blueprint) but premature before TASMIM has any enterprise customers to serve — build in response to real deals, not in anticipation of them. |
| Multi-language localization beyond Arabic/English | Expanding language coverage before the wedge itself is proven spreads effort thin; follow usage data, don't front-run it. |

---

## Tier D — Avoid Building

Every item here is excluded deliberately, not by omission — each was either explicit in the Editorial Bible's long-term vision or an implicit temptation given the scope of the Phase 2 architecture, and each is being consciously cut.

| Feature / Temptation | Why to avoid it |
|---|---|
| Training foundation models from scratch | TASMIM's differentiation is the orchestration layer, brand memory, and vertical specialization (per Creative Intelligence Engine) — not owning a general-purpose foundation model, which is an enormously expensive, undifferentiated arms race against companies TASMIM cannot out-resource. Fine-tune and route across existing foundation models instead (see [`06-technology-stack-decision.md`](./06-technology-stack-decision.md)). |
| Competing on template-library *quantity* with Canva | Canva's 260M-user network effect makes a raw-quantity race unwinnable; compete on relevance (wedge-specific, brand-aware) instead of breadth. |
| Building an in-house type foundry | License professional Arabic and Latin type families from established foundries; type design is a multi-year specialist craft orthogonal to TASMIM's core differentiation. |
| Unattended/ambient auto-publish (from the Phase 2 "Design the Future" ambient-generation idea) | The Phase 2 self-review already flagged this as the idea most likely to feel invasive if built carelessly. Build the draft-generation half; **never** ship the auto-publish-without-review half. |
| A proprietary video encoding/rendering pipeline built from scratch | Use mature, licensable video infrastructure (e.g., FFmpeg-based pipelines, established cloud transcoding services) — building a custom video codec stack is a multi-year, high-risk specialty with no wedge relevance. |
| A crypto/NFT marketplace layer | No connection to any identified user need across ten researched audiences; a scope-creep risk common in "creator economy" platforms that adds legal and trust complexity without validated demand. |
| AR/VR or spatial-computing features | Mentioned only as directional Phase 5 speculation in the Phase 2 architecture; there is no current evidence of demand from any of the ten audiences researched, and pursuing it now would be building for a hypothetical future user rather than a real one — exactly what the project's own engineering principles warn against. |
| Owning physical cloud infrastructure/datacenters | Use established cloud providers (Master Architecture §5); owning infrastructure is a distraction from product differentiation at TASMIM's stage and scale. |
| Proprietary hardware devices | Explicitly speculative in the Phase 2 blueprint; no product-market signal justifies it, and hardware is a categorically different business with its own capital and supply-chain requirements TASMIM has no current reason to take on. |
| A general-purpose social feed unrelated to design/discovery | TASMIM Boards (Tier C) should stay scoped to design-relevant inspiration and creator community — building a broader social network would dilute focus and compete with platforms (Instagram, TikTok, Pinterest itself) far better resourced for that specific fight. |

---

## Challenging the Assumptions Baked Into Phase 2

The Phase 2 architecture set was written to describe the full destination, which means it understandably over-specifies relative to what Phase 1 needs. Three assumptions worth naming and cutting back explicitly:

1. **"Ten AI agents" was always a Phase 3+ target, not a launch requirement.** Shipping three focused agents (Designer, Layout, Typography) that work reliably beats shipping ten shallow ones. The Creative Intelligence Engine document's architecture (shared orchestrator, shared Context Graph) supports adding agents incrementally — use that, rather than trying to launch the full roster at once.
2. **"One document model across every surface" is the right long-term architecture, but does not require building desktop, mobile, and web simultaneously.** Build the shared rendering core once, ship it on web first, and let desktop/mobile follow — the architecture doesn't demand simultaneity, only a shared foundation.
3. **The Islamic Creative Suite does not need to launch complete.** The wedge strategy depends on Arabic typography and a curated event/template set being real and good at launch — it does not require calligraphy tools, the pattern generator, and Mushaf publishing all shipping in Phase 1. Sequencing the Suite's own internal features (Tier A vs. B above) matters as much as sequencing the platform's features overall.

## Removing Unnecessary Complexity

The clearest complexity-reduction opportunity is treating **Tier A as genuinely small**. A credible MVP is: one platform, one language pair (Arabic/English), three AI agents, one wedge-relevant template category done well, and a working 30-second path — not a scaled-down version of every Phase 2 document at once. Every feature above the Tier A line should be justified by "this compounds the wedge or the core loop" — anything justified only by "this is in the long-term vision" belongs in Tier B, C, or D, not in the first build.
