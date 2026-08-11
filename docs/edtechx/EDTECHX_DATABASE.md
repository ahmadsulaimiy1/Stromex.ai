# EdirasX Database Architecture

**Version:** 1.0
**Engine:** PostgreSQL 15+

---

## 1. Conventions

- **Keys:** UUID v4 primary keys (`gen_random_uuid()`). Sequential integers leak volume and invite enumeration.
- **Tenant column:** every tenant-owned table has `tenant_id UUID NOT NULL REFERENCES tenants(id)`, and it is the **first column of every index that matters**.
- **Timestamps:** `created_at`, `updated_at` — `TIMESTAMPTZ NOT NULL`, UTC. All display-time conversion happens in the application using the tenant's timezone.
- **Soft delete:** `deleted_at TIMESTAMPTZ NULL` on user-visible domain records. Queries exclude soft-deleted rows by default; unique constraints are partial (`WHERE deleted_at IS NULL`).
- **Enums:** PostgreSQL enums only for values that are genuinely fixed by the platform (e.g. `invoice_status`). Anything a school might redefine is a **row in a configuration table**, never an enum. Enum changes are migration events; institutional vocabulary must not be.
- **Money:** `NUMERIC(14,2)` plus a `currency CHAR(3)`. Never floating point. Never a bare number without its currency.
- **JSONB:** used for genuinely open structures — theme tokens, custom field values, workflow definitions, AI proposals. Every JSONB column has a documented, versioned schema validated in the application. JSONB is not an excuse to avoid modelling.
- **Naming:** `snake_case`; tables plural; join tables `a_b`; indexes `ix_{table}_{cols}`; unique `uq_`; foreign keys `fk_`; check constraints `ck_`.
- **Referential integrity:** foreign keys always declared; `ON DELETE RESTRICT` by default. Cascades only where the child is genuinely part of the parent (a submission file belongs to a submission).

---

## 2. Row-level security

Every tenant-owned table:

```sql
ALTER TABLE <t> ENABLE ROW LEVEL SECURITY;
ALTER TABLE <t> FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON <t>
  USING       (tenant_id = current_setting('app.tenant_id', true)::uuid)
  WITH CHECK  (tenant_id = current_setting('app.tenant_id', true)::uuid);
```

Three roles:

| Role | Purpose | RLS |
|---|---|---|
| `edtechx_app` | The application's request path | Subject to RLS; no `BYPASSRLS`; not table owner |
| `edtechx_migrator` | Alembic migrations, DDL | Owner; used only by the migration job |
| `edtechx_operator` | Support/analytics with break-glass | Subject to RLS; grants are time-boxed and audited |

`FORCE ROW LEVEL SECURITY` matters: without it, the table owner bypasses the policy, and a deployment that accidentally connects as the owner would silently lose isolation.

**Migration invariant:** a migration that creates a tenant-owned table without enabling RLS fails CI. The check enumerates tables with a `tenant_id` column and asserts policy presence.

### 2.1 Foreign keys are tenant-scoped

Row-level security governs reads and writes. It does **not** govern referential integrity: PostgreSQL performs a foreign-key check with the referenced table's privileges and without applying its policies. A plain `child.parent_id REFERENCES parent(id)` therefore lets one tenant insert a row pointing at another tenant's row — corrupting the record, enabling a cross-tenant denial of service through `ON DELETE RESTRICT`, and turning every foreign key into an existence oracle for ids the tenant may not read.

So every foreign key between two tenant-owned tables references the pair:

```sql
ALTER TABLE parent ADD CONSTRAINT uq_parent_tenant_id_id UNIQUE (tenant_id, id);

ALTER TABLE child ADD CONSTRAINT fk_child_parent_id_tenant
  FOREIGN KEY (tenant_id, parent_id) REFERENCES parent (tenant_id, id)
  ON DELETE RESTRICT;
```

`ON DELETE SET NULL` becomes `ON DELETE SET NULL (parent_id)` so the reference is cleared without nulling `tenant_id`. That form requires PostgreSQL 15 or later.

Applied by `app.db.tenant_fk.bind_foreign_keys_to_tenant`, which rewrites the metadata once after every model is mapped — so a new tenant-owned model gets a tenant-scoped key by existing, on the same principle as the policy and the isolation test. See ADR-026.

### 2.2 Append-only tables

Three tables are append-only for the application role, which holds no `UPDATE` or `DELETE` on them: `audit_events`, `security_events`, and `enrolment_events`. `enrolments` additionally holds no `DELETE` — a placement may be corrected but never erased. The list lives in `app.db.rls.APPEND_ONLY_TABLES` and `UNDELETABLE_TABLES`, and the grants are re-issued by every migration, because `GRANT ... ON ALL TABLES` covers only the tables that existed when it ran.

---

## 3. Schema — platform

**tenants** — `id, slug (uq), name, legal_name, status(provisioning|active|suspended|archived), region, country, timezone, locale, currency, created_at, activated_at, archived_at, settings jsonb`

**tenant_domains** — `id, tenant_id, hostname (uq), kind(subdomain|custom), is_primary, verified_at, tls_status, created_at`

**users** — `id, email (uq, citext), email_verified_at, password_hash, mfa_secret_encrypted, mfa_enabled_at, status, last_login_at, failed_login_count, locked_until, created_at`
Global, deliberately: one human, one credential, even when they belong to several schools.

**memberships** — `id, user_id, tenant_id, status(invited|active|suspended|ended), started_at, ended_at, created_at` · `uq(user_id, tenant_id)`
The join between a person and a school. All tenant-scoped authorization hangs off this row, not off the user.

**membership_roles** — `id, tenant_id, membership_id, role_id, scope jsonb, granted_by, granted_at, expires_at`

**roles** — `id, tenant_id (null = platform-defined template), key, name, description, is_system, created_at`

**role_permissions** — `role_id, permission` (permission is a string, see permission model)

**sessions** — `id, user_id, tenant_id, refresh_token_hash, issued_at, expires_at, revoked_at, ip, user_agent, device_label`

**audit_events** — `id, tenant_id, actor_user_id, actor_membership_id, action, resource_type, resource_id, before jsonb, after jsonb, reason, request_id, ip, user_agent, created_at`
Append-only: no `UPDATE`/`DELETE` grant for `edtechx_app`. Partitioned monthly by `created_at`.

**security_events** — `id, tenant_id, kind, severity, detail jsonb, ip, created_at`

**break_glass_grants** — `id, operator_user_id, tenant_id, reason, scope, granted_at, expires_at, revoked_at, notified_at`

---

## 4. Schema — billing

**plans** — `id, key, name, tier, is_public, created_at`
**plan_features** — `plan_id, feature_key, enabled`
**plan_limits** — `plan_id, limit_key, value` (`NULL` = unlimited)
**price_books** — `id, plan_id, region, currency, interval(month|year), unit(flat|per_student|per_staff|tier), amount, min_qty, max_qty, effective_from, effective_to`
**subscriptions** — `id, tenant_id, plan_id, status(trialing|active|past_due|canceled|paused), quantity, currency, interval, trial_ends_at, current_period_start, current_period_end, canceled_at`
**subscription_overrides** — `id, tenant_id, feature_key|limit_key, value, reason, expires_at, granted_by`
**usage_records** — `id, tenant_id, meter_key, quantity NUMERIC, period_start, period_end, membership_id, feature, provider, model, metadata jsonb, created_at`
Partitioned monthly; the AI metering hot path.
**platform_invoices / platform_payments** — EdirasX billing the school (distinct from the school's own fee invoices in §7).

---

## 5. Schema — institution and academics

**campuses** — `id, tenant_id, name, code, address jsonb, timezone, is_default`
**departments** — `id, tenant_id, name, code, parent_id, head_membership_id`
**houses** — `id, tenant_id, name, code, colour`
**staff_profiles** — `id, tenant_id, membership_id, staff_number, title, employment_type, joined_on, left_on, custom jsonb`

**academic_years** — `id, tenant_id, name, starts_on, ends_on, is_current`
**academic_periods** — `id, tenant_id, academic_year_id, name, kind_label, sequence, starts_on, ends_on, is_current, weight` — term, semester, trimester, quarter, block or session; one row per period, whatever the institution calls them
**levels** — `id, tenant_id, name, short_name, code, sequence, stage_id (nullable), programme_id (nullable), next_level_id, is_terminal` — a level belongs to a stage, a programme, or both; a check constraint requires one. `next_level_id` is explicit rather than `sequence + 1`, because the next level may be in another stage or absent because this one graduates. **There is deliberately no `grade_level` integer.**
**stages** — `id, tenant_id, name, sequence` — "Primary", "Secondary", "Foundation"
**class_groups** — `id, tenant_id, level_id, academic_year_id, name, campus_id, form_tutor_membership_id, capacity`
**courses** — `id, tenant_id, name, code, is_core, is_elective, credits, credit_system_id, contact_hours, academic_unit_id, programme_id, level_id, grading_scale_id, custom` — named `Course` rather than `Subject` because "subject" is a school word that reads oddly for a university module; the terminology layer renders whatever the institution says
**class_subjects** — `id, tenant_id, class_group_id, subject_id, teacher_membership_id, periods_per_week`

**grading_scales** — `id, tenant_id, name, kind(letter|percentage|gpa|descriptor|points), is_default`
**grading_bands** — `id, tenant_id, scale_id, label, min_value, max_value, points, descriptor, is_pass, sequence`

**academic_units** — `id, tenant_id, name, code, kind_label, parent_id, sequence, head_membership_id, custom` — self-referencing; `kind_label` is the institution's word for the tier ("Faculty", "Department", "Campus", "Institute") and is never read to make a decision.

**qualifications** — `id, tenant_id, name, short_name, code, category_label, framework_level, awarding_body, typical_duration_periods, required_credits, credit_system_id, completion_rules jsonb, is_active` — the institution's own framework. `framework_level` orders qualifications *within this institution* and carries no external meaning. **No enum, ever.**

**credit_systems** — `id, tenant_id, name, code, unit_label, unit_label_plural, hours_per_unit, is_default` — because a credit, a credit hour, a unit and an ECTS credit are not interchangeable, and an institution that counts nothing must not be forced to pretend.

**programmes** — `id, tenant_id, name, code, academic_unit_id, qualification_id, stage_id, kind_label, duration_periods, required_credits, credit_system_id, is_research, is_active, custom` — every quantity nullable, because variable-duration and open-ended programmes are ordinary.

**cohorts** — `id, tenant_id, name, code, programme_id, academic_year_id` — a group progressing together.

**milestone_definitions / supervision_roles** — research education's checkpoints and its supervision vocabulary, defined per programme by the institution.

**term_structures / promotion_rules / attendance_policies** — configuration rows holding rule definitions as validated JSONB, evaluated by the application's rule engine. This is what makes the Bible's "Four Schools test" satisfiable without code changes.

---

## 6. Schema — people and operations

Four layers, kept apart because collapsing any two makes an ordinary institution unrepresentable (ADR-027). `users` is the global credential; `people` is what one institution knows about a human; the relationship tables say what that person *is* to the institution; `enrolments` says where they were placed and between which dates.

**people** — `id, tenant_id, user_id (nullable, uq per tenant when set — most people never sign in), full_name, given_names, family_name, preferred_name, sort_name, gender_label, date_of_birth, email, phone, locale, address, custom jsonb, deleted_at`
One required name field, written as the person writes it; the structured parts are optional and independent. `gender_label` is free text, not an enum.

**student_relationships** — `id, tenant_id, person_id, reference (admission / matriculation / registration number, uq per tenant when set), kind_label, status(prospective|active|suspended|ended), started_on, ended_on, custom jsonb`
**staff_relationships** — `id, tenant_id, person_id, reference, kind_label, academic_unit_id, is_teaching, status, started_on, ended_on, custom jsonb`
**guardian_relationships** — `id, tenant_id, guardian_person_id, student_person_id, relationship_label, sequence, is_primary_contact, is_emergency_contact, receives_reports, may_collect, is_financially_responsible, status, custom jsonb` · `uq(tenant_id, guardian_person_id, student_person_id)` · `check(guardian ≠ student)`
Person to person, not user to student. `kind_label` and `relationship_label` are the institution's own words; the platform stores them and never reads them to make a decision.

**Note what is absent from all three:** no class, no level, no programme, no year. Placement is not an attribute of being a student.

**enrolments** — `id, tenant_id, student_relationship_id, academic_year_id?, programme_id?, level_id?, class_group_id?, cohort_id?, status(prospective|active|suspended|ended), outcome?(progressed|repeated|transferred|withdrawn|completed|discontinued), started_on, ended_on?, previous_enrolment_id?, custom jsonb`
Every structural column is nullable — a doctoral placement has a programme and no class group; a rolling-intake course has neither a class group nor a year. Two check constraints: an enrolment cannot end before it began, and `(ended_on IS NULL) = (outcome IS NULL)` so an open placement is unexplained and a closed one never is. There is deliberately **no** constraint forcing one open enrolment per student: concurrent enrolment is ordinary.

**enrolment_events** — `id, tenant_id, enrolment_id, kind(admitted|enrolled|placed|transferred|suspended|resumed|withdrawn|readmitted|progressed|repeated|completed|awarded|corrected), occurred_on, reason, actor_membership_id, detail jsonb`
Append-only (§2.2). Two dates: `occurred_on` is when it took effect, `created_at` is when it was recorded, and they are routinely weeks apart. A correction is a new event of kind `corrected`, never an edit.

**qualification_awards** — `id, tenant_id, student_relationship_id, qualification_id, programme_id?, enrolment_id?, awarded_on, classification_label?, reference?, awarded_by_membership_id, custom jsonb`
The qualification is a row the institution defined (ADR-024), so one table awards a certificate of attendance and a research doctorate. `classification_label` is free text: honours divisions, Latin honours, distinction/merit/pass and competency verdicts are each one institution's vocabulary.

**attendance_sessions** — `id, tenant_id, date, class_group_id, class_subject_id (null for daily), period_id, taken_by_membership_id, taken_at, status(open|submitted|amended)`
**attendance_marks** — `id, tenant_id, session_id, student_id, code_id, minutes_late, note, recorded_by, recorded_at` · `uq(session_id, student_id)`
**attendance_codes** — `id, tenant_id, code, label, category(present|absent|late|excused|other), counts_as_present, requires_reason, colour`
School-defined codes; the `category` gives the platform something stable to compute against.

**assessments** — `id, tenant_id, term_id, class_subject_id, name, kind, max_score, weight, due_on, grading_scale_id, status(draft|open|closed|published)`
**assessment_scores** — `id, tenant_id, assessment_id, student_id, score NUMERIC, band_id, comment, entered_by, entered_at, moderated_by, moderated_at, override_reason` · `uq(assessment_id, student_id)`
**published_results** — `id, tenant_id, result_set_id, student_relationship_id, assessment_id?, course_id?, score, max_score, band_label, points, is_pass, is_absent, grading_scale_code, credits, credit_unit_label, weight, comment, published_at, amended_at?`
The snapshot (ADR-033). The last three of the numeric columns were added by the document engine: a university that revalues a module from 15 credits to 20 must not retroactively change what a graduate earned, and a department that moves coursework from 30% to 40% has not changed last year's report card. `credit_unit_label` travels with the number because "12" means nothing without it — a credit, a credit hour and an ECTS credit are not the same quantity. Undeletable by the application role.

**result_sets / approval_workflows / approval_records / result_amendments** — the publication lifecycle. Publishing is an explicit, audited institutional act; parents never see a mark that has not been through it.

**timetable_periods / rooms / timetable_slots** — the timetable grid, with a clash constraint enforced by a unique index on `(tenant_id, teacher_membership_id, day, period_id, effective_range)` and equivalents for room and class.

**conduct_types / conduct_records** — configurable behaviour taxonomy and the records against it.

### 6.1 Bulk import

**import_batches** — `id, tenant_id, kind, filename, content_hash, status(draft|validated|failed|applied|reversed), columns jsonb, mapping jsonb, options jsonb, notes jsonb, row_count, valid_count, invalid_count, duplicate_count, created_count, uploaded_by_membership_id, applied_by_membership_id, applied_at, reversed_at, failure_reason, summary jsonb`
**import_rows** — `id, tenant_id, batch_id, line_number, raw jsonb, values jsonb, status(pending|valid|invalid|duplicate|skipped|applied|reversed), errors jsonb, matched_by, created jsonb`

`raw` is the evidence — the line exactly as read — and `line_number` is the
file's own, so an error report matches what the person sees in their
spreadsheet. `content_hash` recognises the same file being uploaded twice, which
is the most common way a school ends up with every student recorded twice.
Applying is a single transaction; see ADR-028.

### 6.2 Academic documents

One engine, not one table per document kind (ADR-034).

**document_templates** — `id, tenant_id, code, name, purpose_label, purpose(report_card|transcript|document), status(draft|published|archived), version, parent_version_id, sections jsonb, numbering jsonb, page jsonb, freeze_branding, published_results_only, is_default, custom jsonb, published_at, published_by_membership_id` · `uq(tenant_id, code, version)`

`sections` is the ordered list of `{key, title, visible, omit_when_empty, options}`, validated against the platform's section catalogue when the template is saved — so a template that saves is a template that prints. `purpose` names the permission resource governing it, and there are three rather than one because a school that lets a form tutor print report cards has not thereby let them print transcripts. `purpose_label` is the institution's own word and is never read to make a decision.

**document_sequences** — `id, tenant_id, scope_key, next_value` · `uq(tenant_id, scope_key)`
The counter behind a document number, incremented under `SELECT … FOR UPDATE`. Keyed on the number's **prefix**, not on the template: two templates numbering `RC/…` are sharing a series and must share a counter. `max(number) + 1` would be smaller and would hand two registrars pressing Issue at the same moment the same transcript number.

**documents** — `id, tenant_id, template_id, template_code, template_version, purpose, purpose_label, title, student_relationship_id, academic_year_id?, academic_period_id?, number, sequence, version, supersedes_id?, status(issued|superseded|void), void_reason?, issued_on, issued_at, issued_by_membership_id, payload jsonb, sources jsonb, checksum, verification_code` · `uq(tenant_id, number)` · `uq(tenant_id, verification_code)`

`payload` is what the document said — every grade, total, comment and the terminology in force — frozen at issue. Reprinting reads it; nothing recomposes it. `sources` records which published results were quoted and how many times each had been amended at that moment, so the engine can report that a document has been overtaken without keeping a second copy of the results. `template_code` and `template_version` are denormalised so a document can name its own design after the template row is archived. **Undeletable** by the application role (§2.2): withdrawn is `void` with a reason, replaced is `superseded` with a link, and both survive.

---

## 7. Schema — finance (the school's own money)

**fee_structures** — `id, tenant_id, academic_year_id, term_id, level_id, name, currency`
**fee_items** — `id, tenant_id, structure_id, name, amount, is_optional, category`
**invoices** — `id, tenant_id, student_id, term_id, number (uq per tenant), currency, subtotal, discount_total, total, amount_paid, balance, status(draft|issued|part_paid|paid|void|overdue), issued_on, due_on`
**invoice_lines** — `id, tenant_id, invoice_id, description, amount, quantity, fee_item_id`
**payments** — `id, tenant_id, invoice_id, amount, currency, method, provider, provider_reference, status(pending|succeeded|failed|refunded), paid_at, recorded_by, idempotency_key (uq)`
**receipts** — `id, tenant_id, payment_id, number (uq per tenant), issued_at, document_key`
**discounts / scholarships** — named adjustments applied to structures or individual students, with an approval trail.

**Money invariants**, enforced by check constraints and by the service layer:
`total = subtotal - discount_total`, `balance = total - amount_paid`, `amount_paid = Σ succeeded payments`, and `amount_paid ≤ total` unless an explicit credit note exists.

---

## 8. Schema — learning

**courses** — `id, tenant_id, code, title, description, category_id, subject_id, level_id, status, visibility, starts_on, ends_on`
**course_modules** — `id, tenant_id, course_id, title, sequence, release_at, release_conditions jsonb`
**lessons** — `id, tenant_id, module_id, title, sequence, content jsonb, duration_minutes`
**resources** — `id, tenant_id, course_id, lesson_id, kind, title, storage_key, url, size_bytes, mime_type`
**course_enrolments** — `id, tenant_id, course_id, student_id, cohort_id, role, enrolled_at, completed_at, progress NUMERIC`

**assignments** — `id, tenant_id, course_id, class_subject_id, title, instructions, max_score, grading_scale_id, rubric_id, opens_at, due_at, cutoff_at, late_policy jsonb, allow_resubmission, submission_types, group_mode, status`
**submissions** — `id, tenant_id, assignment_id, student_id, group_id, attempt, status(draft|submitted|graded|returned), submitted_at, is_late, content, storage_keys jsonb` · `uq(assignment_id, student_id, attempt)`
**submission_grades** — `id, tenant_id, submission_id, score, band_id, feedback, rubric_scores jsonb, graded_by, graded_at, released_at`

**question_banks / questions / question_options** — `questions.kind` covers the v1 type list; `content jsonb` holds type-specific structure against a versioned schema.
**quizzes / quiz_questions / quiz_attempts / quiz_responses** — attempt-level state machine with time limits, shuffling, and review rules.
**rubrics / rubric_criteria / rubric_levels**
**forums / threads / posts** — with moderation state.
**cohorts / cohort_members / groups / group_members**
**completions** — `id, tenant_id, subject_type, subject_id, student_id, criteria_met jsonb, completed_at`
**certificates** — `id, tenant_id, template_id, student_id, issued_at, verification_code (uq), document_key`

---

## 9. Schema — customization

**themes** — `id, tenant_id, name, status(draft|published|archived), version, tokens jsonb, typography jsonb, assets jsonb, created_by, published_at, published_by, parent_version_id`
**terminology_sets** — `id, tenant_id, locale, status, version, terms jsonb`
**navigation_configs** — `id, tenant_id, persona, status, version, tree jsonb`
**dashboard_configs** — `id, tenant_id, persona, status, version, widgets jsonb`
**branding_profiles** — `id, tenant_id, status, version, parent_version_id, display_name, legal_name, motto, address, contact_email, contact_phone, website, logo_url, crest_url, signature_image_url, watermark_url, primary_colour, accent_colour, ink_colour, heading_font, body_font, letterhead_note, footer_note, verification_url_template, custom jsonb, published_at, published_by_membership_id`
How an institution presents itself. Deliberately **current presentation metadata**: a document resolves it at render rather than freezing it, so a school that moves reprints an old transcript on today's letterhead (ADR-034). Images are URLs; a crest belongs in object storage.

*(Document templates were planned here with a `kind` enum. They were built in §6.2 without one — a fixed list of document kinds is ADR-024's forbidden enum in another costume, and the institution's word for the document is `purpose_label`.)*
**custom_fields** — `id, tenant_id, entity, key, label, data_type, options jsonb, required, sequence, visibility jsonb`
Values land in the owning table's `custom jsonb`, validated against the definitions on write.
**form_definitions / form_submissions** — the generic form engine used by admissions and by school-defined workflows.
**workflow_definitions / workflow_instances** — configurable approval chains.

Every configuration table shares the `status` / `version` / `parent_version_id` triple, giving draft → preview → publish → rollback uniformly, with history.

---

## 10. Schema — intelligence

**ai_requests** — `id, tenant_id, membership_id, feature, provider, model, prompt_version, input_tokens, output_tokens, cached_tokens, latency_ms, status, error_code, estimated_cost, actual_cost, created_at` — partitioned monthly. **Never stores prompt or completion content by default**; content retention is opt-in per tenant with a stated retention window.
**ai_provider_configs** — `id, tenant_id (null = platform), provider, credential_encrypted, base_url, enabled, priority, allowed_features jsonb, created_by, rotated_at`
**ai_design_proposals** — `id, tenant_id, request_text, status(draft|proposed|previewed|approved|rejected|applied|reverted), proposal jsonb, preview_key, created_by, reviewed_by, reviewed_at, applied_theme_id`
**ai_approvals** — the generic record proving a human approved an AI action before it touched a record of consequence.

---

## 11. Indexing

- Every foreign key is indexed.
- Every tenant-owned index is `(tenant_id, ...)` — leading with `tenant_id` matches how RLS filters and how every query is shaped.
- Hot compound indexes: `attendance_marks(tenant_id, student_id, recorded_at)`, `assessment_scores(tenant_id, student_id, assessment_id)`, `invoices(tenant_id, status, due_on)`, `submissions(tenant_id, assignment_id, status)`, `audit_events(tenant_id, resource_type, resource_id, created_at DESC)`.
- Partial indexes for soft delete: `WHERE deleted_at IS NULL`.
- Keyset pagination on all large lists; `OFFSET` is not used past a few pages.
- `usage_records`, `ai_requests`, and `audit_events` are partitioned by month with a retention policy per table.

---

## 12. Migration discipline

Expand → migrate → contract, always, so that old and new application versions can run against the same schema during a deploy:

1. **Expand:** add nullable column / new table / new index (`CONCURRENTLY`).
2. **Backfill:** batched, resumable, rate-limited.
3. **Dual-write** in the application.
4. **Switch reads.**
5. **Contract:** drop the old column in a *later* release.

Rules: no destructive change in the same release as the code that stops using it; no `ALTER TABLE ... SET NOT NULL` on a large table without a validated check constraint first; no long-held locks; every migration reviewed for lock class and duration; every migration has a tested down path or is explicitly marked irreversible with a reason.

---

## 13. Backup and retention

Continuous WAL archiving with point-in-time recovery; nightly base backup; **restores tested on a schedule — an untested backup is a hypothesis**. Per-tenant logical export for portability and for the data-ownership promise. Retention: audit events 7 years, financial records per jurisdiction, academic records per institutional policy (configurable), AI request metadata 13 months, security events 2 years.
