# THE SPACETALK ROADMAP

### Part 9 — Five Phases

*Governed by `00-EDITORIAL-BIBLE.md`. Every phase states its mission, what it builds, what it explicitly does not build, its team shape, and the gate that must be passed before the next phase begins. Phases are gated by evidence, not by calendar.*

**The rule that makes this roadmap real:** a phase does not begin because the previous one ran out of time. It begins because the previous one met its gate. If a gate is missed, the response is to fix the product, not to move on to the next phase and hope.

---

## Phase 1 — MVP (Months 0–12)

**Mission.** Prove that a communication app can be *dramatically* faster and calmer than the incumbents, with intelligence that actually helps, and that people will move to it for those reasons alone.

**Build.** Exactly the thirteen features in `05-FEATURE-BIBLE.md` — secure messaging, voice notes, voice calls, video calls, groups (≤1,000), channels, stories, AI assistant, file sharing, search, profiles, notifications, multi-device (≤4).

Platforms: iOS, Android, and the Flutter web build as the linked-device client (ADR-012).

Infrastructure: one region, warm standby, the four Go deployables (ADR-002), Postgres + Redis + object storage.

AI at MVP: **on-device only, plus the assistant conversation.** Reply suggestions, tap-to-translate, voice transcription, semantic search, scam detection — all local. Server-side AI features exist only as the assistant conversation, clearly labelled.

**Explicitly NOT in Phase 1:**
- Native desktop clients — the web client covers the need (ADR-012).
- Call summaries, live captions, live translation — quality is not there, and shipping them badly damages the AI promise more than omitting them.
- Payments, mini-apps, commerce, marketplace, bots, an API — every one of these is a platform, and a platform on top of an unproven product is a way to fail at two things.
- Groups above 1,000 — a protocol limit we are honest about (ADR-003).
- Threads, polls, roles, permissions, communities — Phase 2, once we know how groups actually get used here.
- Reels, feeds, discovery, recommendation — rejected permanently (`10-SCOPE-GOVERNANCE.md`).
- Address-book upload (ADR-010).
- Multi-region, Kubernetes, microservices (`06` §6.10).

**Team shape.** ~14 people: 4 client engineers, 4 backend, 1 security/crypto, 1 ML, 2 design, 1 product, 1 ops.

**Gate to Phase 2 — all four must be true:**
1. **D30 retention ≥ 40 %** for users who sent a message in their first week.
2. **Every number in `08-PERFORMANCE-STANDARDS.md` met on Tier-C hardware**, in production, at p95.
3. **A completed third-party security audit** of the cryptographic implementation, with all high and critical findings resolved, published.
4. **Qualitative evidence that the calm promise holds** — notification opt-out below 10 %, and users describing the product as fast and quiet in unprompted research.

Not a gate: signup count, DAU, or time-in-app.

---

## Phase 1 — Execution Sequence

The build order matters, because the dependencies are real and several of them are one-way doors. Quarters are indicative; the ordering is not.

**Q1 — Foundations that cannot be retrofitted.**
Protobuf schemas and the protocol versioning scheme (`06` §6.4). The libsignal FFI binding with its conformance harness in CI from the first commit — if this integration is going to fail, we need to know in month one, not month eight. The token pipeline (`07` §7.1) and the component library skeleton. Local database schema and migration framework, with forward-migration tests against synthetic historical databases. The gateway and `core` skeletons with authentication. **Physical device lab operational.** Pre-MVP research from `13-UX-RESEARCH-AND-JOURNEYS.md` §13.2 runs in parallel throughout.

*Exit:* two devices exchange an encrypted message end to end, over the real protocol, with conformance tests green.

**Q2 — The core loop, at quality.**
Messaging (`05` §5.1) complete: transcript, composer, delivery states, reply, react, edit, delete, disappearing. Offline sync and the outbox (`06` §6.8). Push with content-free payloads (ADR-007). Groups with Sender Keys. Onboarding (J1) and profiles. Performance budgets enforced in CI from the first transcript commit — retrofitting performance into a shipped list is the mistake this ordering exists to prevent.

*Exit:* J1, J2, and J3 complete on Tier-C hardware within budget. Internal dogfooding begins and does not stop.

**Q3 — Everything real-time, plus the differentiator.**
Voice and video calls (1:1 first, then small groups). Voice notes. File sharing. Multi-device linking (J6). Then the AI layer: on-device translation (J4), transcription, reply suggestions, semantic search, and scam detection (J7). AI comes after the core loop deliberately — it is the differentiator, but it is worthless bolted onto a messenger that is not yet excellent.

*Exit:* all thirteen features functionally complete. Third-party security audit begins.

**Q4 — Hardening, not features.**
No new features. Performance work against every budget in `08`. Accessibility passes with real screen-reader users. Full localisation into the twelve launch languages with native-speaker review. Load testing to 10× projected launch traffic. Chaos testing. Security-audit findings resolved and the audit published. Staged rollout: internal → closed beta → open beta → general availability.

*Exit:* the four Phase 1 gate conditions below.

**Standing rules for Phase 1.** Dogfood from Q2 — the team uses SpaceTalk as its primary messenger, which is the only reliable way to notice the small daily failures. No feature merges without its budget met (`08` §8.11). No quarter adds a fourteenth feature; the MVP boundary is `00` §0.8 and it is not negotiated during execution.

---

## Phase 2 — Public Beta and Depth (Months 12–24)

**Mission.** Take the proven core to a wider audience, add the depth that daily users are actually asking for, and prove the infrastructure holds at 10× the load.

**Build.**
- **Native desktop** (macOS, Windows, Linux) from the Flutter codebase; unlimited history sync to linked devices.
- **Groups get depth:** threads, polls, admin roles and permissions, group descriptions, member-level muting, and the moderation tooling that group owners have by then told us they need.
- **Messaging depth:** scheduled send, pinned messages, formatted text, per-conversation themes, custom notification sounds, quiet hours.
- **Calls:** group voice to 32, group video to 32, screen sharing, on-device background blur, **live captions**, and call summaries with per-participant consent (`04` §4.5).
- **Channels:** scheduled posts, drafts, multi-admin, richer analytics, paid subscriptions.
- **AI:** the first server-assisted features under the explicit-grant model (ADR-005) — unread summaries, higher-quality translation for language pairs where on-device quality is insufficient. **Passkeys** for recovery.
- **Business, first version:** verified business profiles, a customer-conversation inbox, and away messages. No CRM, no automation, no payments — just "a business can be talked to properly."
- **Infrastructure:** a second region for latency, read replicas, the first module extraction if §6.10 triggers fire. Bug bounty opens. First transparency report.

**Explicitly NOT in Phase 2:** payments, mini-apps, marketplace, an open bot API, groups above 1,000, live translation.

**Team shape.** ~40 people. Trust & safety becomes a real function, not a rotation.

**Gate to Phase 3:**
1. **1 M monthly active users**, with D30 retention holding ≥ 40 % at scale.
2. **Performance budgets held at 10× load** — the numbers must not have drifted.
3. **Subscription conversion ≥ 3 %** with positive contribution margin per paying user (`11` §11.4).
4. **Zero unresolved critical security findings**, and no privacy incident in the preceding two quarters.

---

## Phase 3 — Creator Tools and Protocol Maturity (Months 24–42)

**Mission.** Let people who broadcast to an audience make a living inside SpaceTalk, and finish the protocol work that the first two phases deliberately deferred.

**Build.**
- **Creator monetisation:** paid channel subscriptions, one-off supporter payments, and a **10 % platform take rate** — deliberately below the market's 30 %, because we do not need to fund an advertising business (ADR-009 has a revenue upside as well as a cost).
- **Live audio broadcast** to channel subscribers. Not a social audio product — a channel format.
- **Creator analytics** that report reach and engagement without profiling subscribers, because we do not collect the data that would allow richer reporting, and we say so.
- **Protocol maturity:** **MLS migration** (ADR-003), lifting the group ceiling and improving the multi-device story; **hybrid post-quantum key agreement** (X25519 + ML-KEM-768); federated on-device search across a user's own linked devices.
- **AI:** live call translation (the flagship Phase 3 capability), cross-device assistant memory.
- **Communities:** groups of groups, events, shared membership — the WeChat/Discord shape, arrived at from the messaging side rather than the server side.
- **Infrastructure:** multi-region with data residency, ScyllaDB migration if triggered, regional TURN and SFU fleets.

**Explicitly NOT in Phase 3:** general-purpose payments, an app platform, commerce, dating, gaming.

**Gate to Phase 4:** 10 M MAU · creator earnings meaningful enough that creators describe SpaceTalk as a primary channel · MLS migration complete with no regression in delivery or latency · profitability on a unit-economics basis.

---

## Phase 4 — Business Platform (Months 42–66)

**Mission.** Become the channel through which businesses and institutions talk to people — the highest-margin, most defensible revenue in messaging, and the one that does not require becoming an advertising company.

**Build.**
- **Business API** (the public HTTP/JSON surface deferred since `06` §6.4) for customer messaging, notifications, and support, priced per conversation.
- **Business tooling:** shared team inboxes, assignment and routing, templates, quick replies, business hours, and conversation-level analytics.
- **AI for businesses:** draft assistance, auto-summarised support threads, and language coverage — all under the same consent rules as consumers, with no exception for commercial context.
- **Payments, carefully and regionally:** in-conversation payment requests and receipts, launched market by market with real licensing and real compliance, never as a global switch-flip.
- **Verified institutional accounts** for schools, health services, and government — the use cases where guaranteed delivery to subscribers (`05` §5.6) is worth the most.
- **Enterprise-grade controls:** audit logs, retention policies, SSO for business accounts, regional data residency.

**Explicitly NOT in Phase 4:** advertising (permanently), a social feed (permanently), a general app store, cryptocurrency of any kind.

**Gate to Phase 5:** business revenue exceeding consumer subscription revenue · regulatory approvals held in the top five markets · no degradation of any consumer-facing performance or privacy standard as a result of business features. That last gate is the important one — the failure mode of every messaging platform that added a business layer is that the consumer product got worse.

---

## Phase 5 — Platform Ecosystem (Months 66+)

**Mission.** Let third parties build inside SpaceTalk — under rules strict enough that the product does not become the thing it was built to replace.

**Build.**
- **Mini-apps**, sandboxed, with a permission model in which an app can see only what the user explicitly hands it, and **never** the conversation it is invoked from unless the user passes specific content to it.
- **A bot API** for legitimate automation, with strict, published rate limits and no ability to initiate contact with a user who has not opted in. The absence of unsolicited bot contact is a feature, and it is the reason to keep the API narrow.
- **Interoperability**, where regulation requires it (EU Digital Markets Act) — implemented honestly, with clear labelling of which conversations cross to another provider and therefore leave our encryption guarantees. Users must never be misled about where a promise stops applying.
- **Open protocol documentation** and reproducible clients, so the security claims are independently verifiable.
- **Institutional deployments** — education, healthcare, government — with the compliance posture each requires.

**Permanent boundaries at every phase.** These are the things that do not arrive at Phase 6:

- No advertising.
- No algorithmic feed of strangers.
- No content moderation of private conversations.
- No mini-app that can read a conversation.
- No feature whose success metric is time-in-app.

---

## Cross-Phase: What Never Changes

| Standard | Phase 1 | Phase 5 |
|---|---|---|
| Cold start (Tier C, p95) | < 1,500 ms | < 1,500 ms |
| E2EE default for personal messages | Yes | Yes |
| AI without explicit grant on private content | Never | Never |
| Notifications from non-humans | Zero | Zero |
| Primary navigation destinations | 4 | 4 |
| Advertising | None | None |

The infrastructure required to hold these standards changes enormously between Phase 1 and Phase 5. The standards themselves do not change at all. That is what makes them standards.
