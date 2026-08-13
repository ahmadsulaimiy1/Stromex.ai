# VOLUME XI — THE FINANCIAL MASTER PLAN

### The Operating Model · Drivers · Scenarios · Sensitivity · Capital

*Edition II. Companion to the workbook `StromeX-Financial-Master-Plan.xlsx`. Book VIII governs the strategy; this book governs the arithmetic beneath it.*

---

## Contents

1. [What This Book Is](#chapter-1--what-this-book-is)
2. [The Structure of the Model](#chapter-2--the-structure-of-the-model)
3. [The Drivers](#chapter-3--the-drivers)
4. [The Customer Engine](#chapter-4--the-customer-engine)
5. [The Twenty Revenue Streams](#chapter-5--the-twenty-revenue-streams)
6. [Margin, Operating Leverage & the Cost Floor](#chapter-6--margin-operating-leverage--the-cost-floor)
7. [Cash, Collection & the Funding Requirement](#chapter-7--cash-collection--the-funding-requirement)
8. [The Three Scenarios, Recomputed](#chapter-8--the-three-scenarios-recomputed)
9. [The Reconciliation with Book VIII](#chapter-9--the-reconciliation-with-book-viii)
10. [Sensitivity — Where the Answer Actually Lives](#chapter-10--sensitivity--where-the-answer-actually-lives)
11. [Valuation, and Why It Is Not a Target](#chapter-11--valuation-and-why-it-is-not-a-target)
12. [How to Maintain This Model](#chapter-12--how-to-maintain-this-model)

---

# CHAPTER 1 — WHAT THIS BOOK IS

## 1.1 A model, not a forecast

Book VIII, Chapter 5 sets out three futures for the group and states which one to plan against. It does so at the level of milestones: revenue in 2035, institutions in 2040, a valuation range in 2046. Those figures were constructed top-down — a view of what the company could become, expressed as round numbers.

This book replaces that sketch with an instrument. Every figure in the accompanying workbook is a formula over a stated assumption. Nothing is typed twice. Nothing is pasted from a previous version. Change one blue cell and the whole model recalculates, which is the only property that makes a financial model worth having: **it can be argued with.**

The correct way to read it is not *"the company will make $1.24 billion in 2046."* It is:

> *If StromeX wins 60 institutions in 2027, grows new wins at the rates in the Assumptions sheet, loses 9% of institutions a year, retains 108% of revenue from those that stay, and the installed base shifts out of Band A pricing by a factor of 2.4 over twenty years — then the arithmetic produces approximately $1.24 billion of revenue in 2046.*

Every clause in that sentence is a cell you can change. If you disagree with the conclusion, the productive response is to name which clause is wrong.

## 1.2 What it is for

Four uses, in order of how often they should occur:

1. **Deciding.** What does a change in churn actually cost us? What does the UK entry have to deliver to be worth its cost? The model answers in the group's own units.
2. **Being challenged.** A board member, investor or auditor should be able to attack an assumption and see the consequence immediately. A model that cannot be attacked is a brochure with a grid on it.
3. **Detecting drift.** Actuals are compared against the driver, not against the output. Revenue missing plan matters far less than *which driver* missed.
4. **Raising capital.** Book VIII, Chapter 7 sets the capital sequence. This model produces the number that sequence has to fund.

## 1.3 The standing honesty clause

These are scenarios constructed from stated assumptions. They are not forecasts of record, not projections of guaranteed outcome, and not a representation that any particular result will be achieved. Actual outcomes will differ and may differ materially. Nothing here constitutes an offer of securities or investment advice.

That paragraph is not boilerplate. It is the reason the model is built the way it is: with every assumption exposed on one sheet rather than buried in the formulas, so that a reader can see precisely how much of the answer is arithmetic and how much is judgement.

---

# CHAPTER 2 — THE STRUCTURE OF THE MODEL

## 2.1 The sheets

| Sheet | What it does |
|---|---|
| **README** | Purpose, how to use, colour convention, the honesty clause |
| **Assumptions** | Every driver, three values per driver — one per scenario — and a switch that selects the live set |
| **Customers** | Institution cohort roll-forward: opening, won, lost, closing. Plus universities, government and enterprise accounts |
| **Revenue** | Twenty streams, grouped into subscription, consumption and platform, and services |
| **P&L** | Gross margin, operating expense with leverage, the cost floor, EBITDA, tax, Rule of 40 |
| **Headcount** | Derived from revenue per employee, split by function |
| **Cash Flow** | Working capital from collection lag, capex, free cash flow, cumulative cash, peak funding requirement |
| **Scenarios** | The milestones for the selected scenario, side by side with the valuation implication |
| **Sensitivity** | 2046 revenue across net revenue retention and new-win growth — the two drivers that dominate |
| **Valuation** | Enterprise value across revenue outcomes and multiples, with the $15–40bn band shaded |

## 2.2 The colour convention

Blue text is a hardcoded input you may edit. Black is a formula. Green is a link to another sheet. Yellow fill marks the assumptions that move the answer most. **Overwriting a black cell silently breaks the model** — the workbook will still compute, and it will be wrong, which is the worst failure mode a model has.

## 2.3 The horizon

Twenty years, 2027 to 2046, matching the phase structure in Book VIII, Chapter 1: Foundation to 2030, Race to 2035, Global Scale to 2040, and six years beyond into maturity.

## 2.4 What the model deliberately does not do

- **It does not model a balance sheet.** Book V of the intended library — the Financial Operating System — covers treasury, working capital policy, debt and reserves. This model produces the cash requirement; it does not manage cash.
- **It does not model per-country P&Ls.** Geographic mix enters through a single band-uplift driver (Chapter 3.4). Country-level modelling belongs with the entry checklists in Book VIII, Chapter 10.
- **It does not model acquisitions.** Book VIII, Chapter 11 governs those, and an acquisition modelled before a target exists is fiction.
- **It does not discount to present value.** A DCF over a twenty-year horizon in a currency-volatile emerging market would produce a number with a precision the inputs cannot support.

---

# CHAPTER 3 — THE DRIVERS

## 3.1 The scenario switch

One cell, `Assumptions!B3`, takes 1, 2 or 3 — Conservative, Expected, Optimistic. Every driver carries three values and the Selected column picks the live one with `INDEX`. There is no other switch and no hidden override.

## 3.2 The driver groups

| Group | Drivers | What it controls |
|---|---|---|
| **Customer acquisition** | New wins in 2027; growth in new wins across three phase bands; gross annual churn | The size of the installed base |
| **Revenue per institution** | Net revenue retention; first-year ARPA; ARPA drift; band mix uplift | What each institution is worth |
| **Up-market accounts** | University share and ACV; government contract count, growth and value; enterprise count, growth and value | The high-ACV tail |
| **Recurring per institution** | AI consumption, cloud, credentials, identity, payments, support, marketplace, licensing | Eight recurring lines |
| **One-time per new institution** | Implementation, creative, hardware | Three build lines |
| **Share-of-subscription** | Consulting, publishing, training | Three services lines |
| **Margin** | Gross margin 2027 and 2040 | Blended margin trajectory |
| **Operating expense** | S&M, R&D and G&A shares at both ends of the horizon; minimum cost base and its growth | Operating leverage and the burn |
| **Cash and capital** | Debtor days, capex share, tax rate | The cash conversion |
| **Valuation** | EV/revenue multiple | The last sheet only |

## 3.3 The three drivers that dominate

Sensitivity analysis (Chapter 10) shows the answer is governed by three assumptions. Everything else is detail.

**Net revenue retention.** Compounded over twenty years, the difference between 1.02 and 1.15 is not a percentage — it is a multiple. Published 2026 benchmarks put median NRR near 97% for accounts below $25k ACV, which is where the founding market sits. **Every scenario in this model assumes we beat our own segment median**, and Book V, Chapter 7 is the plan for how.

**Growth in new wins.** Front-loaded compounding: a point of growth in 2028 is worth more than five points in 2040, because it compounds for eighteen more years.

**Band mix uplift.** Chapter 3.4.

## 3.4 The band mix uplift — the driver that was missing

Book I §6.4 prices Band A at 0.32× list and Band C at 1.00×. An institution in Lagos and an institution in London buy the same modules at prices that differ by a factor of three.

It follows that **average realised price rises as the installed base internationalises, with no change to any list price.** A base that is 95% Band A in 2030 and 55% Band A in 2046 has a materially higher average revenue per institution purely from mix.

This single driver is the difference between a $640 million outcome and a $1.24 billion one at identical institution counts. It is set to 2.4× by 2046 in the Expected case. **And it is entirely a function of whether the UK and US entries in Book VIII, Chapter 9 actually work** — which makes it the most consequential strategic assumption in the corpus expressed as a number.

If international expansion stalls, this driver collapses toward 1.0 and the group is a Conservative-case business regardless of how well it executes domestically. That is worth knowing explicitly.

---

# CHAPTER 4 — THE CUSTOMER ENGINE

## 4.1 The roll-forward

```
Closing(t) = Opening(t) + Won(t) − Lost(t)
Opening(t) = Closing(t−1)
Lost(t)    = Opening(t) × gross annual churn
Won(t)     = Won(t−1) × (1 + growth for the phase band containing t)
```

Three growth bands, matching the phases: 2028–2030, 2031–2035, 2036–2046.

## 4.2 The rates are solved, not asserted

The growth rates in the Assumptions sheet were **solved so that the model reproduces the institution counts already ratified in Book VIII §5.2.** They are outputs of that constraint, not independent guesses:

| Scenario | 2028–30 | 2031–35 | 2036–46 |
|---|---|---|---|
| Conservative | 56.9% | 33.8% | 9.3% |
| Expected | 84.5% | 46.3% | 12.2% |
| Optimistic | 94.3% | 53.7% | 14.9% |

| Milestone | Model (Expected) | Book VIII §5.2 |
|---|---|---|
| Institutions, 2030 | 700 | 700 |
| Institutions, 2035 | 6,496 | 6,500 |
| Institutions, 2040 | 19,480 | 22,000 |
| Institutions, 2046 | 44,983 | 45,000 |

The 2040 figure lands about 12% under Book VIII because a single growth rate spans eleven years; a smooth curve cannot pass through four points fixed independently. The discrepancy is disclosed rather than smoothed away by adding a fourth band.

## 4.3 The reality check on the founding market

Nigeria's 2024/25 school census records 107,017 private schools. The Expected case reaches 44,983 institutions by 2046 **across all countries and all sectors** — schools, universities, clinics, mosques, firms, SMEs, ministries. It is not a claim to 42% of Nigerian private schools. Chapter 3.4's band uplift is the arithmetic expression of that: by 2046 a large share of the base is not Nigerian at all.

Any reading of this model that implies domestic saturation has misread it, and Book II §2.2's sizing method — not this model — is the authority on how much of any single market is reachable.

---

# CHAPTER 5 — THE TWENTY REVENUE STREAMS

## 5.1 Subscription: a cohort model

```
Subscription(t) = Subscription(t−1) × NRR + Won(t) × ARPA(t)
```

This is the only correct way to model subscription revenue, and it is why net revenue retention appears as a driver rather than as an output. Revenue from the existing base grows (or shrinks) at NRR; new customers arrive at the current ARPA. Churn is already inside NRR, which is why the customer count and the revenue roll-forward use different mechanics and must not be reconciled by multiplication.

## 5.2 The streams

| # | Stream | Driven by |
|---|---|---|
| 1 | Institution subscriptions | Cohort model on NRR |
| 2 | University subscriptions | University count × ACV |
| 3 | Government contracts | Contract count × annual value |
| 4 | Enterprise contracts | Account count × ACV |
| 5 | AI consumption credits | Share of subscription |
| 6 | Cloud, hosting and storage | Share of subscription |
| 7 | Credentials and verification | Per institution — **issuance only; verification is free to the verifier forever** (Book I §5.3) |
| 8 | Identity, cards and issuance | Per institution |
| 9 | Payments platform fee | Per institution (0.4% over processor cost) |
| 10 | Support and managed services | Per institution |
| 11 | Marketplace take | Per institution (20% rev-share) |
| 12 | Licensing and white-label | Per institution |
| 13 | Consulting and advisory | Share of subscription |
| 14 | Publishing and print | Share of subscription |
| 15 | Training and certification | Share of subscription |
| 16 | Implementation and migration | Per **new** institution |
| 17 | Creative and design | Per **new** institution |
| 18 | Hardware and smart campus | Per **new** institution |
| 19–20 | *(Reserved)* | Financial services and franchise are specified in Book III but not yet modelled; adding a stream before it has a price is fiction |

## 5.3 The recurring mix constraint

Book I §6.2 requires recurring engines to exceed **65% of group revenue by 2031**. The model computes this on the Revenue sheet as a live check rather than an assertion. In the Expected case it reaches 73.8% in 2030 and 81.9% by 2046 — the constraint binds early and is then comfortably met, which is the intended shape.

---

# CHAPTER 6 — MARGIN, OPERATING LEVERAGE & THE COST FLOOR

## 6.1 Gross margin

Straight-line from the 2027 assumption (52% Expected) to the 2040 assumption (76%), flat thereafter. The improvement comes from **mix shift toward software, not from price rises** — which matters, because Book I §6.3.6 caps price increases at 12% annually and the model must not quietly assume otherwise.

**The exposed assumption:** the 76% terminal margin depends on AI inference cost per task continuing to fall. That is an assumption about the industry, not about us, and Book VIII §13.5 lists it as a condition that would falsify the plan.

## 6.2 Operating leverage

Sales and marketing, R&D and G&A each decline as a share of revenue between 2027 and 2046 — S&M from 30% to 17%, R&D from 28% to 17%, G&A from 18% to 9% in the Expected case. This is not optimism; it is what happens when referral and partner distribution carry more of the acquisition load (Book V §1.1) and fixed corporate cost spreads over a larger base.

R&D declining as a *share* is not a reduction in absolute terms — it grows every year in cash. Book IX §8.4 requires R&D funded as a fixed percentage rather than as a residual, and the model honours that.

## 6.3 The cost floor

A company building a cloud platform, a credential system, an AI layer, a creative division and a hardware practice has a cost base regardless of revenue. Modelling operating expense purely as a share of revenue makes the early years costless, which is false and produces an implausibly small funding requirement.

The model therefore applies:

```
Operating expense(t) = MAX( ratio-based opex(t) , minimum cost base(t) )
```

with the floor starting at $1.2M in 2027 (Expected) and growing 30% a year until ratio-based expense overtakes it — which happens early in Phase II. This is the difference between a modelled peak funding requirement of $215,000, which is nonsense, and $4.5 million, which is a real seed-plus-Series-A.

---

# CHAPTER 7 — CASH, COLLECTION & THE FUNDING REQUIREMENT

## 7.1 Collection is modelled explicitly

Book II R2 identifies collection failure as a live risk in the founding market, not a theoretical one. The model carries **debtor days as a scenario driver** — 75 days Conservative, 55 Expected, 40 Optimistic — and builds a receivables balance that consumes cash as revenue grows.

In a business growing 40%+ a year, working capital is a permanent cash drain, and a model that recognises revenue without modelling its collection will overstate cash in every single year.

## 7.2 The outputs

| Measure (Expected case) | Value |
|---|---|
| Peak funding requirement | **≈ $4.5 million** |
| First cash-positive year | **2033** |
| Cumulative free cash flow by 2046 | ≈ $807 million |

The peak funding requirement is the number Book VIII, Chapter 7's capital sequence has to raise. It is modest because Phase I is deliberately bootstrapped on services revenue — and it is the figure to re-check first whenever any Phase I assumption changes, because it is the one that determines whether the plan survives contact with reality.

---

# CHAPTER 8 — THE THREE SCENARIOS, RECOMPUTED

*Expected case shown; set `Assumptions!B3` to read the others.*

| Measure | 2027 | 2030 | 2035 | 2040 | 2046 |
|---|---|---|---|---|---|
| Institutions | 60 | 700 | 6,496 | 19,480 | 44,983 |
| Revenue | $310k | $4.5M | $66.6M | $311M | **$1.24B** |
| Recurring share | 61.7% | 73.8% | 78.4% | 81.5% | 81.9% |
| Gross margin | 52.0% | 57.5% | 66.8% | 76.0% | 76.0% |
| EBITDA margin | (335.7%) | (13.3%) | 4.7% | 22.6% | 33.0% |
| Rule of 40 | — | 102.1% | 65.4% | 52.4% | 57.3% |
| Free cash flow | ($1.05M) | ($0.42M) | $3.7M | $42.3M | $195M |

**Reading the early years.** A −336% EBITDA margin in 2027 is not a defect; it is a company with $310,000 of revenue and a $1.2 million cost floor, which is exactly what Phase I is. The relevant number in those years is the cumulative cash line, not the margin.

**Rule of 40.** Above 40 throughout, and above 50 from 2040. Book VIII Gate II requires ≥30 by 2035; the model clears it at 65. That is a consequence of high growth rather than high margin, and growth-driven Rule of 40 scores decay — which is why the margin trajectory in Chapter 6.2 matters more than it looks.

---

# CHAPTER 9 — THE RECONCILIATION WITH BOOK VIII

## 9.1 The discrepancy

Building the model from the bottom up surfaced an inconsistency in the corpus that a prose scenario table concealed.

| | Book VIII §5.2 (top-down) | This model (bottom-up) | Gap |
|---|---|---|---|
| Institutions, 2046 | 45,000 | 44,983 | — |
| Revenue, 2040 | $700M | $311M | −56% |
| Revenue, 2046 | $1.8B | $1.24B | −31% |

The institution counts agree exactly, because the model's growth rates were solved to them. **The revenue figures do not agree**, and the reason is arithmetic: Book VIII's $1.8 billion at 45,000 institutions implies about $40,000 of annual revenue per institution. Book III's published prices put a Band A secondary school group at roughly $8,300 recurring and a small primary school at roughly $1,400. Even after twenty years of retention compounding and a 2.4× band-mix shift, the model reaches about $27,700 per institution — not $40,000.

**Book VIII's revenue scenario was constructed independently of its own institution counts and of the price book.** That is precisely the class of error this model exists to catch.

## 9.2 The resolution

Book VIII §13 states the rule for exactly this situation: *when a target triggers, change the plan, not the measurement.* Applied here, the model is the more rigorous artifact — it is built from Book III's actual published prices — and the corpus is corrected toward it, not the reverse.

Accordingly, Book VIII §5.2 is amended to record the model's figures as the governing arithmetic, with the original top-down estimates retained and struck through per Book I §9.2.4. The Growth scenario's 2046 revenue is restated from $1.8 billion to approximately **$1.24 billion**, and its indicative valuation from $10.8–14.4 billion to approximately **$7.5 billion at 6×**.

## 9.3 What this changes strategically

It moves the $15–40 billion ambition further out of reach of the Expected case and places it squarely in the Optimistic one. That is an uncomfortable result and it is the correct one to record. Book VIII §5.5 already instructs the company to *plan against Scenario B, prepare for Scenario A, and build so that Scenario C remains structurally possible* — this reconciliation does not change that instruction. It sharpens what Scenario C would actually require:

- Net revenue retention at 115%+, sustained, against a segment median near 97%
- A band-mix uplift above 3×, meaning genuine scale in developed markets rather than a token presence
- Roughly 130,000 institutions, which is three times the Expected case

None of those is impossible. All three must happen together.

---

# CHAPTER 10 — SENSITIVITY: WHERE THE ANSWER ACTUALLY LIVES

The Sensitivity sheet computes 2046 revenue across net revenue retention (98% to 118%) and growth in new wins during Phase II (30% to 80%), holding the selected scenario's other assumptions.

**What it shows.** Moving one column left on net revenue retention roughly halves the twenty-year outcome. Moving one row down on growth changes it far less. The compounding asymmetry is the entire argument for why Book V, Chapter 7 — retention and expansion — is the most commercially important chapter in the corpus, and why the Customer Success Playbook is not a support function.

**The uncomfortable column.** The leftmost column, 98% NRR, is not a pessimistic case. It is approximately the published segment median for accounts below $25k ACV. A company that merely performs like its peers lands there. Every scenario in this model assumes we do better, and the plan for doing better must be real.

---

# CHAPTER 11 — VALUATION, AND WHY IT IS NOT A TARGET

## 11.1 The grid

The Valuation sheet crosses 2046 revenue outcomes ($150M to $5.5B) against EV/revenue multiples (3× to 10×), shading the cells that land in the $15–40 billion band.

| Target | At 5× | At 6× | At 8× | At 10× |
|---|---|---|---|---|
| $15B | $3.0B revenue | $2.5B | $1.88B | $1.5B |
| $40B | $8.0B revenue | $6.7B | $5.0B | $4.0B |

## 11.2 Two things outside our control

**The multiple.** The same company was worth roughly 16× revenue in 2021 and 4.5× in 2023. Public SaaS medians sat near 8.5× NTM in mid-2026; private medians run 4–5× ARR. A plan whose success depends on a specific multiple depends on the weather.

**The mix discount.** StromeX is not a pure software company. Services, print and hardware drag the blended multiple below a comparable SaaS business. That is a permanent, accepted cost of the completeness strategy in Book II §6 — completeness is what wins the customers in the first place — but it must be stated rather than wished away.

## 11.3 What is in our control

Revenue. Margin. Retention. Growth. The premium band of 7–9× is earned by exactly two numbers — net revenue retention above 120% and a Rule of 40 above 50 — and both of them are outputs of operating the company well.

**Book VIII §5 governs and is not amended by this book:** a valuation is a possible consequence of doing the work exceptionally well over two decades. It is not the mission, and it must never become the operating target, because optimising directly for it produces the behaviours Book I prohibits.

---

# CHAPTER 12 — HOW TO MAINTAIN THIS MODEL

## 12.1 The monthly discipline

Compare actuals against **drivers**, not against outputs. Revenue missing plan is a symptom; the diagnosis is always in a driver — wins, churn, NRR, ARPA, band mix or collection days. A variance report that stops at revenue has not been written.

## 12.2 The quarterly discipline

Re-solve the growth rates against actual wins. Re-derive NRR from the cohort data rather than carrying the assumption forward. Re-check the band mix against the actual geographic distribution of the base. Update the multiple from current market data and note the date.

## 12.3 The annual discipline

Rebuild the scenario set at the strategy offsite (Book VIII §12), and **reconcile against the corpus**. If the model and a ratified book disagree — as they did in Chapter 9 — the disagreement is a finding, not a rounding error. Record it, resolve it explicitly, and amend whichever document is wrong under the Book I, Chapter 9 protocol.

## 12.4 The rules that keep a model honest

1. Never hardcode a result. If a number appears twice, one of them is going to be wrong.
2. Never overwrite a formula cell to make an output look right.
3. Every assumption carries a comment saying where it came from.
4. Every driver has three values, so no scenario is privileged in the structure.
5. When a driver is wrong, change the driver — never the formula that consumes it.
6. Publish the falsification conditions (Book VIII, Chapter 13) alongside the outputs, always.

---

*Volume XI ends. The workbook is the instrument; this book is its documentation. Where they differ, the workbook is authoritative on arithmetic and this book is authoritative on what the arithmetic means.*

*Review due: quarterly (drivers), annually (structure).*
