# THE SPACETALK AI PHILOSOPHY

### Part 4 — Intelligence Inside a Private Medium

*Governed by `00-EDITORIAL-BIBLE.md`, especially clauses 0.6.3 and 0.6.4. This is the hardest document in the Bible, because it governs the one place where two of our promises genuinely pull against each other.*

---

## 4.1 — The Central Tension, Stated Plainly

We promise that personal messages are end-to-end encrypted and that we cannot read them. We also promise the most useful intelligence ever put inside a communication product. Useful intelligence requires plaintext.

Most companies resolve this by quietly weakening the first promise, and describing the result in language vague enough to survive a press cycle. We will not do that. Our resolution has three parts, in strict priority order:

1. **Do it on the device.** If a model small enough to run locally can do the job at acceptable quality, it runs locally and the plaintext never leaves. This is the default, and it is where we invest first.
2. **If it cannot be done on the device, ask — specifically, per conversation, revocably, and visibly.** A user may grant server-side assistance for a particular conversation. The grant is shown persistently in the conversation header, is revocable in one tap, and is disclosed to the *other* participants in that conversation, because their words are involved too.
3. **If neither is acceptable, the feature does not ship.** There is no third path where we process private content quietly because it would make a metric go up.

**The assistant conversation itself is a different surface with different rules**, and we say so in the interface. When you talk *to* the assistant, you are talking to a server. That conversation is encrypted in transit and at rest, is retained under a published schedule, is never used to train a model without opt-in, and is visibly marked as *not* end-to-end encrypted. Pretending otherwise would be the more comfortable lie, and it is the one thing that would permanently destroy the brand.

---

## 4.2 — Principles

1. **Invited, never volunteered.** The assistant does not speak unless addressed, or unless it has standing permission for a specific job the user configured.
2. **In the medium, not beside it.** Intelligence appears as a property of a message — a translation under it, a summary at the top of an unread run — rather than as a chatbot the user must visit.
3. **Always attributable.** Any text a model produced is visually distinct (Aurora, per `02-VISUAL-DESIGN-SYSTEM.md` §2.1 rule 3) and labelled. A user must never be uncertain whether a person or a machine wrote something.
4. **Suggestion, never substitution.** The assistant never sends a message on the user's behalf. Draft, always; send, never — not with a delay, not with a confirmation, not as a setting.
5. **Calibrated, not confident.** When the model is unsure, the interface says so in plain words. We do not launder uncertainty through fluent prose.
6. **Fast or absent.** An AI feature that adds perceptible latency to a core interaction is removed from that interaction. Nothing about intelligence may make messaging slower (Part 0.9 rule 4).
7. **Fully disableable.** A user can turn every AI feature off, permanently, in one setting, and the product remains complete. If turning AI off breaks the app, we built the app wrong.
8. **No training on private content by default.** Ever. Opt-in only, per surface, with a plain-language description of what that means.
9. **The assistant has no persona** (`01-BRAND-BIBLE.md` §1.4). No name, no personality, no emotional performance, no "I'm so happy to help." Warmth comes from being useful.
10. **Refusals are explained.** When the assistant will not do something, it says why in one sentence and, where possible, offers what it can do.

---

## 4.3 — Reply Suggestions

**What it is.** Up to three short, contextually plausible replies offered above the composer.

**Where it runs.** On-device only, always. This is the highest-frequency AI surface in the product and the one closest to private content — it is not worth any server round trip, either in latency or in trust.

**Rules.**
- Appears only when the last message is from someone else and is plausibly answerable in a short reply.
- Never for messages classified as sensitive (grief, medical, conflict, financial). Suggesting "Sounds good!" under a death in the family is the kind of error that ends a product's reputation, and the classifier is tuned to be over-cautious here by design.
- Suppressed entirely for the first 3 messages of any new conversation — the opening of a relationship is not ours to autocomplete.
- Tapping a suggestion **inserts it into the composer**; it does not send. The user always presses send (§4.2 rule 4).
- Suggestions inherit the conversation's language, including code-switching.
- One tap dismisses them for that conversation; two dismissals in a week disables them globally with a quiet confirmation, because the user has told us twice.

**Success metric.** Acceptance rate is *not* the target — a high acceptance rate could mean we are making conversation more generic. The target is: no measurable increase in time-to-reply, and a dismissal rate below 15 %.

---

## 4.4 — Translation

The feature we expect to matter most, and the one most likely to define the product.

**Three modes:**

| Mode | Where it runs | Behaviour |
|---|---|---|
| **Tap to translate** | On-device (downloadable language pack) | A translation appears beneath the original in Aurora. The original is never replaced. |
| **Always translate this conversation** | On-device where a pack exists; server with explicit grant otherwise | Every incoming message arrives with a translation attached. Indicated persistently in the header. |
| **Translate what I send** | On-device or granted server | Shows the translation *and* a back-translation before sending, so the sender can sanity-check what the other person will read. |

**Rules.**
- **The original is always present and always primary.** Translation is an annotation, never a replacement. Tap the translation to collapse it.
- **The recipient is told a message was translated**, and by which side. Hidden translation creates a false impression of shared fluency.
- **Confidence is shown for low-confidence output** — "Rough translation" is an honest and useful label.
- **Names, @mentions, code, and numbers are never translated.**
- **Language packs download over Wi-Fi by default**, are 20–60 MB each, and are removable. We do not silently consume a metered connection.
- **Live call translation is Phase 3, not MVP.** Doing it badly is worse than not doing it, and doing it well requires latency work we will not have finished.

---

## 4.5 — Summaries

**Unread summaries.** When a user opens a conversation with more than 30 unread messages, a collapsed card offers "Summarise 47 messages." It is never generated automatically — generating it automatically would mean processing content the user may not have wanted processed, and would burn compute on conversations nobody opens.

**Group call summaries (Phase 2).** Opt-in per call, with an unmistakable indicator visible to every participant for the entire call, and a consent prompt for each participant on join. Recording or summarising people who did not agree is not a feature we will ship in any jurisdiction, regardless of what local law permits.

**Rules.**
- Summaries are always labelled, always collapsible, and always sit above the transcript without displacing it.
- A summary links each claim back to the specific message it came from — one tap jumps to the source. An unverifiable summary is worse than no summary.
- Summaries never include content from messages that were deleted or that disappeared.
- The user can regenerate, and can report a bad summary in one tap.

---

## 4.6 — Voice Transcription and Smart Search

**Transcription.** Every voice note offers a transcript, generated **on-device** by default. It is available to the sender before sending (so they can check what will be understood) and to the recipient on demand. Recipients in loud environments, deaf and hard-of-hearing users, and people who simply read faster than they listen all benefit; this is an accessibility feature that happens to use a model.

**Smart search.** Literal search always runs first and is never slowed by anything here (`03-UX-BIBLE.md` §3.8). Semantic search is a second, clearly-labelled result group built from an **on-device** embedding index over locally-held messages. Server-side semantic search over private content is not built, because it cannot be built without breaking §4.1.

The practical consequence, stated honestly: semantic search covers only what is on this device. A user searching a five-year-old conversation from a newly linked device will not find it semantically until that history syncs. We accept that limitation rather than resolve it by uploading plaintext.

---

## 4.7 — Spam, Scam, and Fraud Protection

**This is the most valuable AI in the product**, and it must work without reading private conversations.

**How it works within the encryption boundary:**

- **Signals we can legitimately use, server-side:** account age, message *fan-out* rate (how many distinct new recipients an account contacts per hour), the ratio of messages sent to unknown parties versus known contacts, block and report rates, registration patterns, and device attestation. All of these are metadata we necessarily process to route messages — none require reading content.
- **Content-based detection runs on the device.** A small local classifier examines *incoming* messages from senders not in the user's contacts and flags known fraud patterns: advance-fee requests, one-time-passcode phishing, romance-scam scripts, fake-delivery lures, crypto-recovery scams, and impersonation of SpaceTalk itself. The model runs locally; the message never leaves the device for this purpose.
- **Reporting is user-initiated and consent-based.** If a user reports a message, that specific message is shared with us — with a clear statement that it will be. Nothing is exfiltrated silently.

**Interface behaviour.**
- A flagged message shows an inline warning strip in `danger`, above the message, stating the *specific* pattern: "This message asks for a verification code. SpaceTalk staff never ask for one."
- The user can always read the message. We warn; we do not censor personal communication.
- Unknown senders are held in a **message request** state — one preview, no delivery receipt, no notification sound — until accepted. This single mechanism defeats most spam without any model at all.
- **False positives are worse than false negatives here.** A warning on a legitimate message from a grandmother is a trust catastrophe. The threshold is set conservatively and every flag type is tracked for precision, with a rollback trigger if precision drops below 95 % for any pattern class.

**Deepfake and impersonation detection** is explicitly Phase 4 research, not an MVP claim. We will not advertise a capability we cannot measure.

---

## 4.8 — Conversation Memory

**Default: off. Scope: the assistant conversation only.**

The assistant may remember facts you tell it *in the assistant conversation* — your timezone, your preferred language, that you are planning a trip in March. It does not build a profile from your private conversations with other people. That would require the plaintext access that §4.1 forbids.

**Rules.**
- **Memory is a list, not a black box.** Settings → Assistant → Memory shows every stored item as a plain sentence, with when it was learned and from where.
- **Every item is individually deletable**, and there is a single "forget everything" control.
- **Nothing is remembered silently.** When the assistant stores something, it shows a small, non-modal "Remembered: you prefer metric units" that can be undone in one tap.
- **Memory never crosses accounts**, and it never crosses into what other people can see.
- **Memory is exportable** in the standard data export.
- **Deletion is real deletion** — removed from the store and from any index within 24 hours, verified by an automated audit job, not by policy alone.

---

## 4.9 — Privacy Boundaries (the definitive table)

| Surface | Runs where | Sees plaintext | Default | Consent |
|---|---|---|---|---|
| Reply suggestions | Device | Local only | On | Disable in settings |
| Tap-to-translate | Device | Local only | On demand | Per tap |
| Always-translate a conversation | Device, or server with grant | Server only with grant | Off | Per conversation, both parties informed |
| Voice-note transcription | Device | Local only | On demand | Per note |
| Smart (semantic) search | Device | Local only | On | Disable in settings |
| Unread summary | Device if feasible; server with grant | Server only with grant | Off | Per invocation |
| Call summary | Server | Yes, for that call | Off | Every participant, per call |
| Scam detection (content) | Device | Local only | On | Disable in settings |
| Spam detection (metadata) | Server | **No content** | On | Not disableable — it is abuse prevention on data we necessarily hold |
| Assistant conversation | Server | Yes — this is a server conversation, and it is labelled as one | N/A | Using it is the consent; the label is permanent |
| Model training | — | — | **Off** | Explicit opt-in, per surface, revocable |

**Rule of thumb for any future feature:** if you cannot fill in a row of this table honestly, the feature is not designed yet.

---

## 4.10 — AI Transparency

1. **Every AI-generated element is visually and programmatically labelled.** Aurora colour, an "assistant" glyph, and a screen-reader label of "AI generated."
2. **"Why am I seeing this?"** is available on every AI surface and explains, in one plain sentence, what triggered it and what data was used.
3. **A permanent, one-tap Privacy Centre** shows: which conversations have server-side AI grants, what the assistant remembers, what is enabled, and what data has left the device in the last 30 days.
4. **We publish which models we use, where they run, and who operates them**, in human-readable form, and we update it when it changes. Users deserve to know whose infrastructure their words touch.
5. **We publish an accuracy note per feature** — for translation and transcription, per language, including the languages where we are weak. Advertising uniform quality across 100 languages when quality is not uniform is a lie that users detect immediately in the languages that matter to them.
6. **Failures are visible.** When the assistant cannot do something, it says so. There is no silent degradation to a worse model.
7. **A transparency report** covering law-enforcement requests, what we were able to provide (and what we were architecturally unable to provide), and moderation actions, published twice a year from Phase 2.

---

## 4.11 — What We Will Not Build

Recorded here permanently so it does not need re-litigating:

- **Emotion detection on users**, in text, voice, or video. Inaccurate, invasive, and discriminatory in practice.
- **Automatic replies sent without the user pressing send.**
- **Personality-simulating avatars of real people.**
- **Engagement optimisation of any kind** — no model whose objective function is time-in-app.
- **Silent content scanning of private conversations**, for any purpose, including ones we would consider good. Once the capability exists, the pressure to widen its use never stops, and the architecture that resists that pressure is the one where the capability was never built.
- **A model that decides what a user sees from strangers** — because there is no feed (Part 0.6 clause 2), there is no ranking model, and this is not a gap.
