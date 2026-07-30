# TASMIM Technology Stack Decision Report

> Evaluates the candidate technologies against Phase 1's actual scope (Feature Prioritization Framework, Tier A) and the long-term architecture already committed to in the Phase 2 Master Architecture — the goal is a stack that serves Phase 1 well without contradicting decisions the platform will need in Phase 2–3.

---

## Frontend

| Option | Strengths | Weaknesses for TASMIM specifically |
|---|---|---|
| **Flutter** | Single codebase across mobile/desktop/web; strong rendering performance via its own Skia-based engine; good for teams wanting one language (Dart) everywhere. | Its Skia-based rendering engine is a *second* rendering paradigm competing with the custom Rust/WASM rendering core the Master Architecture already commits to for pixel-identical cross-platform fidelity — adopting Flutter means either abandoning that shared-core bet or running two rendering systems long-term. Web SEO/SSR story is weaker than React's ecosystem, which matters for TASMIM's template-gallery and marketing surfaces. |
| **React Native** | Large ecosystem, reuses React/JS skills the web team already needs, strong community. | Same core conflict as Flutter: it's a separate rendering bridge (not the shared native/WASM core), and historically weaker for GPU-intensive, canvas-heavy interactions than a purpose-built renderer — a real risk against the Experience Design System's 60–120fps target. |
| **Next.js (React)** | Server-rendering for SEO-critical marketing/template pages, mature ecosystem and hiring pool, clean code-splitting so the heavy editor bundle loads only when needed, pairs naturally with a future WASM-compiled rendering core loaded into the page. | Not a mobile/desktop solution by itself — but Phase 1 doesn't need one (Engineering Spec §9: PWA, not native app). |
| **Plain React (e.g., Vite SPA)** | Simpler build for a pure editor SPA, less framework overhead than Next.js. | Loses Next.js's SSR benefit for the marketing and template-gallery pages, which genuinely need SEO in a discovery-driven, wedge-focused go-to-market — not a meaningful enough simplification to give that up. |

**Recommendation: Next.js for Phase 1 web**, with the editor itself code-split as a client-rendered module. **Do not adopt Flutter or React Native for the long-term app shell** — they conflict with the Master Architecture's already-made "one shared rendering engine" bet. When native mobile apps are actually built (Tier B, per the Feature Prioritization Framework), build them as native Swift/Kotlin shells around the shared Rust/WASM rendering core, exactly as the Master Architecture specifies — not as a Flutter/React Native detour that would need to be undone later.

---

## Backend

| Option | Strengths | Weaknesses for TASMIM specifically |
|---|---|---|
| **Node.js (TypeScript)** | Same language as the frontend (real velocity benefit for a small early team), huge ecosystem, fast to hire for, excellent for I/O-bound CRUD/orchestration services. | Weaker fit for CPU-bound work (image/export processing, rendering-adjacent compute) — but Phase 1 doesn't need to do that work in the API layer (Engineering Spec §7 keeps rendering client-side; heavy export work belongs on dedicated render-farm workers, not the API tier). |
| **Go** | Excellent concurrency model, simple deployment (single static binary), strong performance for high-throughput API services, good for microservices at scale. | Smaller shared talent pool with the frontend team than TypeScript; a reasonable fallback if Node's concurrency model becomes a real bottleneck, but not a Phase 1 velocity win for a small team. |
| **Rust** | The right language for CPU/GPU-bound, correctness-critical work — the rendering engine and render-farm export workers specifically (already the Master Architecture's stated choice for the shared rendering core). | Steep learning curve and slower iteration speed for ordinary CRUD APIs — using it for every service would slow Phase 1 down for no benefit where performance isn't the bottleneck. |
| **Python** | Dominant ecosystem for ML/AI tooling — model fine-tuning, evaluation pipelines, data processing. | Weaker choice for the primary user-facing API layer (performance, typing rigor at scale) relative to Node/Go. |

**Recommendation: a deliberately small polyglot split, not a single-language purity choice and not a sprawl of five languages:**
- **TypeScript/Node.js** for the primary API/orchestration services (Document, Asset, Billing, AI Orchestration) — matches frontend team skills, fastest Phase 1 velocity, and Node's I/O-bound profile fits these services well.
- **Rust**, scoped narrowly to the rendering engine and (later) render-farm export workers — matching the Master Architecture's existing commitment, not expanded further than that until there's a specific performance case.
- **Python**, held in reserve for AI/ML pipeline work (fine-tuning, evaluation, moderation model tooling) once TASMIM needs it — Phase 1's AI strategy (see below) relies on hosted model APIs, so Python's footprint in Phase 1 itself should be minimal, growing as open-source/fine-tuned models enter the roadmap (Phase 3+).
- **Go held as the explicit fallback**, not adopted now: if a specific Node service becomes a genuine concurrency/performance bottleneck post-launch, migrate that one service to Go rather than defaulting to it platform-wide from day one.

---

## Databases

| Option | Strengths | Weaknesses for TASMIM specifically |
|---|---|---|
| **Firebase** | Very fast to prototype, built-in real-time sync, generous free tier. | NoSQL document model is a poor fit for TASMIM's genuinely relational core data (workspaces, billing, template categorization, brand-kit relationships) — modeling this cleanly in Firestore fights the tool. Deep vendor lock-in to Google's ecosystem. Its generic real-time sync is not the same primitive as the bespoke CRDT collaboration protocol the Master Architecture specifies for Phase 2 — building on Firebase's realtime DB now would mean replacing it later rather than extending it. |
| **Supabase** | Postgres under the hood (real relational integrity, real SQL), bundles auth/storage/realtime as a managed layer, strong velocity for a small team, straightforward migration path to raw Postgres later since the data itself is standard Postgres. | Coupling business logic too tightly to Supabase-specific client SDKs, auth internals, or realtime/edge-function features would make later migration harder — a discipline problem to manage, not a reason to avoid it. |
| **PostgreSQL** (self-managed or via a managed provider) | The right database engine on technical merits regardless of hosting choice — relational integrity plus JSONB flexibility for document content (Engineering Spec §3), mature tooling, zero lock-in. | Self-managing it from day one (provisioning, backups, scaling, auth-from-scratch) is meaningfully slower for a small early team than a managed bundle. |

**Recommendation: PostgreSQL as the database engine, accessed via Supabase (or an equivalent managed Postgres+auth+storage bundle) in Phase 1** for velocity, with an explicit architectural rule: keep the schema and business logic portable — treat Supabase as a convenient *delivery mechanism* for Postgres, auth, and object storage, not as a permanent architectural dependency. This makes a later move to self-managed Postgres plus the custom auth/storage services described in the Engineering Specification a migration, not a rewrite, once scale or Phase 2/3 collaboration requirements exceed what a managed bundle comfortably provides. **Firebase is not recommended** given the relational shape of TASMIM's core data model.

---

## AI Infrastructure

| Option | Strengths | Weaknesses for TASMIM specifically |
|---|---|---|
| **OpenAI** | Broad multimodal capability including mature image generation, large ecosystem, strong general-purpose quality. | Less differentiated as a sole provider; cost scales with usage in a way that needs the Model Router's tiering discipline (Engineering Spec §8) regardless of which provider is chosen; image generation and reasoning/orchestration are different strengths worth sourcing independently rather than assuming one vendor should do both. |
| **Anthropic** | Strong instruction-following and reasoning quality — a good fit for the agent-reasoning work behind AI Designer's brief interpretation, AI Layout/Typography Experts' judgment calls, and AI Design Critic's feedback generation; a safety and steerability posture well-suited to content adjacent to the Islamic Suite's sensitivity requirements (Islamic Creative Suite governance section). | Not a native image-generation provider — the reasoning/orchestration layer and the image-generation layer need to be sourced from different places regardless of vendor choice. |
| **Open-source / open-weight models** | Essential for cost control at real scale, for fine-tuning on TASMIM's own proprietary data (brand kits, Creative Context Graph signals) without sending customer data to a third party, and the *only* realistic path to the on-device mobile AI tier the Master Architecture specifies (§4) — proprietary hosted APIs cannot run on-device. | Currently behind top proprietary models on raw quality for general-purpose generation and image synthesis — not yet the right choice for Phase 1's launch-quality bar on the primary generation path, but the right long-term investment as the on-device and cost-control needs mature. |

**Recommendation: a hybrid, multi-provider strategy from day one, routed through the Model Router abstraction already specified in the Master Architecture (§6) and Engineering Specification (§8) — never hard-coding a single provider into agent logic:**
- **Reasoning/orchestration/critique** (AI Designer's interpretation, AI Layout Expert, AI Typography Expert, and eventually AI Design Critic): a strong instruction-following model — **Anthropic's Claude family is the Phase 1 recommendation** for this layer, given reasoning quality and a safety posture that matters for anything touching Islamic Suite content moderation.
- **Image generation**: sourced from a dedicated image-generation provider (OpenAI or a comparable specialist) behind the same router abstraction, evaluated on quality/cost/latency at build time rather than locked in permanently here.
- **Phase 3+ (on-device tier, cost control at scale, proprietary fine-tuning)**: invest in open-source/open-weight models — not a Phase 1 requirement, but the Model Router should be architected from day one so adding this tier later is additive, not a redesign.
- **The structural point that matters most:** the Model Router, not any single model choice, is TASMIM's actual AI infrastructure decision. Committing early and rigidly to one vendor for every agent would be a mistake regardless of which vendor — cost, quality, and capability leadership all shift over time, and the router is what lets TASMIM follow that without rearchitecting.

---

## Summary Table

| Layer | Phase 1 Recommendation | Long-term direction |
|---|---|---|
| Frontend (web) | Next.js (React) | Same, with the rendering core progressively compiled to WASM and loaded in |
| Frontend (mobile) | Responsive PWA (no native app yet) | Native Swift/Kotlin shells over the shared Rust/WASM core — not Flutter/React Native |
| Backend services | TypeScript/Node.js | Same, with Go as a targeted fallback for specific bottlenecked services |
| Rendering/export compute | Rust (scoped to this layer only) | Same, expanded into the full shared cross-platform core |
| ML/AI pipeline tooling | Minimal (Python held in reserve) | Grows as fine-tuning and on-device models enter scope (Phase 3+) |
| Database | PostgreSQL via a managed bundle (e.g., Supabase) | Self-managed PostgreSQL + custom services once scale/collaboration needs exceed the managed bundle |
| AI models | Anthropic (reasoning/agents) + a dedicated image-generation provider, behind a Model Router | Hybrid expands to include open-weight models for on-device and cost-sensitive tiers |

No single decision in this table is irreversible — that is the point of routing everything (models, and to a lesser extent the managed-database dependency) through an abstraction layer rather than binding business logic directly to a vendor. The one genuinely hard-to-reverse commitment is the rendering engine's long-term direction (custom Rust/WASM core over Flutter/React Native), which is why that decision is flagged here as already made rather than re-litigated.
