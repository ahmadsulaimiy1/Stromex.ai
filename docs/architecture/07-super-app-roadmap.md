# TASMIM Super App Roadmap

> Timelines below assume a well-resourced, funded team scaling from a focused founding group to a full multi-discipline org. They are planning targets, not commitments — treat every duration as a range to be re-validated against actual hiring, funding, and technical discovery. See the risk notes at the end of each phase, and the fuller critical assessment in [`08-design-the-future-and-self-review.md`](./08-design-the-future-and-self-review.md).

**Sequencing principle:** do not attempt to out-template Canva or out-precision Figma or out-discover Pinterest simultaneously. Win one defensible wedge first (the combination of AI-first creation + the Islamic Creative Suite, per the Feature Matrix summary), then expand outward from a real, retained user base.

---

## Phase 1 — MVP (Months 0–6)

**Goal:** prove the core loop — AI-assisted creation that a beginner finishes in seconds and a professional doesn't immediately abandon.

**Scope:**
- TASMIM Studio (web only) — core canvas, vector + basic raster editing.
- AI Designer + AI Layout Expert + AI Typography Expert (3 of 10 agents) — enough to deliver the 30-second path from the Experience Design System.
- Template library (curated, not yet marketplace-driven).
- Basic export (web-ready raster formats; PDF for single-page).
- Basic Islamic Creative Suite wedge: Arabic typography engine + a curated Islamic event template set (not yet Mushaf tools or calligraphy — those are Phase 2+, gated by the governance board being established, see §06).
- Single-player only — no real-time collaboration yet (deliberately deferred; see dependency note).

**Priorities:** rendering engine correctness and performance over feature breadth; a small, sharp AI agent set over a large mediocre one.

**Dependencies:** the shared rendering core (Master Architecture §3) must exist before *any* other client is started — building web, desktop, and mobile against three different renderers now would be the single most expensive architectural mistake TASMIM could make.

**Key risks:** underestimating how hard a professional-grade rendering engine is to build well (this is a multi-year specialty even for well-funded teams); scope creep from trying to include collaboration or marketplace too early.

---

## Phase 2 — Professional (Months 6–14)

**Goal:** close the "professional never feels limited" gap — Affinity/CorelDRAW-level precision plus real collaboration.

**Scope:**
- Full vector/raster precision parity with the Feature Matrix's Section A targets, including CMYK/print export.
- Real-time collaboration (CRDT sync service goes live) — the highest-engineering-risk item on the entire roadmap; budget accordingly.
- TASMIM Desktop (native shell, offline-capable).
- TASMIM Mobile (beta) — read/comment first, full editing parity targeted by end of phase.
- Remaining Creative Intelligence agents expand to 6–7 of 10 (add AI Art Director, AI Brand Strategist, AI Design Critic — the Smart Design Coach becomes live).
- Islamic Creative Suite: calligraphy tools and the geometric pattern generator ship; Mushaf publishing tools begin development *only after* the scholarly advisory board (§06 governance requirement) is formally in place — this is a hard dependency, not a scheduling nicety.
- Brand kits and basic team workspaces.

**Priorities:** collaboration reliability (no data loss, no silent conflicts) over collaboration feature richness.

**Dependencies:** Phase 1's rendering core must be stable and performant before layering CRDT sync on top — real-time collaboration amplifies any existing rendering bugs into multiplayer-visible ones.

**Key risks:** real-time collaboration at Figma's level of polish took Figma's team years with deep systems expertise; treat this as the phase most likely to slip, and protect its timeline by cutting other Phase 2 scope before cutting collaboration quality.

---

## Phase 3 — Enterprise (Months 14–24)

**Goal:** become viable for organizations, not just individuals.

**Scope:**
- Team workspaces with roles/permissions, approval workflows, and version history at the depth described in the Feature Matrix §C.
- Enterprise SSO/SAML, audit logging, brand-lock governance controls.
- Publishing Studio (multi-page/book layout, AI Publishing Assistant) reaches GA.
- Mushaf publishing tools reach GA, gated on the governance board's sign-off (carried over from Phase 2).
- Full Creative Intelligence roster complete (all 10 agents) — AI Presentation Designer, AI Marketing Assistant, AI Social Media Creator round out the set.
- Offline architecture (Master Architecture §7) hardens from "basic local cache" to full CRDT offline-first parity across desktop and mobile.
- Marketplace opens in limited beta (templates and fonts only, to validate trust/payment flows before broader creator-economy scope).

**Priorities:** security and compliance posture (SSO, data residency, audit trails) — enterprise sales cycles stall hard without these, regardless of how good the creative tools are.

**Dependencies:** the Creative Context Graph (Master Architecture §6) must support org-level (not just individual) memory partitions before brand-lock governance can work correctly — a schema decision that should be made in Phase 1, not retrofitted here.

**Key risks:** enterprise security/compliance is its own specialist discipline (SOC 2, data residency across regions, GCC-specific data-protection law given the Islamic Suite's core market) — underinvesting here blocks the exact institutional customers (mosques, universities, publishers) the Islamic Suite is meant to win.

---

## Phase 4 — Global Platform (Months 24–36)

**Goal:** turn the product into a platform — discovery, creator economy, and developer ecosystem at scale.

**Scope:**
- TASMIM Boards (Inspiration Ecosystem) launches in full — boards, trend discovery, creator profiles, Inspiration-to-Design conversion.
- Marketplace expands to the full creator-economy scope (illustrations, brand kits, presentation and publishing layouts) with creator payouts and licensing.
- TASMIM Video (motion graphics, reels, ads) ships as its own product line.
- Plugin/API ecosystem opens externally (Master Architecture §3 sandboxed WASM runtime, previously internal-only).
- Full mobile/desktop feature parity achieved and maintained as an ongoing SLA, not a one-time milestone.
- Localization expands beyond Arabic/English to additional priority languages based on Phase 1–3 usage data.

**Priorities:** trust and safety infrastructure (marketplace fraud prevention, IP-violation reporting, content moderation for the community/discovery layer) must ship *alongside* the growth features that create the need for it, not after.

**Dependencies:** the Vector Search / style-embedding infrastructure (shared between the Inspiration Ecosystem and the Creative Intelligence Engine's Art Director agent, per §05) needs to already be operating at Phase 1–3 scale internally before it can support a public discovery feed's traffic and quality bar.

**Key risks:** creator marketplaces are notoriously hard to bootstrap (chicken-and-egg supply/demand); plan a seeded/curated launch (invite verified creators first) rather than an open floodgate, and budget real trust-and-safety headcount before opening broadly — this is a frequently underestimated cost center.

---

## Phase 5 — Creative Operating System (Months 36+)

**Goal:** the long-term goal stated in the Editorial Bible — "a complete creative operating system where ideas move seamlessly from inspiration to publication," the benchmark by which future design software is measured.

**Scope (directional, not committed):**
- Cross-product AI memory spans every surface seamlessly — a brand's Creative Context Graph informs everything from a social post to a printed book to a video ad without re-briefing the AI.
- Deep third-party ecosystem integrations (OS-level share-sheet integration, CMS/e-commerce publishing connectors, potential AR/spatial exploration for presentation and event branding).
- Global creator economy operating at meaningful scale, with TASMIM functioning as genuine income infrastructure for professional creators, not just a marketplace feature.
- Enterprise-grade reliability and support at Fortune 500 / large-institution scale.

**Priorities:** this phase is explicitly aspirational and should be re-planned from actual Phase 1–4 outcomes, not from this document — five-year platform bets made before Phase 1 ships are a planning exercise, not a roadmap.

**Key risks:** the biggest risk in Phase 5 isn't technical, it's strategic drift — a "creative operating system" ambition can justify building almost anything; the discipline required is saying no to adjacent opportunities that don't reinforce the one-document-model, AI-native, Islamic-Suite-anchored identity established in Phases 1–3.

---

## Cross-Phase Scalability Considerations

- **Cost architecture for AI inference** must be designed from Phase 1, not retrofitted: the Model Router's tiering (on-device → fast specialist → large foundation model, Master Architecture §6) is what keeps a 10-agent AI system economically viable at consumer pricing — without it, AI cost scales linearly with usage in a way that breaks a freemium model.
- **Render farm elasticity:** video/print export spikes (seasonal — Ramadan/Eid content, back-to-school, year-end reports) should be load-tested against realistic seasonal demand curves specific to TASMIM's core markets, not generic SaaS traffic assumptions.
- **Data residency:** GCC and broader MENA data-protection requirements (relevant given the Islamic Suite's core audience) should inform region selection in the Cloud Architecture (Master Architecture §5) well before Phase 3's enterprise push, since migrating a live customer's data residency after the fact is far more expensive than provisioning for it upfront.
