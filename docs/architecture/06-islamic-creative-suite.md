# TASMIM Islamic Creative Suite

> TASMIM's clearest whitespace opportunity: no major design platform currently owns Islamic creative tooling. This document architects it as a first-class product line — and is explicit about the governance obligations that come with touching sacred text.

---

## 1. Arabic Typography Engine

- **Contextual letterform shaping:** correct initial/medial/final/isolated glyph forms, ligatures, and joining behavior — not a Latin-script rendering pipeline with Arabic fonts bolted on.
- **Kashida-aware justification:** proper elongation-based text justification (a fundamentally different justification model than Latin word-spacing), so justified Arabic body text looks typeset, not stretched.
- **Diacritics/tashkeel handling:** correct vertical stacking and spacing of harakat, shadda, and other diacritical marks, independently controllable from base-letter styling.
- **OpenType feature support:** full access to stylistic sets, contextual alternates, and ligature sets exposed by professional Arabic type families — surfaced through the AI Typography Expert ([`04-creative-intelligence-engine.md`](./04-creative-intelligence-engine.md)) rather than requiring manual OpenType feature-code knowledge.
- **Mixed-script layout intelligence:** correct bidirectional (BiDi) text flow when Arabic and Latin content coexist in one design — headline, body, and caption runs each resolve direction independently and correctly.

## 2. Professional Calligraphy Tools

- **Script-calibrated vector brushes:** pressure- and angle-sensitive digital brushes tuned to the proportional rules of major traditional scripts — Naskh, Thuluth, Diwani, and Kufic — rather than a single generic "calligraphy pen."
- **AI-assisted calligraphy generation:** the Creative Intelligence Engine can propose calligraphic compositions from typed text, but every AI-generated calligraphic output is explicitly flagged as a **draft requiring qualified human review** before any liturgical or publication use — calligraphy of sacred phrases carries real cultural and religious weight that a model should assist with, not finalize unsupervised.
- **Digitization pipeline:** mobile camera-native scan-to-vector conversion (Master Architecture §4) lets a calligrapher digitize hand-drawn work directly into editable vector paths.

## 3. Mushaf Publishing Tools

This is the highest-sensitivity feature in the entire platform and is architected accordingly.

- **Uthmani script compliance:** typesetting conforms to the standard Uthmani orthography used in printed Mushaf editions, not simplified modern Arabic orthography.
- **Verse/ayah numbering and tajweed color-coding:** automated ayah-boundary marking and optional tajweed-rule color overlays, matching established Mushaf conventions.
- **Print-standard layout grids:** page templates matching recognized conventions (e.g., 15-line Madinah Mushaf-style pagination) for institutions that require print-standard fidelity.
- **Mandatory scholarly review gate:** unlike every other tool in TASMIM, Mushaf/Qur'anic text features are **not fully self-serve**. Any document using verified Qur'anic text passes through a governance workflow — text sourced only from a certified, verified digital Mushaf source (never freeform AI-generated Qur'anic text), with a mandatory review step by a qualified reviewer before an institution-grade export is released. This is a product requirement, not a nice-to-have: an error here is not a typical software bug, it is a serious credibility and religious-integrity failure. See the governance risk note at the end of this document and the broader discussion in [`08-design-the-future-and-self-review.md`](./08-design-the-future-and-self-review.md).

## 4. Islamic Geometric Pattern Generator

- A parametric tessellation engine generating traditional Islamic geometric patterns (star polygons, girih tiling, arabesque motifs) from adjustable mathematical parameters (symmetry order, line weight, motif complexity) rather than a fixed clip-art library.
- Patterns export as clean, editable vector paths (usable as backgrounds, borders, or standalone motifs) and can be constrained to a brand's color system via the AI Brand Strategist.
- Generated patterns are inherently original (mathematically derived, not copied from historical sources) — a rare case in TASMIM's AI stack where the originality/rights concern from the Inspiration Ecosystem largely does not apply.

## 5. Mosque Branding Kits

- Purpose-built templates for signage, wayfinding, prayer-time boards, donation/fundraising campaigns, and community bulletins — informed by the same brand-kit and consistency-enforcement system used by any TASMIM organization (AI Brand Strategist), applied to a mosque or Islamic institution's identity.

## 6. Islamic Event Templates

- Curated, continuously expanded template sets for the Islamic calendar's major occasions: Ramadan, Eid al-Fitr, Eid al-Adha, Hajj season, Mawlid, and the Islamic New Year, plus institutional use cases (conference/da'wah event branding).
- Templates are built on the same Style DNA system as the Inspiration Ecosystem, so trend discovery (§05) can surface regionally-relevant seasonal design trends ahead of each occasion.

## 7. Da'wah Media Studio

- Social-ready templates and workflows purpose-built for outreach content: short-form video captioning with multi-language subtitle tools, khutbah/lecture slide generation, and quote-card generation with correctly sourced and formatted citations.
- Shares infrastructure with TASMIM Video and the AI Social Media Creator agent, applying the same multi-format "one brief, many platforms" generation pattern to da'wah-specific content types.

## 8. Bilingual Arabic-English Publishing

- **Mirrored-grid layout engine:** publishing layouts that correctly mirror structure for RTL Arabic and LTR English editions of the same document (e.g., a bilingual annual report), rather than forcing one language into a layout designed for the other.
- **Font-pairing intelligence:** the AI Typography Expert recommends Arabic/Latin type pairs that match in weight, x-height, and visual tone — a well-known, difficult typographic problem given how differently Arabic and Latin type families are metriced.
- **Independent per-language flow:** long-document pagination (AI Publishing Assistant) tracks Arabic and English content flows independently so page counts, footnotes, and cross-references stay correct in both editions from a single source document.

---

## Governance Requirement — Read Before Building

The Islamic Creative Suite, and the Mushaf publishing tools in particular, are the one area of TASMIM where "ship fast and iterate" is the wrong default. Recommended structural requirements, carried into the roadmap ([`07-super-app-roadmap.md`](./07-super-app-roadmap.md)) as an explicit dependency before Islamic Suite features reach general availability:

1. **A standing scholarly/religious advisory board** reviews Mushaf typesetting conventions, tajweed color-coding accuracy, and any AI-assisted calligraphy involving Qur'anic or hadith text before release.
2. **Verified-source-only policy** for any Qur'anic text in the product — sourced from certified digital Mushaf databases, never generated or paraphrased by an AI model.
3. **A visible, permanent distinction** between AI-assisted decorative/branding content (fully self-serve) and liturgical text-handling features (review-gated) — the product UI itself should make this boundary obvious to users, not just enforce it on the backend.
4. **Regional legal and cultural review** given the intended core markets (GCC, broader MENA, South/Southeast Asia) — data residency, content standards, and local religious authority relationships vary by country and require local partnership, not a single global policy.

This suite is TASMIM's strongest differentiator specifically because no competitor has invested in it — but that same fact means there is no existing playbook to borrow, and mistakes here carry reputational weight far beyond a typical product bug.
