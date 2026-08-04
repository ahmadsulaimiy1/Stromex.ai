# SPACETALK ARCHITECTURE DECISION RECORDS

### Part 12 — Decisions With Consequences

*Each record states the decision, the context, the alternatives seriously considered, the consequences we accept, and the conditions under which we would revisit. An ADR is never edited after acceptance — it is superseded by a new one.*

**Status values:** Accepted · Superseded · Deprecated.

---

## ADR-001 — Flutter for every client platform

**Status:** Accepted

**Context.** We must ship iOS, Android, and a linked-device client at MVP with a small team, and reach desktop in Phase 2. Native-per-platform gives the best ceiling on performance and platform integration. Cross-platform gives velocity and consistency.

**Decision.** Flutter for all client surfaces, with thin native platform channels for notifications, camera, keystore, and background execution.

**Alternatives considered.**
- *Native Swift + Kotlin.* Best possible performance and platform fidelity. Rejected: it is two teams, two release cycles, and two implementations of every subtle piece of encryption and sync logic — which is also two places for those bugs to differ. For a team of our size it is the difference between shipping and not.
- *React Native.* Larger hiring pool. Rejected: the JS bridge remains a latency and jank risk in exactly our hottest path (a long, media-rich, constantly-updating scroll view), and our differentiator is measured frame rate.
- *Kotlin Multiplatform with native UI.* Shares logic, not UI. A genuinely strong option. Rejected on the grounds that our UI *consistency* is a brand requirement (`00` §0.5), and KMP would leave us building the transcript twice.

**Consequences we accept.**
- Some platform features arrive later than native apps get them.
- Larger binary size than a native app (mitigated per `08-PERFORMANCE-STANDARDS.md` §8.6).
- We must be unusually disciplined about Flutter's known jank sources (`06` §6.2) — shader warm-up, save layers, image decode — and we treat them as first-class engineering work, not incidental tuning.
- Flutter web is not as good as a native desktop app; hence ADR-012.

**Revisit if.** Frame-rate targets prove unreachable on Tier-C hardware after a dedicated optimisation effort, or a platform materially restricts non-native clients.

---

## ADR-002 — A modular monolith in Go, not microservices

**Status:** Accepted

**Context.** The reference architectures for messaging at scale are microservice-based. We are not at scale, and we will not be for at least two years.

**Decision.** Four Go deployables (`gateway`, `core`, `media`, `push`), with `core` internally modular and boundaries enforced by an import linter. Postgres + Redis + object storage. No Kubernetes, no service mesh, no event sourcing at MVP.

**Alternatives considered.**
- *Microservices from day one.* Rejected: distributed transactions, tracing complexity, and deployment overhead consume a small team's entire capacity, and every boundary drawn before the domain is understood is drawn in the wrong place.
- *Elixir/Phoenix.* Genuinely excellent for millions of concurrent connections, and the BEAM's supervision model fits a gateway well. Rejected on hiring: the pool is small, and a language nobody can hire for is a liability that compounds. Go gets us most of the concurrency story with a far larger pool.
- *Node.js/TypeScript.* Rejected for the fan-out path — single-threaded event-loop stalls under CPU-bound crypto and protobuf work are hard to reason about at p99.

**Consequences we accept.**
- A larger blast radius per deploy in `core`, mitigated by feature flags and staged rollout.
- We will have to extract services later, under load. We reduce that cost by enforcing module boundaries now, so extraction is mechanical.
- Some scaling ceilings arrive earlier. Each has a written trigger (`06` §6.10).

**Revisit if.** Any module's scaling profile diverges more than 5× from the rest, or team size exceeds roughly 25 backend engineers, at which point deployment independence starts paying for itself.

---

## ADR-003 — Signal Protocol via libsignal; Sender Keys for groups; MLS deferred

**Status:** Accepted

**Context.** We promise end-to-end encryption for personal messaging as a non-negotiable (`00` §0.6.3). We must choose a protocol and an implementation.

**Decision.** X3DH + Double Ratchet via the official `libsignal` Rust implementation, bound into Flutter through `dart:ffi`. Group messaging uses Sender Keys. **MLS (RFC 9420) is a Phase 3 migration**, planned and scheduled, not claimed earlier.

**Alternatives considered.**
- *Implement the protocol ourselves in Dart.* Rejected without hesitation. Cryptographic implementation bugs are silent, catastrophic, and disproportionately harm the people most in need of the protection.
- *MLS at MVP.* The better long-term protocol: logarithmic group operations, a clean multi-device story, and an actual standard. Rejected for MVP because implementations were not yet battle-tested at the maturity we need, and the integration risk sits on the critical path of everything. We take Sender Keys' known ceiling and schedule the migration.
- *Matrix/Olm+Megolm.* Rejected: adopting the federation model brings metadata and moderation properties we have not chosen.

**Consequences we accept.**
- Sender Keys make group key distribution O(members), which is exactly why groups are capped at 1,000 at MVP (`05` §5.5). We state the cap as a product decision because it *is* one, derived from this protocol choice.
- Removing a member requires a full sender-key rotation — a visible cost in large groups.
- The FFI boundary is the highest-risk integration in the client and is treated accordingly (pinned versions, official test vectors on every commit, dedicated audit — `06` §6.12).

**Revisit.** Scheduled: Phase 3 MLS migration, planned as a dual-stack transition with per-conversation upgrade, never a flag day.

---

## ADR-004 — PostgreSQL for everything at MVP; ScyllaDB only on trigger

**Status:** Accepted

**Context.** Messaging workloads are usually cited as a wide-column-store use case. We have no traffic yet.

**Decision.** Postgres 16 for all persistent state, with message envelopes in monthly partitions. All envelope access goes through one repository interface so the store can be swapped. ScyllaDB is deployed only when envelope writes sustain >30 K/s or the undelivered table exceeds 500 GB.

**Alternatives considered.**
- *Cassandra/Scylla from day one.* Rejected: no transactions, weaker consistency, harder operations, and vastly more expensive per unit of engineering attention — to solve a problem we do not have.
- *A separate store per data type at MVP.* Rejected: five datastores is five on-call surfaces.

**Consequences we accept.**
- A migration is in our future if we succeed. We reduce its cost with the repository interface and by never letting application code depend on Postgres-specific behaviour in the envelope path.
- Partition maintenance is operational work we take on now.

**Key enabling insight.** Delivered envelopes are deleted, not archived (`06` §6.5). The server is a relay, not an archive. That single decision keeps the hot dataset proportional to *undelivered* traffic rather than to total history, and it is what makes Postgres viable far longer than intuition suggests.

---

## ADR-005 — AI never processes E2EE content without an explicit, visible, revocable grant

**Status:** Accepted

**Context.** The product promises both strong privacy and strong intelligence. These genuinely conflict, and the conflict cannot be resolved by wording.

**Decision.** A three-tier rule, in priority order: on-device first; server-side only with a per-conversation, visible, revocable grant that is disclosed to all participants; otherwise the feature does not ship. The assistant conversation is a separate, explicitly non-E2EE surface, labelled as such in the interface.

**Alternatives considered.**
- *Server-side AI on all content with a privacy policy.* Rejected: it makes the encryption promise a marketing claim.
- *No AI features at all.* Rejected: it forfeits one of the three things the product exists to be (`00` §0.7).
- *Confidential computing / TEEs for server-side processing.* Promising, and on the Phase 4 research list. Rejected for MVP: attestation for a user is not verifiable in practice today, and "trust our enclave" is a weaker guarantee than "it never left your phone."

**Consequences we accept.**
- Some AI features are worse than a competitor's equivalent, because small on-device models are worse than large server models. We take the quality hit and say why.
- Semantic search covers only on-device history (`04` §4.6).
- On-device model work becomes a core engineering competency and a real cost centre.
- We must ship an audit that continuously verifies zero ungranted AI invocations on E2EE content, and treat a non-zero result as Sev-1.

---

## ADR-006 — LiveKit SFU with insertable-stream E2EE for group calls

**Status:** Accepted

**Context.** 1:1 calls can be peer-to-peer. Group calls cannot — mesh topology fails past three or four participants on mobile uplinks.

**Decision.** Self-hosted LiveKit as the SFU, with E2EE via insertable streams (SFrame), so the SFU forwards frames it cannot decrypt. 1:1 calls attempt P2P first and fall back to TURN.

**Alternatives considered.**
- *MCU (server-side mixing).* Better for very weak clients. Rejected outright: mixing requires decryption, which means server-side plaintext media.
- *A managed third-party SFU.* Faster to ship. Rejected: media routing is core infrastructure, and a third party in the media path is a party in a conversation.
- *Mesh for small groups.* Retained as an optimisation for 3-participant calls where uplink measurement supports it; not the primary architecture.

**Consequences we accept.**
- Operating an SFU fleet is real work (TURN, regional deployment, capacity planning).
- Insertable-stream E2EE costs some CPU and rules out server-side features that would need plaintext (server-side recording, server-side transcription) — which is consistent with ADR-005 and therefore not a loss we mind.
- Simulcast layer selection must be implemented carefully to honour the audio-priority rule (`05` §5.4).

---

## ADR-007 — Push notification payloads carry no content

**Status:** Accepted

**Context.** The simplest push implementation sends the message text in the payload. It is also the one that hands message content to Apple and Google.

**Decision.** Payloads contain only `{envelope_id, conversation_id_hash, priority}`. The device fetches and decrypts locally — on iOS via a Notification Service Extension, on Android in the FCM handler.

**Alternatives considered.**
- *Content in the payload.* Rejected: it defeats E2EE at the last metre for the most-read text in the product.
- *Generic "New message" with no fetch.* Rejected: it degrades the experience for no additional privacy over the chosen design.

**Consequences we accept.**
- A network round trip in the notification path, which we budget for (p95 < 2 s end to end).
- The iOS extension has a hard memory limit (24 MB) and a short execution window, so the decryption path must be lean and cannot load the full client stack.
- If the fetch fails, we fall back to "New message" rather than showing nothing.

---

## ADR-008 — Local-first architecture with an outbox

**Status:** Accepted

**Context.** Our users are frequently on unreliable networks. A request/response client is unusable there, and "offline support" bolted on afterwards never really works.

**Decision.** The on-device SQLite database is the source of truth for the UI. All mutations are written locally first and drained from a durable outbox. The server is a synchronisation and relay mechanism.

**Alternatives considered.**
- *Network-first with a cache.* Rejected: every screen becomes a loading state, and offline behaviour is a permanent afterthought.
- *A CRDT-based sync engine.* Genuinely elegant. Rejected as over-engineering for our data shapes: messages are append-only with server-assigned ordering, which is a much simpler problem than general concurrent editing. We would be paying CRDT complexity for a conflict class we mostly do not have.

**Consequences we accept.**
- Migration discipline on the local schema becomes critical — a bad client migration can destroy a user's history, so every migration is forward-tested against real historical databases in CI.
- Local storage grows with history, requiring user-visible storage management.
- Some server-side changes need client-side reconciliation logic.

---

## ADR-009 — No advertising, ever; subscription and business revenue only

**Status:** Accepted

**Context.** Advertising is the default business model for communication products at scale, and it is available to us.

**Decision.** No advertising in any form. Revenue from consumer subscriptions (SpaceTalk Plus), business platform fees, and, from Phase 3, creator monetisation take rates. Codified as `00` §0.6 clause 1.

**Alternatives considered.**
- *Ads in a non-conversation surface.* Rejected: it would create an internal incentive to build such a surface and then to grow it — which is precisely how every calm product became a loud one.
- *Selling anonymised data.* Rejected: not re-identification-safe in practice, and inconsistent with everything else here.

**Consequences we accept.**
- Slower revenue ramp and a harder fundraising story against ad-supported comparables.
- Free users cost money; unit economics discipline is a permanent product constraint, not a finance problem (`11-BUSINESS-AND-COMPLIANCE.md` §11.4).
- We cannot subsidise unlimited free storage, which is why file retention has honest, stated limits.

**Why it is an ADR and not just a policy.** Because it constrains architecture: no ad-serving infrastructure, no user-profiling pipeline, no engagement-ranking model, and no data-collection surface built "in case." Those absences are load-bearing.

---

## ADR-010 — No address-book upload at MVP; username-first discovery

**Status:** Accepted

**Context.** Contact discovery drives growth, and every mainstream approach leaks. Hashed phone numbers are trivially reversible across the whole global number space; private set intersection at scale needs infrastructure (secure enclaves, custom protocols) that a startup cannot make credible.

**Decision.** No address-book upload at MVP. Discovery is by username, QR code, or share link. Discoverability by phone/email is opt-in and off by default (`05` §5.11).

**Alternatives considered.**
- *Hashed phone-number upload.* The industry standard. Rejected: the hash provides essentially no protection for a 10–15 digit space, and shipping it would mean holding a social graph we promised not to build.
- *PSI with a trusted enclave.* The right long-term answer. Deferred: we cannot make the attestation story honest at our current maturity.

**Consequences we accept.**
- **Materially slower viral growth.** This is the single largest deliberate growth cost in the product, and we are taking it with open eyes. Growth strategy compensates through share links and channel-led acquisition (`11` §11.6).
- Some users find the app "empty" at first, which puts real weight on the onboarding empty state (`03` §3.6).

**Revisit if.** A discovery mechanism exists that we can explain honestly in two sentences to a non-technical user and defend against a well-resourced adversary. Phase 3 research item.

---

## ADR-011 — SpaceTalk is a greenfield product, not an extension of the existing StromeX codebase

**Status:** Accepted

**Context.** This repository already contains StromeX — an AI knowledge-work product built on FastAPI (Python) and Next.js, with its own Editorial Bible under `docs/`. SpaceTalk is a real-time communication platform. Reuse was considered.

**Decision.** SpaceTalk is built as a separate product with its own stack (Flutter + Go). The StromeX application code and documentation are left untouched; SpaceTalk documentation lives under `docs/spacetalk/`.

**Alternatives considered.**
- *Extend the existing FastAPI backend.* Rejected: Python's concurrency model is a poor fit for holding hundreds of thousands of persistent WebSocket connections and for the CPU-bound fan-out path, and retrofitting a request/response codebase into a realtime one is usually slower than starting clean.
- *Reuse the Next.js web client as the primary surface.* Rejected: the MVP is mobile-first (`00` §0.5), and ADR-001 commits the client to Flutter.

**Consequences we accept.**
- Two stacks in one organisation, with the operational and hiring overhead that implies.
- Shared concerns (identity, billing) will need deliberate integration if the two products ever converge.

**Open question for the founder.** If SpaceTalk is intended as a *rename* of StromeX rather than a second product, this ADR is wrong and must be superseded — the two products have different missions, users, and architectures, and merging them would require revisiting `00-EDITORIAL-BIBLE.md` §0.1 first.

---

## ADR-012 — Multi-device with per-device identity keys; web as the MVP linked client

**Status:** Accepted

**Context.** The MVP requires multi-device support. Historically, encrypted messengers either tethered companion devices to a primary phone (fragile, and it dies with the phone's battery) or shared keys across devices (which weakens the security model).

**Decision.** Every device is an independent cryptographic identity with its own sessions and its own prekey bundle. Senders encrypt once per recipient *device*. No primary device exists. At MVP, the linked client is the Flutter web build; native desktop follows in Phase 2 from the same codebase.

**Alternatives considered.**
- *Tethered companion devices.* Simpler. Rejected: the phone must stay online, which is exactly the failure mode users hate most.
- *Shared identity key across devices.* Rejected: one compromised device compromises all of them, and revocation becomes meaningless.
- *Native desktop at MVP.* Rejected on scope: the web client covers the linked-device need at a fraction of the cost, and shipping four platforms well at MVP is not achievable excellence.

**Consequences we accept.**
- Fan-out is O(recipients × devices), which we cap at 4 devices per account.
- Sender-key rotation on device changes adds load in large groups.
- History does not automatically appear on a new device; it is an explicit, user-controlled sync with a stated transfer size (`05` §5.13).
- Web client key storage (IndexedDB, non-extractable WebCrypto keys) is weaker than a native keystore. We state this in the interface at link time rather than implying parity.
