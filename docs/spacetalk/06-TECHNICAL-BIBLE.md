# THE SPACETALK TECHNICAL BIBLE

### Part 6 — Architecture, Engineering, and Operations

*Governed by `00-EDITORIAL-BIBLE.md`. Decisions with lasting consequence are recorded as ADRs in `12-ADR.md` and referenced here. This document describes the system we intend to build for the MVP and the first two phases beyond it — not a hypothetical system for a billion users. Scale plans that are not yet needed are marked as such.*

---

## 6.1 — Architectural Principles

1. **Boring where it doesn't differentiate.** We are inventing in exactly two places: client performance and the on-device intelligence layer. Everywhere else — datastores, queues, deployment — we use the most well-understood option available.
2. **Local-first.** The device's database is the source of truth for the interface. The network is a synchronisation mechanism, not a data source (ADR-008).
3. **The server should be unable to do the things we promise not to do.** Design so that a compromised server, a subpoenaed server, or a malicious insider still cannot read message content.
4. **One codebase per concern.** One client codebase for all platforms (ADR-001). One backend language (ADR-002).
5. **Scale when measured, not when imagined.** Every scaling step in §6.10 has a numeric trigger. Building for 100 M users at 100 K users is how startups die with excellent architecture diagrams.
6. **Every dependency is a liability.** A dependency must save more work than the sum of its upgrade, audit, and outage costs over three years.

---

## 6.2 — Client: Flutter

**Flutter 3.x, Dart 3.x, one codebase for iOS, Android, web, and desktop** (ADR-001).

**Layering.**

```
  presentation/      Widgets. Stateless where possible. No business logic. No I/O.
  application/       Riverpod providers, view-models, orchestration.
  domain/            Pure Dart entities and use-cases. Zero framework imports.
                     Fully unit-testable with no mocks of Flutter.
  data/              Repositories, local store (Drift/SQLite), remote (gRPC/WS), crypto FFI.
  platform/          Thin channels for notifications, camera, keystore, background tasks.
```

Dependencies point inward only. `domain` imports nothing from the other layers, which is what makes the business logic testable at speed.

**State management:** Riverpod. Chosen for compile-time safety, testability without a widget tree, and fine-grained rebuilds — the last matters because the transcript must rebuild individual bubbles, not the list.

**Local database:** SQLite via **Drift** (typed queries, migrations, and a compile-time schema). SQLCipher for at-rest encryption of the message store, with the key held in the platform keystore (iOS Keychain with `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly`; Android Keystore with StrongBox where available).

**Cryptography:** `libsignal` (Rust) via `dart:ffi`, not a Dart reimplementation (ADR-003). This is the single highest-risk integration in the client and is treated as such: pinned versions, reproducible builds, and a conformance test suite run against the official test vectors on every commit.

**Rendering rules that follow from the performance targets (`08`):**
- The transcript is a `CustomScrollView` with slivers and stable keys; message heights are measured once and cached, so scrolling never re-measures.
- Images decode off the platform thread at their *display* resolution, never full resolution — the most common source of jank and out-of-memory kills on cheap Android devices.
- `RepaintBoundary` around every bubble; no `Opacity` or `ClipRRect` in scrolling content (both force expensive save layers) — rounded corners come from `ShapeDecoration`.
- No `setState` above a list item. Ever.
- Shader warm-up on first launch to avoid the first-run jank Flutter is known for; verified with `--purge-persistent-cache` in the performance test suite.

**Platform split.** iOS and Android are full clients at MVP. The linked-device client is the Flutter web build (ADR-012); native desktop follows in Phase 2 from the same codebase.

---

## 6.3 — Backend

**Go 1.2x, a modular monolith, deployed as a handful of services** (ADR-002). Not microservices. Not Kubernetes at MVP.

**Services at MVP (four deployables):**

| Service | Responsibility | Scaling property |
|---|---|---|
| **gateway** | WebSocket termination, authentication, connection state, per-connection rate limiting, fan-out to connected devices | Stateful (holds sockets); scales horizontally with consistent hashing over user ID |
| **core** | Everything transactional: accounts, conversations, message envelopes, groups, channels, profiles, devices | Stateless; scales horizontally |
| **media** | Upload/download orchestration, presigned URLs, thumbnail generation of *ciphertext-adjacent* metadata only | Stateless |
| **push** | APNs/FCM dispatch, token lifecycle, wake-up envelopes | Stateless; queue-driven |

**Why a modular monolith.** At MVP, a five-person backend team splitting into twelve microservices spends its time on distributed-systems debugging rather than product. The module boundaries inside `core` are enforced by package structure and an import linter, so extracting a module into its own service later is a mechanical change. We take on the *boundary* discipline immediately and the *deployment* complexity only when a module's scaling profile actually diverges. Trigger conditions are in §6.10.

**Realtime transport.** A single WebSocket per device carrying length-prefixed Protocol Buffers. Chosen over raw HTTP/2 streams for browser parity and over MQTT for control. The protocol is a small, versioned, bidirectional command/event stream — not JSON, because envelope overhead at 100 K messages/second is real money and real latency.

---

## 6.4 — API Architecture

**Three surfaces, deliberately different:**

1. **Realtime (WebSocket + protobuf)** — everything in the hot path: send, receive, typing, presence, receipts, calls signalling. Bidirectional, ordered per conversation, with per-connection backpressure.
2. **Request/response (gRPC, with a gRPC-Web gateway)** — account operations, group management, media orchestration, settings. Strongly typed, versioned, code-generated for Dart and Go from one `.proto` source of truth.
3. **Public HTTP/JSON API (Phase 3)** — for business integrations and bots. Deliberately separate from the internal API so we are never forced to keep an internal shape stable for external reasons.

**Contracts.**
- Protobuf schemas live in one repository and are the single source of truth. Breaking changes require a new field number, never a reused one; a CI check (`buf breaking`) fails the build on any incompatible change.
- **Every client supports N and N−1 protocol versions.** Servers support N through N−3, giving roughly 12 months of client-upgrade runway before a forced update.
- Idempotency keys on every mutating call, so a retry after a timeout can never duplicate a message.
- Errors are typed enums, never strings parsed by clients.

**Envelope model.** The server stores and routes *envelopes*: `{conversation_id, sender_device_id, recipient_device_id, sequence, ciphertext, ciphertext_len, server_timestamp}`. The server can see who talked to whom and when — this is unavoidable metadata for routing — and it can see nothing else. Minimising and expiring that metadata is covered in §6.13.

---

## 6.5 — Database

**PostgreSQL 16 as the primary store at MVP** (ADR-004), with Redis for ephemeral state and S3-compatible object storage for media.

| Data | Store | Notes |
|---|---|---|
| Accounts, devices, prekeys, profiles | Postgres | Small, highly relational, strongly consistent |
| Conversations, membership, groups, channels | Postgres | Same |
| Message envelopes (undelivered) | Postgres, partitioned by month | Deleted on delivery to all devices, or at 30 days |
| Message envelopes (delivered) | **Not stored** | Devices hold history; the server is a relay with a retention window, not an archive. This is a privacy decision *and* a cost decision. |
| Media blobs | S3-compatible object storage + CDN | Client-side encrypted; the storage layer holds ciphertext only |
| Presence, typing, connection routing | Redis | Ephemeral, TTL'd, never persisted |
| Rate limits | Redis | Sliding window |
| Push tokens | Postgres | Rotated, pruned on invalidation |
| Search index | **On-device SQLite FTS5 only** | No server-side message index exists, because there is no server-side plaintext |

**Key schema decisions.**
- Message envelopes are partitioned by month and dropped by partition, not deleted by row — deleting 100 M rows individually is how a database dies.
- `(conversation_id, sequence)` is the ordering authority, assigned server-side, monotonic per conversation, and never derived from a clock.
- Device fan-out is materialised at send time: one envelope row per recipient device, so delivery state is per-device and truthful (`05-FEATURE-BIBLE.md` §5.5).
- Prekey bundles are consumed atomically with `SELECT ... FOR UPDATE SKIP LOCKED`, with a last-resort signed prekey when one-time keys are exhausted.
- All destructive operations are soft-delete plus a scheduled purge, so a bug cannot cause instant irreversible loss.

**Scaling path (triggered, not pre-built).** When envelope write throughput sustains >30 K/s or the undelivered table exceeds ~500 GB, envelopes migrate to ScyllaDB behind the existing repository interface. That interface exists from day one precisely so the migration is a swap; Scylla itself is not deployed until the trigger fires (ADR-004).

---

## 6.6 — Authentication, Identity, and Push

**Registration.** Username plus a recovery method (phone or email, optional but strongly recommended and clearly explained). Verification by code. Registration is rate-limited by IP, device attestation, and proof-of-work escalation under attack.

**Session authentication.** Per-device long-lived credentials backed by a device keypair; access tokens are short-lived (15 min) and refreshed with a rotating refresh token bound to the device key. Token theft without the device key is useless.

**Passkeys / WebAuthn** for account recovery from Phase 2, replacing SMS wherever the platform supports it — SMS is the weakest link in every messenger's security model and we intend to reduce our dependence on it rather than build on it.

**Biometric app lock** is local-only: it gates access to the local database key in the platform keystore. It is not a server-side authentication factor, and we do not claim it is.

**Push notifications.**
- APNs (with an iOS Notification Service Extension) and FCM.
- **Payloads contain no content**: `{envelope_id, conversation_id_hash, priority}`. The extension fetches the envelope and decrypts locally to build the notification (`05-FEATURE-BIBLE.md` §5.12).
- A fallback persistent socket exists for devices without Google services, with battery-aware backoff.
- Push tokens are rotated and pruned; an invalid token is a signal to prune, never to retry indefinitely.

---

## 6.7 — Encryption

**The protocol** (ADR-003): **X3DH** for asynchronous key agreement, **Double Ratchet** for message encryption, via `libsignal`. We are not designing a protocol. Rolling our own cryptography would be the single most likely way for this project to cause real harm to real people.

| Concern | Approach |
|---|---|
| 1:1 messages | Double Ratchet, per-device sessions, forward secrecy and post-compromise security |
| Group messages | **Sender Keys** — each sender has a per-group chain key distributed pairwise; sender keys rotate on every membership removal |
| Group scaling limit | Sender Keys are O(members) on key distribution. Practical ceiling ~1,000 members, which is exactly why `05-FEATURE-BIBLE.md` §5.5 caps groups there at MVP. **MLS (RFC 9420) is the Phase 3 migration** that lifts it — planned, scheduled, and not pretended to exist earlier. |
| Multi-device | Each device is a separate cryptographic identity with its own sessions. No key sharing between devices, no primary device (ADR-012). |
| Media | Per-file AES-256-GCM key, generated client-side, transmitted inside the encrypted message envelope. Storage holds ciphertext and cannot decrypt it. |
| Calls | SRTP with DTLS-SRTP for 1:1. Group calls use an SFU with **insertable-stream E2EE (SFrame)** so the SFU forwards frames it cannot decrypt (ADR-006). |
| Stories | Encrypted to the selected audience's device keys |
| Channels | **Not E2EE** — encrypted in transit (TLS 1.3) and at rest. Stated in the UI (`05-FEATURE-BIBLE.md` §5.6). |
| Assistant conversation | **Not E2EE** — it is a conversation with a server. Stated in the UI (`04-AI-PHILOSOPHY.md` §4.1). |
| At rest on device | SQLCipher, key in platform keystore |
| Transport | TLS 1.3, certificate pinning with a backup pin and a documented rotation runbook |
| Post-quantum | Hybrid X25519 + ML-KEM-768 key agreement, Phase 3. Recorded as a roadmap item with a date, not a marketing claim. |

**Verification.** Safety numbers per contact, QR verification, and a mandatory acknowledgement when a contact's keys change (`02-VISUAL-DESIGN-SYSTEM.md` §2.4).

**What we deliberately do not build:** key escrow, a server-side "recover my messages" path, plaintext backup to any cloud, or a message-content moderation pipeline. Each is technically simple and would void the core promise.

**Honest statement of limits.** E2EE protects content in transit and at rest on our servers. It does not protect against a compromised device, a screenshot, a malicious participant in a conversation, or an OS-level attacker. We say this plainly in the product rather than allowing the marketing implication that encryption makes users invulnerable.

---

## 6.8 — Offline Sync and Caching

**The sync model.**

1. The client writes to its **local SQLite store first** and renders from it. Always.
2. Mutations go into a durable **outbox** table with a monotonic local sequence, an idempotency key, and a retry policy.
3. A background worker drains the outbox in order, respecting per-conversation ordering. A failed send blocks only its own conversation, never the whole queue.
4. Inbound: the client holds a **per-conversation cursor**. On connect, it requests everything after the cursor. The server streams envelopes; the client decrypts, writes, advances the cursor, and acknowledges. Acknowledgement is what allows the server to delete.
5. **Gap detection**: sequence numbers are contiguous per conversation. A gap triggers an automatic retransmit request. An unfillable gap becomes a visible marker in the transcript (`05-FEATURE-BIBLE.md` §5.13) — never an invisible hole.

**Conflict resolution is by rule, never by prompt** (`03-UX-BIBLE.md` §3.7): server sequence for ordering; last-writer-wins by device timestamp for edits, with losers retained in edit history; deletions always dominate edits; group membership is server-authoritative.

**Caching.**

| Layer | Policy |
|---|---|
| Message store | Permanent on device until the user deletes it. Never evicted automatically. |
| Media | LRU with a user-configurable cap (default 4 GB); originals re-downloadable while server retention holds |
| Thumbnails | Permanent, small, generated on device |
| Avatars | Memory + disk LRU, content-hash-keyed, immutable |
| Search index | Rebuilt from the message store; disposable |
| CDN | Immutable media objects, `Cache-Control: immutable`, long TTL, keyed by content hash |

**A rule with teeth:** the app must fully render the conversation list and the last screen of any open conversation **with the network stack disabled**. This is asserted by an automated test on every release, not verified by hand.

---

## 6.9 — Realtime Media (Calls)

- **Signalling** over the existing WebSocket — no separate signalling infrastructure.
- **1:1 calls attempt peer-to-peer first** (ICE with STUN), falling back to TURN relay when NAT traversal fails. P2P means lower latency and no media touching our servers.
- **Group calls use an SFU** (LiveKit, self-hosted) with insertable-stream E2EE, so the SFU routes frames it cannot decrypt (ADR-006). An MCU is rejected: server-side mixing means server-side plaintext.
- **Codecs:** Opus for audio (always, with in-band FEC and DTX), VP8 at MVP for video with AV1 evaluated in Phase 2 where hardware support exists.
- **The audio-priority rule** (`05-FEATURE-BIBLE.md` §5.4) is implemented as an explicit bandwidth allocator: audio gets its floor first, video receives the remainder, and simulcast layers are dropped from the top down.
- TURN servers are deployed in every region; media never crosses regions unnecessarily.

---

## 6.10 — Scalability

**Present target: 1 M registered users, 200 K concurrent connections, 50 K messages/second peak.** That is a real target for the first two years and is achievable with the architecture above on a modest fleet. Everything beyond it is written as a *trigger*, not a plan we execute now.

| Trigger | Action |
|---|---|
| >150 K concurrent sockets | Add gateway instances; shard connection routing by consistent hash on user ID |
| Postgres write CPU sustained >60 % | Read replicas for all non-authoritative reads; then partition `core` by user-ID range |
| Envelope writes >30 K/s **or** undelivered table >500 GB | Migrate envelopes to ScyllaDB behind the existing interface (ADR-004) |
| p95 client latency >400 ms in a region | Deploy a regional gateway + TURN + CDN edge; core stays central until data-residency requires otherwise |
| A regulatory data-residency obligation | Regional deployment with data pinned by account home region |
| Any single module's scaling profile diverges >5× from the rest | Extract that module from the monolith into its own deployable |

**What we are explicitly *not* doing at MVP:** Kubernetes, service mesh, multi-region active-active, event sourcing, CQRS, a custom orchestration layer. Each is defensible at scale and each would cost us the first year (ADR-002).

**Deployment at MVP:** containers on a managed platform, one primary region, a warm standby in a second region, infrastructure as code (Terraform) from commit one. Migrating to Kubernetes later is a well-trodden path; migrating away from premature complexity is not.

---

## 6.11 — Monitoring and Observability

**Instrumentation:** OpenTelemetry throughout — traces, metrics, logs — with trace context propagated from the client through the gateway to the datastore.

**The four numbers on the wall**, reviewed daily:
1. p50/p95/p99 send-to-delivered latency.
2. Message delivery success rate (the correctness metric from `05-FEATURE-BIBLE.md` §5.1).
3. Crash-free sessions and crash-free users.
4. Cold-start time at p95, segmented by device tier.

**Stack:** Prometheus + Grafana for metrics, Tempo/Jaeger for traces, Loki for logs, Sentry for client crashes and errors.

**SLOs** (Phase 1): message delivery 99.95 % monthly; API availability 99.9 %; call setup success 99 %. Error budgets are real: when a budget is exhausted, feature work stops until reliability work restores it. This is a written policy, not an aspiration.

**Logging discipline — a privacy requirement, not a hygiene one:**
- **Message content is never logged.** Not at debug level, not behind a flag, not in a crash report. A lint rule and a CI check block any log call taking a message body.
- Logs carry IDs, never phone numbers, emails, or handles.
- Retention: 30 days for application logs, 7 days for connection logs, 90 days for security-relevant audit logs.
- Client crash reports are scrubbed on-device before upload, and the user can disable them.

**Alerting** distinguishes pages (user-visible breakage) from tickets (everything else). An alert that pages without an actionable runbook is deleted.

---

## 6.12 — Testing

| Layer | Coverage requirement | Tooling |
|---|---|---|
| Domain logic (Dart) | **90 % line coverage, enforced in CI** | `package:test` |
| Widgets | Every component in every state, both themes, LTR + RTL | `flutter_test` |
| Golden/visual | Every component; diffs require explicit approval | `golden_toolkit` |
| Integration (client) | Sign-up, send, receive, call, link device, offline→online | `integration_test` on real devices |
| Backend unit | 85 % on `core` | Go `testing` |
| Backend integration | Full API against real Postgres/Redis in containers | `testcontainers` |
| **Crypto conformance** | **100 % of official libsignal test vectors, every commit** | Custom harness |
| Protocol compatibility | Client N against server N, N−1, N−2, N−3 | Matrix job |
| Load | 200 K concurrent connections, 50 K msg/s, weekly | k6 + custom WS harness |
| Chaos | Kill gateway, partition database, saturate the network — monthly in staging | Custom |
| Accessibility | Contrast, target size, missing semantic labels — every PR | Automated + manual VoiceOver/TalkBack gate |
| Performance | Cold start, frame rate, memory — every PR, on real hardware | `flutter driver` + a physical device lab |

**Non-negotiable test gates.** A release is blocked by: any crypto conformance failure, any performance regression beyond budget (`08`), any accessibility regression, any protocol-compatibility failure, or any drop in the offline-render assertion (§6.8).

**The device lab.** A physical rack of the Tier-A/B/C reference devices (`08-PERFORMANCE-STANDARDS.md` §8.7) running the performance and integration suites on every merge to main. Emulators do not tell the truth about jank, thermals, or memory pressure, and the cheap-Android experience is the one most likely to be quietly bad.

---

## 6.13 — Data Retention and Minimisation

A published schedule, enforced by automated jobs, and audited quarterly:

| Data | Retention |
|---|---|
| Undelivered message envelopes | Until delivered to all devices, or 30 days |
| Delivered message envelopes | Deleted immediately (server-side) |
| Media blobs | 90 days after last access (free) / 365 days (Plus) |
| Connection metadata (IP, timestamps) | 7 days |
| Push tokens | Until invalidated |
| Account record | Until deletion, then 30 days of tombstone, then purged |
| Assistant conversation | 90 days by default, user-configurable down to 0 |
| Security audit logs | 90 days |
| Analytics events | 13 months, aggregated and pseudonymous (`11-BUSINESS-AND-COMPLIANCE.md` §11.5) |

**Deletion means deletion**, including from backups within the backup rotation window (35 days), and this is verified by a quarterly audit that attempts to retrieve deleted records rather than assuming a policy was followed.

---

## 6.14 — CI/CD

**Pipeline (every pull request):** format → static analysis → domain unit tests → widget + golden tests → backend unit + integration tests → crypto conformance → protobuf breaking-change check → accessibility checks → build all targets → performance smoke on a physical device.

**On merge to main:** full integration suite → device-lab performance suite → deploy backend to staging → nightly load test.

**Release trains.** A client release every two weeks; the backend deploys continuously behind feature flags. The two are decoupled by protocol versioning (§6.4) — the backend never requires a client release, and a client release never requires a coordinated backend deploy.

**Client rollout:** internal → 1 % → 10 % → 50 % → 100 %, each stage gated on crash-free rate and the four wall numbers (§6.11). Automatic halt on any regression. Every release is one tap from rollback, and rollback is *rehearsed*, not theorised.

**Feature flags** are server-controlled, default-off, and have a mandatory expiry date — a flag older than 90 days fails the build, because permanent flags are how a codebase becomes untestable.

**Secrets** never touch the repository; they live in a managed secret store with per-environment scoping and automatic rotation. Signing keys for both app stores are in an HSM with a documented, tested recovery procedure.

**Supply chain:** dependencies pinned by hash, an SBOM generated per release, automated CVE scanning that blocks on high severity, and reproducible builds for the client so that a published binary can be verified against its source. Reproducible builds matter enormously for an encrypted messenger: it is the only way for outsiders to check that the app they installed is the app we published.

---

## 6.15 — Security Operations

- **Threat model published and maintained**, covering: malicious server, compromised device, malicious conversation participant, network adversary, hostile insider, and supply-chain attacker.
- **Third-party security audit before public launch**, and annually thereafter. The cryptographic implementation is audited separately by a specialist firm. Results are published.
- **Bug bounty** from public beta, with published severity tiers and response times.
- **Insider-risk controls:** production data access requires a ticket, is time-boxed, is logged immutably, and is reviewed weekly. No engineer has standing production database access.
- **Incident response:** documented severity levels, on-call rotation, a 72-hour user-notification commitment for any breach affecting user data, and a published post-mortem for anything user-visible.
- **Transparency report** twice yearly from Phase 2 (`04-AI-PHILOSOPHY.md` §4.10).
