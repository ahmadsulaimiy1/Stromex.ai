# THE SPACETALK EDITORIAL BIBLE

### Part 0 — The Constitution

*Version 1.0. This document governs every design, engineering, brand, and business decision made about SpaceTalk. Where any other document, roadmap, ticket, mockup, or opinion conflicts with this one, this one wins until it is formally amended. Amendments require a written rationale appended to Part 0.10 and sign-off from the CEO, CPO, and CDO.*

---

## 0.1 — Purpose

**SpaceTalk exists to give people back the feeling of talking to someone.**

Messaging apps are now the highest-traffic software on earth, and almost all of them have drifted away from that purpose. They have accumulated feeds, stores, games, discovery tabs, badge counts, and engagement machinery until the act of sending a message to a person you care about is surrounded by things designed to keep you from leaving. The interfaces have grown louder while the conversations have not grown better.

At the same time, a genuine capability arrived — language models that can translate, summarise, recall, transcribe, and detect fraud in real time — and it has been bolted onto those products as a chatbot in a tab, or as a mascot that interrupts. Nobody has yet built a communication product where intelligence is *part of the medium* rather than a passenger inside it.

SpaceTalk is the correction to both drifts. It is a communication space that is fast, quiet, and private, in which intelligence is ambient, invited, and accountable.

## 0.2 — Mission

To build the fastest, calmest, most trustworthy way for people to talk — and to make useful intelligence a native property of conversation rather than a product bolted onto it.

## 0.3 — Long-Term Vision

By 2036, SpaceTalk is the default communication layer for hundreds of millions of people who chose it deliberately — not because their family was already there, but because using anything else feels like going back to a slower, noisier machine. The language barrier is, in practice, gone inside SpaceTalk. Fraud and impersonation are meaningfully harder here than anywhere else. The app has not grown a feed, and it has not grown an advertising business.

The proof of success is negative as much as positive: in 2036 SpaceTalk still opens in under a second, still has fewer than five primary destinations, and a person who learned it in 2027 still knows where everything is.

## 0.4 — Values

| Value | What it means in practice |
|---|---|
| **Calm** | The product never manufactures urgency. No engagement notifications, no streaks, no "someone you may know," no red badge for anything that isn't addressed to you. |
| **Speed as respect** | Latency is a moral property, not a technical one. Every millisecond we spend is a millisecond of someone's life. |
| **Privacy by construction** | We design so that we *cannot* read what we promise not to read. Policy is a weaker guarantee than architecture, and we prefer the stronger one. |
| **Invited intelligence** | AI acts when asked, or when it has explicit standing permission. It never inserts itself into a conversation on its own initiative. |
| **Legibility** | A user should always be able to answer: what just happened, who can see this, and why am I seeing it. |
| **Restraint** | The hardest work in this product is deletion. Every feature we do not ship is a feature nobody has to learn. |
| **Craft** | Nothing ships that we would not be happy to have screenshotted and compared, pixel for pixel, against the best software in the world. |

## 0.5 — Design Philosophy

**Content is the interface.** Chrome recedes; messages, faces, and voices are the only things allowed to be visually loud.

**Typography before decoration.** Hierarchy is established with type, weight, and space. Colour is used to encode meaning — state, identity, danger — not to entertain.

**Motion explains, never performs.** Every animation answers "where did this come from and where did it go." An animation that does not explain something is deleted.

**One-handed by default.** The primary market holds the phone in one hand, often while doing something else. Anything a user does more than five times a day must be reachable by a thumb.

**Dark mode is not a theme, it is a first-class design.** Both modes are designed, not derived. Neither is an inversion of the other.

**The same product on every screen.** A user who learns SpaceTalk on a 5-inch Android phone should not have to relearn it on a desktop. Layouts adapt; concepts do not.

## 0.6 — Non-Negotiable Principles

These are the clauses that may not be traded away for growth, revenue, a deadline, or a competitor's feature launch. Violating one of these is grounds for reverting a release.

1. **No advertising business, ever.** Not banner ads, not sponsored messages, not "promoted" contacts, not a discovery surface sold to brands. The moment attention is the product, calm is impossible. Revenue comes from subscriptions and from businesses paying to use the platform (see `11-BUSINESS-AND-COMPLIANCE.md`).
2. **No algorithmic feed of strangers.** SpaceTalk shows you what you subscribed to and who talked to you, in the order it happened. There is no engagement-ranked timeline of people you did not choose.
3. **Personal messages are end-to-end encrypted by default and cannot be silently downgraded.** There is no "off" switch we can flip server-side, and no key-escrow backdoor for any party, including us.
4. **AI never reads an end-to-end encrypted conversation without an explicit, revocable, per-conversation grant from the user, shown in the interface.** Silent processing of private content is a firing offence, not a bug.
5. **Notifications are for humans addressing you.** The system may never notify a user to drive re-engagement.
6. **No dark patterns.** No confirm-shaming, no hidden unsubscribe, no fake scarcity, no interstitial upsell between a user and a message.
7. **Data minimisation.** We do not collect metadata we do not operationally need, and we delete what we no longer need on a published schedule.
8. **No feature ships that regresses cold-start, frame rate, or crash-free-session targets** (`08-PERFORMANCE-STANDARDS.md`). Performance is a release gate, not a follow-up ticket.
9. **Accessibility is a launch requirement.** WCAG 2.2 AA and platform screen-reader parity for every shipped surface — not a Phase 2 item.
10. **The user owns their data and can export and delete all of it**, in a machine-readable format, without contacting support.

## 0.7 — Identity: The Only Three Things

SpaceTalk is allowed to be known for exactly three things. Every roadmap review asks which of the three a proposal strengthens; a proposal that strengthens none of them is rejected regardless of merit.

1. **The fastest messaging experience in the world.** Measured, published, and defended (see `08`).
2. **The most useful intelligence ever integrated into communication** — translation, recall, summarisation, and fraud protection that work inside the conversation.
3. **The cleanest, most enjoyable interface in the category.** Learnable in ninety seconds, still elegant after five years of feature pressure.

Everything else — stories, channels, files, profiles — is *supporting cast*. Supporting cast is held to a lower ambition ceiling and a higher deletion risk. This is deliberate.

## 0.8 — The MVP Boundary

The first public version ships exactly this, and nothing else:

Secure messaging · Voice notes · Voice calls · Video calls · Group conversations · Channels · Stories · AI assistant · File sharing · Search · Profile system · Notifications · Multi-device support.

Feature specifications are in `05-FEATURE-BIBLE.md`. The full triage of every rejected and deferred idea — including the large "build everything from every app" ambition that this project began with — is in `10-SCOPE-GOVERNANCE.md`. The scope register is a permanent, maintained document; ideas are not silently dropped, they are recorded with a reason and a phase.

## 0.9 — Decision Rules

When a decision is genuinely close, apply these in order. They are ordered; a higher rule overrides a lower one.

1. **When uncertain, choose simplicity.** The simpler version can be made powerful later. The complex version can almost never be made simple later.
2. **When two features compete, ship the one with the better experience**, even if the other tests better on engagement.
3. **When a feature exists only because a competitor has it, delete it.** "Parity" is not a user problem.
4. **When performance and beauty conflict, performance wins.** A beautiful interface that stutters is not beautiful.
5. **When cleverness and usability conflict, usability wins.** Nobody has ever loved a product for being clever at them.
6. **When privacy and capability conflict, privacy wins by default — and the capability may be offered as an explicit, informed, revocable choice.** We do not decide for the user, and we do not decide *quietly*.
7. **When a decision cannot be reversed cheaply, take the reversible path** and buy time to learn.

## 0.10 — Amendments

| # | Date | Clause | Change | Rationale | Approved by |
|---|---|---|---|---|---|
| — | — | — | Ratified v1.0 | Founding document | CEO / CPO / CDO |

---

**Document map.** `01` Brand · `02` Visual Design System · `03` UX · `04` AI Philosophy · `05` Features · `06` Technical · `07` Design System · `08` Performance · `09` Roadmap · `10` Scope Governance · `11` Business & Compliance · `12` ADRs.
