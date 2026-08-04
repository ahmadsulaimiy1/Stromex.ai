# SPACETALK SCOPE GOVERNANCE

### Part 10 — The Full Ambition, Triaged

*Governed by `00-EDITORIAL-BIBLE.md` §0.8 and §0.9. This is the permanent register of every idea proposed for SpaceTalk. Nothing is silently dropped. Each entry is either **scheduled** to a phase or **rejected** with a stated reason.*

---

## 10.1 — Why This Document Exists

The founding brief for this project asked for every feature of WhatsApp, Telegram, Facebook, Instagram, Discord, Signal, and WeChat, plus payments, healthcare, education, commerce, government services, a creator studio, and an AI companion — all at once.

That brief describes an ecosystem worth roughly a decade of work by thousands of engineers, and it contains genuinely good ideas. It also contains, in its final paragraph, its own correction: *design the full ecosystem, then identify a focused MVP, validate it, and expand in stages.* This document is that correction made operational.

**The honest engineering assessment**, stated once so it does not need repeating:

- **WeChat's superapp was not built as a superapp.** It shipped as a messenger in 2011 and did not add mini-programs until 2017 — six years and hundreds of millions of users later. The platform was built on the distribution the messenger earned, not the other way round.
- **Every product that launched as an ecosystem failed as one.** Users adopt one thing at a time. A product that is thirty things is not adopted at all; it is browsed once.
- **The binding constraint is not ambition, it is quality per feature.** A team that builds thirteen features builds them well. The same team building sixty builds sixty poor ones, and in a communication product a poor feature is not neutral — it makes the app slower, larger, and harder to learn for every user, including the ones who never touch it.
- **Some of the requested items are not features, they are companies.** "Payments" is a licensing, compliance, fraud, and treasury organisation. "Healthcare" is a regulated business under HIPAA, GDPR Article 9, and dozens of national regimes. Calling them features on a roadmap is the clearest sign a plan is not real.

So: the full ecosystem is designed here. The MVP is thirteen features. The path between them is `09-ROADMAP.md`.

---

## 10.2 — How to Read the Register

| Verdict | Meaning |
|---|---|
| **MVP** | In `05-FEATURE-BIBLE.md` |
| **P2 / P3 / P4 / P5** | Scheduled to that phase in `09-ROADMAP.md` |
| **Rejected** | Will not be built. Reason stated. Reversing a rejection requires a Part 0.10 amendment. |

---

## 10.3 — WhatsApp-Class Features

| Feature | Verdict | Reasoning |
|---|---|---|
| Personal messaging, voice/video calls, groups | **MVP** | The core. |
| Broadcast channels | **MVP** | Shipped as Channels (`05` §5.6), chronological and unranked. |
| Status / Stories | **MVP** | Shipped without viewer counts or a ring above the inbox (`05` §5.7). |
| Disappearing messages | **MVP** | Per-conversation setting. |
| Multi-device sync | **MVP** | Per-device keys, no primary device (ADR-012). |
| Message editing, reactions | **MVP** | With visible edit history. |
| HD media | **MVP** | Original-quality sending is a first-class option, not buried. |
| Polls | **P2** | Genuinely useful in groups; needs group depth first. |
| Live location | **P2** | High value, real privacy design work — auto-expiry, granular audience, no historical trail retained. |
| Screen sharing | **P2** | Needs the group-call infrastructure that Phase 2 builds. |
| Communities (groups of groups) | **P3** | Requires MLS and moderation tooling to be honest at scale. |

---

## 10.4 — Telegram-Class Features

| Feature | Verdict | Reasoning |
|---|---|---|
| Advanced search | **MVP** | On-device, local-first (`05` §5.10). |
| Multiple accounts on one device | **P2** | Common in our target markets; needs multi-identity key management done carefully. |
| Scheduled messages, drafts | **P2** | Cheap, useful, no architectural cost. |
| Folder organisation | **P2** | Only if research shows users actually have enough conversations to need it. Not assumed. |
| Massive groups / supergroups | **P3** | Blocked on MLS (ADR-003). We publish the 1,000 cap rather than pretending otherwise. |
| Voice chat rooms | **P3** | As a channel format, not a social-audio product. |
| Live streaming | **P3** | Channel-owner broadcast only. |
| Bots | **P5** | With a permission model where a bot cannot initiate contact. |
| Mini Apps | **P5** | Sandboxed, no conversation access. The last thing we build, not the first. |
| **Unlimited cloud storage** | **Rejected as stated** | It is not free, and "unlimited" is a promise funded either by advertising (ADR-009 forbids it) or by subscribers cross-subsidising a small number of heavy users. We ship honest, stated limits with a paid tier instead. |
| **Secret chats as a separate mode** | **Rejected** | All personal chats are already E2EE by default. A separate "extra secure" mode implies the default is not secure, which teaches users exactly the wrong thing. Per-device isolation ships as a property, not a mode. |

---

## 10.5 — Facebook-Class Features

| Feature | Verdict | Reasoning |
|---|---|---|
| Friends / social graph | **Rejected** | We have contacts and subscriptions. A bidirectional friend graph exists to power a feed and a recommendation engine, and we are building neither (Part 0.6 clause 2). |
| **News Feed** | **Rejected — permanently** | The single most consequential rejection in this document. A ranked feed of strangers is structurally incompatible with §0.6 clause 2 and with the entire calm thesis. It is also the mechanism by which every product in this category became the thing users complain about. |
| Pages | **P4** | As verified business profiles, not as a content-publishing surface. |
| Groups | **MVP** | Already core. |
| Events | **P3** | Inside communities, where they belong. |
| Marketplace | **Rejected** | A classifieds business with its own fraud, trust, logistics, and payments problems. It is a company, not a feature. Commerce arrives, if at all, through business messaging in Phase 4. |
| Watch / Gaming | **Rejected** | Video content and games are attention businesses. Directly contrary to §0.4. |
| Dating | **Rejected** | An entirely different product with an entirely different safety model. Bundling it would compromise both. |
| Fundraising | **P5** | Only if payments infrastructure exists and the compliance burden is already carried. |
| Memories | **Rejected** | Resurfacing old content is engagement machinery wearing sentiment as a costume, and it has real capacity to hurt people. |
| Professional mode | **P4** | As part of business profiles. |

---

## 10.6 — Instagram-Class Features

| Feature | Verdict | Reasoning |
|---|---|---|
| Stories | **MVP** | Deliberately capped (`05` §5.7). |
| Broadcast channels | **MVP** | Shipped as Channels. |
| Live streaming | **P3** | Channel format. |
| Creator tools & analytics | **P3** | Reach and engagement, without subscriber profiling. |
| Collaborative posts | **P3** | Co-authored channel posts. |
| Professional dashboards | **P4** | Business tooling. |
| **Reels / short-form video** | **Rejected — permanently** | The purest expression of the attention economy. Requires a recommendation engine, which requires a behavioural profile, which requires the data collection we have forsworn. It would also, on its own, make the app slower, larger, and louder for every user. |
| **Posts / grid / carousels** | **Rejected** | A permanent public content surface is a social network. Stories cover ephemeral sharing; channels cover broadcast. |
| Shopping | **Rejected** | See Marketplace. |
| Filters / AR effects | **P3, minimal** | Background blur in calls (on-device) and basic crop/rotate. No face filters — they are a content-platform feature and a heavy client cost. |

---

## 10.7 — Discord-Class Features

| Feature | Verdict | Reasoning |
|---|---|---|
| Roles and permissions | **P2** | For groups, at the level groups actually need. |
| Voice channels | **P3** | As persistent group voice rooms inside communities. |
| Moderation tools | **P2 (channels) / P3 (communities)** | For public content only. Private conversations are never moderated because they cannot be read — a distinction we state plainly (`05` §5.6). |
| Stage events | **P3** | Channel live audio. |
| Screen sharing | **P2** | Already scheduled. |
| **Servers as the primary structure** | **Rejected** | Discord's server model is excellent for communities and hostile to one-to-one conversation. Our atomic unit is the conversation (`03` §3.1). Communities arrive in Phase 3 built on that unit, not replacing it. |
| Gaming integrations | **Rejected** | A different product for a different audience. |

---

## 10.8 — Signal-Class Features

| Feature | Verdict | Reasoning |
|---|---|---|
| E2EE by default | **MVP** | Same protocol family, same guarantees (ADR-003). |
| Safety-number verification | **MVP** | With mandatory acknowledgement on change. |
| Sealed sender | **P3** | Genuine metadata reduction. Requires careful abuse-prevention design, since it removes a signal we use for spam. |
| Private contact discovery | **P3 research** | ADR-010 explains why we ship *no* address-book upload rather than a hashed one that leaks. |
| Post-quantum key agreement | **P3** | Hybrid X25519 + ML-KEM-768, on the roadmap with a date rather than in the marketing today. |
| **"Stronger privacy than Signal"** | **Rejected as a claim** | Signal's model is excellent and we adopt its protocol. We differ in some places (phone-optional identity is stronger; on-device AI is a capability they lack) and are weaker in others (they have years of audits and a non-profit structure that removes commercial pressure). Claiming superiority we have not earned would be exactly the kind of unearned confidence §0.4 forbids. We will let audits speak. |

---

## 10.9 — WeChat-Class Features

| Feature | Verdict | Reasoning |
|---|---|---|
| Business messaging | **P4** | The commercially strongest item in this entire register, and the reason to build a business platform at all. |
| Payments | **P4, region by region** | Requires licensing, treasury, fraud operations, and per-market compliance. Launched as a real business line, never as a feature toggle. |
| Booking / ordering | **P5** | Via mini-apps, not as first-party features. |
| Government services | **P4, partnership-led** | Verified institutional accounts (`09` Phase 4). Guaranteed delivery to subscribers is genuinely valuable here. |
| Healthcare | **Rejected as a first-party product; P4 as a channel** | We will not build medical records, telemedicine, or prescriptions. We will let a verified health service message its patients — which is the 80 % of the value at 2 % of the regulatory burden. |
| Education | **Rejected as a first-party product; P4 as a channel** | Same reasoning. A school broadcasting to parents through a verified channel is high value. An LMS is a different company. |
| Transport | **Rejected** | No plausible connection to communication. |
| Mini Apps | **P5** | Sandboxed (`09` Phase 5). |

---

## 10.10 — The "Invent New Features" List

| Proposal | Verdict | Reasoning |
|---|---|---|
| AI companion that summarises, translates, transcribes, detects scams, searches | **MVP** | This is the assistant (`04`, `05` §5.8) — built on-device first. |
| AI that writes replies | **MVP, as suggestions only** | Drafts, never sends (`04` §4.2 rule 4). |
| AI that schedules meetings, organises files, answers from past conversations | **P4** | Requires an assistant-actions permission model that does not exist yet. |
| Universal real-time translation in chats | **MVP** (chats) / **P3** (calls) | Text now; calls when latency and quality justify it (`04` §4.4). |
| AI search by memory, person, image, location, object | **MVP, partially** | On-device semantic and literal search. Image and object search are **P3** and on-device only. **Emotion search is rejected** (`04` §4.11). |
| **Universal communication** (text → voice → video → livestream → webinar → community → course) | **Partially scheduled, mostly rejected as framed** | Text↔voice↔video switching is **MVP** and genuinely good. Video→livestream is **P3**. Livestream→webinar→community→course is a chain of increasingly different products; "one click turns a chat into a course" is a slide, not a specification. |
| AI Camera | **Rejected** | A camera "smarter than any social media camera" is a content-platform feature. We need a camera that captures quickly and reliably. |
| AI Creator Studio (generate posts, reels, podcasts, ads, logos, presentations) | **Rejected** | A creative-tools company. It has no dependency on being a messenger, which is the clearest possible sign it belongs in a different product. |
| AI Business Platform (CRM, invoices, orders, marketing automation) | **P4, narrowly** | Shared inbox, templates, and analytics. Not CRM, not invoicing, not marketing automation — those are SaaS categories with entrenched incumbents. |
| Commerce platform (stores, subscriptions, auctions, escrow, delivery) | **Rejected** | Multiple companies. |
| Deepfake detection | **P4 research** | We will not advertise a capability we cannot measure (`04` §4.7). |
| Quantum-resistant cryptography | **P3** | Scheduled with a specific algorithm (ADR-003, `06` §6.7). |
| Wearables, Smart TVs, cars | **P3, minimal** | Watch: notify and reply. TV: calls only. Car: platform standards (CarPlay/Android Auto), never a custom interface. |

---

## 10.11 — Rejections That Will Be Re-Proposed

These will come back — from a growth team, an investor, or a competitor's launch. They are rejected permanently, and the counter-argument is written here so it does not have to be re-derived under pressure:

| Proposal | The pitch | The answer |
|---|---|---|
| A feed | "Users spend hours in feeds; we're leaving engagement on the table." | Engagement is not our metric (`11` §11.5). A feed requires a ranking model, which requires a behavioural profile, which requires the data collection ADR-009 and Part 0.6 forbid. It also permanently changes what the app is. |
| Ads, "just tastefully" | "One sponsored channel wouldn't hurt." | It would create an incentive to build more inventory, and that incentive never reverses. ADR-009. |
| Short-form video | "It's where attention is." | It is where attention is *taken*. Rejected in §10.6. |
| Read-your-messages AI | "Competitors do server-side AI and it's much better." | It is better, and it voids the promise. ADR-005 gives users the choice explicitly instead. |
| Address-book upload | "Growth is 3× slower without it." | Correct, and accepted (ADR-010). |
| Streaks and gamification | "Retention would go up." | Retention through manufactured obligation is the definition of a dark pattern (Part 0.6 clause 6). |
| Unlimited free storage | "Telegram does it." | Telegram's economics are not ours, and "unlimited" is never true. §10.4. |
| A crypto token | "Payments, but decentralised." | Adds regulatory risk, volatility, and fraud surface to a product whose entire value is trust. |

---

## 10.12 — The Process for Adding Anything

1. **Which of the three identity pillars does it strengthen** (`00` §0.7)? If none: rejected, no further discussion.
2. **What is its performance budget** (`08` §8.11)? A feature without one is not specified.
3. **What is its row in the AI privacy table** (`04` §4.9), if it touches user content?
4. **What does it cost every user who never uses it** — in binary size, cold start, memory, and cognitive load on the navigation? This question kills more proposals than any other, and it is the one most often skipped.
5. **Can a team of our current size build *and maintain* it at the quality bar?** If not, it is deferred to a phase where the answer is yes, or rejected.
6. **What are we deleting to make room?** Not always required — but asked every time, because a product that only adds is a product that is getting worse.
