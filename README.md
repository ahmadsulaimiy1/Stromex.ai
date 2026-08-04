# StromeX

StromeX is an AI Operating System for knowledge work — unifying learning, research, writing, design, and publishing behind one trusted, memory-bearing intelligence layer, with Arabic and Islamic scholarship engineered as first-class domains rather than an afterthought.

## Founding Documents

Every future decision in this repository — features, architecture, design, and process — derives from these three governing documents. Where any future work conflicts with them, these documents win until formally amended.

1. **[The StromeX Editorial Bible](docs/00-STROMEX-EDITORIAL-BIBLE.md)** — the strategic constitution and product philosophy manual: vision, product/user/intelligence philosophy, editorial standards, design philosophy, AI architecture philosophy, trust & safety constitution, and scalability constitution.
2. **[The StromeX Master Feature Atlas](docs/01-STROMEX-MASTER-FEATURE-ATLAS.md)** — the classified, scored inventory of features across all 14 product domains, including what was reviewed and rejected and why.
3. **[The StromeX 10-Year Master Roadmap](docs/02-STROMEX-10-YEAR-ROADMAP.md)** — the phased build plan (MVP → Growth → Platform → Ecosystem → Global Scale), including explicit non-goals per phase and the assumptions challenged along the way.

Read the Bible first. It is the supreme governing authority of the StromeX ecosystem.

## MVP Codebase

- **[`apps/api`](apps/api)** — FastAPI backend: auth, chat + multi-model routing (Claude/OpenAI/DeepSeek/Perplexity), memory (Postgres + Qdrant), Qur'an tutor (SM-2 spaced repetition), book writing + PDF export, admin dashboard.
- **[`apps/web`](apps/web)** — Next.js 15 + TypeScript + Tailwind frontend, styled with the StromeX brand system (Fraunces/Archivo/Amiri/Cairo, brass/verdigris/ink palette).
- **[`infra`](infra)** — Docker Compose for local development, `DEPLOYMENT.md` for the Cloudflare + VPS production topology.
- **[`docs/03-STROMEX-MVP-ARCHITECTURE.md`](docs/03-STROMEX-MVP-ARCHITECTURE.md)** — what was actually built, run, and verified vs. what's deferred pending real credentials/infra.
- **[`docs/04-STROMEX-INDEPENDENT-AUDIT.md`](docs/04-STROMEX-INDEPENDENT-AUDIT.md)** — the security/scalability/reliability/performance audit run against the MVP, including a critical SSRF vulnerability found, reproduced, and fixed; real benchmarks; and per-dimension grades.

Quickest way to run it locally is `apps/api/README.md` and `apps/web/README.md`, in that order.

## SAJJIL™ — Android audio studio

**[`apps/sajjil`](apps/sajjil)** is a native Android recording, editing, enhancement and export
application, built around one journey — Record → Review → Edit → Enhance → Export → Archive — and
five sections: Record, Studio, Library, Qur'an, Assistant.

It shares this repository with StromeX but not its runtime; it has no network code and no
dependency on `apps/api`.

- **[`apps/sajjil/core-audio`](apps/sajjil/core-audio)** — the audio engine in dependency-free
  Kotlin: filters, dynamics, restoration, FDN reverb, BS.1770-4 loudness metering and
  normalisation, a reversible edit model, and WAV/FLAC codecs. Platform-free on purpose, so all of
  it is verifiable by unit test on a plain JVM.
- **[`apps/sajjil/app`](apps/sajjil/app)** — the Android application: Jetpack Compose UI,
  `AudioRecord` capture with crash recovery, Media3 playback with lock-screen controls, Room
  persistence, and export to WAV, FLAC, M4A and AAC.
- **[`docs/15-SAJJIL-ARCHITECTURE.md`](docs/15-SAJJIL-ARCHITECTURE.md)** — what was built and why
  the structure is the way it is.
- **[`docs/16-SAJJIL-VERIFICATION.md`](docs/16-SAJJIL-VERIFICATION.md)** — what is proven by test,
  what merely compiles, and what is deliberately not implemented. Read this before relying on any
  capability.

`./gradlew :core-audio:test` from `apps/sajjil` runs the engine's test suite with no Android SDK
required.
