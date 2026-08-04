# SPACETALK UX RESEARCH, JOURNEYS, AND INFORMATION ARCHITECTURE

### Part 13 — Who We Are Building For, and What They Do

*Governed by `00-EDITORIAL-BIBLE.md`. Behaviour rules are in `03-UX-BIBLE.md`; this document holds the research programme, the user model, the journeys, and the information architecture those rules serve.*

**An honest framing, up front.** No user research has been conducted for SpaceTalk. The user model below is therefore a set of **hypotheses to be tested**, not findings to be cited. They are written as falsifiable statements with a stated test, because a persona presented as fact — invented, given a name and a stock photo, and then quoted in design reviews for three years — is one of the most reliably damaging artefacts in product development. Every hypothesis here is either confirmed by the research in §13.2 before Phase 1 ships, or revised.

---

## 13.1 — The Core Hypotheses

| # | Hypothesis | How we falsify it |
|---|---|---|
| **H1** | People notice and value messaging speed, and can be moved by it. Cold start and send latency are felt, not just measured. | Side-by-side timed task tests against incumbents; unprompted mentions of speed in post-use interviews. If nobody mentions speed unprompted, Identity Pillar 1 is not a positioning, only an engineering standard. |
| **H2** | Notification fatigue is severe enough that "quiet by default" is a reason to switch, not merely a nice property. | Diary studies of notification volume and reaction; measure whether the calm promise appears in stated switching reasons. |
| **H3** | Translation inside conversation is a daily need for a large, identifiable population — not an occasional convenience. | Field research in multilingual regions and among migrant and cross-border-business communities; frequency counts, not attitudes. |
| **H4** | Users will accept a phone-number-free, username-first identity and find people via links and QR codes. | Onboarding completion and first-conversation rates without address-book access. **This is the highest-risk hypothesis in the product** (ADR-010). |
| **H5** | Users want AI help with specific tasks (translate, catch up, transcribe) and actively dislike an assistant that speaks unprompted. | Concept tests contrasting invited versus proactive assistance; measure irritation as carefully as usefulness. |
| **H6** | Privacy is a tiebreaker, not a primary driver, for mainstream users — but it is a primary driver for an identifiable early-adopter segment large enough to launch into. | Segment-level willingness-to-switch studies. If false, the go-to-market in `11` §11.6 needs reordering, though nothing in Part 0.6 changes. |
| **H7** | Group conversations fail for structural reasons (undifferentiated urgency), and @mention-cuts-through-mute materially fixes it. | Longitudinal group-health tracking: mute rate, abandonment, and message-per-member decay over 90 days. |

**The rule:** any of these that survives Phase 1 unvalidated must be marked as unvalidated wherever it is used to justify a decision. We do not launder assumption into fact by repetition.

---

## 13.2 — The Research Programme

**Before MVP ships:**

| Method | Scope | Answers |
|---|---|---|
| Contextual inquiry | 40 participants, 4 markets, on their own devices, in their own environments | How messaging actually happens — one-handed, interrupted, on bad networks. Grounds `03` §3.12. |
| Comparative timed tasks | 30 participants | H1. Does speed register perceptually? |
| Notification diary study | 25 participants, 2 weeks | H2. Real volume, real reactions. |
| Multilingual field study | 30 participants across 3 multilingual regions | H3. Translation frequency and failure modes. |
| Onboarding usability | 20 participants, iterative | H4. The 90-second target in `03` §3.10. |
| AI concept testing | 25 participants | H5. Invited versus proactive. |
| Accessibility research | 12 participants who use screen readers, switch control, or large type daily | Not a compliance check — a design input. Run early enough to change the design, which means before the components are built. |

**Continuously, after launch:**
- Quarterly longitudinal panel (~50 users, tracked over time) — the only method that reliably catches slow degradation.
- Retention-cohort interviews with users who *left*, which is where the real information is.
- Group-health tracking (H7).
- Per-language AI quality panels, native speakers, feeding the published accuracy notes (`04` §4.10).

**Research standards.** Recruit outside our own network. Never test with a design or engineering team member facilitating their own work. Include Tier-C devices and poor networks in every session — testing on a flagship on office Wi-Fi produces conclusions that do not survive contact with the market we are entering. Publish findings internally in full, including the ones that contradict the roadmap.

---

## 13.3 — Who We Are Building For

Segments, defined by behaviour and constraint rather than by demography — and stated as hypotheses per §13.1.

**The cross-language communicator.** Talks daily with people who do not share their first language: family across borders, a small business with foreign suppliers, a migrant worker. Currently copy-pastes into a translation app, several times a day, losing tone and context each time. *This is our sharpest wedge, and translation is why they would switch.*

**The overwhelmed group member.** In fifteen groups, has muted eleven, and now misses things that matter. Wants to participate partially without either drowning or disappearing. Served by @mention-cuts-through-mute, granular mute, and the absence of engagement notifications.

**The privacy-attentive early adopter.** Already uses an encrypted messenger, cannot persuade their contacts to join it, and gives up capability for privacy today. Served by not making them choose — and reached first, because they are the segment that evaluates on architecture rather than on familiarity.

**The constrained-device user.** An entry-level phone, limited storage, a metered data plan, and an unreliable network. Currently endures an app that is slow, huge, and data-hungry. Served by every number in `08-PERFORMANCE-STANDARDS.md` — and this is the segment most likely to be quietly failed if Tier C is treated as a fallback rather than the design target.

**The broadcaster.** A creator, a teacher, a clinic, or a municipal office that needs to reach a subscribed audience reliably. Currently at the mercy of an algorithm that decides whether their announcement is seen. Served by 100 % chronological delivery (`05` §5.6).

**Who we are explicitly not building for:** people who want a social feed, an audience of strangers, short-form video, or a place to be discovered. That is not a market we are underserving by accident; it is one we are declining on purpose (`10-SCOPE-GOVERNANCE.md`).

---

## 13.4 — Primary User Journeys

Each journey states the entry point, the steps, the target time, the failure modes, and what it is worth measuring.

### J1 — First run to first message sent

**Target: under 90 seconds, four screens** (`03` §3.10).

1. Open → value statement, one line, one button. *(no carousel, no account tour)*
2. Choose a username → live availability check, suggestions on conflict.
3. Add a recovery method → phone or email, with a plain, unavoidable statement of what happens if they skip it and lose the device (`05` §5.11).
4. Display name and optional photo → skippable, and visibly so.
5. Land on an empty Chats screen with one action: *Find someone* (QR, link, or username search).
6. First conversation → first message sent.
7. **Only now** ask for notification permission, framed as "so you know when they reply" (`03` §3.9).

**Failure modes.** Username taken repeatedly (mitigate with good suggestions); no one to talk to (the entire weight of ADR-010 lands here — the empty state must offer a share link that is genuinely pleasant to send); permission denied (the app must remain fully usable, with a non-nagging path to reconsider).

**Measure:** completion rate per step, time to first message, share-link send rate, and D1 return.

### J2 — Daily glance

The highest-frequency journey in the product, run 50–150 times a day. It has three steps and must be flawless.

1. Notification or app icon → app open (**<450 ms Tier A / <1,500 ms Tier C**, `08` §8.2).
2. Conversation list, already populated from disk. No spinner, no skeleton, no shift.
3. Tap → transcript at the last-read position, rendered locally, in <120 ms.

**Failure modes.** Cold-start regression (a release gate); list jumping as network data arrives (forbidden by `03` §3.4); notification opening the wrong conversation or losing the back stack (`03` §3.1 rule 6).

**Measure:** cold start p95 by tier, notification-to-conversation latency, and any rendered-then-shifted event, which is treated as a defect rather than a metric.

### J3 — Send under bad conditions

Entry: composing on a poor or intermittent connection — the condition a large share of our users live in permanently.

1. Type; draft persists on every keystroke pause.
2. Send → bubble appears immediately with a pending glyph (**<50 ms**, local write).
3. Network absent → one quiet banner, no per-message error, no modal.
4. Reconnect → queue drains in order; ticks update in place; no announcement.

**Failure modes.** Reordering (prevented by outbox sequencing, `06` §6.8); silent loss (the worst failure in a messenger — prevented by the durable outbox and gap detection); an error-per-message storm (prevented by the severity ladder, `03` §3.5).

**Measure:** outbox drain success, message loss (target: zero, treated as correctness), and duplicate delivery (prevented by idempotency keys).

### J4 — Cross-language conversation

The journey that most defines the product's differentiation.

1. Receive a message in another language.
2. **Automatic detection** → a "Translate" affordance appears under the message. Nothing is translated without a tap the first time.
3. Tap → translation appears beneath the original, in Aurora, labelled. The original stays.
4. Offer: "Always translate this conversation?" → a persistent header indicator if accepted.
5. Reply → optionally see the translation and back-translation before sending.
6. The recipient sees that the message was translated (`04` §4.4).

**Failure modes.** No language pack (offer download over Wi-Fi, state the size); low-confidence output (label it "Rough translation" rather than presenting it as reliable); names and @mentions mangled (never translated).

**Measure:** translation invocation rate, always-on adoption, conversations sustained across a language boundary, and reported translation errors per language pair.

### J5 — Catching up on a busy group

1. Open a group with 47 unread messages.
2. A collapsed card offers "Summarise 47 messages." **Never generated automatically** (`04` §4.5).
3. Tap → summary appears above the transcript, labelled, collapsible, with each claim linked to its source message.
4. Tap a claim → jump to that message, highlighted.

**Failure modes.** A summary that misses the one thing that mattered (mitigate with per-claim source links so the user can verify in seconds, and one-tap reporting); on-device model unavailable on Tier C (offer the server path with an explicit grant, and say why).

**Measure:** summary invocation, source-link tap-through (a proxy for whether people trust it enough to check), and report rate.

### J6 — Linking a second device

1. On the new device: "Link to an existing account" → a QR code appears, valid for 60 s.
2. On the phone: Settings → Devices → Link a device → scan.
3. **Both screens show the new device's safety number**; the user confirms they match.
4. Choose history: none / 30 days / everything — **with the transfer size shown** before it starts.
5. **All existing devices receive a notification**, and a permanent entry appears in the device log (`05` §5.13).

**Failure modes.** QR expiry mid-flow (regenerate automatically, no restart); history transfer interrupted (resumable); a device the user does not recognise (the log and the notification are the defence, which is exactly why silent linking is forbidden).

**Measure:** link completion rate, time to complete, and the rate at which users actually read the device notification — because a security notification nobody reads is not a security control.

### J7 — Encountering a scam

1. A message arrives from an unknown sender → held as a **message request**: one preview, no notification sound, no delivery receipt.
2. The on-device classifier flags a known fraud pattern.
3. An inline `danger` strip states the **specific** pattern: "This message asks for a verification code. SpaceTalk never asks for one."
4. The message remains readable. We warn; we do not censor personal communication.
5. One-tap block and report; reporting states exactly what will be shared before it is shared.

**Failure modes.** A false positive on a legitimate message — the trust catastrophe this feature is most likely to cause. Precision is tracked per pattern class with automatic rollback below 95 % (`04` §4.7).

**Measure:** precision and recall per pattern, block-after-warning rate, and — the number that matters — user-reported fraud losses.

---

## 13.5 — Information Architecture

```
SpaceTalk
│
├── Chats  ─────────────────────────────  [primary destination]
│   ├── Filter chips: All · Unread · Groups · Channels
│   ├── Conversation rows (people, groups, channels, assistant — one list, by recency)
│   ├── Archived  (below the fold, never a badge)
│   └── Conversation
│       ├── Transcript
│       ├── Composer  (text · attach · voice · send)
│       ├── Conversation profile
│       │   ├── Members / contact info
│       │   ├── Media · Files · Links
│       │   ├── Disappearing messages
│       │   ├── Encryption + safety number
│       │   └── Mute · Block · Report · Leave
│       └── Search within conversation
│
├── Calls  ──────────────────────────────  [primary destination]
│   ├── History (all · missed)
│   └── Start a call
│
├── Stories  ────────────────────────────  [primary destination]
│   ├── Others' stories
│   ├── My story  (+ viewers, visible only to me)
│   └── Create  (audience chosen before posting, every time)
│
└── Settings  ───────────────────────────  [primary destination]
    ├── Profile  (username · name · photo · bio)
    ├── Privacy  (per-field visibility · read receipts · who can add me · who can call me · blocked)
    ├── Devices  (linked devices · link new · device log)
    ├── Notifications  (per type · quiet hours · previews)
    ├── Assistant  (features on/off · grants · memory · Privacy Centre)
    ├── Storage & data  (media cache · auto-download · metered-network behaviour)
    ├── Appearance  (theme · text size · language)
    └── Help & about  (privacy policy · terms · transparency report · version)
```

**Global search** is available from Chats and spans conversations, messages, media, files, and people (`03` §3.8). It is not a destination, because searching is something you do *from* somewhere.

**IA rules.**
1. **Maximum depth is three levels** from any tab. Settings → Assistant → Memory is the deepest legal path.
2. **Every conversation type is a row in one list.** A channel, a group, a person, and the assistant differ in what they contain, not in where they live. This is the single decision that keeps the app learnable.
3. **Nothing lives in two places.** If it belongs in Settings, there is no shortcut to it from a conversation that creates a second mental model.
4. **Archived is a place, not a state to be badged.** It never contributes to any count.
5. **Adding a destination requires CPO and CDO sign-off** (`03` §3.1). The default answer is no.

---

## 13.6 — Design File Specification

How design artefacts are organised so that the system in `07-DESIGN-SYSTEM.md` stays real rather than becoming a folder of stale screens.

**Structure:**

```
SpaceTalk Design (Figma)
├── 00 Foundations      Tokens as Figma variables — generated, never hand-edited
├── 01 Components       The library in 07 §7.2, every variant, every state
├── 02 Patterns         Composed patterns from 07 §7.10
├── 03 Flows            The journeys in §13.4, as connected prototypes
├── 04 Surfaces         Screen specs, per feature, per breakpoint, both themes, LTR + RTL
├── 05 Motion           Prototypes with real timings from 07 §7.7
├── 06 Explorations     Not a source of truth. Dated. Archived quarterly.
└── 07 Marketing        Brand assets per 01
```

**Rules.**
- **Tokens flow one way:** JSON source → Figma variables *and* Dart *and* CSS, generated in CI (`07` §7.1). A designer who changes a hex value in Figma has changed nothing; they must change the token source.
- **Every screen exists in four versions** — light LTR, light RTL, dark LTR, dark RTL — before it is handed off. Not "we'll check RTL later," because later means never and Arabic is a launch language.
- **Every screen is specified at default and 200 % type scale.**
- **Every interactive element is annotated** with its component name, its states, and its accessibility label.
- **Redlines are not produced by hand.** If a spec cannot be read from tokens and component names, the design is not using the system.
- **A screen not built within one quarter moves to Explorations.** A library full of unbuilt screens is a library nobody trusts.
