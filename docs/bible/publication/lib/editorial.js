'use strict';
/* Front matter, back matter and per-volume executive summaries.
   Authored for the printed edition; the markdown corpus carries the body. */

const EDITION = 'Edition II';
const VERSION = '2.0';
const DATE = '13 August 2026';

// ── the ten volumes ───────────────────────────────────────────────────────
const VOLUMES = [
  {
    roman: 'I', n: 1, file: 'VOLUME-I-CONSTITUTION.md',
    slug: 'stromex-book-01-constitution',
    status: 'Ratified',
    owner: 'Office of the Founder; Board for entrenched provisions',
    review: 'Annually, or on any Board-tier amendment',
    title: 'The Constitution',
    sub: 'Vision · Philosophy · Governance · Culture · Brand',
    authority: 'Entrenched & Constitutional',
    summary:
      'Volume I is the root of the corpus; every other volume derives its authority from it. It states why StromeX exists — that the gap between what an institution could be and what it is has little to do with ambition and everything to do with access to competent execution — and sets the doctrine of ecosystems, in which eight architectural layers are shared across every sector so that breadth becomes affordable. It establishes the eleven product principles, the value-before-revenue doctrine, the Free Constitution (including the permanent commitment that credential verification is free for the verifier), the Commercial Constitution and its regional price bands, the Ethics Constitution, the group structure and decision rights, the amendment protocol with its four tiers of authority, the brand system and the logo decision, the editorial voice, the design philosophy and the standing non-goals.',
  },
  {
    roman: 'II', n: 2, file: 'VOLUME-II-MARKET-AND-POSITIONING.md',
    slug: 'stromex-book-02-market-strategy',
    status: 'Ratified',
    owner: 'Executive',
    review: 'Quarterly (risk register); annually otherwise',
    title: 'Market Strategy & Competitive Positioning',
    sub: 'Who we serve · Who we compete with · Why we win',
    authority: 'Strategic',
    summary:
      'Volume II locates the company in its market. It identifies four converging structural forces — the collapsed cost of building software against the unchanged cost of finishing it, the decade-long lag in institutional digitisation, the growing enforceability of credential fraud, and the shift from projects to subscriptions — and sets out the founding market thesis with its risks stated alongside. It supplies a method for market sizing rather than a headline figure, anatomises the buyer and the four other people in the room, applies established findings in behavioural economics while naming the techniques the group refuses to use, classifies the competitive landscape into six classes each requiring a different response, sets out the seven wedges, and closes with an honest assessment of the moat in which every advantage is stated together with the condition under which it expires.',
  },
  {
    roman: 'III', n: 3, file: 'VOLUME-III-CATALOGUE-AND-PRICING.md',
    slug: 'stromex-book-03-catalogue',
    status: 'Ratified · Price Book v2.0',
    owner: 'Pricing Council',
    review: 'Quarterly',
    title: 'The Catalogue',
    sub: 'Products · Services · Modules · Transparent Pricing',
    authority: 'Operational — Pricing Council',
    summary:
      'Volume III is the commercial heart of the corpus and the sole authority on StromeX prices. Seventeen divisions carry itemised, published, module-level pricing — web and digital presence, the institutional platform, identity and credentials, cloud, AI, payments, automation, mobile, intelligence, security, hardware and smart campus, design, publishing and print, consulting, the academy, the marketplace, and support — each line stating its purpose, specification, price, exclusions and upgrade path. It defines the regional band multipliers, discount authority, credits and verification tokens, and the anti-bill-shock rules. Every line is marked according to whether it is built, partial, or specified but not yet built. Four worked configurations show what an institution actually pays, including a state ministry deployment at approximately $1.48 per student per year.',
  },
  {
    roman: 'IV', n: 4, file: 'VOLUME-IV-ENGINEERING-AI-CLOUD.md',
    slug: 'stromex-book-04-technology',
    status: 'Ratified',
    owner: 'Chief Technology Officer',
    review: 'Annually; Security Bible half-yearly',
    title: 'Engineering, AI Architecture, Cloud & Security',
    sub: 'How it is built · How it stays up · How it stays safe',
    authority: 'Operational — CTO',
    summary:
      'Volume IV governs construction. It sets ten engineering principles, the canonical stack, and the static-site pattern that four reference implementations converged on independently. It specifies multi-tenancy with the no-fork rule, the data architecture and its classification scheme, and — in the most consequential subsystem the group operates — the credential and verification architecture, including the signing model in which StromeX never signs on an institution’s behalf. It defines the AI architecture and its provider-independence doctrine, the stakes ladder that determines when a human must decide, the data rights and model-training policy, the performance budgets and degraded modes required by constrained environments, and internationalisation engineering. Chapters twelve to seventeen constitute the Security Bible, covering zero trust, identity, cryptography, secure development, resilience and incident response.',
  },
  {
    roman: 'V', n: 5, file: 'VOLUME-V-GTM-SALES-PARTNERS.md',
    slug: 'stromex-book-05-go-to-market',
    status: 'Ratified',
    owner: 'Commercial Executive',
    review: 'Annually; GTM metrics monthly',
    title: 'Go-to-Market',
    sub: 'Sales · Customer Success · Partners · Ecosystem',
    authority: 'Operational',
    summary:
      'Volume V begins from a binding constraint: paid acquisition does not work in the founding market, so growth must come from mechanisms whose cost does not scale with customers acquired. It identifies seven such engines, of which the most defensible is that every credential a StromeX institution issues is a permanent, cost-free advertisement seen by an employer or a university. It sets out the funnel, the sales motions, the sales playbook and its seven discovery questions, the discipline of public procurement, and — at its centre — the eleven-stage Customer Success Playbook with its health scoring and value ledger. It confronts the segment’s unforgiving retention benchmarks directly, sets the partner network economics deliberately above the industry norm, and defines the platform ecosystem and community programmes.',
  },
  {
    roman: 'VI', n: 6, file: 'VOLUME-VI-CREATIVE-PUBLISHING-PRINT.md',
    slug: 'stromex-book-06-creative',
    status: 'Ratified',
    owner: 'Creative Director',
    review: 'Annually',
    title: 'The Creative Division',
    sub: 'Design · Publishing · Print · Media · The Craft Standard',
    authority: 'Operational — Creative Director',
    summary:
      'Volume VI explains why a technology group owns a creative division: craft is the differentiator competitors cannot copy cheaply, it closes the loop on the institution’s physical reality, and it is the reason institutions refer one another. It sets the craft standard — work indistinguishable from a good London or New York studio that a Lagos printer can reproduce correctly on the first attempt — and the anti-slop rules that govern AI-assisted production, including the prohibition on inventing facts a client has not published. It specifies institutional identity and heraldry, security-document design and its layered defences, publishing practice, the exacting standards for Islamic and Arabic typesetting, rights and licensing, international print coordination, audio and motion, and educational publishing.',
  },
  {
    roman: 'VII', n: 7, file: 'VOLUME-VII-INDUSTRY-ECOSYSTEMS.md',
    slug: 'stromex-book-07-industry-ecosystems',
    status: 'Ratified',
    owner: 'Executive',
    review: 'Half-yearly (sector readiness review)',
    title: 'Industry Ecosystems',
    sub: 'Sector solutions · The Enterprise Division',
    authority: 'Strategic',
    summary:
      'Volume VII sets out how an ecosystem is built and the five conditions that must all hold before one may open — of which a domain expert already hired is the first and enthusiasm is not one. It then treats each sector in turn across three waves: education and higher education, faith institutions, publishing, professional services and small business in the first; healthcare, government, financial services, development, hospitality and property in the second; and the large, slow industrial ecosystems in the third. Each chapter states the institution’s real problem, its buyer, its regulatory surface, its ecosystem stack, its AI agents and its hard boundaries. The volume closes with the Enterprise Division and the retention economics that argue for moving up-market over time.',
  },
  {
    roman: 'VIII', n: 8, file: 'VOLUME-VIII-EXPANSION-FINANCE-ROADMAP.md',
    slug: 'stromex-book-08-expansion-finance',
    status: 'Ratified',
    owner: 'Executive; Board',
    review: 'Annually at the strategy offsite',
    title: 'Expansion, Finance & the Roadmap',
    sub: 'The three phases · The three scenarios · Capital · Geography · Acquisitions',
    authority: 'Strategic — Board',
    summary:
      'Volume VIII carries the canonical three-phase roadmap — Foundation, Race and Global Scale — from which every date in the corpus derives, together with the gates that a phase must pass before the next may open. It builds the unit economics from the ground up, states plainly where the founding market’s favourable ratios will compress and why, and models the group’s future as three scenarios rather than one target: a conservative path that is a good outcome and not a failure, a growth path the company should plan against, and a transformational path that alone reaches the stated ambition. It sets the capital strategy and the constitutional condition on capital, the allocation framework, the international expansion sequence and its entry checklist, the acquisition doctrine, and the conditions that would make the plan wrong.',
  },
  {
    roman: 'IX', n: 9, file: 'VOLUME-IX-THE-INSTITUTION.md',
    slug: 'stromex-book-09-the-institution',
    status: 'Ratified',
    owner: 'Office of the Founder',
    review: 'Annually',
    title: 'The Institution',
    sub: 'Innovation · Research · Talent · Operations · The 100-Year Plan',
    authority: 'Constitutional & Strategic',
    summary:
      'Volume IX defines StromeX as an institution rather than as a business — the parts that must outlive any product, market or founder. It establishes the innovation laboratory with its annual production targets and its kill discipline, the research institute and the independence clause that permits it to publish findings unfavourable to the company, and the measurement constitution together with the anti-metrics the group refuses to optimise. It sets the talent system from hiring through promotion, leadership development, entry programmes and performance review; the standard operating procedure library; the future-technology watch list and its adoption test; and the sustainability commitments. It closes with the 100-Year Plan, the values that must never change, and the Living Constitution Directive that governs every future addition to this corpus.',
  },
  {
    roman: 'X', n: 10, file: 'VOLUME-X-SPACETALK.md',
    slug: 'stromex-book-10-spacetalk',
    status: 'Ratified · Product bible',
    owner: 'Product Executive',
    review: 'Half-yearly until launch, then quarterly',
    title: 'SpaceTalk',
    sub: 'The Communication Operating System',
    authority: 'Product',
    summary:
      'Volume X opens by stating what most documents in its category avoid: a general-purpose consumer messenger competing directly with the incumbents cannot be won, and attempting it would be the most expensive mistake available to the group. It then sets out the position that is winnable — institutional communication infrastructure that grows institution by institution rather than person by person, entering through relationships StromeX already holds. It establishes three wedges in verified identity, the institutional record and federation; specifies the architecture and the encryption position that reconciles user privacy with institutional obligation without concealment; answers the connectivity question honestly; and defines trust and safety, the business model, the roadmap and the risks, including the most likely one — that the product is started too early.',
  },
  {
    roman: 'XI', n: 11, file: 'VOLUME-XI-FINANCIAL-MASTER-PLAN.md',
    slug: 'stromex-book-11-financial-master-plan',
    status: 'Ratified · companion to the operating model',
    owner: 'Chief Financial Officer; Executive; Board',
    review: 'Quarterly (drivers); annually (structure)',
    title: 'The Financial Master Plan',
    sub: 'The Operating Model · Drivers · Scenarios · Sensitivity · Capital',
    authority: 'Strategic — Board',
    summary:
      'Volume XI replaces the scenario sketch in Book VIII, Chapter 5 with an instrument. Every figure in the accompanying workbook is a formula over a stated assumption, so the model can be argued with rather than merely read: change one driver and the twenty-year outcome recomputes. It documents the customer cohort engine, the twenty revenue streams, the margin and operating-leverage trajectory, the cost floor that makes the funding requirement realistic, and the collection lag that makes the cash line honest. Its growth rates are solved so the model reproduces Book VIII’s ratified institution counts exactly — and doing so surfaced a genuine inconsistency in the corpus, since those counts at the published prices in Book III produce materially less revenue than Book VIII asserted. Chapter 9 records that reconciliation and the strategic consequence: the stated valuation ambition sits in the Optimistic case alone.',
  },
];

// ── front matter prose ────────────────────────────────────────────────────
const FOREWORD = `
This corpus exists because of a specific failure that is easy to observe and difficult to correct.

Institutions across much of the world know exactly what they should become. A school knows its certificates ought to be verifiable, that parents should see results on a phone, that admissions should not consume six weeks of a registrar's life. A hospital, a ministry, a publisher and a bank each know the equivalent. What they lack is not ambition. It is a supplier they can trust, a price they can plan around, and a partner who will still exist in year three.

The world does not have a shortage of software. It has a shortage of finished transformation.

A company built to close that gap will face a particular temptation, repeatedly and persuasively. It will be offered revenue in exchange for opacity — for charging where value was not created, for making cancellation difficult, for holding data as leverage, for promising delivery it cannot staff. Each individual concession will be small, defensible, and argued for by intelligent people with a real business case.

This document exists to make those decisions in advance, in daylight, while nothing is at stake — so that the person who faces them later does not face them alone.

It is therefore written as a constitution rather than as a plan. A plan is a prediction and is usually wrong. A constitution is a commitment and can be kept. Where this corpus states a number it states the assumptions beneath it; where it states a principle it states the reasoning, so that a future reader may argue with the argument rather than guess at it; and where it entrenches a provision it does so precisely because that provision will one day be inconvenient.

Everything here is expected to change except the small number of things that must not.
`.trim();

const FOUNDER = `
I did not set out to write a constitution. I set out to build a school's website.

What became clear in the building is that an institution's website, portal, admissions, results, certificates, identity and payments are not seven systems. They are one system wearing seven costumes, and the original error — the one nearly every institution in our markets has made — is buying them separately, from separate people, at separate times, and then employing someone whose real job becomes reconciling them by hand.

Once that is clear, it does not stay confined to schools. A hospital has the same shape. So does a ministry, a publisher, a law firm, a mosque. The vocabulary changes and the underlying structure does not.

I want StromeX to be the company institutions call when they decide to become modern. Not a vendor of components — a partner that takes responsibility for the whole outcome, charges a price it publishes openly, and is still there in a decade.

Two commitments matter more to me than the rest, and I have asked for both to be entrenched so that they cannot be traded away by a future version of this company under pressure.

The first is that verification is free, forever, for whoever is checking. A graduate's certificate belongs to the graduate. An employer, a university or a visa officer must never pay to confirm it is real, and it must never stop working because the school's subscription lapsed. That single commitment costs us a revenue line we could easily have taken, and it is the most valuable thing we will ever give away.

The second is that a customer's data is theirs, completely, and leaves with them whenever they wish. If institutions stay with us it must be because we are good, not because leaving is painful.

I am aware that the ambitions recorded in Volume VIII are large, and that most companies which set out with ambitions of that size do not reach them. This corpus is deliberately honest about that. It models three futures rather than one, and it says plainly which of them we should plan against and which we should merely keep possible.

What I am certain of is the standard. A child in Ikorodu should learn in an institution whose systems are as good as any in London, and should carry a certificate that is believed anywhere in the world without a phone call. Whether we become large is not fully within our control. Whether we are trustworthy is entirely within it.

If those two things ever conflict, Volume IX, Chapter 9 already contains the answer.
`.trim();

const VISION = `
By 2127, that institutions serving ordinary people have extraordinary tools — and that where a person is born no longer determines the quality of the systems that shape their life.
`.trim();

const MISSION = `
To digitise, automate, modernise and intelligently transform organisations across every sector we can serve competently — and to make world-class execution available at a price the institution can actually plan around.
`.trim();

const HOWTOREAD = `
This corpus is written to be consulted rather than read through. It is long by design: a document intended to govern for decades must answer questions its authors did not anticipate, and brevity is bought by leaving those answers out.

Read Volume I first regardless of your role. It is the root from which every other volume draws its authority, and a decision made without it will eventually contradict it.

Thereafter, read by need. Each volume opens with an executive summary sufficient for a reader who will not go further, and each chapter states its reasoning before its conclusion so that a reader who disagrees can locate precisely where.

Three conventions govern the whole corpus. Every recommendation states why it is included, what value it creates, what risk it introduces, what assumptions it rests on, and how success will be measured. Every estimate is labelled as an estimate and carries its assumptions inline — no figure here is a forecast of record or a guarantee. And nothing is fabricated: where the corpus reasons from established practice it says so, where it reasons from first principles it says so, and where it lacks a number it states the method by which the number should be obtained rather than inventing one.
`.trim();

// ── back matter ───────────────────────────────────────────────────────────
const GLOSSARY = [
  ['ACV', 'Annual contract value. The recurring revenue a customer contributes in a year, excluding one-time implementation and build fees.'],
  ['Band A / B / C', 'The three regional price bands defined in Volume I §6.4. All catalogue prices are quoted at Band C (list); Band A applies a 0.32× multiplier and Band B a 0.65×. The band follows the institution’s operating jurisdiction, not its billing address.'],
  ['CAC', 'Customer acquisition cost. Loaded sales and marketing cost divided by customers acquired in the period.'],
  ['CAC payback', 'The number of months of gross profit from a customer required to recover that customer’s acquisition cost.'],
  ['Craft standard', 'The requirement in Volume VI §2.1 that creative work be indistinguishable from that of a good London or New York studio while remaining reproducible by a regional printer on the first attempt.'],
  ['Credential', 'Any institution-issued, cryptographically signed record of an award, qualification, identity or transaction that a third party may need to verify. The subject of Volume IV, Chapter 5.'],
  ['Degraded mode', 'The defined, designed and tested behaviour of a surface under failure — no network, slow network, provider outage. Required of every surface by Volume IV §10.2.'],
  ['Ecosystem', 'A complete sector solution spanning all eight architectural layers, rather than a product sold into a sector. The unit of strategic expansion; see Volume I, Chapter 2.'],
  ['Entrenched provision', 'A clause amendable only by board supermajority with published rationale and thirty days’ notice. Enumerated in Volume IX §9.2.'],
  ['Federation', 'Server-to-server interoperation across independently operated instances, allowing an institution to own its data while remaining reachable. The basis of the SpaceTalk government strategy; Volume X, Chapter 5.'],
  ['Foundation tier', 'The permanently free tier. Not a trial and not a demo; governed by the Free Constitution in Volume I, Chapter 5.'],
  ['Gate', 'A set of conditions that must be met before a roadmap phase may end. A phase ends when its gate is passed, not when its years elapse. Volume VIII, Chapter 2.'],
  ['GRR', 'Gross revenue retention. Recurring revenue retained from existing customers excluding expansion; measures churn alone.'],
  ['Guilloche', 'Fine mathematical line-work used in security printing, extremely difficult to reproduce by scan-and-print. The primary visual security element of a StromeX credential; Volume VI §6.2.'],
  ['Human-in-the-loop', 'The requirement that a named human decides, and is recorded as deciding, wherever the stakes ladder classifies a decision as high. Volume IV §8.1.'],
  ['LTV', 'Lifetime value. The discounted gross profit expected from a customer over the expected life of the relationship.'],
  ['No-fork rule', 'The prohibition on forking shared platform layers for a single customer without written CTO approval and a sunset date. Volume IV §3.2.'],
  ['NRR', 'Net revenue retention. Recurring revenue from existing customers including expansion and contraction. Above 100% means the existing base grows without new customers.'],
  ['Pricing Council', 'The standing body that owns Volume III, meets quarterly, and reviews every price against delivered margin. Volume I §8.4.'],
  ['Reference Implementation', 'A delivered institutional deployment used as proof of method and as a permanent sales asset. Four are recorded in this edition.'],
  ['Rule of 40', 'Revenue growth percentage plus operating margin percentage. A common composite measure of whether a software company balances growth against profitability.'],
  ['Stakes ladder', 'The four-level classification — low, medium, high, prohibited — determining how much autonomy an AI system may exercise over a decision. Volume IV §8.1.'],
  ['System of record', 'The authoritative store of an institution’s people, money, documents, credentials and decisions. Identified in Volume II §9 as the group’s only genuinely durable moat.'],
  ['Value ledger', 'The running, honest account of what an institution has gained from StromeX, shown at every renewal including the periods where the numbers are unimpressive. Volume I §4.4.'],
  ['Verification token', 'A prepaid unit purchased by an institution for verification-adjacent services carrying real marginal cost. Verification itself is always free to the verifier. Volume III §3.5.'],
  ['Wave', 'A group of industry ecosystems opened in the same roadmap phase. Volume I §2.2.'],
];

const BIBLIOGRAPHY = [
  ['Federal Ministry of Education, Nigeria', 'Nigeria Education Statistics — Annual School Census 2024/25. Education Management Information System portal.', 'https://emis.education.gov.ng/portal/', 'Cited in Volume VII §1.1 for the count of private schools and enrolment in the founding market.'],
  ['Growthspree', 'B2B SaaS NRR and GRR Benchmarks 2026, by ARR Stage, ACV Tier, Vertical and GTM Motion.', 'https://www.growthspreeofficial.com/blogs/b2b-saas-nrr-grr-net-gross-revenue-retention-benchmarks-2026-by-acv-stage-vertical', 'Cited in Volume V §7.1 and Volume VII §14.4 for retention by contract-value band.'],
  ['Digital Applied', 'Net Revenue Retention Benchmarks 2026: SaaS Expansion Data.', 'https://www.digitalapplied.com/blog/net-revenue-retention-benchmarks-2026-saas-expansion-data', 'Cited in Volume V §7.1 for median B2B net revenue retention.'],
  ['Value Add VC', 'SaaS Valuation Multiples 2026.', 'https://valueaddvc.com/saas-valuations', 'Cited in Volume VIII §5.4 for public SaaS enterprise-value-to-revenue multiples.'],
  ['Aventis Advisors', 'SaaS Valuation Multiples: 2015–2026.', 'https://aventis-advisors.com/saas-valuation-multiples/', 'Cited in Volume VIII §5.4 for the historical range of software multiples.'],
  ['L40', 'SaaS Multiples 2026: The Real Private Range.', 'https://www.l40.com/insights/saas-multiples', 'Cited in Volume VIII §5.4 for private-company multiples and the premium band.'],
  ['Eqvista', 'SaaS Index: Revenue Multiples, Valuations & Market Trends.', 'https://eqvista.com/saas-index-revenue-multiples-valuations-market-trends/', 'Cited in Volume VIII §5.4 for the distribution of Rule of 40 outcomes.'],
  ['Priori Data', 'Most Popular Messaging App Statistics 2026.', 'https://prioridata.com/data/messaging-app-stats/', 'Cited in Volume X §1.1 for messaging platform monthly active users.'],
  ['The Register', 'Matrix messaging gaining ground in government IT, February 2026.', 'https://www.theregister.com/on-prem/2026/02/09/matrix-messaging-gaining-ground-in-government-it/4663932', 'Cited in Volume X §5.1 for public-sector adoption of federated messaging.'],
  ['Element', 'Sweden goes live with Matrix-based federation.', 'https://element.io/blog/sweden-goes-live-with-matrix-based-federation/', 'Cited in Volume X §5.1.'],
  ['Open Source For You', 'EU Backs Open Source Matrix For Secure Internal Communications, February 2026.', 'https://www.opensourceforu.com/2026/02/eu-backs-open-source-matrix-for-secure-internal-communications/', 'Cited in Volume X §5.1 for the European Commission trial.'],
];

const INTERNAL_SOURCES = [
  ['StromeX MVP', 'apps/api, apps/web, infra', 'FastAPI backend with multi-provider AI routing, memory, spaced-repetition tutor and PDF export; Next.js frontend; Docker Compose infrastructure. Establishes the canonical stack in Volume IV §2.2.'],
  ['Independent MVP Audit', 'docs/04-STROMEX-INDEPENDENT-AUDIT.md', 'Security, scalability, reliability and performance audit including a critical server-side request forgery vulnerability found, reproduced and fixed. Carried forward as a standing engineering rule in Volume IV §15.'],
  ['Reference Implementation №1', 'Sultan Hanafi Royal Schools', 'Four-language institutional build (English, Arabic RTL, Yorùbá, French) with approximately thirty-five page templates per locale; four verification surfaces; certificate generation with documented identifier architecture, security model and signing-key deployment; digital identity and card system; finance platform; eight role portals; personalisation centre; and approximately one hundred and twenty institutional system, governance and design documents.'],
  ['Reference Implementation №2', 'WorldWide English College', 'A seventy-three-table credential and commerce schema across fifteen migrations, covering enrolment integrity, competencies, evidence, awards, credential signing, issued documents, verifying institutions, payments, instalment plans, multi-currency routing, corporate seats and alumni chapters. The evidential basis for Volume IV §4.2.'],
  ['Reference Implementation №3', 'Al-Madeenah College', 'Bilingual static build system with offline service worker, verification surfaces, font subsetting pipeline and document generation to PDF and DOCX.'],
  ['Reference Implementation №4', 'Institutional portal system', 'Multi-role portal implementation covering student, staff, parent, applicant and administrative roles, admissions pipeline, attendance, timetable, assessment, finance and library.'],
];

module.exports = {
  EDITION, VERSION, DATE, VOLUMES,
  FOREWORD, FOUNDER, VISION, MISSION, HOWTOREAD,
  GLOSSARY, BIBLIOGRAPHY, INTERNAL_SOURCES,
};
