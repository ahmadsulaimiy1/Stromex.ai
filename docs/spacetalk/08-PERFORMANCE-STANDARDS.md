# THE SPACETALK PERFORMANCE STANDARDS

### Part 8 — The Numbers We Defend

*Governed by `00-EDITORIAL-BIBLE.md` §0.6 clause 8: no feature ships that regresses these targets. Performance is a release gate, not a follow-up ticket.*

**How to read this.** Every number below is a **budget**, measured on the reference hardware in §8.7, in production, at the stated percentile. A budget that is not measured in CI does not exist. Where a target differs by device tier, all three are given — the Tier-C number is the one that matters most, because it describes the experience of the users most likely to have no alternative.

---

## 8.1 — Why Speed Is the First Feature

A messaging app is opened 50–150 times a day. A 400 ms cold start costs a heavy user roughly a minute a day, and — more importantly — it changes what the app *is*: something you decide to open rather than something you glance at. Every competitor in this category has, over a decade, traded launch time for features. That accumulated debt is the opening we are attacking.

This is why speed is Identity Pillar 1 (`00` §0.7) and why Part 0.9 rule 4 resolves performance-versus-beauty in performance's favour.

---

## 8.2 — Cold Launch

| Measurement | Tier A | Tier B | Tier C |
|---|---|---|---|
| Process start → first frame | **< 350 ms** | < 600 ms | < 1,100 ms |
| First frame → conversation list populated | **< 100 ms** | < 180 ms | < 350 ms |
| **Total to interactive (p95)** | **< 450 ms** | **< 800 ms** | **< 1,500 ms** |
| Warm launch to interactive | < 120 ms | < 200 ms | < 400 ms |

**How it is achieved, specifically:**
- The conversation list renders from SQLite before any network call is made. Networking initialises *after* the first frame.
- The theme is read synchronously from platform preferences before the first frame, so there is never a flash of the wrong theme.
- Crypto (libsignal FFI) initialises lazily, on first use, not at launch.
- Deferred components use Flutter's deferred loading; nothing is constructed at startup that the first screen does not need.
- Shader warm-up runs on first launch only, from a pre-recorded SkSL bundle.

**Enforcement.** Cold start is measured on physical devices in CI on every pull request. A regression above budget fails the build. There is no "we'll fix it next sprint" path.

---

## 8.3 — Frame Rate

| Surface | Target |
|---|---|
| All scrolling and animation | **60 fps floor; 120 fps on capable displays** |
| Dropped frames while scrolling a 10,000-message transcript | **< 0.5 %** |
| Jank (frames > 16.6 ms) during any transition | **< 1 %** |
| Frame build time (p99) | **< 8 ms** — half the budget, leaving room for raster |
| Raster time (p99) | < 8 ms |

**The transcript is the benchmark.** If the message list holds frame rate on Tier-C hardware with a large history, mixed media, and an active network, everything else in the product will too. Techniques are specified in `06-TECHNICAL-BIBLE.md` §6.2; the ones that matter most: cached message heights, `RepaintBoundary` per bubble, no save layers in scrolling content, and image decode at display resolution.

---

## 8.4 — Latency

| Interaction | Target (p95) |
|---|---|
| Touch → first visual response | **< 100 ms** |
| Keystroke → character rendered | < 16 ms (one frame) |
| Send tap → bubble visible | **< 50 ms** (local write, optimistic) |
| Send → delivered to a recipient device | **< 250 ms p50, < 700 ms p95** |
| Search keystroke → local results | **< 50 ms** |
| Open a conversation → last screen rendered | < 120 ms |
| Tap notification → conversation visible | < 400 ms |
| Call initiate → callee ringing | **< 1.2 s p75** |
| Media thumbnail → visible | < 100 ms (cached), < 400 ms (network) |

**The 100 ms rule** (`03-UX-BIBLE.md` §3.3) is the one to internalise: below roughly 100 ms an interface feels like a direct extension of the hand; above it, like a system being asked to do something.

---

## 8.5 — Memory

| State | Tier A | Tier B | Tier C |
|---|---|---|---|
| Idle (conversation list) | < 120 MB | < 100 MB | **< 80 MB** |
| Active conversation with media | < 220 MB | < 180 MB | **< 140 MB** |
| Video call | < 320 MB | < 280 MB | < 220 MB |
| Peak, any operation | < 400 MB | < 350 MB | **< 260 MB** |

**Why Tier C is stricter, not looser:** low-memory Android devices kill background apps aggressively. An app with a large footprint is evicted between glances, which turns every warm launch into a cold one. Memory discipline on cheap hardware *is* launch-speed discipline.

**Rules.** Image caches are bounded in bytes, not entries. Decoded images are released on scroll-out. No unbounded collection anywhere in the client — every cache has an eviction policy asserted by a test. Memory is profiled on Tier-C hardware weekly, and leaks are release blockers.

---

## 8.6 — Binary Size, Battery, and Network

**Binary size.** Android app bundle **< 30 MB** initial download; iOS **< 60 MB**; per-architecture split, deferred components for calls and AI models. Language packs and on-device models are downloaded on demand, never bundled — a user who needs two languages should not carry sixty.

**Battery** (measured over a standardised 1-hour scenario on the Tier-B reference device):

| Scenario | Budget |
|---|---|
| Idle, connected, receiving occasional messages | **< 1 % per hour** |
| Active messaging | < 4 % per hour |
| Voice call | < 6 % per hour |
| Video call | **< 12 % per hour** |

Achieved by: a single multiplexed connection (never one per feature), push-driven wake-ups with exponential backoff, batched writes, no polling anywhere, hardware codecs for all media, and no background work when the app is not foregrounded except the outbox drain.

**Network.**

| Item | Budget |
|---|---|
| Text message overhead (envelope + protocol, excluding content) | **< 400 bytes** |
| Idle keepalive | < 1 KB per 5 minutes |
| Typing indicators | Coalesced, max 1 per 3 s per conversation |
| Presence | Push-driven, never polled |
| Daily background data, idle account | **< 1 MB** |

Protobuf over JSON, gzip on anything above 1 KB, and delta sync rather than full-state refresh. A user on a metered 500 MB monthly plan must be able to use SpaceTalk normally, and this is tested against a simulated metered connection.

---

## 8.7 — Reference Hardware and Network Profiles

**Device tiers.** Every budget is stated per tier; every tier is a physical device in the CI lab (`06-TECHNICAL-BIBLE.md` §6.12).

| Tier | Definition | Reference devices | Share of target market |
|---|---|---|---|
| **A** | Flagship, ≤2 years old | Current iPhone Pro, current Pixel Pro | ~15 % |
| **B** | Mainstream, 2–4 years old | iPhone from ~4 years ago, mid-range Android with 6 GB RAM | ~50 % |
| **C** | Entry-level, low RAM | Android Go-class, 3–4 GB RAM, eMMC storage | ~35 % |

**Tier C is the design target, not the fallback.** Any screen that only feels good on Tier A is unfinished.

**Network profiles**, applied in automated testing:

| Profile | Bandwidth | RTT | Loss |
|---|---|---|---|
| Good | 20 Mbps | 30 ms | 0 % |
| Typical mobile | 4 Mbps | 90 ms | 0.5 % |
| **Poor** | 500 kbps | 300 ms | 3 % |
| **Very poor** | 100 kbps | 800 ms | 8 % |
| Offline | — | — | 100 % |

Messaging must remain fully usable on *Poor*. Voice calls must remain intelligible on *Very poor*. Every release runs the full integration suite across all five profiles.

---

## 8.8 — Media Optimisation

**Images.** Uploaded as-is when the user chooses original quality (`05-FEATURE-BIBLE.md` §5.9). Otherwise: longest edge 2,048 px, JPEG q82 or AVIF where both ends support it. Thumbnails are generated on-device at 400 px and shipped inside the message envelope, so a thumbnail is visible before any media download begins. Progressive decode; blurhash placeholder at the exact final dimensions so nothing shifts.

**Video.** H.264 baseline for compatibility, HEVC where hardware supports it, capped at 1080p30 for sharing. Always hardware-encoded — software encoding on Tier C is a thermal and battery failure. A poster frame and duration ship in the envelope.

**Audio.** Opus 24 kbps mono for voice notes — indistinguishable from higher rates for speech and roughly a third of the bytes. Waveform data (64 samples) is precomputed on-device and sent in the envelope so the waveform renders before the audio downloads.

**Universal rule:** the recipient sees *something* correct — thumbnail, blurhash, waveform, poster frame — before any byte of the media itself arrives. This is what makes the app feel fast on a bad connection, and it costs a few hundred bytes per message.

---

## 8.9 — Accessibility Score

| Metric | Target |
|---|---|
| Automated accessibility checks | **100 % pass, zero suppressions** |
| Contrast (all text) | 100 % of pairs meet `02-VISUAL-DESIGN-SYSTEM.md` §2.15 |
| Touch targets ≥44 px | 100 %, asserted by test |
| Screen-reader labelled elements | 100 % (compile-enforced for icons, `07` §7.3) |
| Full task completion via screen reader | Every MVP feature, verified manually per release |
| Dynamic type to 200 % | No clipping or overlap on any screen |
| Keyboard operation (web/desktop) | Every action reachable, focus always visible |

---

## 8.10 — Stability

| Metric | Target | Gate |
|---|---|---|
| Crash-free sessions | **> 99.9 %** | Rollout halts below 99.8 % |
| Crash-free users | **> 99.5 %** | Rollout halts below 99.3 % |
| ANR rate (Android) | < 0.2 % | Play Store vitals threshold |
| Message delivery success | **100 %** (correctness, not a percentage to optimise) | Any loss is Sev-1 |
| Data loss incidents | **0** | Any occurrence halts all releases |
| Backend availability | > 99.9 % monthly | Error budget policy (`06` §6.11) |

---

## 8.11 — The Performance Budget Process

1. **Every feature has a budget before it has a design.** "This must not add more than 8 MB of memory, 30 ms to cold start, or 200 KB to the binary." A feature that cannot state its budget is not specified yet.
2. **Budgets are measured in CI on physical hardware**, per pull request, per tier.
3. **A regression fails the build.** Not a warning, not a dashboard, not a ticket.
4. **Exceeding a budget requires an explicit trade**: something else gives up an equivalent amount, and the trade is recorded in the pull request. Budgets do not inflate quietly, which is the only way they survive contact with a roadmap.
5. **Production is measured continuously**, segmented by device tier, network profile, and region. Lab numbers describe the machine; production numbers describe the user.
6. **The four wall numbers** (`06` §6.11) are reviewed daily by the whole team, and are visible to everyone in the company.
7. **A quarterly performance week** where no features ship and the entire engineering team works on the numbers. Not a reward for good behaviour — a standing calendar item, because entropy is constant and every product in this category lost this fight by degrees.
