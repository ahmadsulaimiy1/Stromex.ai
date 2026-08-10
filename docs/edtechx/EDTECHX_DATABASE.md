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
**terms** — `id, tenant_id, academic_year_id, name, sequence, starts_on, ends_on, is_current`
**levels** — `id, tenant_id, name, short_name, sequence, stage_id` — "Year 7", "Grade 5", "JSS 1"; **data, not code**
**stages** — `id, tenant_id, name, sequence` — "Primary", "Secondary", "Foundation"
**class_groups** — `id, tenant_id, level_id, academic_year_id, name, campus_id, form_tutor_membership_id, capacity`
**subjects** — `id, tenant_id, name, code, department_id, is_examinable`
**class_subjects** — `id, tenant_id, class_group_id, subject_id, teacher_membership_id, periods_per_week`

**grading_scales** — `id, tenant_id, name, kind(letter|percentage|gpa|descriptor|points), is_default`
**grading_bands** — `id, tenant_id, scale_id, label, min_value, max_value, points, descriptor, is_pass, sequence`

**term_structures / promotion_rules / attendance_policies** — configuration rows holding rule definitions as validated JSONB, evaluated by the application's rule engine. This is what makes the Bible's "Four Schools test" satisfiable without code changes.

---

## 6. Schema — people and operations

**students** — `id, tenant_id, admission_number (uq per tenant), first_name, middle_name, last_name, preferred_name, date_of_birth, gender, photo_key, status(applicant|enrolled|graduated|withdrawn|suspended), custom jsonb, created_at, deleted_at`
**enrolments** — `id, tenant_id, student_id, academic_year_id, class_group_id, level_id, house_id, roll_number, started_on, ended_on, status`
**guardians** — `id, tenant_id, membership_id (nullable — not every guardian has a login), first_name, last_name, email, phone, relationship, is_primary, has_custody, receives_billing, receives_academic, custom jsonb`
**student_guardians** — `student_id, guardian_id, relationship, priority`

**attendance_sessions** — `id, tenant_id, date, class_group_id, class_subject_id (null for daily), period_id, taken_by_membership_id, taken_at, status(open|submitted|amended)`
**attendance_marks** — `id, tenant_id, session_id, student_id, code_id, minutes_late, note, recorded_by, recorded_at` · `uq(session_id, student_id)`
**attendance_codes** — `id, tenant_id, code, label, category(present|absent|late|excused|other), counts_as_present, requires_reason, colour`
School-defined codes; the `category` gives the platform something stable to compute against.

**assessments** — `id, tenant_id, term_id, class_subject_id, name, kind, max_score, weight, due_on, grading_scale_id, status(draft|open|closed|published)`
**assessment_scores** — `id, tenant_id, assessment_id, student_id, score NUMERIC, band_id, comment, entered_by, entered_at, moderated_by, moderated_at, override_reason` · `uq(assessment_id, student_id)`
**result_publications** — `id, tenant_id, term_id, scope jsonb, published_by, published_at, unpublished_at, audience jsonb`
Publishing is an explicit, audited event; parents never see a mark that has not been through it.

**timetable_periods / rooms / timetable_slots** — the timetable grid, with a clash constraint enforced by a unique index on `(tenant_id, teacher_membership_id, day, period_id, effective_range)` and equivalents for room and class.

**conduct_types / conduct_records** — configurable behaviour taxonomy and the records against it.

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
**document_templates** — `id, tenant_id, kind(report_card|transcript|certificate|invoice|receipt|letter), name, status, version, template jsonb, page jsonb`
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
