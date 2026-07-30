# StromeX Modern Auth — Verification Report

## Honesty statement, up front

Same standing constraint as the original Android delivery
(`docs/09-STROMEX-ANDROID-VERIFICATION-REPORT.md`): no emulator, no
physical device in this environment. This phase adds one more genuine
external dependency this environment cannot supply on its own: a real
Google Cloud OAuth Client, which only the account owner can create (see
`docs/10-STROMEX-AUTH-FEATURE.md`). What follows is exactly what could and
could not be verified as a result — stated plainly, not glossed over.

## 1. Rebuilt APK/AAB — static verification

```
$ aapt2 dump badging release/stromex-v1.0.0-dev.apk
package: name='ai.stromex.app' versionCode='2' versionName='1.0.0-dev' ...
sdkVersion:'29'
targetSdkVersion:'36'
uses-permission: name='android.permission.INTERNET'
uses-permission: name='android.permission.ACCESS_NETWORK_STATE'
launchable-activity: name='ai.stromex.app.MainActivity'
```

`versionCode` bumped from `1` → `2` to mark this as an update over the
originally delivered build. Permissions unchanged (still only the two
already justified — this feature added no new permission requirement,
including for Google Sign-In, since it never touches Play Services).

```
$ apksigner verify --verbose release/stromex-v1.0.0-dev.apk
Verifies
Verified using v3 scheme (APK Signature Scheme v3): true
Number of signers: 1
```

```
$ jarsigner -verify release/stromex-v1.0.0-dev.aab
jar verified.
$ bundletool validate --bundle=release/stromex-v1.0.0-dev.aab
App Bundle information ... (parses successfully)
```

Deep-link intent-filter confirmed present in the built manifest:

```
$ aapt2 dump xmltree release/stromex-v1.0.0-dev.apk --file AndroidManifest.xml
...
E: data (line=37)
  A: android:scheme="ai.stromex.app"
  A: android:host="auth-callback"
```

Checksums:

```
ba1c193f2f4e273eac78cb98cbcb760e9546ec3be7c755171a77100cd811a213  release/stromex-v1.0.0-dev.apk
5a6932d335616bd89bace8c620f4dc8c77828760399fb340890435a44bff873f  release/stromex-v1.0.0-dev.aab
```

Note the filename: `-dev` reflects that this build's `NEXT_PUBLIC_API_URL`
points at `http://localhost:8000` (this environment's own reachable
backend, used for testing) rather than a real deployed URL — same
disclosed limitation as the original delivery (no way to expose a public
backend URL from this sandbox). See
`apps/android/build-for-env.sh`/`environments/*.env` to rebuild against a
real backend once one is deployed.

## 2. Backend — automated test verification

66/66 tests pass, including all 16 new tests for this phase (guest mode,
password reset, email verification, logout-all, account deletion, Google
OAuth's not-configured state). Full detail in
`docs/11-STROMEX-AUTH-TEST-REPORT.md`.

## 3. Functional (browser) verification

36/38 Playwright-driven checks pass against the real backend, using the
exact bundle the APK ships. Full detail and the 2 expected "failures" in
`docs/11-STROMEX-AUTH-TEST-REPORT.md`.

## 4. What remains unverified — explicitly

- **A real, successful Google sign-in end to end.** This requires:
  (a) a Google Cloud OAuth Client the account owner creates (cannot be
  fabricated), and (b) a human completing Google's real consent screen
  with a real Google account (cannot be automated or simulated by this
  agent). What **is** verified: every piece of the flow that doesn't
  require an actual Google account — CSRF-state handling, the
  not-configured `503`, the deep-link registration on the Android side,
  and (via backend tests) correct upsert/link behavior given a well-formed
  identity. Once real credentials exist, the remaining verification step
  is: tap "Continue with Google" on a real device, sign in, confirm you
  land in `/chat`. That is the one step this environment cannot perform
  for you, for reasons outside engineering (Google account interaction,
  not sandbox tooling).
- **Real SMTP email delivery.** Deliberately out of scope this round (see
  `docs/10-STROMEX-AUTH-FEATURE.md`) — dev-mode logging is what's built
  and tested; wiring a real provider is an env-var change away, with no
  code change.
- **Installation and interaction on a real Android OS instance** — same
  standing limitation as the original delivery.
- **Settings page mobile layout** is functionally correct but visually
  cramped at phone width (pre-existing `AppShell` characteristic, not
  introduced this phase) — see the test report.

## 5. Commit

Everything in this report reflects the state at the commit referenced in
the final delivery message for this phase.
