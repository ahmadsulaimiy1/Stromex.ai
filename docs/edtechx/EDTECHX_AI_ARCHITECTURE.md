# EdirasX AI Architecture

**Version:** 1.0
**Constitution:** `EDTECHX_EDITORIAL_BIBLE.md` §7 is binding on everything below.

---

## 1. Principle

The application never talks to an AI provider. It talks to the **EdirasX AI Gateway**, which decides who serves the request.

```
Feature (Teacher AI, Design AI, …)
   → AI Gateway
       ├─ policy      : which providers may serve this feature, for this tenant
       ├─ routing     : capability, cost, latency, health, tenant preference
       ├─ entitlement : is this feature and this quota available?
       ├─ adapter     : provider-specific translation
       ├─ metering    : tokens, cost, latency, outcome
       └─ safety      : provenance, approval gate, injection posture
```

Provider-specific code exists in exactly one place per provider: its adapter. No `import anthropic` outside `intelligence/providers/anthropic.py`. A test asserts this.

---

## 2. Gateway contract

```python
class AIRequest:
    feature: FeatureKey          # teacher.lesson_plan, design.propose, …
    messages: list[Message]
    system: str | None
    max_tokens: int
    temperature: float
    response_schema: dict | None # structured output where the feature needs it
    tenant_id: UUID
    membership_id: UUID | None
    idempotency_key: str | None

class AIResponse:
    content: str | dict
    provider: str
    model: str
    usage: Usage                 # input, output, cached tokens
    cost_estimate: Decimal
    latency_ms: int
    provenance: Provenance       # provider, model, prompt_version, timestamp, request_id
    finish_reason: str
```

Every adapter normalizes to this shape: message roles, system prompts, tool declarations, streaming chunks, token accounting, finish reasons, and errors. A caller must not be able to tell which provider served a request except by reading `provenance`.

---

## 3. Provider registry

| Provider | Adapter | Notes |
|---|---|---|
| Anthropic (Claude) | `anthropic` | Default for reasoning-heavy and long-context features |
| OpenAI (GPT) | `openai` | Alternate general-purpose |
| Google (Gemini) | `google` | Alternate; strong multimodal |
| DeepSeek | `deepseek` | Cost-optimized tier |
| Self-hosted / OpenAI-compatible | `openai_compatible` | Enterprise on-premise or regional residency |
| Development | `dev` | Deterministic, offline. **Refuses to load when `ENVIRONMENT=production`.** Labelled in the UI as a development provider — never presented as a model |

Each registry entry declares: capabilities (context window, structured output, tools, vision, streaming), cost per million tokens in and out, region availability, **whether the provider contractually excludes training on submitted data**, and health state.

The gateway will not route tenant content to a provider whose no-training flag is false. That is a hard rule, not a preference.

---

## 4. Routing

Order of consideration:

1. **Tenant preference** — a school with BYO keys or a residency requirement is honoured absolutely.
2. **Feature policy** — some features declare a minimum capability (long context for whole-document analysis; structured output for design proposals).
3. **Health** — a provider failing its circuit breaker is skipped.
4. **Cost/quality tier** — the plan determines which tier a feature may use. Drafting a routine message does not need the most expensive model; analysing a cohort's performance might.
5. **Latency** — interactive features prefer faster models; batch features do not care.

**Fallback:** on retryable failure, the gateway tries the next eligible provider, with a total attempt budget and a total time budget. Non-retryable failures (content policy, invalid request) do not cascade — they return honestly. If no provider is eligible, the feature reports itself unavailable with a clear reason. It never silently degrades to a worse answer without saying so.

**Circuit breaker** per provider: open after a failure threshold, half-open probe, close on success. State is shared across workers via Redis.

---

## 5. School-owned keys (BYO AI)

Optional, Premium and above. The default is EdirasX-managed AI, because a school should not need to understand APIs to benefit from them.

- Credentials encrypted with envelope encryption; stored in `ai_provider_configs`; **write-only through the API** — no endpoint ever returns a key, masked or otherwise.
- Validation on save: a minimal live call confirms the key works before it is accepted.
- Rotation and revocation are first-class; revocation takes effect immediately across all workers.
- When a tenant's own key fails, the school is notified and the tenant chooses in advance whether to fall back to EdirasX-managed AI or to fail closed.
- BYO usage is metered for the school's visibility but not billed by EdirasX.

---

## 6. Safety rails

**The approval gate.** Any AI-originated change to a record of consequence — grade, attendance mark, promotion decision, conduct record, invoice, published result, live theme — must pass through:

```
AI proposes  →  proposal persisted  →  human reviews  →  human approves  →  applied
                                                      ↘ rejects → recorded, discarded
```

The applying code path requires an `ai_approvals` row with a distinct approver, a timestamp, and the proposal hash. There is no code path that writes such a record from an AI response. This is enforced by a test that attempts it.

**Provenance.** Every AI-generated artefact shown to a user is visibly labelled and carries retrievable provenance.

**Injection posture.** Tenant data placed into a prompt is untrusted. Model output is never executed, never interpolated into SQL, never used to make an authorization decision, and never permitted to invoke a tool the feature did not explicitly grant.

**Content boundaries.** Student-facing assistants are configured per tenant for age-appropriateness and academic-integrity policy — a school decides whether the student assistant explains a concept or refuses to do the homework.

**Privacy.** Prompts and completions are **not stored by default**; only metadata is. Content retention is opt-in per tenant with a stated window, and is excluded entirely for safeguarding and medical contexts.

---

## 7. The assistants

Each is a *feature* with its own policy, prompt versioning, entitlement key, and meter — not a chatbot with a different name.

| Assistant | Representative capabilities |
|---|---|
| **Teacher AI** | Lesson planning, question generation from a syllabus, rubric drafting, report-card comment drafting from *actual* marks and attendance, differentiation suggestions, marking assistance with justification |
| **Student AI** | Concept explanation at the right level, study planning, self-quizzing, feedback interpretation — bounded by the school's academic-integrity setting |
| **Parent AI** | Plain-language explanation of results and school communications, translation, "what should I ask at parents' evening" |
| **Administrator AI** | Natural-language search across records the principal is authorized to see, timetable conflict suggestions, bulk-communication drafting, anomaly surfacing |
| **Principal AI** | Cohort and trend analysis, narrative summaries of institutional data, board-report drafting |
| **Finance AI** | Collection summaries, reconciliation assistance, dunning message drafting |
| **Admissions AI** | Application summarization against school-defined criteria, interview scheduling assistance, communication drafting |
| **Design AI** | Natural-language design proposals — see §8 |

**Two invariants across all of them:** an assistant may only see what its invoking principal is authorized to see (the same scope predicates as any query — the AI is not a permission bypass), and no assistant writes to a record of consequence without §6.

---

## 8. AI Design Studio

A school administrator describes what they want; the AI proposes a complete visual identity; a human approves; only then does it apply.

**Input examples the system must handle:**
- "Make our school portal feel like a prestigious British boarding school."
- "Use our existing royal blue and gold branding."
- "Make the interface more luxurious but minimal."
- "Make the student portal youthful and energetic."
- "Make the parent portal extremely simple for less technical parents."
- "Create a modern Islamic educational identity while respecting our existing logo."
- "Make our dashboard resemble the visual quality of a premium financial application while retaining an education-focused experience."

**Output — a structured proposal, validated against a schema, never free text:**
colour palette (every semantic role, light and dark) · typography (families from the licensed catalogue, scale adjustments) · spacing density · component style (radius, elevation, border weight) · navigation structure and labels · dashboard composition per persona · login page treatment · document styles · a written rationale in the school's language.

**Hard constraints the generator operates under:**
1. Output must be valid design-system tokens. The AI chooses *values*; it cannot invent new token names or emit raw CSS.
2. **Every colour pair is contrast-checked before the proposal is shown.** A proposal that fails WCAG AA is corrected to the nearest compliant value, and the correction is disclosed. We do not present an inaccessible design and let the school choose it.
3. Fonts come from the licensed catalogue or the school's own uploaded licence.
4. The school's existing logo and stated brand colours are treated as fixed input, not as suggestions.

**Workflow:** request → proposal → live preview across personas and breakpoints → compare against current and against alternative proposals → refine in natural language → approve → publish as a new theme version → rollback available forever.

The AI never writes to the live theme. It writes to `ai_design_proposals`. The publish step is an ordinary, audited, human theme publication.

---

## 9. Metering and economics

Every request writes an `ai_requests` row: tenant, membership, feature, provider, model, input/output/cached tokens, latency, status, estimated cost, and actual cost where the provider reports it.

Quotas resolve through the entitlement engine (`EDTECHX_BILLING.md`): a plan grants a monthly token or credit allowance per feature class; overage behaviour is per-tenant policy (block, notify, or bill).

The school sees its own usage: what was used, by whom, for what, and what remains. **No school is ever surprised by an AI bill or a quota wall** — warnings fire at 70%, 90%, and 100%.

The platform sees margin: cost by tenant, feature, provider, and model, so routing can be tuned against real economics rather than assumption.

---

## 10. Prompt management

Prompts are versioned assets in the repository, not strings inline in business logic. Each has an id, a version, its expected input variables, its output schema, and its evaluation set. A prompt change is a reviewed code change, and `ai_requests.prompt_version` makes any past output traceable to the exact prompt that produced it.

Evaluation: each feature carries a small golden set with assertions on structure, safety, and (where objective) correctness. Regressions are caught before release, not by teachers.
