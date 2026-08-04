# THE SPACETALK FEATURE BIBLE

### Part 5 — The MVP, Specified

*Governed by `00-EDITORIAL-BIBLE.md` §0.8. This document specifies the thirteen features of the first public version and nothing else. Every idea outside this list is triaged in `10-SCOPE-GOVERNANCE.md` — deferred with a phase, or rejected with a reason. Nothing is silently dropped.*

**Format.** Every feature states: **Purpose · User problem · Success metrics · UI behaviour · Edge cases · Failure cases · Future roadmap.**

**A note on metrics.** No metric in this document is an engagement metric. We do not target time-in-app, sessions per day, or messages per user — those go up when a product gets worse as reliably as when it gets better. We measure whether the thing worked, how fast, and whether people came back.

---

## 5.1 — Secure Messaging

**Purpose.** The core of the product: send text to a person or a group, encrypted end-to-end, delivered faster than anything else on the market, and readable forever afterwards.

**User problem.** Existing messengers are either fast but not private, private but slow and awkward, or both but visually exhausting. Users have also learned to expect that history is fragile — lost on device change, capped by storage, or trapped on one phone.

**Success metrics.**
- p50 send-to-delivered (sender network → recipient device, both on 4G+) **< 250 ms**; p95 < 700 ms.
- Message loss rate **0** — measured as: every message accepted by the client eventually reaches every recipient device or is explicitly surfaced as failed. This is a correctness target, not a percentage.
- Transcript scroll holds the frame-rate floor (`08-PERFORMANCE-STANDARDS.md`) on Tier-B hardware with a 50,000-message history.
- Day-7 retention of new users who sent ≥1 message: the primary product health number.

**UI behaviour.**
- Composer per `02-VISUAL-DESIGN-SYSTEM.md` §2.14 and `03-UX-BIBLE.md` §3.2. Send is optimistic: the bubble appears instantly with a pending glyph.
- **Delivery states** are four, each with a distinct *glyph* (not just colour): pending (hollow clock) → sent (single tick) → delivered (double tick) → read (double tick, filled). Read receipts are reciprocal — turning yours off turns off your ability to see others'.
- Consecutive messages from one sender within 60 s group into a run with tightened spacing and shared corner geometry (`02` §2.10).
- **Reply** quotes the target inline above the new message; tapping the quote jumps to the original and briefly highlights it.
- **Reactions** are a single emoji per person per message, shown as a compact pill below the bubble. Tapping the pill lists who reacted.
- **Edit** is allowed for 15 minutes, marks the message "edited," and keeps a viewable edit history. **Delete for me** is always available; **delete for everyone** is allowed for 48 hours and leaves a tombstone ("This message was deleted") rather than silently altering history.
- **Disappearing messages** are a per-conversation setting (off / 24 h / 7 d / 90 d), applied from the moment it is set, announced in the transcript, and changeable by any participant with a visible system message.
- Link previews are generated **on the sender's device** and sent as part of the message. The recipient's device never contacts the linked site — this closes an IP-leak vector that most messengers still have open.

**Edge cases.**
- *Clock skew:* ordering uses the server-assigned per-conversation sequence number, never device clocks. Display timestamps use device time but ordering never does.
- *A recipient device that has been offline for 6 months:* the server retains undelivered envelopes for 30 days; beyond that, the sender's other devices backfill on reconnect where possible, and history that no live device holds is genuinely gone. This is stated in the interface, not hidden.
- *Message arrives before the conversation exists* (first contact): the conversation is created locally from the envelope; the sender lands in message requests (`04-AI-PHILOSOPHY.md` §4.7).
- *Very long message* (>4,000 characters): collapsed with "Show more" rather than rejected.
- *Simultaneous edit from two linked devices:* last-writer-wins by device timestamp; the losing edit is preserved in edit history and never silently discarded.
- *User deletes for everyone while a recipient is offline:* the deletion is queued as its own envelope; it always beats a pending edit on arrival.

**Failure cases.**
- *No network:* message sits in the outbox with a clock glyph, sends on reconnect, order preserved (`03-UX-BIBLE.md` §3.7).
- *Send rejected by the server (rate limit, blocked, account suspended):* the specific reason is shown inline; a rate limit says when to retry.
- *Decryption failure* (missing session, corrupted envelope): the message renders as "Couldn't decrypt this message" with a one-tap "Ask sender to resend," which sends a machine-readable retransmit request. We never render a decryption failure as an empty bubble — silent loss is the worst failure mode in a messenger.
- *Local database corruption:* the client detects it on open, rebuilds the index from the message store, and if the store itself is unrecoverable, re-syncs from the server what the server still holds — telling the user exactly what could and could not be recovered.

**Future roadmap.** Phase 2: scheduled send, message pinning, per-conversation themes, formatted text (bold/italic/lists/code), threads inside groups. Phase 3: MLS group protocol migration (`12-ADR.md` ADR-003), post-quantum key agreement, secret chats with per-device isolation.

---

## 5.2 — Voice Notes

**Purpose.** Say it faster than you can type it, and let the recipient consume it however suits them.

**User problem.** Voice notes are the fastest way to communicate warmth and nuance, and the worst way to receive information — you cannot skim them, cannot search them, cannot listen in a meeting, and cannot tell whether a 4-minute note contains anything urgent.

**Success metrics.**
- Record-start latency (touch to first captured sample) **< 120 ms**.
- Transcript availability **> 95 %** of notes in the top 12 supported languages, generated on-device.
- Playback abandonment (started, stopped before 30 %) **< 20 %** — a proxy for "the transcript let people skip what they didn't need."

**UI behaviour.**
- Long-press the mic to record; slide up to lock hands-free; slide left to cancel with an unmistakable cancel affordance. Release to review-and-send, not to send blind — a one-tap send follows, so an accidental release never fires off an unintended note.
- A live waveform renders during recording, and the same waveform is the playback scrubber.
- **Playback speed** 1×/1.5×/2×, remembered per user.
- **Transcript** available under every note via a single tap; the sender can also see their own transcript *before* sending.
- Playback continues across conversations and into the background, with a compact persistent control.
- Notes played through the earpiece when the phone is raised to the ear, speaker otherwise.

**Edge cases.**
- *Interrupted by an incoming call:* recording stops and is saved as a draft, never lost.
- *Extremely long note* (>10 min): capped at 15 minutes with a visible countdown from 14:00.
- *Silent recording* (microphone muted at OS level, or a dead mic): detected on stop; we warn before sending rather than delivering silence.
- *Bluetooth device connects mid-recording:* recording continues on the original input; switching inputs mid-note is not attempted, as it produces audible artefacts.
- *Language not supported for transcription:* the note sends normally, with a quiet "Transcript not available for this language" rather than a broken transcript.

**Failure cases.**
- *Microphone permission denied:* an inline explanation with a one-tap route to settings; the mic control never simply does nothing.
- *Upload fails:* the audio is retained locally and retried; the user is never told it sent when it didn't.
- *Transcription model fails or times out:* the note is unaffected; the transcript control shows "Couldn't transcribe" with a retry.

**Future roadmap.** Phase 2: voice-note replies with quoted audio segments, noise suppression on-device, transcript search integrated into global search. Phase 3: instant voice-to-voice translation of notes (with the original always attached, per `04-AI-PHILOSOPHY.md` §4.4).

---

## 5.3 — Voice Calls

**Purpose.** One-to-one and small-group real-time voice that connects faster and sounds better than the phone network.

**User problem.** VoIP calls in existing apps take 3–8 seconds to connect, degrade unpredictably, and give no honest indication of what is wrong when they do.

**Success metrics.**
- **Time-to-ring < 1.2 s** (initiate → callee's device rings) at p75.
- **Mouth-to-ear latency < 200 ms** at p75 on a 4G connection.
- **Call setup success rate > 99 %**; drop rate < 1 % per 10-minute call.
- MOS ≥ 4.0 at p50 on the reference network profile.

**UI behaviour.**
- Full-screen incoming call with two large targets (answer/decline), reachable one-handed, plus a "reply with message" option.
- In-call: mute, speaker, video-upgrade, add-participant, end. Five controls, in the natural thumb zone, nothing hidden.
- **Honest network state:** a connection-quality indicator that names the actual problem ("Your connection is unstable") rather than a generic bar count.
- Ongoing calls collapse to a system-level pill so the user can use the rest of the app.
- Calls are E2EE; the encryption state is shown once at connect, not as a persistent badge.

**Edge cases.**
- *Callee on another call:* caller hears busy state immediately, callee gets a call-waiting prompt.
- *Both call each other simultaneously:* deterministic resolution by user ID ordering; one call is auto-answered into the other, no double-ring.
- *Network switch mid-call* (Wi-Fi → cellular): the session migrates without dropping; a brief "Reconnecting" state, and if it exceeds 20 s the call ends cleanly with a recorded duration.
- *Callee has no compatible device linked:* stated plainly before dialling.
- *Do Not Disturb / focus modes:* honoured; the platform's repeat-caller escape hatch is supported.

**Failure cases.**
- *NAT traversal failure:* automatic relay fallback (TURN); the user sees nothing except slightly higher latency.
- *No audio path* (headset routing failure): detected within 3 s and surfaced with a route picker, rather than leaving two people saying "hello?"
- *Server capacity exhaustion:* calls fail *before* ringing, with a clear message — never a ring that cannot connect.

**Future roadmap.** Phase 2: group voice up to 32, call recording with all-party consent, live captions. Phase 3: spatial audio for groups, live translated calls (`04-AI-PHILOSOPHY.md` §4.4), voice rooms for communities.

---

## 5.4 — Video Calls

**Purpose.** See the person. Work on a bad connection. Never be surprised by how you look or what is behind you.

**User problem.** Video calls fail hardest exactly where they are needed most — low bandwidth, cheap devices, poor light. Most apps respond by freezing video and dropping audio, which is precisely backwards.

**Success metrics.**
- **Audio survives to 40 kbps** — when bandwidth collapses, video degrades progressively and audio is protected absolutely. Audio never sacrifices for video. This is the defining engineering rule of the feature.
- 720p30 sustained at p75 on a 5 Mbps connection; graceful ladder down to 180p and then to audio-only.
- Connect time < 2 s at p75; battery drain < 12 % per hour of 1:1 video on the Tier-B reference device.

**UI behaviour.**
- **A pre-call preview by default** — see your camera, your background, and your mic level before you are visible to anyone.
- Self-view is a small draggable tile that can be minimised entirely; it snaps to corners and never covers the active speaker.
- Controls auto-hide after 4 s and return on any tap.
- Group video (up to 8 at MVP) uses an active-speaker layout with a filmstrip; no gallery grid on phone, because 8 faces on a 6" screen is 8 unrecognisable faces.
- One-tap switch between voice and video, in either direction, mid-call, with the other party notified.

**Edge cases.**
- *Rotation mid-call:* re-layout without renegotiating the media session.
- *Backgrounding the app:* video pauses with a clear "Camera off" state shown to others; audio continues.
- *Very slow device:* the encoder ladder is capped by measured device capability at call start, not attempted and failed.
- *Participant with no camera:* joins audio-only with an avatar tile; no error.

**Failure cases.**
- *Camera permission denied or camera busy:* the call proceeds as audio with a clear inline explanation.
- *Sustained packet loss > 15 %:* automatic step-down through the quality ladder, with one honest message ("Poor connection — video paused").
- *Encoder crash:* the call recovers to audio-only rather than ending.

**Future roadmap.** Phase 2: screen sharing, background blur (on-device), live captions, group video to 32. Phase 3: real-time translated subtitles; low-bandwidth mode targeting 2G-class networks.

---

## 5.5 — Group Conversations

**Purpose.** A shared space for a family, a team, or a community of up to 1,000 people, that stays legible as it grows.

**User problem.** Groups get loud, then get muted, then get abandoned. The failure is structural: every message is treated as equally urgent, and there is no way to participate partially.

**Success metrics.**
- Groups still active (≥1 message/week) at day 90 after creation: **> 40 %**.
- Mute rate below 30 % for groups under 20 members — high mute rates mean the notification model is failing (`03-UX-BIBLE.md` §3.9).
- Fan-out delivery: a message to 1,000 members reaches p95 of online devices within **1 s**.

**UI behaviour.**
- Any user can create a group; a name is optional (a default is derived from members) and a photo is optional.
- **Roles are minimal at MVP:** owner and member. Owners can rename, set the photo, add/remove members, and configure who may add others. Full role systems are deliberately deferred (`10-SCOPE-GOVERNANCE.md`).
- **@mentions** cut through mute — this is what makes mute safe to use, and therefore what makes groups survivable.
- **Invite links** with optional expiry and optional admin approval. Links are revocable and rotate on demand.
- **Join/leave system messages** are collapsed into a single line per hour rather than one per event; noise from membership churn is the most common reason groups become unreadable.
- Group profile lists members with a search field, and shows shared media, files, and links.

**Edge cases.**
- *Last owner leaves:* ownership transfers to the longest-tenured active member, announced in the transcript.
- *Member removed while offline:* they receive the removal on reconnect and retain their local history — we cannot and do not delete data from a device we do not control, and we say so rather than implying otherwise.
- *A user is added to a group by someone they blocked:* the add is rejected. Blocks are transitive to group invitations.
- *1,000-member group where 300 come online at once:* fan-out is queued and rate-shaped server-side; no client behaviour changes.
- *Someone joins a group and scrolls to the beginning:* new members see history from their join point by default; the owner may enable full-history sharing at creation, and it cannot be changed retroactively (it is an encryption-key decision, not a policy toggle).

**Failure cases.**
- *Partial fan-out failure:* per-recipient retry with an eventual delivery guarantee; the sender's ticks reflect real per-device delivery, not an optimistic aggregate.
- *Sender-key rotation failure* after a member leaves: the group is held in a re-keying state for at most 10 s with a visible indicator; messages queue, nothing is sent under a key the departed member holds.
- *Group state divergence between devices:* the server's membership state is authoritative and reconciles on reconnect.

**Future roadmap.** Phase 2: threads, polls, admin roles and permissions, group description and rules, member-level muting. Phase 3: communities (groups of groups), events, moderation tooling, groups above 1,000 via MLS.

---

## 5.6 — Channels

**Purpose.** One-to-many broadcast — a creator, a school, a business, or a government agency reaching subscribers — without becoming a feed.

**User problem.** Announcements today happen in groups (where 500 people can reply and destroy the signal) or on social platforms (where an algorithm decides whether the message is seen at all). Neither is acceptable for information that matters.

**Success metrics.**
- **Delivery rate to subscribers: 100 %.** There is no ranking, so there is no reason for a subscriber to miss a post. This is the entire value proposition, and it is a correctness metric, not a percentage to optimise.
- Subscriber retention at day 30 > 70 %.
- Median time from post to p95 device delivery **< 2 s** for channels under 100,000 subscribers.

**UI behaviour.**
- Channels appear **in the Chats list** behind a filter chip — not as a separate destination (`03-UX-BIBLE.md` §3.1). A channel you follow is a conversation you subscribe to.
- **Chronological, always.** No ranking, no "suggested," no engagement sorting. Ever (Part 0.6 clause 2).
- Subscribers can react and, if the owner allows, comment in a discussion area that is visually separate from the posts.
- Channels have a public link, a handle, and a verified state for identity-verified organisations.
- **Channels are not end-to-end encrypted, and the interface says so** on the channel's header and at subscribe time. A public broadcast to 100,000 strangers is not a private conversation, and pretending it is would be dishonest. Content is encrypted in transit and at rest.
- Basic analytics for owners: subscriber count, post reach, reactions. No demographic profiling of subscribers — we do not collect it, so we cannot report it.

**Edge cases.**
- *A channel grows past 1M subscribers:* fan-out shifts to a pull-based model with push wake-ups; users notice nothing.
- *Owner deletes a post:* removed for everyone; a tombstone appears only if the post had been delivered.
- *Subscriber has notifications off:* posts still arrive, silently, in the list.
- *A channel is reported:* moderation applies to channels, which are public content, under the published policy (`11-BUSINESS-AND-COMPLIANCE.md` §11.7). Private conversations are not moderated because they cannot be — a distinction we state clearly rather than blurring.

**Failure cases.**
- *Post fails partway through fan-out:* the post is durable server-side; delivery resumes and completes. Owners see true delivery counts.
- *Impersonation of a known organisation:* handled by verification plus proactive name-similarity detection at creation time, not by reactive takedowns alone.

**Future roadmap.** Phase 2: scheduled posts, post drafts, multi-admin, richer analytics, paid subscriptions. Phase 3: creator monetisation (`11-BUSINESS-AND-COMPLIANCE.md`), live audio broadcast to subscribers.

---

## 5.7 — Stories

**Purpose.** Lightweight, ephemeral sharing with the people you actually talk to.

**User problem.** Stories in existing apps have become performance venues with viewer counts, rankings, and pressure. The original idea — a low-stakes glimpse of your day for people who know you — is worth keeping; the anxiety machinery around it is not.

**Success metrics.**
- Share-back rate: proportion of viewers who *reply* rather than merely view. This is the health metric; a story that is watched but never answered is content, not communication.
- Posting frequency stable over time (not growing) — if we see it climbing, we are creating pressure, which is a failure.
- Zero notifications generated by stories, verified continuously in production.

**UI behaviour.**
- Stories live in their own destination, not as a ring above the conversation list — putting stories above the inbox is the design decision that turned messaging apps into social apps, and we are declining it deliberately.
- 24-hour expiry. Photo, video (≤30 s), or text on a solid colour. No filters at MVP beyond crop and rotate.
- **Audience is chosen per story:** all contacts, selected people, or everyone except selected people. The audience is shown before posting, every time.
- **No public viewer counts.** The poster sees who viewed; nobody else sees anything. There is no ranking of who watched most.
- Replies to a story open a normal 1:1 conversation with the story quoted — this is the point of the feature.
- Stories are end-to-end encrypted to the chosen audience.

**Edge cases.**
- *Viewer's clock is wrong:* expiry is enforced server-side and client-side against server time.
- *Poster deletes early:* removed from all viewers immediately; already-viewed copies are removed from the viewer's cache.
- *Screenshot:* not detected and not reported. Screenshot detection creates false security; we tell users plainly that anything they post can be captured.
- *Large video on a slow connection:* uploads in the background with a progress row; the story posts when it completes.

**Failure cases.**
- *Upload fails:* draft is retained locally, retried, never silently discarded.
- *Media processing fails:* the original is preserved and posted at reduced quality rather than lost.

**Future roadmap.** Phase 2: story replies with reactions, close-friends list, text/drawing tools, mute-a-poster. Phase 3 and beyond: nothing. Stories are deliberately capped — see `10-SCOPE-GOVERNANCE.md` for why Reels-style content is rejected outright.

---

## 5.8 — AI Assistant

**Purpose.** Ambient, invited intelligence: translation, transcription, summarisation, recall, and fraud protection — delivered inside conversations, plus one dedicated assistant conversation for direct questions.

**User problem.** People need help across a language barrier, in a long unread group, with a voice note they cannot play, and against fraudsters — and today they must leave the conversation and go to a different app to get any of it.

**Success metrics.**
- **On-device execution rate > 85 %** of all AI invocations. This is the primary metric, because it is the privacy promise made measurable.
- Translation user-reported accuracy ≥ 90 % in the top 12 language pairs.
- Scam-warning precision **> 95 %** per pattern class, with automatic rollback below that (`04-AI-PHILOSOPHY.md` §4.7).
- **Zero** AI invocations on E2EE content without a recorded, user-visible grant — audited continuously; any non-zero result is a Sev-1 incident.
- p95 added latency to any core interaction from an AI feature: **0 ms** (AI is never in the critical path of sending or receiving).

**UI behaviour.** Fully specified in `04-AI-PHILOSOPHY.md`. In summary: Aurora colour exclusively; labelled; never sends on the user's behalf; disableable entirely; a permanent Privacy Centre showing every grant.

**Edge cases.**
- *Model unavailable / not yet downloaded:* the feature is hidden rather than shown-and-broken, with a one-tap download offer.
- *Device too weak for on-device models* (below Tier-C): AI features are offered only in their server form, with explicit consent, and the user is told why.
- *User revokes a grant mid-operation:* the operation is cancelled and any server-side copy is deleted within 24 hours, verified by audit.
- *Mixed-language conversation:* per-message language detection, not per-conversation.

**Failure cases.**
- *Model produces nothing or times out:* "Couldn't do that" with a retry. Never a fabricated fallback.
- *Server-side provider outage:* on-device features are unaffected — a deliberate architectural benefit of the on-device-first rule.
- *Wrong or harmful output:* one-tap report on every AI element, routed to a standing review queue with weekly triage.

**Future roadmap.** Phase 2: call summaries with all-party consent, richer assistant tools, live captions. Phase 3: live call translation, cross-device assistant memory. Phase 4: assistant actions on user data (find, organise, schedule) under an explicit permission model.

---

## 5.9 — File Sharing

**Purpose.** Send any file to anyone, encrypted, without a size limit that forces people back to email.

**User problem.** File sharing in messengers is arbitrarily capped, silently recompresses images into mush, and loses files when the sender's device changes.

**Success metrics.**
- Upload success rate > 99.5 % including resumed uploads.
- Median time-to-first-byte on download < 300 ms via edge cache.
- Image quality: **original-quality sending is the default option shown**, not buried. Complaints about recompression: near zero.

**UI behaviour.**
- Limits: **2 GB per file free, 10 GB on Plus.** Stated up front, not discovered at 99 %.
- **Resumable uploads and downloads** across app restarts and network changes.
- Send photos at original quality or compressed — the choice is offered on send, with the resulting size shown for both, and the choice is remembered per conversation.
- Files, media, and links are browsable per conversation from the conversation profile.
- Every file is client-side encrypted with a per-file key; the storage layer holds ciphertext only.
- Downloaded files land in the platform's normal file location and are visible to the user's own file manager — they are the user's files.

**Edge cases.**
- *Storage full on the receiving device:* checked before download starts, with a clear message and the required amount.
- *File type blocked by the platform* (e.g. iOS restrictions): stated before sending, not after.
- *Executable file types:* delivered but marked with a plain warning; we do not block file types unilaterally, because it breaks legitimate use, and we do not scan file contents, because we cannot decrypt them.
- *Sender deletes the file locally after sending:* the encrypted copy on the server persists for the retention window; recipients are unaffected.

**Failure cases.**
- *Upload interrupted:* resumed from the last committed chunk; never restarted from zero.
- *Storage backend unavailable:* upload is queued locally and retried; the message shows a pending state rather than a failure.
- *Retention expiry* (files are retained 90 days free / 1 year on Plus after last access): the user is warned at 7 days, and expiry is shown in the file's info. No file ever silently vanishes.

**Future roadmap.** Phase 2: folders in shared media, in-app document preview, cross-conversation file search. Phase 3: cloud storage tier with unlimited retention, collaborative documents.

---

## 5.10 — Search

**Purpose.** Find any message, person, file, or conversation instantly, without our servers being able to read any of it.

**User problem.** Search in encrypted messengers is usually terrible, because doing it properly requires an on-device index that most products never invested in.

**Success metrics.**
- **Local results within 50 ms of a keystroke** at p95, over a 100,000-message history.
- Search success rate (a search followed by a result tap) > 70 %.
- Index size < 5 % of the message store; index build for 100,000 messages < 30 s on Tier-B hardware, running in the background without blocking the UI.

**UI behaviour.** Fully specified in `03-UX-BIBLE.md` §3.8: one field, local-first, chips for filters, semantic results as a labelled second group.

**Edge cases.**
- *Search in a language with no word boundaries* (Chinese, Japanese, Thai): n-gram indexing rather than word tokenisation.
- *RTL and mixed-direction queries:* normalised before indexing, with correct bidi rendering of highlighted results.
- *Diacritics and Arabic orthographic variants:* normalised on both index and query, so a search without diacritics finds text with them.
- *Newly linked device with no history:* search states honestly that it covers messages on this device, and offers to sync more.
- *Index rebuild in progress:* search still works against the message store directly, slower, with a quiet indicator.

**Failure cases.**
- *Index corruption:* detected on open, rebuilt in the background; search degrades to a slower direct scan rather than failing.
- *Query too broad:* results are streamed progressively rather than blocking on a full scan.

**Future roadmap.** Phase 2: search inside file contents on-device, search within voice-note transcripts. Phase 3: cross-device federated local search (query fanned to your own linked devices, results returned encrypted — never through a server that can read them).

---

## 5.11 — Profile System

**Purpose.** Be findable by the people you want, and invisible to everyone else.

**User problem.** Most messengers make the phone number the identity, which means anyone with a number can reach you, and leaving means losing everything.

**Success metrics.**
- Profile completion (display name + photo) > 80 %.
- **Percentage of accounts created without a phone number**: tracked as a strategic metric, because phone-optional identity is a differentiator.
- Unwanted-contact reports per 1,000 users: the number this feature exists to keep near zero.

**UI behaviour.**
- **Identity is a username** (`@handle`), globally unique, changeable twice a year, with the old handle reserved for 90 days.
- A phone number or email is used for account recovery and is **optional to expose**. Discoverability by phone/email is off by default.
- Profile carries: display name, photo, optional short bio, optional links. No follower counts, no "last seen" by default.
- **Privacy controls are per-field**, each with three options — everyone / contacts / nobody: profile photo, bio, last seen, read receipts, story audience, who can add me to groups, who can call me.
- **QR code and share link** are the primary ways to connect (`03-UX-BIBLE.md` §3.10 rule 5).
- **Safety numbers** per contact for out-of-band verification, rendered in a monospaced face with an unambiguous glyph set (`02-VISUAL-DESIGN-SYSTEM.md` §2.13).
- **Block** is complete and silent: blocked users see no state change, and receive no signal that they were blocked.

**Edge cases.**
- *Username squatting:* handles inactive for 12 months are reclaimable through a published process; trademark disputes follow a documented policy.
- *Changing a username mid-conversation:* existing conversations follow the account, not the handle; a system message notes the change so impersonation is harder.
- *Two accounts, same display name:* the handle disambiguates and is always shown in ambiguous contexts.
- *Account recovery with no phone or email:* the user is warned clearly at signup that recovery will be impossible, and must acknowledge it. We will not build a recovery backdoor.

**Failure cases.**
- *Recovery method lost:* the account and its history are unrecoverable. This is a direct consequence of E2EE, we state it at signup, and we do not soften it.
- *Impersonation report:* handled by a verification process, with proactive similarity checks at registration.

**Future roadmap.** Phase 2: multiple accounts on one device, profile verification for organisations, per-contact nicknames. Phase 3: portable identity/key export, business profiles.

---

## 5.12 — Notifications

**Purpose.** Tell the user when a human needs them, and never otherwise.

**User problem.** Notifications have become an advertising channel. Users respond by turning them off entirely, which breaks the actual purpose of a messenger.

**Success metrics.**
- **Notification opt-out rate < 10 %** — the single clearest measure of whether we kept the promise.
- Delivery latency p95 **< 2 s** from send to device notification.
- Notification-to-open rate > 40 % (high, because every notification should matter).
- **Zero** non-human-originated notifications in production, verified by an automated audit of every notification type on every release.

**UI behaviour.** Fully specified in `03-UX-BIBLE.md` §3.9. Key architecture: push payloads carry **no content** — only an encrypted envelope and a conversation identifier; the device decrypts locally to build the text (`06-TECHNICAL-BIBLE.md` §6.6).

**Edge cases.**
- *Push service unavailable* (no Google services, or a restricted network): a persistent foreground socket with battery-aware backoff, and the trade-off is explained to the user rather than silently degrading.
- *Device asleep in a deep power state:* high-priority push wake-up, with the platform's own rate limits respected.
- *Notification arrives for a message already read on another device:* dismissed automatically across all linked devices within 1 s of the read event.
- *Aggressive battery managers* (a real, documented problem on several Android OEM builds): detected, with a one-time explanation and a direct route to the relevant setting.

**Failure cases.**
- *Decryption fails on the notification path:* fall back to "New message" rather than showing nothing — a silent notification failure is indistinguishable from being ignored.
- *Push token invalid:* re-registered on next foreground; undelivered messages arrive on reconnect.

**Future roadmap.** Phase 2: per-conversation custom sounds, quiet hours schedules, notification summaries for muted groups. Phase 3: cross-device notification intelligence (notify only the device you are actually using).

---

## 5.13 — Multi-Device Support

**Purpose.** Use SpaceTalk on your phone, your laptop, and your tablet — all end-to-end encrypted, with no device designated as the master that must stay online.

**User problem.** Multi-device support in encrypted messengers has historically been either absent, or implemented as a tethered mirror that dies when the phone's battery does.

**Success metrics.**
- Up to **4 linked devices** per account at MVP.
- Sync latency between linked devices **< 500 ms** at p95 when both are online.
- **Phone-independent operation:** a linked device works with the phone off. Verified as a release gate.
- Link-flow completion rate > 90 %.

**UI behaviour.**
- **Each device has its own identity key**; messages are encrypted per-device (`12-ADR.md` ADR-003). There is no key sharing between devices, and no primary device.
- Linking is a QR-code scan from an already-linked device, with the new device's safety number shown on both screens for confirmation.
- **Every linking event generates a notification on all existing devices** and a permanent entry in a device log that shows: name, platform, when linked, last active, and current location by coarse region. Silent device addition is the attack that breaks E2EE for real people, and it must be loud.
- Any device can unlink any other device, immediately.
- History sync to a new device is explicit and user-controlled: none, last 30 days, or everything — with the transfer size shown before it starts.
- At MVP the linked-device client is the **Flutter desktop-class web client**; iOS and Android are full clients (`12-ADR.md` ADR-012).

**Edge cases.**
- *Device linked while offline:* the link is pending until it can be confirmed by a live device; it never activates on the strength of a stale QR code (codes expire in 60 s).
- *All devices lost:* the account is recoverable via the recovery method, but the message history is not (§5.11 failure case). Stated at signup.
- *A device is compromised:* unlinking it immediately rotates all group sender keys and invalidates its sessions; messages sent to it before unlinking were already delivered and cannot be recalled, and we say so.
- *Clock skew between devices:* server sequence numbers, never device clocks (§5.1).
- *Same account, two devices editing the same draft:* drafts are per-device and are not synced. Attempting to sync drafts creates more confusion than it resolves.

**Failure cases.**
- *Sync divergence* (one device missing messages): a per-conversation sequence-gap detector requests retransmission automatically; unrecoverable gaps are shown in the transcript as an explicit "Some messages could not be synced here" marker rather than an invisible hole.
- *Session establishment failure with a new device:* messages queue and retry; the sender sees a partial-delivery state, never a false "delivered."

**Future roadmap.** Phase 2: native macOS/Windows/Linux clients, unlimited history sync, per-device notification preferences. Phase 3: wearables (notification and reply only), car integration via platform standards, TV for calls only.

---

## 5.14 — Cross-Cutting Requirements

Every feature above must also satisfy, without exception:

| Requirement | Where specified |
|---|---|
| Meets the performance budget for its surface | `08-PERFORMANCE-STANDARDS.md` |
| Full RTL, bidi, and 200 % dynamic-type support | `02` §2.13, §2.15 |
| Screen-reader complete, keyboard complete | `03` §3.11 |
| Works offline or degrades honestly | `03` §3.7 |
| Every string localised, no concatenated sentences | `11-BUSINESS-AND-COMPLIANCE.md` §11.6 |
| Errors follow the severity ladder | `03` §3.5 |
| No notification unless a human is addressing the user | `03` §3.9 |
| Data exportable and deletable | Part 0.6 clause 10 |
| Instrumented for its own success metrics, and no others | `11` §11.5 |
