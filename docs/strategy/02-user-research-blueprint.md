# TASMIM User Research Blueprint

> Ten primary audiences, evaluated on pain points, tools they actually use today, what remains unmet, and where TASMIM has a genuine (not aspirational) opportunity. This is a research *plan structure* to validate with real interviews before Phase 1 ships — not a substitute for talking to actual users, which the self-review in the Phase 2 architecture set already flagged as a precondition, not an afterthought.

---

## Students

- **Pain points:** no budget for paid tools; assignments require polished output (posters, presentations, reports) with zero design training; time pressure means no patience for a learning curve.
- **Existing tools:** Canva (free tier), Google Slides/PowerPoint, PicsArt, phone-native photo editors.
- **Unmet needs:** genuinely free access to AI-assisted design that doesn't feel like a stripped-down trial; help meeting academic formatting requirements (citations, reference-page layout) that general design tools ignore entirely.
- **TASMIM opportunity:** a real free tier (not a time-boxed trial) targeting the 30-second path for common academic formats, plus Publishing Studio's structure-aware layout for reports/theses — a use case none of the ten competitors in the Market Opportunity Report specifically serve.

## Teachers

- **Pain points:** create classroom materials, worksheets, and presentations constantly, with almost no design training and minimal time; need to produce the same material in multiple formats (print handout, slide, parent-facing flyer).
- **Existing tools:** Canva for Education, Google Slides, PowerPoint, worksheet-generator sites.
- **Unmet needs:** one input producing multiple correctly-formatted outputs (a lesson plan becoming a handout, a slide deck, and a parent newsletter without re-authoring three times); curriculum-aware AI that understands educational content structure, not just generic layout.
- **TASMIM opportunity:** the AI Presentation Designer and AI Publishing Assistant's "one brief, many formats" pattern (see [`../architecture/04-creative-intelligence-engine.md`](../architecture/04-creative-intelligence-engine.md)) applies directly here; Canva for Education is the incumbent to unseat, not an open field — see Wedge Strategy discussion.

## Schools (as institutions)

- **Pain points:** need brand-consistent materials across many individually low-skilled staff authors (every teacher and admin making flyers); no governance over what gets published under the school's name; licensing/procurement budgets are small relative to enterprise software.
- **Existing tools:** Canva for Education/Teams, shared template folders, print shops for anything formal.
- **Unmet needs:** brand-lock enforcement (Enterprise Mode, see [`../architecture/03-experience-design-system.md`](../architecture/03-experience-design-system.md)) at a price point schools can actually afford — most "enterprise governance" tooling in the market is priced for corporations, not K-12 budgets.
- **TASMIM opportunity:** a school-tier Enterprise Mode with brand governance at education pricing is a genuine gap; the ten competitors analyzed either lack governance tooling entirely (Canva's is comparatively thin) or price it for enterprise, not education, budgets.

## Universities

- **Pain points:** far more complex publishing needs than K-12 — research papers, journals, conference materials, multi-department brand variation, bilingual (often Arabic-English in TASMIM's core markets) publications; departments frequently go outside sanctioned tools entirely, fragmenting brand consistency.
- **Existing tools:** Adobe Creative Cloud (design/comms departments), Word/LaTeX (research output), Canva (informal/social use), print vendors for prospectuses and formal publications.
- **Unmet needs:** long-document, citation-aware publishing with real collaboration, bilingual layout support, and brand governance that spans dozens of semi-autonomous departments.
- **TASMIM opportunity:** Publishing Studio plus the bilingual Arabic-English publishing engine ([`../architecture/06-islamic-creative-suite.md`](../architecture/06-islamic-creative-suite.md), §8) is a strong fit for universities in TASMIM's core geographic markets specifically — a genuinely underserved combination, though this is a higher-complexity, longer-sales-cycle segment better suited to Phase 3 (Enterprise) than Phase 1.

## Small Businesses

- **Pain points:** need to look professional across social media, print, and signage with no design staff and minimal time or budget; brand consistency erodes fast when whoever's available makes each individual asset.
- **Existing tools:** Canva (overwhelmingly dominant in this segment), PicsArt, Adobe Express, freelancers on Fiverr/Upwork for anything higher-stakes.
- **Unmet needs:** an AI system that actually remembers the business's brand across every asset without the owner re-explaining it each time — the Creative Context Graph's core value proposition, and a real gap even against Canva's Magic Studio, which does not persist brand memory across sessions the way TASMIM's architecture is designed to.
- **TASMIM opportunity:** the AI Brand Strategist agent is close to a direct answer to this pain point, but small business is Canva's single strongest, most defended segment (260M MAU, deep template network effects) — a hard, not open, fight. See Wedge Strategy for why this is not the recommended first beachhead.

## Marketing Agencies

- **Pain points:** manage many clients' brand systems simultaneously; need fast production of on-brand, multi-format campaigns; approval workflows with clients are constant friction; tool-switching between design, presentation, and video software slows delivery.
- **Existing tools:** Adobe Creative Cloud (professional output), Figma (campaign/web mockups), Canva (fast turnaround work), CapCut (short-form video), plus separate project-management tools for approvals.
- **Unmet needs:** one platform spanning graphic design, presentation, video, and publishing with per-client brand governance and a real approval workflow — agencies currently stitch together 3–5 tools to cover what one coherent platform could.
- **TASMIM opportunity:** this is the clearest expression of the "one document model" architectural bet (Master Architecture, cross-cutting principle) — but it's a Phase 3 (Enterprise workflow/governance) fit, not a Phase 1 fit, and agencies are a discerning, high-switching-cost segment that will not move on an unproven MVP.

## Islamic Organizations

- **Pain points:** need Arabic typography, calligraphy, and Islamic-calendar-aware content (Ramadan, Eid, Hajj season, Mawlid) that mainstream tools handle poorly or not at all; Mushaf-adjacent and liturgical content requires accuracy and religious sensitivity no general design tool is built to respect; often multilingual (Arabic + English or other local languages) with layout needs mainstream tools don't support well.
- **Existing tools:** Canva (with generic Arabic font support, no calligraphy or Mushaf tooling), CorelDRAW (used informally by some sign/print shops in the region for its vector precision), print vendors, and — for anything liturgically sensitive — manual work by specialists outside any mainstream design software entirely.
- **Unmet needs:** everything specified in the Islamic Creative Suite ([`../architecture/06-islamic-creative-suite.md`](../architecture/06-islamic-creative-suite.md)) — none of it exists in a mainstream product today, per the Market Opportunity Report's synthesis (gap #4, the only gap with zero competitive response from any of the ten companies analyzed).
- **TASMIM opportunity:** this is the strongest, most defensible opportunity in this entire blueprint precisely because it is not contested — see Wedge Strategy recommendation. The tradeoff, addressed head-on in the Islamic Suite's governance section, is that this audience is also the least tolerant of error, making it high-reward and genuinely high-responsibility at once.

## Publishers

- **Pain points:** long-document layout at scale (books, journals, magazines, newspapers), multi-author/multi-editor collaborative workflows, print-production fidelity (CMYK, bleed, resolution), and — for publishers in TASMIM's core markets — frequent need for Arabic or bilingual typesetting that most modern publishing software treats as an edge case.
- **Existing tools:** Adobe InDesign (the entrenched standard), Affinity Publisher, CorelDRAW for some print-production workflows, and specialized Arabic-typesetting software for anything liturgical or classical-Arabic-heavy.
- **Unmet needs:** InDesign-equivalent long-document precision with real-time collaboration (InDesign has neither collaboration nor AI-native assistance) and native, non-afterthought Arabic/bilingual typesetting.
- **TASMIM opportunity:** Publishing Studio plus the Arabic Typography Engine directly targets this, but InDesign's decades of entrenchment among professional publishers (Market Opportunity Report, Adobe section) means this segment requires a genuinely superior, trusted product before switching costs are worth paying — a Phase 3+ segment, not a Phase 1 wedge.

## Social Media Creators

- **Pain points:** need constant, fast, multi-format content (Story, Reel, feed post, carousel) that stays on-brand without becoming repetitive; trend-awareness is time-consuming to track manually; most have no formal design training.
- **Existing tools:** Canva, CapCut, PicsArt, Adobe Express, plus manually following trend accounts on the platforms themselves.
- **Unmet needs:** trend-aware generation tied to an actual discovery feed (not a static template library) and one-brief-to-many-formats generation that doesn't require manually resizing and re-laying-out each platform variant.
- **TASMIM opportunity:** the AI Social Media Creator agent plus TASMIM Boards' trend discovery (Creative Intelligence Engine §8, Inspiration Ecosystem §3) is a strong structural fit, but this segment is heavily served today (Canva, CapCut, PicsArt all compete hard here) — a valuable expansion audience, not a low-competition entry point.

## Government Institutions

- **Pain points:** public communications (announcements, campaigns, multilingual civic information) must meet accessibility and brand-governance standards; procurement cycles are slow and security/compliance-driven; frequently need Arabic-first or bilingual public communication in TASMIM's core regional markets.
- **Existing tools:** Adobe Creative Cloud (where design staff exist), Canva for government-tier accounts, print vendors, and — often — outdated internal tools or outsourced agencies for anything beyond basic materials.
- **Unmet needs:** accessibility-by-default output (the Smart Design Coach's accessibility checking, [`../architecture/03-experience-design-system.md`](../architecture/03-experience-design-system.md) §5), data residency and security guarantees for a sensitive customer class, and native Arabic-first public communication tooling.
- **TASMIM opportunity:** real, but this is the slowest-moving, highest-compliance-bar segment on this list (procurement cycles, security certification, data residency — see Roadmap Phase 3 dependencies) — appropriate as a mid-to-late Enterprise-phase target, not an early one, despite genuine product fit.

---

## Cross-Audience Pattern

Two things are true across all ten audiences simultaneously, and the tension between them is the actual strategic question this research blueprint exists to surface:

1. **The audiences with the clearest, most immediate product-market fit for TASMIM's differentiated features (Islamic Organizations, Publishers, Universities) are institutional, slower-moving, and lower-volume than the audiences with the fastest adoption cycles (Students, Small Businesses, Social Media Creators).**
2. **The audiences with the fastest adoption cycles are also the most heavily contested by well-capitalized incumbents** (Canva above all) **and the least differentiated by TASMIM's unique architecture** — a student or small business's core need (fast, free, easy) is served adequately, if not perfectly, by Canva today.

This tension is resolved directly in [`03-wedge-strategy.md`](./03-wedge-strategy.md): the recommended wedge deliberately favors depth of differentiation over speed of initial adoption, on the reasoning that TASMIM cannot win a volume race against Canva's existing 260M-user base, but can win an unowned category outright.
