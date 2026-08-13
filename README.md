# StromeX

StromeX is an AI-powered digital transformation company. We digitise, automate, modernise and intelligently transform organisations across every sector we can serve competently — building complete ecosystems rather than isolated products, at a published price the institution can plan around.

## The Editorial Bible — Edition II

> ### 📖 **[THE STROMEX EDITORIAL BIBLE](docs/bible/README.md)**
> **The constitution, operating manual and strategic corpus of the StromeX group.**

Ten volumes. The supreme governing authority of the group. Where a roadmap, contract, pricing sheet, deck or line of code conflicts with it, the corpus wins until formally amended.

| Vol. | Title |
|---|---|
| **I** | [Constitution — Vision, Philosophy, Governance, Culture, Brand](docs/bible/VOLUME-I-CONSTITUTION.md) |
| **II** | [Market Strategy & Competitive Positioning](docs/bible/VOLUME-II-MARKET-AND-POSITIONING.md) |
| **III** | [The Catalogue — Products, Services, Modules & Transparent Pricing](docs/bible/VOLUME-III-CATALOGUE-AND-PRICING.md) |
| **IV** | [Engineering, AI Architecture, Cloud & Security](docs/bible/VOLUME-IV-ENGINEERING-AI-CLOUD.md) |
| **V** | [Go-to-Market — Sales, Customer Success, Partners, Ecosystem](docs/bible/VOLUME-V-GTM-SALES-PARTNERS.md) |
| **VI** | [Creative — Publishing, Design, Print, Media](docs/bible/VOLUME-VI-CREATIVE-PUBLISHING-PRINT.md) |
| **VII** | [Industry Ecosystems & the Enterprise Division](docs/bible/VOLUME-VII-INDUSTRY-ECOSYSTEMS.md) |
| **VIII** | [Expansion, Finance & the Roadmap](docs/bible/VOLUME-VIII-EXPANSION-FINANCE-ROADMAP.md) |
| **IX** | [The Institution — Innovation, Research, Talent, Operations, the 100-Year Plan](docs/bible/VOLUME-IX-THE-INSTITUTION.md) |
| **X** | [SpaceTalk — The Communication Operating System](docs/bible/VOLUME-X-SPACETALK.md) |

**The three phases** (Volume VIII §1): **Foundation** 2027–2030 · **Race** 2031–2035 · **Global Scale** 2036–2040.

### Published editions

| Edition | File |
|---|---|
| Microsoft Word master (299pp, A4) | [`docs/bible/StromeX-Editorial-Bible.docx`](docs/bible/StromeX-Editorial-Bible.docx) |
| Press-quality PDF | [`docs/bible/StromeX-Editorial-Bible.pdf`](docs/bible/StromeX-Editorial-Bible.pdf) |

Both are generated from the markdown corpus and are content-identical. Rebuild instructions: [`docs/bible/publication/`](docs/bible/publication/README.md).

### Edition I (superseded, retained for the record)

Edition I described the AI knowledge-work operating system that is now one product line among many (Volume III, Division 1). It is retained unamended because the corpus never silently deletes what it used to believe (Volume I §9.2).

1. [Editorial Bible, Edition I](docs/00-STROMEX-EDITORIAL-BIBLE.md) — superseded by `docs/bible/`
2. [Master Feature Atlas](docs/01-STROMEX-MASTER-FEATURE-ATLAS.md)
3. [10-Year Master Roadmap](docs/02-STROMEX-10-YEAR-ROADMAP.md) — superseded by Volume VIII

## MVP Codebase

- **[`apps/api`](apps/api)** — FastAPI backend: auth, chat + multi-model routing (Claude/OpenAI/DeepSeek/Perplexity), memory (Postgres + Qdrant), Qur'an tutor (SM-2 spaced repetition), book writing + PDF export, admin dashboard.
- **[`apps/web`](apps/web)** — Next.js 15 + TypeScript + Tailwind frontend, styled with the StromeX brand system (Fraunces/Archivo/Amiri/Cairo, brass/verdigris/ink palette).
- **[`infra`](infra)** — Docker Compose for local development, `DEPLOYMENT.md` for the Cloudflare + VPS production topology.
- **[`docs/03-STROMEX-MVP-ARCHITECTURE.md`](docs/03-STROMEX-MVP-ARCHITECTURE.md)** — what was actually built, run, and verified vs. what's deferred pending real credentials/infra.
- **[`docs/04-STROMEX-INDEPENDENT-AUDIT.md`](docs/04-STROMEX-INDEPENDENT-AUDIT.md)** — the security/scalability/reliability/performance audit run against the MVP, including a critical SSRF vulnerability found, reproduced, and fixed; real benchmarks; and per-dimension grades.

Quickest way to run it locally is `apps/api/README.md` and `apps/web/README.md`, in that order.
