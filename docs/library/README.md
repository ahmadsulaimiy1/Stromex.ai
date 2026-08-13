# THE STROMEX EXECUTIVE KNOWLEDGE SYSTEM

### Eleven independently-issued books · Edition II

---

## Why a library rather than a book

A constitution changes once a decade. A price book changes quarterly. A technology standard changes whenever the stack does. Binding them into one document forces a single version number onto documents with entirely different lifecycles, and hands every reader four hundred pages when they needed forty.

So the corpus is issued as **eleven separate publications**, each with its own cover, front matter, document control, contents, apparatus, owner, review cycle and version. Each stands alone: a reader who opens Book IV never needs Book III to make sense of it, because every book carries the full glossary, the full bibliography and its own index.

The markdown in [`../bible/`](../bible/) remains the single source of truth. Every book — and the omnibus edition — is generated from it, so the eleven can never drift apart.

## The books

| # | Book | Pages | Owner | Review |
|---|---|---|---|---|
| **I** | [The Constitution](stromex-book-01-constitution/) | 42 | Office of the Founder; Board for entrenched provisions | Annually |
| **II** | [Market Strategy & Competitive Positioning](stromex-book-02-market-strategy/) | 34 | Executive | Quarterly (risk); annually |
| **III** | [The Catalogue](stromex-book-03-catalogue/) | 79 | **Pricing Council** | **Quarterly** |
| **IV** | [Engineering, AI Architecture, Cloud & Security](stromex-book-04-technology/) | 40 | Chief Technology Officer | Annually; security half-yearly |
| **V** | [Go-to-Market](stromex-book-05-go-to-market/) | 34 | Commercial Executive | Annually; metrics monthly |
| **VI** | [The Creative Division](stromex-book-06-creative/) | 30 | Creative Director | Annually |
| **VII** | [Industry Ecosystems](stromex-book-07-industry-ecosystems/) | 32 | Executive | Half-yearly |
| **VIII** | [Expansion, Finance & the Roadmap](stromex-book-08-expansion-finance/) | 40 | Executive; Board | Annually at the offsite |
| **IX** | [The Institution](stromex-book-09-the-institution/) | 37 | Office of the Founder | Annually |
| **X** | [SpaceTalk](stromex-book-10-spacetalk/) | 38 | Product Executive | Half-yearly |
| **XI** | [The Financial Master Plan](stromex-book-11-financial-master-plan/) | 30 + model | CFO; Executive; Board | Quarterly (drivers) |

**435 pages across eleven books**, plus the operating model. Each folder holds a `.docx` master and a press-quality `.pdf` generated from it.

The **omnibus edition** — all eleven volumes bound as one 317-page document — remains available at [`../bible/StromeX-Editorial-Bible.pdf`](../bible/StromeX-Editorial-Bible.pdf) for readers who want the whole corpus in a single file.

## Book XI is different

Book XI ships with **[`StromeX-Financial-Master-Plan.xlsx`](stromex-book-11-financial-master-plan/StromeX-Financial-Master-Plan.xlsx)** — a live, driver-based operating model. 1,500 formulas, zero hardcoded results, three scenarios on one switch, twenty revenue streams, twenty years, with sensitivity and valuation grids.

The book documents the model; the model *is* the plan. Change one blue cell and the twenty-year outcome recomputes, which is the only property that makes a financial model worth having: it can be argued with.

**Building it surfaced a real defect in the corpus.** Solving the model's growth rates to reproduce Book VIII's ratified institution counts showed that those counts, at Book III's published prices, produce materially less revenue than Book VIII asserted — $1.24B by 2046 against a stated $1.8B. Book VIII has been amended to the model's arithmetic, with the original estimates struck through and retained per Book I §9.2.4. Book XI, Chapter 9 carries the reconciliation. This is exactly what a model is for.

## Precedence

**Book I governs.** Where any book conflicts with Book I, Book I wins until formally amended under the protocol in Book I, Chapter 9. Where the model and a ratified book disagree, the disagreement is a finding to be resolved explicitly — not a rounding error to be absorbed.

## Reading paths

| You are | Read |
|---|---|
| New employee, first week | Book I in full, then the Book VII chapter for your sector |
| Sales or partner | Books III and V |
| Engineer | Book IV, then Book I chapters 3–5 |
| Designer, writer, editor | Book VI, then Book I chapters 10–12 |
| Board, investor, bank | Books I, II, VIII and XI — and open the model |
| Auditor or regulator | Book I chapter 7, Book IV chapters 12–17, Book VIII chapter 12 |
| About to quote a price | Book III, and nothing else is authoritative |
| About to add to the corpus | Book IX, Chapter 10 first |

## Regenerating

```bash
cd ../bible/publication
npm install
python3 makebooks.py ../ ../../library      # the eleven books
python3 make.py ../                          # the omnibus
python3 model.py && python3 <xlsx>/recalc.py StromeX-Financial-Master-Plan.xlsx 300
```

Each book converges independently: its lists of tables and figures and its index carry real page numbers, so the build renders, reads the apparatus back off the rendered pages, recomposes, and repeats until the numbers settle. Full notes in [`../bible/publication/README.md`](../bible/publication/README.md).

## The standing instruction

> Do not treat this corpus as finished. Treat it as a living constitution. Whenever you identify a missing capability, governance principle, product category, revenue model, technology, operational process or strategic opportunity that aligns with the mission and long-term sustainability, propose and incorporate it with clear justification. Distinguish evidence-based recommendations from aspirational ideas, preserve internal consistency, and ensure every addition strengthens the company over decades rather than optimising for short-term gains.
>
> — Book IX, Chapter 10

**What this library is not yet.** Six of the intended books — a Financial Operating System, an Operations Bible, and deeper Design, Technology, Sales and Innovation volumes — exist today as chapters inside Books IV, V, VI and IX rather than as separate publications. They are promoted to their own books when there is enough operational reality to fill them honestly. A book written to a page target ahead of the reality it describes is the failure this corpus exists to prevent.
