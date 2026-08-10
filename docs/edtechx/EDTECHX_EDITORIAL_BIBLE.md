# The EdirasX Editorial Bible

**Status:** Living document — the constitution of EdirasX
**Custodian:** Imam Ahmad Sulaimiy, Senior Developer — the expert behind the development of EdirasX
**Version:** 1.0
**Supremacy clause:** Where any other document, design, or line of code conflicts with this Bible, the Bible wins until formally amended here.

---

## 0. How to use this document

This is not marketing copy. It is a decision instrument. When an engineer, designer, or AI agent faces a choice that the specification does not settle, the answer is derived here — from the principles, not from taste.

Every section is written so that it can be applied as a test. If a principle cannot be used to reject something, it is not a principle; it is a slogan, and it does not belong in this document.

---

## 1. Brand foundation

### 1.1 Name

**EdirasX.**

Written as one word: capital E, lowercase *diras*, capital X. Never "Edirasx", "Ediras X", "EDIRASX" in running prose, "Ediras-X", or "EX". The uppercase logotype `EDIRASX` is a logo treatment, not a spelling.

The name derives from the Arabic root of study and learning — **الدراسة** (*al-dirāsa*, "study") and **ادرس** (*idrus*, "study!"). The X carries the same meaning it always did: the variable a school fills in with its own identity.

Pronounced *ed-EE-ras-ex*.

**Technical namespace.** The repository, package names, and documentation filenames presently use the earlier `edtechx` / `EDTECHX_` namespace. That is a deliberate, temporary divergence from the product name, recorded as ADR-017, and it is a migration to be scheduled rather than a naming inconsistency to be tolerated indefinitely. Product-facing text uses EdirasX without exception.

### 1.2 Positioning

> **The education platform that becomes your school's own platform.**

This is the single sentence from which the entire product derives. It contains a promise and a constraint:

- **The promise:** a school does not adopt EdirasX; a school *becomes itself* on EdirasX.
- **The constraint:** any feature that makes EdirasX more visible to the end user at the expense of the school's identity is, by definition, working against the positioning.

### 1.3 Mission

To provide a world-class, intelligent, customizable education operating system that prestigious institutions worldwide are proud to deploy — one that adapts to each school's identity rather than imposing a generic experience.

### 1.4 Vision

A future in which every educational institution has a digital environment that feels authentically its own, powered by technology that understands educational context rather than merely storing educational data.

### 1.5 Promise

Institutional-grade technology with consumer-grade elegance, so that schools spend their attention on education rather than on fighting their platform.

### 1.6 Personality

| We are | We are not |
|---|---|
| Confident | Arrogant |
| Prestigious | Elitist |
| Intelligent | Cold |
| Professional | Sterile |
| Innovative | Gimmicky |
| Supportive | Intrusive |

Each pair is a live editorial test. "Confident, not arrogant" means: state what the product does without superlatives about ourselves. "Supportive, not intrusive" means: the assistant waits to be asked, except where waiting would cause harm.

### 1.7 Tone

Respectful of educational professionals. Clear and concise. Warm where warmth is earned, professional everywhere. Reassuring in moments of uncertainty. Encouraging without flattery.

The tone floor: **a teacher reading our interface copy at 07:50, four minutes before a lesson, must not feel talked down to and must not have to read anything twice.**

### 1.8 Voice

- Authoritative about education technology.
- Humble about the importance of teachers. We do not claim to teach; we claim to remove obstacles to teaching.
- Progressive about educational innovation, practical about institutional reality.
- Visionary about learning, never speculative about a school's own data.

### 1.9 Vocabulary

Use educational terminology precisely. Avoid jargon where a plain word serves.

| Prefer | Over | Why |
|---|---|---|
| school, institution | organization, org, company | Schools are not businesses first |
| learners, students | users, end users | Never call a child a "user" in the UI |
| educators, teachers | instructors, content providers | Teaching is a profession, not a role in a workflow |
| families, parents | guardians (in UI copy) | "Guardian" is correct in data models, cold in interface copy |
| enrolled | onboarded, provisioned | Enrolment is the school's word |
| record, register | log, entry | Academic records carry weight |

**The Terminology Rule:** every noun in the list above is *also* configurable by the school (see `EDTECHX_CUSTOMIZATION_ENGINE.md`). The table defines EdirasX's *defaults*, not the platform's assumptions. A school that calls a class a "form" and a grade a "year" must never see our defaults leak through.

### 1.10 Messaging principles

1. Lead with outcomes, not features.
2. Emphasize institutional ownership over platform capability.
3. Highlight flexibility as a property of the architecture, never as a list of settings.
4. Present intelligence as assistance, never as authority.
5. Celebrate educational excellence; never imply we are the source of it.

### 1.11 What EdirasX will never say

- That it improves learning outcomes. We enable the people who do.
- That its AI knows a student. It observes records; educators know students.
- That a school "runs on EdirasX." Schools run on teaching. EdirasX runs underneath.

---

## 2. Product philosophy

Eleven beliefs. Each is stated as a claim, then as an engineering consequence, because a belief with no consequence is decoration.

**1. Technology serves pedagogy; it does not define it.**
*Consequence:* no academic structure may be hard-coded. Terms, grading scales, promotion rules, attendance models, and assessment structures are data, not enums baked into application logic.

**2. Simplicity is sophistication.**
*Consequence:* a feature that requires training to discover has failed. Depth is reached through progressive disclosure, not through density.

**3. Institutions deserve ownership.**
*Consequence:* white-labelling, custom domains, and full theming are architecture, not upsell decorations bolted on later. Data export is a right, not a retention lever.

**4. Personalization is not optional.**
*Consequence:* six distinct primary experiences (admin, teacher, student, parent, principal, platform operator) with genuinely different information architecture — not one dashboard with the heading swapped.

**5. AI assists; it does not replace.**
*Consequence:* no AI output may mutate an official academic record without an explicit, attributable human approval step. This is enforced in code, not in policy. See §7.

**6. Accessibility is a right, not a feature.**
*Consequence:* WCAG 2.2 AA is a merge requirement, not a backlog item.

**7. Teacher experience is paramount.**
*Consequence:* teacher-facing flows are optimized for elapsed time and click count, measured. Attendance for a class of forty must be markable in under thirty seconds on a phone.

**8. Student experience drives engagement.**
*Consequence:* students see clarity — what is due, what is expected, how they are doing — before they see anything else.

**9. Parent experience builds trust.**
*Consequence:* the parent portal is designed for the least technically confident parent in the school, on the cheapest phone, on the worst connection.

**10. Administrator experience enables excellence.**
*Consequence:* administrators get insight and bulk operations, not spreadsheets rendered as HTML.

**11. Prestige is earned through quality.**
*Consequence:* we do not ship a screen we would be embarrassed to project in a board meeting.

---

## 3. UX philosophy

**Hierarchy.** Every screen has exactly one primary thing. If two things compete, one of them is wrong.

**Simplicity.** Every element justifies its presence or is removed. "It might be useful" is not a justification.

**Discoverability.** Features are found when needed, without documentation. The test: a competent teacher who has never seen the screen completes the task without asking anyone.

**Progressive disclosure.** Show what is needed now. Advanced capability is one deliberate step away, never zero (clutter) and never three (buried).

**Consistency.** Established patterns beat clever ones. A user's prediction about behaviour must be correct.

**Feedback.** Every action produces a response within 100ms, even if the response is only acknowledgement. Users must never wonder whether something happened.

**Error prevention.** Design out the error first. Constrain inputs, default sensibly, confirm destructively. When errors happen, provide the recovery path in the error itself.

**Accessibility.** WCAG 2.2 AA minimum: keyboard operation of every flow, screen-reader semantics, visible focus, 4.5:1 text contrast, respect for reduced-motion.

**Responsiveness.** The experience works on a 360px phone over a throttled 3G connection. That is the design target, not the degraded case.

**Cognitive load.** Minimize what the user must hold in their head. Never require a user to remember something the system already knows.

**Information density.** Balance. Neither a wall of data nor a page with four numbers on it. Density is a *setting* the school can adjust (comfortable / compact), because a registrar and a parent want different things.

**Navigation.** The user always knows where they are, how they got there, and how to leave.

**Onboarding.** Welcoming, educational, and respectful of time. Never a mandatory tour.

**Empty states.** Informative, encouraging, actionable. An empty state is a teaching opportunity, not a blank rectangle.

**Loading states.** Honest. Skeletons that match the shape of what is coming. Never a spinner where a skeleton would inform.

**Error states.** Clear, actionable, blameless. Never "an error occurred."

**Success states.** Confirm plainly, and offer the natural next action.

---

## 4. Visual philosophy — what "prestigious" means here

### 4.1 Prestige is not

- Excessive gradients
- Excessive glassmorphism
- Giant cards and cavernous whitespace
- Heavy or stacked shadows
- Animation without purpose
- Visual noise
- Trend-chasing
- Hype aesthetics

These are the visual language of products that need to *look* expensive. EdirasX serves institutions that already are.

### 4.2 Prestige is

**Typography.** Professional typefaces. Excellent hierarchy. Restrained sizes. Generous but not loose line height. Consistent weights. Never more than three families (heading, body, and optionally a script/regional face).

**Proportion.** Balanced composition. Harmonious spacing. Element sizes that reflect importance.

**Spacing.** A consistent 4px base grid. Breathing room around content. Purposeful padding. Clear grouping by proximity.

**Restraint.** Knowing when to stop. Colour used sparingly. Emphasis reserved for what matters. Motion for meaning, not for show.

**Hierarchy.** Obvious primary action. Supporting secondary. Quiet tertiary. Nothing shouting.

**Visual rhythm.** Predictable patterns; repetition of a small set of elements; variation only for emphasis.

**Precision.** Pixel alignment. Consistent borders. Exact spacing. Zero visual artefacts. Precision is the single most reliable signal of care.

**Imagery.** Professional or none. A missing image beats a stock image of smiling models.

**Motion.** Purposeful, fast (150–250ms), interruptible, and fully disabled under `prefers-reduced-motion`.

**Composition.** Grid-based. Clear focal points. Deliberate asymmetry only where it serves.

**Intelligent colour.** Brand colour carries meaning consistently; contrast is verified, not assumed; cultural connotation is considered.

**Excellent information design.** Data presented so the reader draws the correct conclusion quickly. Readable tables. Forms that guide. Charts that inform rather than decorate.

### 4.3 The standard

> A screen is finished when a prestigious institution would be proud to project it in a board meeting, and a teacher would be happy to use it every day for a year.

Both halves must be true. Prestige without daily usability is a brochure; usability without prestige is the market we are displacing.

---

## 5. The six humans

EdirasX does not have "users." It has six people with materially different jobs. Each gets its own information architecture. Full IA specifications live in `EDTECHX_PRODUCT_SPEC.md` §4; the essence is here because it is editorial, not merely functional.

### 5.1 School administrator / registrar
**Job:** keep the institution running correctly.
**Emotional state:** responsible, interrupted, accountable.
**Design posture:** efficiency-first. Data-rich. Bulk operations. Clear action paths. Audit trail always reachable.
**Failure mode to avoid:** making them do one-at-a-time what should be done in bulk.

### 5.2 Teacher
**Job:** teach; record the minimum necessary; be left alone.
**Emotional state:** time-poor, often standing, often on a phone.
**Design posture:** task-focused, minimum clicks, mobile-first, no distraction.
**Failure mode to avoid:** any flow that costs more time than the paper process it replaced.

### 5.3 Student
**Job:** know what is expected and how they are doing.
**Emotional state:** variable; sometimes anxious about grades.
**Design posture:** encouraging, clear next steps, honest feedback, mobile-first.
**Failure mode to avoid:** gamification that trivializes, or ranking that shames.

### 5.4 Parent / family
**Job:** be reassured, and know when to act.
**Emotional state:** caring, busy, sometimes unfamiliar with software.
**Design posture:** reassuring, plain language, low density, unmistakable next steps.
**Failure mode to avoid:** presenting raw academic data without interpretation.

### 5.5 Principal / school owner
**Job:** understand institutional health and decide.
**Emotional state:** strategic, sceptical of dashboards.
**Design posture:** high-level with drill-down, visual, trustworthy, comparative over time.
**Failure mode to avoid:** vanity metrics; numbers with no decision attached.

### 5.6 Platform operator (EdirasX staff)
**Job:** keep every tenant healthy.
**Emotional state:** operational, alert-driven.
**Design posture:** system-wide perspective, actionable alerts, technical detail one click away.
**Failure mode to avoid:** any operator tool that can read tenant academic content without an audited, justified break-glass action.

---

## 6. The "it should feel like our school" principle

The most important UX principle in this document.

**Not:** "We use EdirasX."
**But:** "This is our school's digital environment."

EdirasX is the engine underneath. The school owns the experience.

Operationally this means:
- The school's name, mark, colours, and typography are what users see. Ours are not.
- Every user-facing term is the school's term.
- The URL can be the school's own.
- Documents (report cards, certificates, transcripts, emails) carry the school's identity, not ours.
- EdirasX attribution appears only where commercially required by plan (Free tier), and even then quietly, in one place.

**The test:** show a screenshot to a parent at that school. If their first reaction is anything other than recognizing their own school, we have failed.

---

## 7. AI constitution

AI in EdirasX is bound by five rules. These are enforced in code (`EDTECHX_AI_ARCHITECTURE.md` §6), not merely stated.

1. **No silent mutation of the record.** AI may draft, suggest, summarize, and analyse. It may never write to an academic record — a grade, an attendance mark, a promotion decision, a disciplinary entry — without an explicit human approval that is attributed and audited.
2. **Provenance is mandatory.** Any AI-generated content shown to a user is labelled as such, and its origin (provider, model, prompt version, timestamp) is retrievable.
3. **Tenant data does not cross tenants, and does not train anyone's model.** Provider selection must respect a no-training guarantee; providers without one are unavailable for tenant content by default.
4. **Human judgement outranks the model.** Where AI output and an educator disagree, the interface presents the educator's view as authoritative.
5. **Cost and usage are visible to the school.** No school is surprised by an AI bill or a quota wall.

---

## 8. Flexibility constitution

EdirasX must not encode assumptions about how an institution works. The
following are **data**, never code:

grades · terms · semesters · houses · departments · faculties · campuses ·
programmes · qualifications · credit systems · grading scales · attendance
methods · examination structures · progression rules · academic calendars ·
terminology · curriculum · organizational hierarchy · report-card format ·
roles and permissions

### 8.1 EdirasX is a universal education operating system

Not a school system that also serves universities. One academic engine,
spanning the whole continuum:

**Early childhood** — pre-nursery, nursery, kindergarten, preschool, reception,
early years, foundation.
**Primary / elementary** — any numbering, any span, any key-stage grouping.
**Secondary** — junior and senior secondary, middle and high school, GCSE and
A-Level shapes, IB, JSS/SSS, and national models we have not met.
**Vocational, technical and professional** — certificates, diplomas, advanced
and higher national diplomas, apprenticeships, competency-based programmes.
**Undergraduate** — associate, foundation, higher national, bachelor's,
honours, professional degrees.
**Postgraduate** — postgraduate certificates and diplomas, taught and research
master's, MPhil.
**Doctoral and research** — PhD, professional doctorates, supervision,
milestones, thesis, viva, completion.

None of these appears in executable code. Every one is a configuration an
institution creates, names, and orders for itself.

### 8.2 The layers, and why they are separate

```
Institution (the tenant)
  └── Academic unit ......... campus · faculty · school · department · division
        └── Programme ....... a named course of study, usually leading to a qualification
              └── Level ..... a stage within it: Year 3 · Level 200 · Intermediate
                    └── Class group ... form · section · seminar group · arm
Academic stage .............. a broad phase, where the institution uses one
Qualification ............... what completion awards, in the institution's own framework
Course ...................... subject · module · unit · paper
Academic period ............. term · semester · trimester · quarter · block · session
```

**No institution is required to use every layer.** A primary school uses stage,
level, class group and course. A university uses unit, programme, level,
cohort, course and section. A research institute uses unit, programme,
supervision and milestone. The layers a school does not use are simply absent,
not empty ceremony it must fill in.

**These are genuinely different things and must never be collapsed:**

- A **programme** is what a student is admitted to. A **level** is where they
  have reached within it. A **course** is what they study. A **class group** is
  who they sit with. A **qualification** is what they leave with.
- Bachelor of Computer Science may run Level 100–400, or Year 1–3, or
  Foundation/Intermediate/Advanced. The same programme structure, three
  institutional vocabularies.

### 8.3 What must never be hard-coded

No enum, constant, branch, or column may encode:

- a national qualification framework, or any qualification as a fixed concept
  (`BACHELORS`, `MASTERS`, `PHD`, `PRIMARY`, `SECONDARY`);
- a duration ("a bachelor's is three years", "a term is one third of a year");
- a credit system, credit value, or contact-hour rule;
- a level's position in a national system, or arithmetic over level numbers;
- a grading scale, threshold, pass mark, or classification;
- a progression or completion condition;
- the number or names of academic periods.

The system asks the configured academic model what applies. It never assumes.

### 8.4 The Universal Education Test

The acceptance suite proves the same engine represents at least these eight,
through configuration alone:

| # | Institution |
|---|---|
| 1 | Nursery → Primary → Secondary |
| 2 | Elementary → Middle → High School |
| 3 | Foundation → Undergraduate → Postgraduate |
| 4 | Diploma → HND → Bachelor's → Master's → PhD |
| 5 | A credit-based university with faculties and departments |
| 6 | A non-credit institution |
| 7 | A research-oriented postgraduate programme with supervision |
| 8 | A vocational / competency-based institution |

This is the **minimum** flexibility standard, not the maximum. A proposed
feature that requires a code change to serve any of the eight — or a ninth we
have not imagined — is wrongly designed.

Static checks accompany the suite: no product module may name a specific
educational system in executable code, and no comparison in the academic engine
may test an academic quantity against a hard-coded number.

### 8.5 The principle

> The institution defines its academic world. EdirasX provides the technology
> to represent it.

## 9. Cultural constitution

EdirasX serves secular, Islamic, Christian, international, public, private, and boarding schools; universities, colleges, academies, and training institutions — across Nigeria, wider Africa, the GCC and Middle East, the UK, Europe, and the USA.

Therefore:
- No cultural or religious assumption ships as a default. Religious features exist as *installable configurations*, never as baked-in structure.
- The calendar system, week start, weekend days, date format, number format, and name order are configuration.
- Right-to-left layout is a first-class rendering mode, not a stylesheet patch.
- Translation is a platform capability; the interface is authored to be translatable (no concatenated sentences, no baked-in plurals).
- **No cheap regional edition.** Product quality is identical in every market. Pricing varies; the product does not.

---

## 10. Non-negotiables

The following are grounds to block a release, regardless of schedule:

1. A cross-tenant data access path.
2. A privilege-escalation path.
3. AI writing to an academic record without human approval.
4. A WCAG 2.2 AA failure on a critical journey.
5. A screen that ships with placeholder or fabricated data presented as real.
6. A destructive action without confirmation and an audit entry.
7. Secrets reachable from a browser, or written to logs.
8. A required flow that is unusable on a 360px viewport.

---

## 11. Definition of done

A feature is done when *all* of the following are true. "The code works" is one of thirteen.

- [ ] Implementation is functionally complete
- [ ] UI is polished to the §4 standard
- [ ] Backend is real (no stub outside a marked development adapter)
- [ ] Input validation is enforced server-side
- [ ] Authorization is enforced server-side, including tenant scope
- [ ] Tests pass, including an authorization test and a tenant-isolation test where applicable
- [ ] Responsive behaviour verified at 360 / 768 / 1280
- [ ] Accessibility verified: keyboard path, focus order, labels, contrast
- [ ] Error handling is comprehensive and actionable
- [ ] Loading states present
- [ ] Empty states designed
- [ ] Security considerations reviewed against `EDTECHX_SECURITY.md`
- [ ] Documentation updated, including this Bible if a principle changed

---

## 12. Amendment

This Bible is amended by an entry in `EDTECHX_DECISIONS.md` that states the principle being changed, the reason, and the consequences. Silent divergence between this document and the product is a defect in the product *or* in this document — never an acceptable steady state.
