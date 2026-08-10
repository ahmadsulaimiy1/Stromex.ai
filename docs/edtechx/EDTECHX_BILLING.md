# EdTechX Billing and Commercial Architecture

**Version:** 1.0

---

## 1. Principle

**No price, plan name, or limit appears in application logic.** Plans are rows; entitlements are computed; features ask the entitlement engine a question and act on the answer.

```python
entitlements.require(Feature.AI_DESIGN_STUDIO)   # → 402 with an upgrade path
entitlements.limit(Limit.ACTIVE_STUDENTS)        # → int | None (None = unlimited)
entitlements.meter(Meter.AI_TOKENS, tokens)      # → records usage, may raise QuotaExceeded
```

A grep for a plan name outside the `billing` module is a defect.

---

## 2. Freemium philosophy

Free must be **genuinely useful**. A crippled free tier teaches a school that the product is poor; a generous one teaches them what it feels like to run on EdTechX, which is the only argument that converts.

What Free is *not* allowed to do: lose the school's data, hide their data behind a paywall, degrade support to nothing, or display advertising. What Free *is* allowed to do: cap scale, cap AI, cap customization depth, and carry a discreet EdTechX mark in one place.

---

## 3. Plans

Features and limits are illustrative defaults, seeded as data and tunable without a release.

### Free
Core school management (students, staff, classes, subjects, attendance, basic assessment) · basic LMS (courses, assignments, submissions) · up to 100 active students · 2GB storage · limited AI (a small monthly allowance across drafting assistants) · logo and primary colour customization · community support · discreet EdTechX attribution.

### Starter
Up to 500 active students · 20GB · parent portal · full attendance and assessment · report cards from templates · fee tracking · richer AI allowance · theme customization (full palette and typography) · email support.

### Professional
Up to 2,000 active students · 200GB · full finance (invoicing, payments, receipts, ledgers) · admissions · timetabling · advanced LMS (quizzes, question banks, rubrics, gradebook depth) · full customization (navigation, dashboards, terminology, documents) · substantial AI · custom subdomain · priority support.

### Premium
Up to 10,000 active students · 1TB · advanced AI across all assistants · **AI Design Studio** · **Design Studio** · custom domain with managed TLS · BYO AI keys · advanced analytics · white-label documents and email · professional-services options · named support contact.

### Enterprise
Custom scale · SSO (SAML/OIDC) · advanced integrations and API access · dedicated support with an SLA · custom contractual terms · migration services · optional dedicated database or regional residency · enterprise AI terms · sandbox tenant.

---

## 4. Entitlement engine

```
plan features/limits
  + subscription overrides   (trial grants, pilot terms, negotiated Enterprise)
  + promotional grants       (time-boxed)
  = effective entitlement set
```

Cached in Redis keyed by `tenant_id` and subscription version; invalidated on any subscription, override, or plan change. Evaluated on every request that touches a gated capability.

**Limit enforcement is graduated, not cliff-edged.** Crossing a limit must never destroy work or lock a school out of its own records:

| Limit type | Behaviour at the ceiling |
|---|---|
| Scale (students, staff) | Blocks *new* creation; existing records fully accessible and editable |
| Storage | Blocks new uploads; existing files fully accessible |
| AI tokens | Blocks new AI requests; the rest of the product is unaffected |
| Feature gates | The feature is presented as available-on-upgrade, never hidden as if it did not exist |

Warnings at 70%, 90%, and 100% of any limit, to the tenant's billing contacts.

---

## 5. Pricing engine

Price is resolved, never hard-coded:

```
price = f(plan, region, currency, interval, quantity, promotions, contract)
```

`price_books` rows carry `plan × region × currency × interval × unit × amount`, with tiered bands and effective dates. A price change is a new row with a new `effective_from`; **existing subscriptions keep their agreed price** until renewal, and price history is auditable.

Units supported: flat, per active student, per staff member, and tiered bands. Most school markets price per student; some prefer a flat institutional fee. Both must work without code.

---

## 6. Regional pricing

Markets: Nigeria · wider Africa · GCC · Middle East · UK · Europe · USA · rest of world.

**The rule from the Bible §9 governs here: there is no cheap regional edition.** Product capability is identical everywhere. Only the price, currency, and payment methods differ.

Region is determined by the tenant's declared country on the subscription record — a deliberate, auditable field — **not by IP geolocation**, which is trivially manipulated, wrong for VPN users, and insulting when it guesses badly. Changing declared country changes price at renewal, not retroactively, and is recorded.

Local payment methods matter more than local pricing: bank transfer and Paystack/Flutterwave in Nigeria; cards and mandates in the UK/EU; invoicing and purchase orders for institutional buyers everywhere. Annual and termly billing cycles are supported because school budgets are annual and termly, not monthly.

---

## 7. Metering

`usage_records`, partitioned monthly, written asynchronously so metering never sits in the request's latency path (but never dropped — failures queue and retry).

Meters: active students · active staff · storage bytes · AI input/output/cached tokens (by feature, provider, and model) · AI requests · documents generated · messages sent by channel · API calls (Enterprise) · export operations.

Aggregation is nightly into per-tenant, per-period rollups; the raw rows are retained 13 months for dispute resolution and margin analysis.

---

## 8. Subscription lifecycle

```
trialing → active → past_due → (recovered → active | canceled)
                  ↘ paused
active → canceled → grace period → archived
```

- **Trial:** 30 days at Professional level, no card required. Ends into Free, not into a lockout.
- **Downgrade:** takes effect at period end; the school is told exactly what will change and what will be blocked *before* it happens.
- **Past due:** dunning over 21 days with escalating notice; features are not cut during a school term without notice; academic records remain readable throughout. We do not hold a school's attendance register hostage.
- **Cancellation:** immediate export offered; data retained for a 90-day grace period; then archived; then deleted per retention policy. Export is always available, on every plan, including Free.

---

## 9. School-facing finance vs platform billing

Two distinct systems, deliberately separated:

| | Platform billing | School finance |
|---|---|---|
| Who pays whom | School → EdTechX | Family → School |
| Tables | `platform_invoices`, `platform_payments`, `subscriptions` | `invoices`, `payments`, `receipts`, `fee_structures` |
| Module | `billing` | `finance` |

They share only the payment-provider abstraction. Conflating them would make a school's fee ledger an artefact of our commercial model, which is both wrong and dangerous.

---

## 10. Payment abstraction

```
PaymentProvider
  ├─ create_intent / charge
  ├─ verify / capture
  ├─ refund
  ├─ webhook verification (signature checked before any work)
  └─ reconciliation
```

Adapters: Paystack, Flutterwave, Stripe, bank transfer (manual reconciliation with a real state machine), and a sandbox adapter for development that drives the same state machine and is refused in production.

Invariants: every charge carries an idempotency key; webhooks are idempotent and signature-verified; a payment's state is only ever advanced by a verified provider event or an audited manual action; reconciliation is a scheduled job, not a hope.

---

## 11. Professional services and marketplace (architected, not yet built)

**Professional services:** branding, dashboard and portal design, migration, integrations, workflow configuration, custom reports, AI configuration, custom domains, training. Modelled as `service_engagements` with scope, quote, milestones, and delivery — because the ecosystem goal is self-service *plus* AI design *plus* human design in one platform.

**Experience marketplace:** dashboard and portal themes, report-card and certificate designs, course and academic templates, workflow templates, AI assistants, communication templates. Flow: designer creates → EdTechX reviews → school selects or purchases → installed as a *draft* configuration version → school customizes → publishes.

The architectural requirement today is only this: because every configuration object is already a versioned, portable, schema-validated document (`EDTECHX_CUSTOMIZATION_ENGINE.md`), an "experience" is just a bundle of those documents. The marketplace is therefore a distribution and commerce problem later, not an architecture problem now. See `EDTECHX_DECISIONS.md` ADR-009.

---

## 12. Commercial invariants

1. A school's own data is always exportable, on every plan, including after cancellation's grace period begins.
2. No plan change ever deletes data.
3. No limit is enforced retroactively against existing records.
4. Price changes never apply mid-term to an existing subscription.
5. Every entitlement denial is logged — it is simultaneously an upsell signal and evidence that a limit may be set wrongly.
6. A school can always see exactly what it is paying for and what it has used.
