# SpaceTalk — The Editorial Bible

**SpaceTalk is a communication space that is fast, quiet, and private, in which intelligence is ambient, invited, and accountable.**

*Room to talk.*

This directory is the constitution of the product. It governs every design, engineering, brand, and business decision. Where any document, roadmap, ticket, mockup, or opinion conflicts with `00-EDITORIAL-BIBLE.md`, that document wins until formally amended.

---

## Read in this order

| # | Document | What it governs |
|---|---|---|
| **00** | [Editorial Bible](00-EDITORIAL-BIBLE.md) | Purpose, mission, vision, values, design philosophy, the ten non-negotiables, the MVP boundary, the decision rules |
| **01** | [Brand Bible](01-BRAND-BIBLE.md) | Personality, voice, naming, logo, photography, illustration, icons, animation philosophy |
| **02** | [Visual Design System](02-VISUAL-DESIGN-SYSTEM.md) | Every colour with HEX and measured contrast, type, spacing, grid, radius, elevation, glass, dark/light, accessibility |
| **03** | [UX Bible](03-UX-BIBLE.md) | Navigation, interaction, motion, loading, errors, empty states, offline, search, notifications, onboarding, one-handed use |
| **04** | [AI Philosophy](04-AI-PHILOSOPHY.md) | The privacy/intelligence tension and its resolution; suggestions, translation, summaries, transcription, scam detection, memory, transparency |
| **05** | [Feature Bible](05-FEATURE-BIBLE.md) | All thirteen MVP features: purpose, problem, metrics, UI, edge cases, failure cases, roadmap |
| **06** | [Technical Bible](06-TECHNICAL-BIBLE.md) | Flutter client, Go backend, API, database, auth, push, encryption, offline sync, caching, scaling, monitoring, testing, CI/CD, security ops |
| **07** | [Design System](07-DESIGN-SYSTEM.md) | Tokens, component inventory, motion tokens, gestures, transitions, patterns, contribution rules |
| **08** | [Performance Standards](08-PERFORMANCE-STANDARDS.md) | Cold launch, frame rate, latency, memory, battery, network, media, accessibility, stability — and the budget process |
| **09** | [Roadmap](09-ROADMAP.md) | Five phases, each with what it builds, what it refuses to build, and its evidence-based gate |
| **10** | [Scope Governance](10-SCOPE-GOVERNANCE.md) | Every proposed feature from the full ecosystem brief, scheduled to a phase or rejected with a reason |
| **11** | [Business & Compliance](11-BUSINESS-AND-COMPLIANCE.md) | Revenue, subscriptions, creator economy, unit economics, analytics, growth, moderation, i18n, legal, risk register |
| **12** | [Architecture Decision Records](12-ADR.md) | The twelve decisions with lasting consequence, with alternatives and accepted costs |
| **13** | [UX Research, Journeys & IA](13-UX-RESEARCH-AND-JOURNEYS.md) | The research programme, the user hypotheses, seven primary journeys, the information architecture, and the design-file specification |

---

## The short version

**Three things this product is allowed to be known for** (`00` §0.7): the fastest messaging experience, the most useful intelligence inside communication, and the cleanest interface in the category.

**Thirteen MVP features** (`05`): secure messaging · voice notes · voice calls · video calls · groups · channels · stories · AI assistant · file sharing · search · profiles · notifications · multi-device.

**The stack** (`06`, `12`): Flutter on every client · Go modular monolith · PostgreSQL, Redis, object storage · Signal Protocol via libsignal · local-first SQLite with an outbox · LiveKit SFU with E2EE for calls.

**The five decisions everything else follows from:**

1. **No advertising, ever** (ADR-009) — which is why there is no feed, no ranking model, and no profiling pipeline.
2. **AI runs on-device by default and never touches encrypted content without a visible, revocable grant** (ADR-005).
3. **Delivered messages are deleted from the server, not archived** (ADR-004) — a privacy decision that turns out to also be what makes the economics work.
4. **No address-book upload** (ADR-010) — the largest deliberate growth cost in the product, taken with open eyes.
5. **Performance budgets are release gates** (`08` §8.11) — not dashboards, not tickets.

---

## Notes on scope

**On the founding brief.** This project began with a brief asking for every feature of WhatsApp, Telegram, Facebook, Instagram, Discord, Signal, and WeChat, plus payments, healthcare, education, commerce, and a creator studio. That brief also contained its own correction: design the full ecosystem, ship a focused MVP, validate, then expand. `10-SCOPE-GOVERNANCE.md` is that correction made operational — the full ecosystem is designed and triaged there, every item either scheduled to a phase or rejected with a stated reason. Nothing was silently dropped, including the ideas we declined.

**On this repository.** SpaceTalk is treated here as a **new product line**, distinct from the existing StromeX AI knowledge-work product also in this repository. StromeX's documentation (`docs/00-STROMEX-*` onward) and its application code are untouched. The reasoning, and the alternative, are recorded in **ADR-011** — which flags an open question for the founder: *if SpaceTalk is intended as a rename of StromeX rather than a second product, ADR-011 is wrong and must be superseded*, starting with `00-EDITORIAL-BIBLE.md` §0.1, because the two products have different missions, users, and architectures.

**On research.** No user research has been run yet. `13-UX-RESEARCH-AND-JOURNEYS.md` states the user model as seven falsifiable hypotheses with a test for each, rather than as invented personas presented as findings. H4 — that users will accept username-first identity with no address-book access — is the highest-risk assumption in the product, and it follows directly from ADR-010.

**On what is documentation and what is built.** Everything in this directory is specification. No SpaceTalk application code has been written yet; the numbers in `08-PERFORMANCE-STANDARDS.md` are budgets to be defended, not measurements taken. The one exception is the colour system in `02-VISUAL-DESIGN-SYSTEM.md`: every contrast ratio quoted there was computed against the WCAG relative-luminance formula, and one accessibility claim was measured, found false, and corrected rather than shipped (see §2.15).
