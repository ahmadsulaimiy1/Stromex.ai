# EdirasX Security Architecture

**Version:** 1.0
**Scope:** EdirasX holds children's personal data, academic records, safeguarding information, and money. The security posture is sized for that, not for a SaaS dashboard.

---

## 1. Threat model

| Threat | Primary control |
|---|---|
| Cross-tenant data access | PostgreSQL RLS + context binding + generated isolation tests (`ARCHITECTURE.md` §4) |
| Privilege escalation | Additive permissions, delegation ceiling, elevation for high-risk actions |
| Account takeover | Argon2id hashing, MFA, session revocation, breach-aware lockout, device visibility |
| IDOR | UUID keys + scope predicates in queries + 404-on-out-of-scope |
| Injection | Parameterized queries only; no dynamic SQL from user input |
| XSS | No `dangerouslySetInnerHTML` on user content; sanitize rich text server-side against an allow-list; strict CSP |
| CSRF | Bearer tokens (no ambient cookie auth for the API); `SameSite=Strict` on any cookie; explicit origin check on state-changing routes |
| SSRF | Central egress guard for every outbound fetch (§6) |
| File-based attack | Type sniffing, extension/MIME agreement, size caps, no execution, isolated download origin, `Content-Disposition: attachment` |
| Brute force / credential stuffing | Layered rate limits, exponential backoff, per-account lockout, anomaly signals |
| Insider / operator abuse | Break-glass with reason, expiry, tenant notification, and audit |
| Supply chain | Pinned dependencies, lockfiles, automated advisory scanning, no unvetted transitive additions |
| Data exfiltration via export | Export permissions, rate limits, audit, watermarking of generated documents |

---

## 2. Authentication

- **Password hashing:** Argon2id (memory 64MB, time 3, parallelism 4). bcrypt accepted for legacy import and transparently rehashed on next successful login.
- **Password policy:** minimum 12 characters, checked against a breached-password corpus. No composition rules, no forced rotation — both reduce real-world strength.
- **Tokens:** JWT access token, 15 minutes, carrying `sub`, `tid`, `mid` (membership), `jti`, `iat`, `exp`. Refresh token: opaque, 30 days, stored hashed, **rotated on every use with reuse detection** — a replayed refresh token revokes the entire family and raises a security event.
- **Revocation:** `jti` denylist in Redis until natural expiry; session records support "sign out everywhere".
- **MFA:** TOTP for all staff roles; required by default for `owner`, `admin`, `bursar`, and `platform_operator`. Recovery codes issued once, stored hashed. WebAuthn planned (ADR-014).
- **SSO:** SAML 2.0 and OIDC for Enterprise, per tenant, with just-in-time membership provisioning against a mapped role. Domain claims must be verified before an SSO connection can be enabled.
- **Lockout:** progressive delay from the 5th failure, hard lock at 10 for 15 minutes, keyed on account *and* on source. Lockout never reveals whether the account exists.
- **Enumeration resistance:** login, registration, password reset, and invitation all return identical responses and comparable timing regardless of account existence.

---

## 3. Authorization

Specified in `EDTECHX_PERMISSION_MODEL.md`. Security-relevant invariants:
- Server-side, in the service layer, on every request.
- Scope compiled into the query — never applied after loading.
- Out-of-scope resources return 404 with timing that does not distinguish.
- No route reaches a handler without either a permission requirement or an explicit public marker; enforced by test.

---

## 4. Data protection

**In transit:** TLS 1.2+ (1.3 preferred), HSTS with preload, no mixed content. Internal service traffic is TLS or on a private network.

**At rest:** full-disk/volume encryption plus **application-level encryption for the sensitive set**: AI provider credentials, MFA secrets, SSO signing material, payment provider keys, safeguarding notes, medical notes. AES-256-GCM with envelope encryption; keys in a KMS; per-tenant data keys; rotation without re-encrypting the world.

**Secrets:** never in source, never in client bundles, never in logs, never in error messages. Injected via environment or secret manager. A pre-commit and CI scan blocks committed secrets. `ENVIRONMENT=production` refuses to boot with a default secret, a development adapter enabled, or debug mode on.

**PII discipline:** logs carry identifiers, never contents. Analytics events carry no free text. Support tooling shows redacted values by default. Data subject requests (access, rectification, erasure, portability) are supported as first-class operations with per-tenant scope.

---

## 5. Input and output handling

- All request bodies validated by Pydantic models; unknown fields rejected rather than ignored.
- Path and query parameters typed and bounded; every list endpoint has a maximum page size.
- Body size capped globally; upload size capped per plan.
- Rich text sanitized **server-side** against an allow-list of tags and attributes; URL schemes restricted to `http`, `https`, `mailto`.
- All output encoded contextually. React's default escaping is relied upon; any exception requires a documented review.
- **CSP:** `default-src 'self'`, no `unsafe-inline` for scripts (nonce-based), `frame-ancestors 'none'`, `object-src 'none'`. Tenant themes inject *values* into CSS custom properties — never raw CSS text, which would be a stylesheet injection vector.
- Additional headers: `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy` denying unused features, `Cross-Origin-Opener-Policy: same-origin`.

---

## 6. SSRF prevention

Every outbound HTTP request from the server — AI providers, payment webhooks, SSO metadata, logo fetch, custom-domain verification — goes through one egress client that:

1. Resolves the hostname and **rejects private, loopback, link-local, multicast, and reserved ranges** (IPv4 and IPv6, including IPv4-mapped forms).
2. Re-validates the address after every redirect (a redirect to `169.254.169.254` is the classic bypass).
3. Pins the connection to the validated address so DNS cannot be re-resolved between check and connect.
4. Enforces an allow-list of schemes and, for provider calls, an allow-list of hosts.
5. Caps redirects, response size, and total time.

*(The StromeX codebase in this repository had exactly this class of vulnerability found and fixed during its audit — see `docs/04-STROMEX-INDEPENDENT-AUDIT.md`. EdirasX starts with the control in place rather than discovering it later.)*

---

## 7. File handling

Validate declared MIME against sniffed content and against the extension; reject on disagreement. Store with a generated key, never the user's filename. Serve from a separate origin with `Content-Disposition: attachment` and no script execution. Presigned URLs are short-lived, single-purpose, and tenant-path-scoped. Antivirus scanning hook before a file becomes downloadable. Images are re-encoded to strip metadata and embedded payloads.

---

## 8. Rate limiting

Layered, all Redis-backed, all keyed by tenant:

| Class | Limit |
|---|---|
| Unauthenticated (per IP) | 60/min |
| Authentication attempts | 10/15min per account, 30/15min per IP |
| Password reset / invite | 5/hour per account |
| Authenticated general | 600/min per principal |
| Write operations | 120/min per principal |
| Export / report generation | 10/hour per principal |
| AI requests | Per plan quota plus a burst limit |
| Webhook ingress | Per provider, with signature verification before any work |

Responses include `Retry-After`. Limits are configurable per tenant for Enterprise.

---

## 9. Audit logging

Append-only, tamper-evident, seven-year retention. `edtechx_app` holds no `UPDATE`/`DELETE` grant on the audit table.

Always audited: authentication events; authorization denials; every academic record mutation with before/after; every financial mutation; result publication and unpublication; role and permission changes; configuration publication and rollback; data export and document generation; break-glass grant, use, and expiry; AI actions that touched a record of consequence; tenant lifecycle events.

---

## 10. AI-specific controls

- Provider credentials encrypted, never returned by any API (write-only fields), rotatable, revocable.
- Prompt-injection posture: content retrieved from a tenant's own data is untrusted input to the model. AI output is never executed, never used to construct SQL, and never authorizes an action. The gateway strips tool-use requests that were not explicitly granted for the feature.
- No AI write path to academic or financial records without a recorded human approval (`ai_approvals`).
- Tenant content is sent only to providers under a no-training commitment; the provider registry records this per provider and the gateway refuses non-compliant routing for tenant content.
- Per-tenant, per-feature quotas prevent one tenant's runaway usage from becoming a platform incident.

---

## 11. Security testing

| Test | Cadence |
|---|---|
| Tenant isolation suite (generated over every tenant-owned model) | Every commit |
| Authorization matrix | Every commit |
| Escalation and IDOR suite | Every commit |
| SSRF guard suite (redirect, IPv6, DNS-rebind cases) | Every commit |
| Dependency advisory scan | Daily |
| Secret scan | Every commit |
| SAST | Every commit |
| DAST against staging | Weekly |
| Penetration test | Before pilot, then annually and after major change |

**Release gate:** the isolation, authorization, escalation, and SSRF suites are blocking. A release does not go out with any of them red.

---

## 12. Incident response

Severity 1 is any confirmed cross-tenant data access, credential compromise, or academic-record integrity failure.

Flow: detect → contain (revoke sessions, disable the path, isolate the tenant) → assess scope from audit logs → notify affected tenants within the contractual window and regulators where required → remediate → publish a post-incident review with a mandatory control change. Every Sev-1 produces a new automated test that would have caught it.

---

## 13. Compliance posture

Designed against GDPR/UK GDPR (lawful basis, DSRs, DPIA, processor terms, breach notification), FERPA-style expectations for US institutions, Nigeria's NDPA, and children's-data principles generally: data minimization, purpose limitation, no profiling of children for commercial ends, no advertising, no sale of data, and no use of tenant content to train models.
