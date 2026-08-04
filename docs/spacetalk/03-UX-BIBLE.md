# THE SPACETALK UX BIBLE

### Part 3 — How the Product Behaves

*Governed by `00-EDITORIAL-BIBLE.md`. Visual specifications live in `02-VISUAL-DESIGN-SYSTEM.md`; this document governs behaviour.*

---

## 3.1 — Navigation Philosophy

**Four destinations. One level of depth to reach any conversation. Never more than three taps to any feature in the product.**

```
Chats  ·  Calls  ·  Stories  ·  Settings
```

**Why these four, and why nothing else.** Chats is where 90 % of time is spent. Calls is a distinct mental mode (real-time vs. asynchronous) with its own history. Stories is ephemeral and must not compete with the transcript for attention. Settings holds identity, privacy, and devices. Channels is *not* a fifth tab — a channel is a conversation you subscribe to, so it lives in Chats behind a filter chip. Adding a fifth destination is a Part 0.9 decision requiring CPO and CDO sign-off, and the default answer is no.

**Rules.**

1. **Back always means back.** The back gesture and control undo the last navigation, never "up to a parent you didn't come from."
2. **Tapping the active tab scrolls to top; tapping again jumps to the oldest unread.** Two-stage, learnable, no menu required.
3. **No hamburger menu.** A drawer hides structure behind an unlabelled affordance and doubles the depth of everything inside it.
4. **No nested tabs.** Tabs inside tabs are the clearest sign the information architecture has failed.
5. **Modals are for one decision.** A modal that contains navigation is a screen wearing the wrong clothes.
6. **Deep links resolve to real state with a real back stack** — opening a message from a notification and pressing back returns to Chats, not to the home screen.
7. **The conversation is the atomic unit.** Everything — a person, a group, a channel, the assistant — is a row in one list, sorted by recency. There is no separate inbox for different kinds of talking.

---

## 3.2 — Interaction Philosophy

**Optimistic, reversible, and honest.**

- **Optimistic by default.** Sending a message renders it immediately at `body` weight with a pending indicator. The network confirms afterwards. A user should never watch a spinner to find out whether they said something.
- **Everything reversible where physics allows.** Deleting a chat, leaving a group, and unsending a message all offer undo for 5 seconds via a non-blocking snackbar. Undo is preferred over a confirmation dialog for anything recoverable — confirmations tax every use to prevent the rare mistake, undo taxes only the mistake.
- **Confirm only the irreversible.** Deleting an account, unlinking a device you are currently using, and clearing a chat for everyone get a typed or explicitly-labelled confirmation. Nothing else does.
- **Long-press is the universal "more."** Every message, row, and media item reveals its full action set on long-press with a haptic tick. Nothing is *only* available on long-press.
- **Gestures are shortcuts, never the only path.** Swipe-to-reply is fast; a reply action also exists in the long-press menu, because gestures are undiscoverable and unavailable to switch-control users.
- **Direct manipulation over menus.** Drag a photo into the composer; drag the video-call window anywhere; pull a message down to reply.
- **The composer never moves.** Nothing that appears — attachment tray, emoji picker, assistant panel — displaces the text field or the send control. Muscle memory is a feature.
- **No confirmation of success.** Nothing says "Message sent!" A message that appears in the transcript with a delivered tick has already said it.

### The gesture set (fixed — additions require CDO approval)

| Gesture | Result |
|---|---|
| Swipe right on a message | Reply |
| Swipe left on a message | (Reserved — no action at MVP, so it cannot conflict with a system back gesture) |
| Long-press message | Action menu: react, reply, forward, copy, edit, translate, delete, info |
| Double-tap message | Apply the last-used reaction |
| Swipe right on a conversation row | Read/unread toggle |
| Swipe left on a conversation row | Mute, then Archive |
| Pull down in a transcript | Search this conversation |
| Long-press the mic | Record; slide up to lock hands-free; slide left to cancel |
| Pinch in media viewer | Zoom; drag down to dismiss |

---

## 3.3 — Motion Guidelines

Philosophy is `01-BRAND-BIBLE.md` §1.9; tokens are `07-DESIGN-SYSTEM.md` §7.7. Behavioural rules:

| Transition | Duration | Curve | Note |
|---|---|---|---|
| Touch feedback (press) | 80 ms | `standard` | Instant enough to feel physical |
| Sheet in | 240 ms | `emphasised-decelerate` | Rises from the trigger |
| Sheet out | 200 ms | `emphasised-accelerate` | Returns to the trigger |
| Screen push | 280 ms | `emphasised` | Shared-element where an avatar or image persists |
| Message send | 180 ms | `standard-decelerate` | Bubble rises from the composer to its resting place |
| List reorder | 220 ms | `standard` | Moved item is tracked, never teleported |
| Skeleton → content | 120 ms cross-fade | `linear` | Never a "pop" |

**The 100 ms rule.** Any transition that begins in direct response to a touch must show its first changed frame within 100 ms, even if the underlying work has not finished. If data is not ready, the destination appears in its loading state. Waiting on the origin screen is the single worst thing an interface can do.

---

## 3.4 — Loading Behaviour

**A hierarchy of four states, applied in strict order of preference.**

1. **No loading state at all** — the content was already there. This is the goal, and it is achievable for the conversation list, the last screen of every open transcript, all cached media, and the user's own profile, because they are read from the local database (`06-TECHNICAL-BIBLE.md` §6.8).
2. **Stale content plus a quiet refresh indicator** — show what we have, update in place. Never blank out correct-but-old content to show a spinner.
3. **Skeleton** — only for content never seen before, and only if it will plausibly take >300 ms. Skeletons must match the real layout's geometry so nothing shifts on arrival.
4. **Spinner** — the last resort, and only for indeterminate work of unknown length, never for list loads.

**Rules.**
- **No full-screen loading screens after the first launch.** Cold start goes straight to the conversation list, populated from disk.
- **Nothing may shift after it has been rendered.** Reserve space for images using their known dimensions (stored in the message envelope) so the transcript never jumps.
- **Progress must be honest.** A determinate bar reflects real bytes. If we don't know, we don't fake a bar.
- **Anything over 10 seconds becomes backgroundable** with a persistent, dismissible status row — a large upload never holds the user hostage on one screen.

---

## 3.5 — Error Handling

**Principles.** Errors are events in a system, not accusations. Every error message answers three questions in this order: *what happened*, *what it means for you*, *what to do next*. If we can do the next step ourselves, we do it and don't show an error at all.

**Severity ladder.**

| Level | Presentation | Example |
|---|---|---|
| Silent | Nothing shown; retried automatically | One failed message delivery attempt on a flaky connection |
| Ambient | Inline state change on the affected object | A single message shows "Not sent · Tap to retry" |
| Snackbar | Non-blocking, 4 s, with an action | "Couldn't upload photo. Retry" |
| Banner | Persistent, dismissible, top of screen | "You're offline" |
| Dialog | Blocking — only when the user must decide | "This contact's safety number changed. Verify or continue?" |
| Full screen | Only when the app cannot function | Account suspended; version end-of-life |

**Rules.**
- **Retry automatically before telling anyone.** Exponential backoff with jitter, capped; only surface after the retry budget is spent.
- **Never show an error code alone.** If diagnostics are needed, put the code behind "Details," and make it copyable.
- **Never lose user input.** A failed send keeps the text in the transcript as a retryable draft. A crashed composer restores its draft on relaunch. Drafts are persisted per conversation on every keystroke pause.
- **Distinguish "we failed" from "you can't."** A permission error is not a system failure and must not read like one.
- **One error at a time.** Errors do not stack; the newest replaces the oldest of equal severity.

---

## 3.6 — Empty States

Every empty state has exactly three parts: an illustration (per `01-BRAND-BIBLE.md` §1.7), a one-line explanation of *why* it is empty, and a single action that fills it. No more.

| Surface | Line | Action |
|---|---|---|
| No conversations | "No conversations yet." | "Find someone" |
| No calls | "No calls yet." | "Start a call" |
| Search, no results | "Nothing found for '<query>'." | "Search all messages" (widens scope) |
| Offline with no cache | "You're offline and this hasn't loaded yet." | "Retry" |
| Channel with no posts | "Nothing posted yet." | (none — this is the owner's cue, not a task) |
| Archived, empty | "Nothing archived." | (none) |

**Empty states never sell.** They do not advertise Plus, do not suggest inviting five friends, and do not congratulate the user on inbox zero.

---

## 3.7 — Offline Behaviour

**SpaceTalk is a local-first application that syncs, not a client that fetches.** Every screen is rendered from the on-device database; the network updates that database in the background. This is an architectural commitment (`06-TECHNICAL-BIBLE.md` §6.8), and the UX consequences are:

- **The entire app is fully usable offline** except for the acts that inherently need a peer: placing a call, and loading media that was never downloaded.
- **Composing is always available.** Messages, voice notes, reactions, edits, and deletions queue in an outbox and send in order when connectivity returns. Queued items are shown in the transcript with a clock glyph, in place, not in a separate outbox screen.
- **Offline is stated once, quietly.** A single top banner, not a per-message error, not a modal, not a toast every 30 seconds.
- **Reconnection is invisible.** The banner disappears, the queue drains, ticks update in place. No "Back online!" celebration.
- **Conflicts resolve by rule, never by asking.** Message ordering is by the server's assigned sequence within a conversation; edits use last-writer-wins by device timestamp with the loser preserved in edit history; deletions always win over edits. The user is never shown a merge dialog.
- **Airplane-mode is a tested state**, exercised in CI on every release (`06-TECHNICAL-BIBLE.md` §6.12).

---

## 3.8 — Search Philosophy

**One search field. It searches everything the user can see, and nothing they cannot.**

- **Instant local results first.** Keystroke-by-keystroke over the on-device index, ranked: exact-match contacts → conversations → messages → media → files. Results appear within 50 ms of the keystroke (`08-PERFORMANCE-STANDARDS.md`).
- **Server search only for what cannot be local** — public channel discovery, and message history not yet downloaded on this device. It is clearly labelled as a separate, later-arriving section, never blended into local results in a way that makes the list jump.
- **Semantic search is opt-in and additive** (`04-AI-PHILOSOPHY.md` §4.6). Literal search always works first and never gets slower because semantic search exists.
- **Filters are chips, not a form.** From · In · Type · Date, applied progressively, always visible, always removable.
- **Search never leaves the encryption boundary.** Message search over E2EE content runs entirely on-device against a locally built index. We cannot search server-side for content we cannot read, and we will not build a system that lets us.
- **Recent searches are local and clearable**, and are never used to personalise anything.

---

## 3.9 — Notification Philosophy

**A notification is a promise that something needs you. Every false promise costs trust that cannot be repurchased.**

**What may notify:**
- A message addressed to you (direct, group, or an @mention in a muted group).
- An incoming call.
- A security event on your account (new linked device, safety-number change).
- A completion you explicitly asked to be told about (large file finished uploading).

**What may never notify:** re-engagement prompts, "you have unread messages," feature announcements, tips, someone joining SpaceTalk, someone posting a story, streaks, birthdays, anniversaries, "your friend is active now," or anything a growth team wants.

**Behaviour.**
- **Content is decrypted on the device, never sent by the server.** Push payloads carry only an encrypted envelope and a conversation identifier; the device fetches and decrypts to build the notification text (`06-TECHNICAL-BIBLE.md` §6.6). If the user hides previews, we show "New message" — and the server could not have shown more even if it wanted to.
- **Grouped by conversation, always.** Ten messages from one person is one notification with a count, never ten.
- **Actionable inline:** reply, mark read, mute — without opening the app.
- **Sound is one short, low, non-startling tone**, and a distinct one for calls. No custom sounds at MVP; per-conversation sounds are Phase 2.
- **Mute is granular and honest:** 8 hours, 1 week, always. A muted conversation produces no sound, no badge, no banner — mute means mute.
- **Badges count only messages addressed to you.** Muted conversations never contribute. A badge that overstates is a lie told in a number.
- **Permission is requested in context, after value.** Never on first launch. We ask when the user has just sent their first message, framed as "so you know when they reply."
- **Quiet hours are a first-class setting** and default to off — we do not guess someone's sleep.

---

## 3.10 — Onboarding Principles

**Target: from app open to first message sent in under 90 seconds, with 4 screens maximum.**

1. **Value before permission.** Nothing is requested until it is needed to do something the user already wants.
2. **No account tour.** No carousel of features. Nobody has ever read one.
3. **Progressive disclosure.** The assistant, channels, stories, and linked devices are discovered in use, not taught up front. Each has a single first-use coach mark that appears once and never returns.
4. **Identity is the only required step.** Choose a username, confirm a contact method, set a display name. Photo, bio, and everything else are skippable and clearly marked so.
5. **No address-book upload at MVP.** We do not ask for the contact list, because we have decided not to build a contact-discovery system we cannot make private (`12-ADR.md` ADR-010). Users find each other by username, by QR code, or by a share link. This is slower to grow and it is the correct decision.
6. **Restoring beats re-onboarding.** A returning user or a new linked device goes through a distinct, shorter path.
7. **The empty first screen must be inviting, not accusatory** (`§3.6`).

---

## 3.11 — Accessibility (behavioural)

Visual requirements are in `02-VISUAL-DESIGN-SYSTEM.md` §2.15. Behavioural requirements:

- **Screen-reader transcript navigation** is message-by-message; each message announces sender, content, time, and delivery state in that order, and reactions are a sub-element rather than an interruption.
- **Incoming messages announce politely** (queued behind whatever the user is reading), never assertively.
- **Voice notes always offer a transcript** — this serves deaf and hard-of-hearing users and, in practice, most users in loud or quiet places.
- **Calls surface live captions** from Phase 2, on-device where the platform allows.
- **All gestures have a non-gesture equivalent** (§3.2).
- **No time-limited interactions.** Nothing disappears on a timer that a user must act within, except a call ringing — and that has a generous duration and a missed-call record.
- **Switch and keyboard control** reach every action.
- **Haptics are informational, never decorative**, and fully disableable.

---

## 3.12 — One-Handed Use and Thumb Reach

The product is designed for a person holding a large phone in one hand, thumb anchored at the bottom corner.

**The reach zones**, on a 6.1"–6.9" device held one-handed:

| Zone | Screen region | What lives there |
|---|---|---|
| **Natural** | Bottom 40 % | Composer, send, mic, tab bar, primary actions, sheet actions |
| **Stretch** | Middle 35 % | Message content, list rows (large targets, tap-anywhere) |
| **Hard** | Top 25 % | Titles, back (also served by the edge-swipe gesture), secondary actions |

**Rules.**
1. **Every high-frequency action is in the natural zone.** Send, record, react, reply, answer, and end call are all thumb-reachable without regrip.
2. **Destructive actions are never in the natural zone.** Delete and block live in menus, deliberately requiring intent.
3. **Sheets over dialogs.** A bottom sheet puts its actions where the thumb is; a centred dialog puts them where it isn't. Dialogs are reserved for blocking decisions (§3.5).
4. **Primary actions sit bottom-right in LTR and bottom-left in RTL**, mirroring with the layout.
5. **The top-of-screen back control is always redundant** with an edge-swipe gesture.
6. **Tested one-handed.** Every new screen is reviewed on a 6.7" device, held in one hand, by someone who is not the designer. If it needs a regrip for a common task, it is not done.
7. **Foldables and tablets shift to the two-pane grid** (`02-VISUAL-DESIGN-SYSTEM.md` §2.12) and move primary actions to the pane edges nearest the thumbs, not the screen centre.
