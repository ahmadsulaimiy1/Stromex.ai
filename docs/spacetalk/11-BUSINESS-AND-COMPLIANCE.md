# SPACETALK BUSINESS, GROWTH, AND COMPLIANCE

### Part 11 — How It Sustains Itself, and Under What Rules

*Governed by `00-EDITORIAL-BIBLE.md`, especially §0.6 clause 1 (no advertising) and ADR-009. Business decisions that conflict with Part 0.6 are void, regardless of revenue impact.*

---

## 11.1 — The Business Thesis

We are building a product whose defining qualities — calm, speed, privacy — are exactly the qualities an advertising business destroys. So the business model is chosen first and constrains everything after it, rather than being discovered later under pressure.

**Three revenue lines, in the order they arrive:**

1. **Consumer subscription (Phase 2).** People pay for more storage, larger files, and higher-quality AI.
2. **Business platform (Phase 4).** Businesses pay to have conversations with customers. Highest margin, most defensible, and structurally aligned — a business pays for a conversation the user *wanted*.
3. **Creator take rate (Phase 3).** A 10 % cut of creator earnings, deliberately below the market's 30 %, because we do not need to fund an ad business.

**What the model implies.** Free users cost money. Storage, bandwidth, and push are real per-user costs, so unit economics are a permanent product constraint, not a finance department problem. Every free-tier limit in this product exists because someone did the arithmetic, and every one of them is stated honestly in the interface rather than discovered at the moment of failure.

---

## 11.2 — Subscription Plans

| | **SpaceTalk** (free) | **SpaceTalk Plus** | **SpaceTalk Business** |
|---|---|---|---|
| Price | — | ~$4.99/mo, regionally adjusted | Per-seat + per-conversation |
| Messaging, calls, groups, channels, stories | Everything | Everything | Everything |
| File size | 2 GB | 10 GB | 10 GB |
| Media retention (server) | 90 days after last access | 1 year | Policy-controlled |
| Linked devices | 4 | 10 | Per policy |
| On-device AI | **All of it** | All of it | All of it |
| Server-assisted AI | Limited monthly allowance | Generous allowance | Pooled allowance |
| Translation language packs | 5 concurrent | Unlimited | Unlimited |
| Shared inbox, roles, analytics | — | — | Yes |
| SSO, audit logs, data residency | — | — | Yes |

**Principles that govern pricing.**

- **Nothing that protects a user is behind a paywall.** Encryption, scam detection, privacy controls, and blocking are free forever. Charging for safety is the clearest way to lose the right to call the product trustworthy.
- **Regional pricing is real pricing**, indexed to purchasing power, not a token discount. A product that intends to serve emerging markets and prices in US dollars does not actually intend to.
- **No feature is removed from the free tier once shipped.** Growth-by-degradation is a dark pattern.
- **Cancellation is one tap**, in-app, with no retention interstitial (Part 0.6 clause 6).
- **The upgrade prompt appears at the moment of the limit**, states the specific limit, and never interrupts a conversation.

---

## 11.3 — Creator Economy (Phase 3)

- **Paid channel subscriptions** and one-off supporter payments.
- **10 % platform take rate**, versus 30 % elsewhere. This is a deliberate, structural advantage that follows from ADR-009: an advertising business has to fund itself from somewhere, and we do not have one.
- **Payouts within 7 days**, in local currency, with fees stated up front.
- **No algorithmic distribution**, which means no creator ever has to guess whether the platform will show their post. 100 % subscriber delivery (`05` §5.6) is the product promise to creators, and it is the opposite of every incumbent's relationship with them.
- **Analytics report reach and engagement, never subscriber demographics** — we do not collect that data, so we cannot sell reporting built on it, and we tell creators why.
- **No exclusivity contracts, no creator fund, no promotional boosts.** Every one of those is a mechanism for the platform to pick winners.

---

## 11.4 — Unit Economics

Approximate per-user monthly cost at Phase 2 scale, which is what every free-tier limit in §11.2 is derived from:

| Cost | Free user | Plus user |
|---|---|---|
| Storage (media, ciphertext) | $0.02–0.08 | $0.15–0.40 |
| Bandwidth (egress + CDN) | $0.03–0.10 | $0.10–0.30 |
| Compute (gateway, core, push) | $0.01–0.03 | $0.02–0.05 |
| Calls (TURN/SFU) | $0.01–0.05 | $0.02–0.08 |
| Server-assisted AI | ~$0.00 (on-device) | $0.10–0.50 |
| **Total** | **~$0.07–0.26** | **~$0.39–1.33** |

**The economics work because of two architectural decisions**, and it is worth naming them: delivered message envelopes are deleted rather than archived (ADR-004), so the server does not carry the world's message history; and AI runs on-device by default (ADR-005), so the largest cost line in a modern AI product is close to zero for most usage. Privacy decisions and cost decisions turn out to be the same decisions here — which is why they are stable.

**Target:** contribution-positive per paying user from launch of Plus; company-level profitability by Phase 3 (`09` gate).

---

## 11.5 — Analytics

**What we measure:**

- Delivery success, latency percentiles, crash rate, cold start — by device tier, network profile, and region.
- Retention cohorts (D1, D7, D30, D90).
- Feature adoption as a *count of users who used it*, never as time spent.
- Funnel completion for onboarding, device linking, and subscription.
- Error and failure rates, per surface.

**What we do not measure, ever:** time in app, session count as a goal, scroll depth, message volume as a success metric, or anything about message *content*.

**How.**
- **Event data is pseudonymous and aggregated**, retained 13 months (`06` §6.13).
- **No third-party analytics SDKs in the client.** Not one. Every analytics SDK is a data-sharing relationship with a company the user never agreed to.
- **Analytics are opt-out in the EU and opt-in wherever law requires it**, with a plain-language description of every event category.
- **No event may carry message content, contact identifiers, or a precise location.** Enforced by a schema allowlist in CI — an event that adds a disallowed field fails the build.

**The governing rule:** if a metric could be improved by making the product more annoying, it is not one of our metrics. This single test eliminates almost every engagement metric in the industry.

---

## 11.6 — Growth Strategy

We have deliberately given up the industry's main growth engine (ADR-010: no address-book upload). What replaces it:

1. **Be conspicuously faster.** Speed is the most demonstrable, least explainable-away differentiator. A side-by-side launch comparison is a marketing asset that requires no argument.
2. **Share links and QR codes as the primary connection mechanism** (`03` §3.10), designed to be pleasant enough that people actually send them.
3. **Channel-led acquisition.** A creator, school, or institution brings its audience. This is why Channels is an MVP feature rather than a Phase 2 one, and why guaranteed delivery matters commercially as well as ethically.
4. **Language-first market entry.** Enter markets where translation is the daily problem, not an occasional one — multilingual regions, migrant communities, cross-border families and businesses. In those markets translation is not a feature, it is the reason to switch.
5. **Trust as a growth channel.** Published audits, a transparency report, reproducible builds, and open protocol documentation. Slow, compounding, and very hard for an ad-funded competitor to copy.
6. **No growth hacking.** No dark-pattern invites, no "your friend joined" notifications, no contact-list nagging, no fake activity. Every one of them would violate Part 0.6.

**Honest expectation:** slower early growth than a contacts-uploading competitor, with better retention per acquired user. The gate metrics in `09-ROADMAP.md` are retention metrics, not signup metrics, precisely because that is the shape we expect and the shape we want.

---

## 11.7 — Moderation Architecture

**The foundational distinction, stated plainly:** private conversations are end-to-end encrypted, so we cannot read them and therefore cannot moderate their content. Public content — channels, public group metadata, profiles, and usernames — we can and do moderate. We state this distinction clearly rather than blurring it, because blurring it is how platforms end up promising both perfect privacy and perfect safety and delivering neither.

**What we do for private conversations:**
- **User-side tools:** block (silent and complete), report (which shares only the specific reported messages, with the user told exactly what will be shared), message requests for unknown senders, and granular privacy controls.
- **Metadata-based abuse prevention** (`04` §4.7): fan-out rate, account age, block and report rates, registration patterns. This catches the overwhelming majority of spam without any content access.
- **On-device scam detection** with content never leaving the device.

**What we do for public content:**
- Reactive review of reported channels and profiles, by a trained human team with published policies and a published appeals process.
- Proactive detection limited to impersonation (name similarity at registration) and known-illegal content hashes where legally required.
- Published enforcement statistics in the transparency report.

**Child safety.** The most difficult area, and the one where we refuse to be vague. We will not build client-side scanning of private messages: it is a general-purpose surveillance capability that, once built, cannot be limited to one purpose, and the technical consensus is that it does not survive adversarial contact. What we do instead: default-private profiles for accounts registered as minors, strict limits on who may initiate contact with them, aggressive metadata-based detection of grooming *patterns* (mass contact of new accounts, rapid block accumulation), immediate reporting to the relevant authority when public content is identified, and active participation in industry information-sharing. We will state this position publicly and defend it, rather than implying a capability we have chosen not to build.

**Government requests.** Answered only through valid legal process, narrowly scoped, with the affected user notified unless legally prohibited. We publish what we were compelled to provide — and, importantly, what we were *architecturally unable* to provide. Where a jurisdiction demands a backdoor, we exit the market rather than comply. This is a Part 0.6 clause 3 consequence, and it is written down now so it is not decided for the first time under pressure.

---

## 11.8 — Internationalisation

**Launch languages (Phase 1, 12):** English, Spanish, Portuguese, French, German, Arabic, Hindi, Indonesian, Russian, Turkish, Japanese, Simplified Chinese. Chosen by target-market reach, not by convenience.

**Engineering requirements, enforced in CI:**
- **No concatenated sentences.** Every user-visible string is a complete, translatable unit with named placeholders. Building a sentence from fragments produces gibberish in most languages and is a build failure here.
- **Full ICU message format** for plurals, gender, and select cases. Languages with six plural forms are not an edge case, they are Arabic and Russian.
- **RTL is a first-class layout**, not a mirror transform (`02` §2.13). Every screen is reviewed in Arabic before it ships.
- **Locale-aware everything:** dates, times, numbers, currency, name order, calendars (Hijri and Gregorian where relevant), and week start.
- **Pseudo-localisation in CI** — every string expanded 40 % and wrapped in markers, so truncation and hard-coded strings are caught automatically rather than by a translator later.
- **Translation quality is reviewed by native speakers, per release.** Machine translation of the interface of a product whose flagship feature is translation would be indefensible.

**Content translation** is a separate concern, specified in `04-AI-PHILOSOPHY.md` §4.4.

---

## 11.9 — Legal and Compliance

| Regime | Obligation | Our position |
|---|---|---|
| **GDPR** (EU) | Lawful basis, DSARs, erasure, portability, DPO, DPIAs | Data minimisation is architectural (`06` §6.13). Export and delete are self-service (Part 0.6 clause 10). DPIA per feature touching personal data. |
| **ePrivacy** | Consent for non-essential storage | No advertising trackers exist to consent to. |
| **DSA** (EU) | Notice-and-action, transparency reporting, appeals | Applies to public content. Private messaging is out of scope, and we document why. |
| **DMA** (EU) | Interoperability if designated a gatekeeper | Phase 5. Implemented with explicit labelling of where our encryption guarantees stop (`09` Phase 5). |
| **CCPA/CPRA** (California) | Disclosure, deletion, opt-out of sale | We do not sell data. Disclosure and deletion are self-service. |
| **COPPA / age assurance** | Under-13 protections; varying regional age gates | Minimum age 13 (16 where required). Age assurance without collecting identity documents — a hard problem we will solve conservatively rather than by demanding IDs. |
| **UK Online Safety Act** | Duties of care; potential scanning pressure | Compliance with everything short of breaking encryption. Our published position on client-side scanning (§11.7) applies. |
| **Telecom / VoIP** | Per-market registration; emergency-calling rules | Market-by-market legal review before launch. **We state clearly that SpaceTalk does not support emergency calls** — a real obligation that VoIP products routinely handle badly. |
| **Payments** (Phase 4) | Licensing, KYC/AML, PCI-DSS | A separate regulated business line, launched per market. Never a feature toggle. |
| **Export control** | Cryptography export regimes | Standard notifications filed; we use published, standard algorithms. |
| **Data residency** | Regional storage requirements | Regional deployment from Phase 3 (`06` §6.10). |

**Standing commitments.**
- Terms of service and privacy policy written in plain language, at a reading level a fifteen-year-old can follow, with a summary at the top. If our own users cannot understand what they agreed to, consent is a formality rather than a fact.
- Every material change is notified in-app 30 days in advance.
- No arbitration clause that removes a user's right to a remedy.
- The privacy policy describes what we actually do, verified against the codebase annually by someone outside the team that wrote it.

---

## 11.10 — Risk Register

The things most likely to kill this product, and what we do about each.

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Network effects** — nobody switches messengers alone | High | Fatal | Channel-led and language-led acquisition (§11.6); make the switch worth it for a *pair* of people, not one |
| **Growth too slow without contact discovery** | High | Severe | Accepted cost (ADR-010); gates are retention-based, and we fund accordingly |
| **A crypto implementation flaw** | Medium | Fatal | Use libsignal, never roll our own; conformance vectors in CI; independent audit pre-launch and annually |
| **Performance promise not met on Tier C** | Medium | Severe | Budgets as release gates (`08` §8.11); physical device lab; quarterly performance week |
| **On-device AI quality below expectation** | Medium | Moderate | Honest per-language accuracy notes (`04` §4.10); explicit-grant server path for users who want it |
| **Abuse at scale without content moderation** | Medium | Severe | Metadata detection, message requests, on-device classifiers, fast reporting (§11.7) |
| **Regulatory pressure to break encryption** | Medium | Fatal if conceded | Published position; exit a market rather than comply (§11.7) |
| **A big-tech competitor copies the calm positioning** | Medium | Moderate | They cannot: their revenue depends on the machinery we refuse to build. This is the structural moat. |
| **Team dilutes the standards under growth pressure** | **High** | **Fatal, slowly** | This Bible, the amendment process (`00` §0.10), and gates that are evidence-based rather than calendar-based. Every product in this category lost this fight by degrees, and the loss was never a single decision. |

The last row is the one to take most seriously. No competitor will beat SpaceTalk in a way that is visible on a dashboard. The realistic failure is thirty small, individually reasonable compromises over four years, at the end of which the product is another loud messenger with an AI tab. That is what the constitution in Part 0 exists to prevent, and it only works if people actually invoke it.
