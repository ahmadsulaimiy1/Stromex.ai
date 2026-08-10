# EdirasX Runbook

Operational procedures. Written to be followed at 03:00 by someone who did not
write the code.

---

## 1. Environments

| Environment | Purpose | Data |
|---|---|---|
| `development` | Local | Synthetic |
| `test` | CI | Ephemeral, rebuilt per run |
| `staging` | Production-shaped rehearsal | Anonymized |
| `production` | Live schools | Real, and irreplaceable |

`ENVIRONMENT=production` **refuses to boot** on: a default or short secret key,
debug mode, a localhost database URL, plaintext CORS origins, or a database URL
equal to the migration URL. That last one is the important one — see §3.

---

## 2. Deploying

1. CI green, including every blocking suite in `EDTECHX_TESTS.md` §3.
2. Migrations reviewed for lock class and duration (`EDTECHX_DATABASE.md` §12).
3. Run migrations as `edtechx_migrator`, as a **separate gated step**, never as part of application start.
4. Verify RLS immediately after migrating — see §3.
5. Deploy application containers (rolling).
6. Smoke check: `/api/v1/health`, then `/api/v1/context` against a known tenant host.
7. Watch error rate and p95 for 15 minutes.

**Rollback:** redeploy the previous image. Schema rollback is *not* the first
response — the expand/contract discipline means the previous application version
runs against the new schema. If it does not, the migration violated the
discipline and that is the incident.

---

## 3. The isolation check — run after every migration

The single most important operational check in this system.

```bash
python -c "
from sqlalchemy import create_engine
from app.core.config import get_settings
from app.db.registry import Base
from app.db.rls import verify_rls
e = create_engine(get_settings().migration_database_url)
with e.connect() as c:
    bad = verify_rls(c)
print('UNPROTECTED:', bad or 'none')
raise SystemExit(1 if bad else 0)
"
```

Non-empty output is a **Severity 1 incident**: tenant-owned tables are readable
across schools. Do not proceed; do not "fix it in the morning".

Also confirm the request-path role is still harmless:

```sql
SELECT rolname, rolsuper, rolbypassrls FROM pg_roles WHERE rolname = 'edtechx_app';
-- must be: f | f

SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname='public' AND c.relkind='r' AND pg_get_userbyid(c.relowner) = 'edtechx_app';
-- must be: 0   (an owner bypasses FORCE RLS)
```

---

## 4. Provisioning a school

1. Create the tenant (slug, name, country, timezone, locale, currency).
2. Create the subdomain `tenant_domains` row; custom domains additionally require verification before they resolve.
3. Materialize the system roles from the templates.
4. Create the owner's user and membership; grant the `owner` role.
5. Send the invitation; require MFA enrolment at first sign-in.
6. Seed the default theme, terminology, and navigation.
7. Attach a subscription (trial by default).

Verification: sign in on the school's own hostname, confirm `/api/v1/context`
returns that school, and confirm a token issued there is refused on another
school's hostname.

---

## 5. Suspending and archiving

**Suspend** (non-payment, abuse, at request): set `status = suspended`. Host
resolution then fails closed with `school_unavailable`. Data is untouched.

**Archive:** only after the cancellation grace period, with export offered and
confirmed. Retention then follows `EDTECHX_DATABASE.md` §13.

Never delete a school's data as a first response to a commercial dispute.

---

## 6. Break-glass access to tenant content

Operator access to tenant *metadata* is ordinary. Access to *content* is not.

1. Record reason and duration (maximum 4 hours).
2. Issue the scoped grant.
3. Notify the tenant's administrators — automatically, not at the operator's discretion.
4. Every action under the grant is audited with the grant id.
5. The grant expires on its own; renewal is a new grant with a new reason.

A break-glass grant used without a corresponding support ticket is reviewed.

---

## 7. Incidents

**Severity 1** — confirmed cross-tenant access, credential compromise, or
academic-record integrity failure.

```
Detect  → page on-call
Contain → revoke sessions; disable the affected path; suspend the tenant if needed
Assess  → scope from audit_events and security_events; identify affected tenants
Notify  → affected tenants within the contractual window; regulators where required
Remediate
Review  → post-incident review with a mandatory control change
```

**Every Sev-1 produces a new automated test that would have caught it.** A fix
without a test is not a fix.

### Common signals

| Symptom | First check |
|---|---|
| Users see no data | Tenant context binding — is `app.tenant_id` being set? (`SELECT current_setting('app.tenant_id', true)`) |
| Users see *wrong* data | **Stop. Sev-1.** Run §3 immediately |
| Spike of 403 `tenant_mismatch` | Tokens replayed across hosts, or a client caching a token across a tenant switch |
| Spike of `permission_denied` | A role edit went wrong, or an account is being probed. `security_events` distinguishes them |
| Spike of 402 | An entitlement limit is set wrongly, or a school genuinely outgrew its plan |
| Slow requests | Pool saturation, a missing `(tenant_id, …)` index, or an unbounded list endpoint |

---

## 8. Backups

Continuous WAL archiving with PITR; nightly base backup.

**Restore drills are scheduled and mandatory.** An untested backup is a
hypothesis, not a backup. Each drill restores to a scratch instance, runs the
isolation check from §3, and records the elapsed time — because the number that
matters in an incident is how long a restore actually takes, not how long it is
supposed to take.

Per-tenant logical export exists for portability and for the data-ownership
promise, and is available on every plan including Free.

---

## 9. Key rotation

| Secret | Cadence | Procedure |
|---|---|---|
| `SECRET_KEY` | Annually, or on suspicion | Dual-key window: accept old, sign with new; expire after the refresh TTL |
| Database passwords | Quarterly | Rotate `edtechx_app` first; `edtechx_migrator` during a maintenance window |
| AI provider keys | Per provider policy | Rotate in `ai_provider_configs`; validation call must succeed before the old key is revoked |
| Payment keys | Per provider policy | Rotate in a low-traffic window; reconcile before and after |

Rotating `SECRET_KEY` without the dual-key window signs every user out at once.
For a school, that means every teacher losing access mid-lesson.

---

## 10. Scaling levers, in order

1. Connection pool size (`db_pool_size`, `db_max_overflow`) — the usual first bottleneck.
2. Read replicas for analytics and reporting.
3. Cache the customization resolution bundle harder (it changes rarely and is read constantly).
4. Move background work out of process.
5. Partition the hot append-only tables (`audit_events`, `usage_records`, `ai_requests`).
6. Dedicated database for the largest tenants — a connection-string change, by design.

Do these in order and only on measurement. Skipping to 6 because it sounds
serious is how a simple system becomes an unmaintainable one.

---

## 11. Deliberate non-automation

Some things stay manual because the failure mode of getting them wrong is worse
than the cost of a human doing them:

- Deleting a tenant's data.
- Publishing results on a school's behalf.
- Overriding an academic record.
- Granting break-glass access.
- Changing a school's plan without their instruction.
