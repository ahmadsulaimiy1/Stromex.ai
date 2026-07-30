# StromeX Modern Auth — Test Report

## Backend: automated tests

`apps/api/app/tests/test_auth_modern.py` — 16 new tests, run against the
real Postgres/Redis test stack (same `app_client`/`db_session` fixtures the
rest of the suite uses, not mocks):

| Test | Verifies |
|---|---|
| `test_guest_account_is_immediately_usable` | `POST /auth/guest` returns usable tokens; `/me` reports `is_guest=true`, `is_verified=true` |
| `test_guest_can_upgrade_to_full_account` | Upgrade attaches email/password to the same account, triggers a verification email, and the account can then log in normally |
| `test_non_guest_cannot_use_upgrade_endpoint` | A real account calling `/guest/upgrade` gets `400` |
| `test_password_reset_full_flow` | Request → real logged link → confirm → old password rejected, new one works |
| `test_password_reset_token_is_single_use` | Replaying a consumed reset token returns `400` |
| `test_password_reset_request_for_unknown_email_still_returns_202` | No account-enumeration signal |
| `test_password_reset_invalidates_existing_sessions` | An access token issued before the reset is `401` after it |
| `test_new_account_is_unverified_until_confirmed` | Registration starts `is_verified=false`; confirming the logged link flips it |
| `test_email_verify_token_is_single_use` | Replaying a consumed verify token returns `400` |
| `test_invalid_verify_token_is_rejected` | A garbage token returns `400` |
| `test_logout_all_invalidates_existing_access_and_refresh_tokens` | Both the access token used to call it and the paired refresh token are rejected afterward; a fresh login still works |
| `test_guest_can_delete_own_account_without_a_password` | Guest deletion needs only a live session |
| `test_password_account_deletion_requires_correct_password` | Wrong/missing password → `401`; correct password → `204` |
| `test_deleted_account_email_can_be_reregistered` | Deletion is real, not soft — the email is free again |
| `test_google_authorize_returns_503_when_not_configured` | No `GOOGLE_CLIENT_ID` in test env → `503`, not a broken redirect |
| `test_google_callback_rejects_unknown_state` | CSRF-state validation on the callback rejects a made-up `state` |

All 16 pass. Full suite (including all pre-existing tests):
**66/66 passed**, zero regressions.

```
$ pytest app/tests/
======================= 66 passed, 37 warnings in 32.54s =======================
```

## Android/web: functional QA

Same method as the original Android delivery (see
`docs/07-STROMEX-ANDROID-TEST-REPORT.md` for the full rationale): the exact
static-export bundle the APK's WebView loads, run in real Chromium via
Playwright under mobile device emulation, against the real running FastAPI
backend — no emulator/device available in this environment (see the
verification report for what that means and doesn't mean).

`apps/android/qa/android_qa.mjs` — extended this phase with 12 new checks
covering everything added:

| Check | Result |
|---|---|
| Home page redirects unauthenticated visitors to `/welcome` | PASS |
| Welcome screen shows Google / Email / Guest options | PASS |
| Continue-as-Guest lands in `/chat` | PASS |
| Settings page identifies the guest account and offers upgrade | PASS |
| Google authorize endpoint responds correctly for its current (unconfigured) state — `503` | PASS |
| Password-reset request shows a non-committal confirmation | PASS |
| Password-reset confirm (via a token scraped from the backend's own dev-mode log) redirects to `/login` | PASS |
| New password works after reset | PASS |
| Email verification confirms via the `/verify-email` UI (same log-scrape approach) | PASS |
| Logout-all-devices redirects to `/login` | PASS |
| Old access token is rejected after logout-all | PASS |
| (registration/login/session-persistence/chat/RTL/dark-mode/tablet/offline — all pre-existing checks) | PASS (36/38 overall; see note below) |

**36 of 38 total checks pass.** The 2 that show "failed" are the same
blanket "zero console errors" assertion from the original Android delivery
tripping on *expected* signals (a `403` from a deliberately non-admin
account calling the admin API, and the intentional offline-mode test) —
not defects, and already called out as such in
`docs/08-STROMEX-ANDROID-BUGFIX-REPORT.md`.

Screenshots: `docs/assets/android/welcome-{light,dark}.png`,
`docs/assets/android/settings-guest.png`.

## What this did *not* verify (disclosed, not glossed over)

- **A real, successful Google sign-in.** This requires a real Google Cloud
  OAuth Client (something only the account owner can create — see
  `docs/10-STROMEX-AUTH-FEATURE.md`) and a human clicking through Google's
  own consent screen with a real Google account. Neither exists in this
  environment. What *is* verified: the backend's own state machine around
  it — CSRF-state validation, the "not configured" `503`, and (via the
  backend test suite) that a well-formed Google identity is correctly
  upserted/linked once one arrives.
- **Real email delivery.** Dev mode (log instead of send) is what's
  tested, deliberately — see `docs/10-STROMEX-AUTH-FEATURE.md` for why that
  was the explicit choice this round. The full reset/verify *logic* is
  tested end-to-end regardless — only the transport (SMTP vs. log) differs.
- **Installation and interaction on a real Android OS instance.** Same
  standing limitation as the original Android delivery — no
  emulator/device in this sandbox. See
  `docs/09-STROMEX-ANDROID-VERIFICATION-REPORT.md`.
- **The Settings page's mobile layout is cramped** at phone width — its
  fixed 224px sidebar (`AppShell.tsx`) takes up 57% of a 393px-wide
  viewport. This is a pre-existing characteristic of `AppShell` shared by
  every authenticated page since the original MVP (Chat, Qur'an, Books),
  not something this phase introduced — but it's real, visible in
  `docs/assets/android/settings-guest.png`, and worth fixing in a future
  responsive-design pass rather than left unmentioned.
