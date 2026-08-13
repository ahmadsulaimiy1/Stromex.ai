# VOLUME II — MARKET STRATEGY & COMPETITIVE POSITIONING

### Who we serve · Who we compete with · Why we win · What we refuse to fight over

*Edition II. Derives its authority from Volume I. Phase references follow Volume VIII, Chapter 1: **Phase I Foundation 2027–2030 · Phase II Race 2031–2035 · Phase III Global Scale 2036–2040**.*

---

## Contents

1. [The Structural Opportunity](#chapter-1--the-structural-opportunity)
2. [Market Sizing Method](#chapter-2--market-sizing-method)
3. [The Buyer Anatomy](#chapter-3--the-buyer-anatomy)
4. [Buyer Psychology](#chapter-4--buyer-psychology)
5. [The Competitive Landscape](#chapter-5--the-competitive-landscape)
6. [Why We Win — The Seven Wedges](#chapter-6--why-we-win--the-seven-wedges)
7. [Positioning Statements](#chapter-7--positioning-statements)
8. [What We Refuse to Compete On](#chapter-8--what-we-refuse-to-compete-on)
9. [The Moat, Honestly Assessed](#chapter-9--the-moat-honestly-assessed)
10. [Risk Register](#chapter-10--risk-register)

---

# CHAPTER 1 — THE STRUCTURAL OPPORTUNITY

## 1.1 Four forces, converging

StromeX is not betting on a trend. It is positioned at the intersection of four independent structural forces, each of which would justify a company on its own, and whose convergence is the actual opportunity.

**Force 1 — The cost of building software collapsed, but the cost of *finishing* it did not.**
AI-assisted development has compressed the labour required to produce working software by a large factor. It has compressed the labour required to *specify, integrate, migrate, train, support and maintain* software by very little. The result is a widening gap: an explosion of software that mostly does not get adopted, and a scarcity premium on organisations that can actually land it. StromeX is architected to arbitrage exactly this gap — heavy AI leverage on production, deliberately human investment on landing.

**Force 2 — Institutional digitisation in emerging markets is a decade behind and moving fast.**
Most African, South Asian and Middle Eastern institutions have already digitised communications (WhatsApp reached them before any ERP did) but have not digitised *records* — admissions, finance, credentials, HR, assets. The gap between "has a smartphone" and "has a system of record" is the single largest addressable inefficiency in these economies, and mobile penetration means the last-mile problem is already solved for us.

**Force 3 — Credential fraud is becoming enforceable.**
Certificate and transcript forgery has always been endemic; what changed is that employers, universities and immigration authorities increasingly *check*, and increasingly check digitally. An institution whose credentials cannot be verified online is beginning to suffer real consequences for its graduates. This converts verification from a nice-to-have into a competitive necessity for the institution — which is the strongest possible position for a vendor.

**Force 4 — Procurement is shifting from projects to subscriptions.**
Institutions that once bought a system every eight years now expect to rent capability continuously. This is unambiguously good for a company designed around recurring revenue and continuous delivery, and unambiguously bad for the incumbent consultancies whose model depends on large, infrequent, capitalised projects.

## 1.2 The founding market thesis

Begin in Nigerian education, for six specific reasons, none of which is sentiment:

1. **Volume.** Nigeria has tens of thousands of private secondary and primary schools and hundreds of tertiary institutions, overwhelmingly under-served by software.
2. **Willingness to pay.** Private schools charge fees and compete on prestige. Prestige is purchasable, and modern digital infrastructure is visible prestige to fee-paying parents.
3. **Proof exists.** Reference Implementation №1 (SHRS) demonstrates end-to-end delivery on a real institution.
4. **The buying committee is small.** A proprietor or principal can sign. Compare a hospital or a ministry, where the same decision takes eleven months.
5. **Referral density.** School proprietors know other school proprietors. Word of mouth in this market is unusually efficient, which matters enormously when paid acquisition is uneconomic.
6. **Everything generalises.** A school is a small institution containing every problem a large one has: identity, records, money, credentials, communications, compliance, assets, people. Solving education properly builds layers 1–7 of the Chapter 2 stack for every other sector.

**The corresponding risk, stated honestly:** the Nigerian private education market is price-sensitive, FX-exposed, and has a meaningful share of institutions whose ability to pay a recurring subscription is genuinely fragile. Volume VIII, Chapter 6 models churn and collection assumptions accordingly, and Chapter 10 of this volume carries the risk.

---

# CHAPTER 2 — MARKET SIZING METHOD

## 2.1 Why this chapter contains a method rather than a number

This corpus does not print market-size figures it cannot source. Published TAM figures for "African EdTech" or "global digital transformation" vary by an order of magnitude between analysts, are frequently circular, and are almost never useful for deciding anything. What follows is the method by which the group produces its own sizing, so that any figure quoted internally can be traced to its inputs and challenged.

## 2.2 The bottom-up formula

For any market:

```
Serviceable Revenue  =  Σ (institutions in segment
                        × share reachable by our channel
                        × realistic win rate
                        × annual contract value at that segment's band)
```

Each of the four inputs must be independently sourced and dated:

| Input | Source of truth | Refresh |
|---|---|---|
| Institution count | National registries, ministry data, accreditation bodies, licensing lists | Annually |
| Reachability | Our own channel data: partner coverage, sales capacity, marketing reach | Quarterly |
| Win rate | Our own pipeline history by segment — never an assumption | Quarterly |
| ACV | Volume III at the applicable band, times observed attach rate | Quarterly |

**Rule:** any market-size claim in a StromeX document must cite the four inputs and the date. A figure without inputs may not appear in a board pack, an investor document, or a proposal.

## 2.3 Segmentation model

Institutions are segmented by **decision complexity**, not by size or revenue — because decision complexity is what actually determines sales cost, cycle length and win rate.

| Segment | Signature | Cycle | Motion | Where value comes from |
|---|---|---|---|---|
| **Self-serve** | One person decides, pays by card | Minutes–days | Product-led, zero touch | Volume, expansion revenue |
| **Owner-led** | Proprietor/principal/founder decides | 2–8 weeks | Low-touch, one salesperson | The core of Phase I |
| **Committee** | 3–8 stakeholders, budget cycle | 3–9 months | Full sales cycle, proposal, pilot | Higher ACV, stickier |
| **Procurement** | Formal tender, evaluation matrix | 6–24 months | Bid team, compliance, references | Largest ACV, slowest |
| **Programme** | Multi-institution, donor or ministry funded | 12–36 months | Consortium, partner-led | Transformational, high risk |

Phase I deliberately concentrates on self-serve and owner-led. Committee and procurement open in Phase II, and only once the reference base makes them winnable — bidding for a ministry contract without twenty referenceable schools is not ambition, it is a donation of proposal costs.

---

# CHAPTER 3 — THE BUYER ANATOMY

## 3.1 The economic buyer

Who actually signs, by sector:

| Sector | Signs | Cares most about | Kills deals over |
|---|---|---|---|
| Private K-12 | Proprietor / Director | Prestige, parent perception, fee collection | Price, and fear of disruption during term |
| Public K-12 | Ministry / Board | Compliance, reporting, cost per student | Procurement irregularity |
| University | Registrar / VC / Bursar | Accreditation, integrity of records | Data migration risk |
| Hospital | MD / CMD / Admin | Patient throughput, regulatory compliance | Clinical risk, downtime |
| Government | Permanent Secretary / DG | Delivery visibility, audit defensibility | Anything resembling scandal |
| Bank / Fintech | COO / CTO | Regulatory posture, uptime | Security review failure |
| Publisher | Publisher / MD | Speed to market, unit economics | Quality of finish |
| SME | Owner | Getting customers, getting paid | Complexity, monthly cost |
| NGO | Country Director | Donor reporting, beneficiary data | Cost per beneficiary |
| Mosque / Church | Imam / Board / Trustee | Community trust, propriety | Anything culturally careless |

## 3.2 The other four people in the room

The economic buyer signs, but four other roles decide:

- **The champion** — usually an ICT coordinator, a young registrar, or an ambitious head of department. They want the institution modernised and their own standing raised by having brought it. *We arm them with materials they can present as their own.*
- **The blocker** — typically the person whose manual process is being automated, or an incumbent vendor's relationship holder. Their objection is real and is never actually about the feature list. *We address it by naming it: this changes your role, here is the training, here is what you get to do instead.*
- **The technical evaluator** — asks about hosting, backups, security, integration, and exit. *We answer with documentation, not reassurance.* The published security posture and the free export guarantee close more technical evaluations than any demo.
- **The finance gate** — the bursar. Wants predictability above all, and hates variable bills. *We win here on published, itemised, plannable pricing — this is where transparency converts directly into revenue.*

## 3.3 The five objections and their answers

| Objection | What's underneath | Our answer |
|---|---|---|
| "It's too expensive" | *I can't predict the total* | The configurator: itemised, running total, 3-year total, before we take their name |
| "We'll do it next term" | *I'm afraid of disruption mid-year* | Phased go-live; parallel running; nothing is switched off until the replacement is proven |
| "Our staff won't use it" | *Correct, if you don't train them* | Included training, in-language, on their devices, plus adoption reporting we're accountable for |
| "What if you disappear?" | *We've been abandoned before* | Free complete export, open formats, source-available options, published status history |
| "Can't we just use WhatsApp/Excel?" | *Genuinely, sometimes yes* | Then do — and here's the free tier. We win them when they outgrow it, and they will |

That last answer is doctrine, not politeness. Telling a 40-student school that they do not need our ERP builds more revenue over ten years than selling it to them today.

---

# CHAPTER 4 — BUYER PSYCHOLOGY

*Synthesis of well-established findings in behavioural economics, consumer psychology and pricing research, applied to our specific market. No fabricated studies; where a principle is contested, it is flagged.*

## 4.1 Principles we deliberately apply

**Anchoring.** The first number a buyer sees frames every subsequent number. We anchor with the *complete ecosystem* price and then show how little the entry configuration costs — the entry price feels like relief rather than expense. This is legitimate because the anchor is a real, purchasable configuration, not an inflated decoy.

**Loss aversion, applied to their loss, not manufactured fear.** People weigh losses more heavily than equivalent gains. We frame around losses the institution is *already suffering* and can verify — staff hours, uncollected fees, forged certificates in circulation — never around invented threats. The distinction between "here is what you are already losing" and "here is what might happen to you" is the line between honest framing and fear-selling, and Volume I §11.2.6 makes the latter prohibited.

**Choice architecture.** Excessive choice reduces conversion. Our configurator's default view offers a small number of curated configurations, with full modularity one click away. Both are real; neither is hidden.

**The endowment effect, earned through the free tier.** People value what they already possess. An institution that has used free StromeX tools for a year already feels ownership. This is the primary conversion mechanism of Chapter 5 of Volume I and is worth more than any discount.

**Transparency as a trust shortcut.** In low-trust markets, published pricing is not merely convenient — it is *evidence of character*. It signals we are not deciding what to charge based on how wealthy you look. In our founding market this is the single most disarming thing we do.

**Social proof, correctly scoped.** A proprietor is moved by the school down the road, not by a Fortune 500 logo. Reference customers are recruited and celebrated *locally*.

**Reciprocity.** Substantial free value given before any ask creates genuine obligation. This works only when the gift is real; a "gift" with strings attached inverts into resentment.

## 4.2 Techniques we deliberately refuse

Each of these reliably increases short-term conversion and reliably degrades trust. All are prohibited:

- Manufactured scarcity ("3 slots left this month")
- Fake countdown timers
- Decoy pricing designed purely to make the middle tier look good
- Drip pricing — a low headline that grows during checkout
- Pre-ticked add-ons
- Confirmshaming ("No thanks, I prefer wasting money")
- Cancellation obstacle courses
- Roach-motel onboarding — easy in, hard out
- Sales pressure on institutions that clearly cannot afford the commitment

## 4.3 The presentation of price

Derived from the founder's instruction that prices should never look shocking, and that the elite tiers should look genuinely premium:

1. **Show unit economics, not just totals.** "$0.12 per certificate" lands very differently from "$1,200 for 10,000 certificates" — and both are true, so we show both.
2. **Show cost per beneficiary.** "$1.40 per student per year" is the number a proprietor can defend to a board.
3. **Show the comparison the buyer would make anyway.** Manual cost, incumbent cost, cost of doing nothing.
4. **Never hide the total.** The running total is always on screen.
5. **Let premium look premium.** Elite pricing is presented without apology, hedging, or discount language. A discounted Elite tier is a contradiction — the price is part of the assurance.
6. **Annual framing for recurring, one-time framing for capital.** Institutions budget in these two shapes; matching their mental accounting reduces friction honestly.

---

# CHAPTER 5 — THE COMPETITIVE LANDSCAPE

## 5.1 The six competitor classes

We do not have one competitor. We have six kinds, and they must be beaten differently.

### Class 1 — Global horizontal SaaS
*Examples: Microsoft 365, Google Workspace, Salesforce, Zoho, HubSpot*
**Strength:** enormous, trusted, cheap at the entry point, already installed.
**Weakness:** generic. They supply capability, not outcome. Nobody at Microsoft will migrate your student records or design your certificate.
**Our posture:** **integrate, never fight.** We are the sector layer on top. A school on Google Workspace is a *better* prospect, not a worse one — the plumbing is already there. Explicit interoperability with these platforms is a permanent product requirement, not a roadmap item.

### Class 2 — Global vertical SaaS
*Examples: PowerSchool, Blackbaud, Ellucian, Instructure, Epic, Tyler Technologies*
**Strength:** deep domain functionality, decades of accumulated edge cases, entrenched.
**Weakness:** priced for North America and Western Europe; implementation costs that exceed our entire contract value; localisation that stops at currency; and near-total absence from our founding markets.
**Our posture:** avoid direct collision in their home markets during Phases I–II. Win our markets so completely that when we enter theirs in Phase III we arrive with scale, references and a structural cost advantage rather than as a challenger.

### Class 3 — Regional and local vendors
*Examples: local school-management systems, regional ERP shops, national portal builders*
**Strength:** local presence, local language, local price, existing relationships.
**Weakness:** thin engineering, weak design, no security posture, no roadmap, high abandonment risk, single-product. Most cannot survive their founder leaving.
**Our posture:** **this is the real competitive fight of Phase I.** We win on completeness, craft, reliability and published pricing. We must be careful not to win on arrogance — many of these vendors are the incumbent relationship, and the graceful path is often to acquire them, partner with them, or absorb their customers when they fail rather than to attack them.

### Class 4 — Consultancies and systems integrators
*Examples: Big Four advisory arms, regional SI firms, agency networks*
**Strength:** boardroom access, procurement fluency, credibility with ministries and donors.
**Weakness:** they sell hours. Their incentive is duration, not outcome. They own no IP, so every engagement restarts from zero and the client pays for it.
**Our posture:** **partner where they have access we lack; compete where the client has been burned.** Our decisive advantage is that we own the product, so our incentive is a fast, correct, permanent implementation. Say this plainly in competitive situations, without disparagement.

### Class 5 — Freelancers and small agencies
*Strength:* cheap, fast, personally accountable, everywhere.
*Weakness:* no continuity, no security, no support, no scale, no exit path. The single largest cause of abandoned institutional software in our market.
**Our posture:** we do not compete at the bottom of this market — we *recruit* it. The best of these become StromeX Partners (Volume V, Chapter 6), which converts the most fragmented part of the competitive landscape into our distribution network.

### Class 6 — AI-native newcomers
*Strength:* fast, cheap, technically current, no legacy.
*Weakness:* almost all are a thin layer over a foundation model with no system of record, no implementation capability, no hardware, no compliance posture, and no reason for an institution to trust them with student data.
**Our posture:** this is the class that could genuinely disrupt us, and it deserves respect rather than dismissal. Our defence is not our model — models commoditise. Our defence is layers 1–5 of the Volume I stack: the record, the identity, the credentials, the money, the physical estate. **A competitor can replicate our intelligence layer in a quarter. Replicating an institution's ten-year system of record takes ten years.**

## 5.2 The competitive rules

1. Never disparage a competitor by name to a customer. Compare on specifics, in writing, verifiably.
2. Never claim a capability we do not have. If a competitor genuinely does something better, say so and explain the trade.
3. Never win a deal by promising a delivery date we have not capacity-checked.
4. Losing to a better fit is acceptable. Losing to a worse product because we communicated badly is a defect and is reviewed like one.
5. Every loss is logged with a real reason. "Price" is almost never the real reason and is not accepted as one without evidence.

---

# CHAPTER 6 — WHY WE WIN — THE SEVEN WEDGES

Seven advantages. None is individually decisive; the combination is very hard to assemble, which is precisely why it is the strategy.

**Wedge 1 — Radical price transparency.**
Published, itemised, module-level pricing in a market where opacity is the norm. It disarms the finance gate, shortens the cycle, removes the negotiation tax, and signals character. Competitors can copy this — but Class 3 and 4 competitors mostly *cannot*, because their margins depend on the opacity.

**Wedge 2 — Completeness.**
Website, portal, ERP, identity, credentials, payments, hardware, design, print, publishing and consulting from one accountable supplier. The institution stops being the integrator of last resort. No competitor class covers more than a third of this span.

**Wedge 3 — The free layer.**
A permanently free tier substantial enough to be the market's default toolkit, and free verification forever. It builds distribution where paid acquisition does not work and converts the trust problem into a trust asset.

**Wedge 4 — AI leverage with human accountability.**
Heavy AI leverage on production (design, drafting, code, translation, layout, data migration), deliberate human investment on judgement and landing. This produces developed-market quality at emerging-market cost — the structural margin advantage the whole plan rests on. Disclosed, never concealed (Volume I §7.2).

**Wedge 5 — Craft.**
In a market where "good enough" is the norm, finished work is a moat. It is the reason for referral, the reason for premium pricing, and the reason an institution shows its portal to a rival proprietor.

**Wedge 6 — The physical bridge.**
Almost no software company will also print your ID cards, install your gate, coordinate your UK book printing and design your prospectus. It is operationally messy and lower-margin — which is exactly why it is defensible. It also anchors the relationship in the institution's physical reality, where switching costs are real.

**Wedge 7 — Emerging-market-native architecture.**
Offline-first, low-bandwidth, low-spec-device, intermittent-power, multi-currency, bidirectional-language, cash-adjacent. Retrofitting this into a product designed for fibre and mains power is close to impossible, which is why Class 1 and 2 competitors will not do it.

---

# CHAPTER 7 — POSITIONING STATEMENTS

## 7.1 The group positioning

> **For institutions that need to become modern and cannot afford to get it wrong, StromeX is the digital transformation company that builds the whole ecosystem — software, design, identity, credentials, payments, publishing and physical infrastructure — at a published price, with the craft of a developed-market firm and the economics of an emerging-market one.**

## 7.2 The one-liner

> **StromeX builds the institution's operating system.**

## 7.3 By audience

| Audience | Statement |
|---|---|
| School proprietor | "Everything your school needs to run and to be seen as serious — website, portal, admissions, results, fees, verifiable certificates, ID cards — from one company, at a price on the website." |
| University registrar | "Records you can defend at accreditation, credentials the world can verify, and a migration we take responsibility for." |
| Ministry | "Delivery you can see, records you can audit, and a supplier whose pricing is public." |
| Hospital administrator | "Patient records, staff, billing and compliance in one system that works when the power doesn't." |
| SME owner | "Get found, get paid, get organised. Start free." |
| Publisher / author | "From manuscript to a book printed in the UK or US, designed to a standard your readers will notice." |
| Developer | "Open design system, open formats, documented APIs, free verification. Build on us." |
| Investor | "Recurring institutional infrastructure revenue in the fastest-growing markets on earth, with a structural cost advantage and a free layer that owns distribution." |
| Prospective employee | "Build things that matter for institutions that have never had them, to a standard that would pass in London, without moving there." |

## 7.4 The five proof points every asset must be able to substantiate

1. Published, itemised pricing — verifiable on the website, right now.
2. Reference Implementation №1 delivered end-to-end.
3. Free tier and free credential verification, permanent, no card.
4. Complete data export, open format, no fee — contractual.
5. Public status page and published incident history.

Marketing may not claim a sixth thing until a sixth thing is true.

---

# CHAPTER 8 — WHAT WE REFUSE TO COMPETE ON

**Price as the primary axis.** There is always someone cheaper. Competing on price against an operator with no engineering costs, no security posture and no intention of existing in three years is a race to a place we do not want to arrive at. We compete on transparency and completeness, and we let the cheap option be cheap.

**Feature count.** Feature-list warfare produces bloated products and is won by whoever has the most engineers. We compete on whether the institution's actual problem is solved.

**Model benchmarks.** We do not market on which foundation model we use or how it scores. Models commoditise; the record does not.

**Speed of announcement.** We do not pre-announce. A thing is announced when a customer can buy it. This costs us press and saves us the credibility that press would eventually consume.

**Being everywhere at once.** Geographic and sector breadth is the twenty-year plan, and depth is the twelve-month rule (Volume I §2.4).

**Prestige logos we did not earn.** No customer appears in our marketing without written permission and an accurate description of what we actually did for them.

---

# CHAPTER 9 — THE MOAT, HONESTLY ASSESSED

A moat claim is worthless without an assessment of how it fails. Each of ours is stated with its expiry condition.

| Moat | Strength | Time to build | How a competitor beats it |
|---|---|---|---|
| **System of record** | Very strong | 3–10 years per customer | Only by waiting for us to fail a customer badly enough to justify migration. This is the real moat. |
| **Switching cost from physical estate** | Strong | 1–3 years | Rip-and-replace of gates, cards and readers — expensive and disruptive, rarely worth it |
| **Free-tier distribution** | Strong | 2–4 years | A better-funded rival giving away more. Real risk in Phase III. Defence: quality and breadth, not volume of giveaway |
| **Craft and reputation** | Moderate–strong | 3–7 years | Hiring better designers than us. Entirely possible; requires them to also want our markets |
| **Price transparency** | Moderate | Immediate to copy | Trivially copyable in principle; blocked in practice by competitors whose margins require opacity. Assume erosion by Phase III |
| **Partner network** | Moderate | 2–5 years | Outbidding us on partner economics. Defence: partners who are genuinely better off with us |
| **Cost structure** | Moderate | 1–3 years | Any competitor adopting the same AI-leverage model. **Assume this advantage is temporary and largely gone by 2032.** It funds the durable moats; it is not itself durable |
| **Regulatory / data residency posture** | Moderate | 2–4 years per market | Investment. Slow but not hard |

**The honest conclusion:** only the system of record and the physical estate are genuinely durable. Everything else is a head start. The strategic implication is direct and governs Phase I: **get institutions onto the record as fast as possible, at whatever depth they will accept, and make leaving unattractive by being good rather than by being sticky.** Every other advantage exists to buy time for that one.

---

# CHAPTER 10 — RISK REGISTER

Reviewed quarterly by the Executive. Each risk carries its owner and its live mitigation.

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **FX volatility** erodes Band A revenue in USD terms | High | High | Price locally, cost locally; USD-denominate international contracts; maintain hard-currency reserve; band multipliers reviewed, not fixed |
| R2 | **Collection failure** — institutions that sign and do not pay | High | Medium | Term-aligned billing; direct debit and mandate where possible; automatic feature degradation before disconnection; credit assessment above a threshold |
| R3 | **Key-person dependency** on the founder | High | Very high | Write everything down (this corpus); build a genuine executive layer in Phase I; no undocumented decisions |
| R4 | **Over-extension** — too many sectors before depth | High | High | Volume I §2.4 depth gate; Volume VIII phase gates; sector entry requires a domain hire |
| R5 | **Delivery quality collapse under growth** | Medium | Very high | Partner certification; templated delivery; capacity confirmed in writing before signature; hard rule: never sign what we cannot deliver |
| R6 | **Security incident involving children's data** | Medium | Catastrophic | Volume IV Chapters 6–9; independent audit cadence; minimisation by default; breach protocol rehearsed, not merely written |
| R7 | **Foundation model dependency** — pricing, availability, terms | Medium | High | Multi-provider routing (already in the MVP); no capability may depend on a single provider; self-hosted fallback for critical paths |
| R8 | **Well-funded AI-native entrant** targeting the same wedge | Medium | High | Depth of record; physical estate; partner network; move faster in Phase I than a newcomer can |
| R9 | **Political / regulatory shock** in a concentrated market | Medium | High | Geographic diversification is a risk control, not only a growth strategy — this is a core reason for the UK/US entries |
| R10 | **Free tier costs outrun the funding capacity** | Medium | Medium | Central budget with a hard ceiling; per-tool unit-cost monitoring; degrade generosity before degrading quality |
| R11 | **Reputational damage from an automation-driven redundancy story** | Medium | Medium | Volume I §7.1 workforce policy applied and visible; never market on headcount reduction |
| R12 | **Hardware supply chain and import volatility** | Medium | Medium | Multi-supplier; local assembly where viable; hardware treated as an enabler, never a margin engine |
| R13 | **Talent loss to overseas remote employers** | High | Medium | Pay competitively against remote-work benchmarks, not local ones; equity; the work itself is the retention argument |
| R14 | **Founder ambition outrunning capital** | Medium | High | Volume VIII capital plan; phase gates that cannot be skipped by enthusiasm |
| R15 | **AI regulation** restricting deployment in education or health | Medium | Medium | Human-in-the-loop is already architectural (Volume I P10); disclosure already policy; compliance is a small delta rather than a rebuild |

---

*Volume II ends. Volume III — [The Catalogue](VOLUME-III-CATALOGUE-AND-PRICING.md).*

*Review due: quarterly (risk register), annually (rest).*
