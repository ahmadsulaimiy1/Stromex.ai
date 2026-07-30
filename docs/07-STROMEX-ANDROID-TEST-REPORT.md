# StromeX Android — Test Report

## Method

No Android emulator or physical device was available in the build
environment (no `/dev/kvm`, no VMX/SVM CPU flags — a hardware-accelerated
emulator cannot run at usable speed or at all; no physical device attached).
So the QA cycle below runs the **exact static-export web bundle that ships
inside the app's WebView** (`apps/web/out`, byte-identical to
`apps/android/assets/`) in real Chromium via Playwright, served through a
small local HTTP server (`apps/android/qa/static_server.py`) that
deliberately reimplements `MainActivity.serveAsset()`'s own
extensionless-path fallback (`/chat` → try `chat.html`, then
`chat/index.html`) — so the test exercises the same asset-resolution
behavior the real WebView uses, not just raw static files. Mobile device
emulation (Playwright's `devices['Pixel 5']`, `devices['iPad (gen 7)']`,
`devices['Galaxy S5']`) stands in for real hardware. All tests ran against
the real FastAPI backend (`apps/api`), not a mock.

This is a legitimate, high-fidelity functional test of every code path the
app runs — but it is **not** the same as launching the compiled APK on a
real Android OS instance. See
[09-STROMEX-ANDROID-VERIFICATION-REPORT.md](./09-STROMEX-ANDROID-VERIFICATION-REPORT.md)
for exactly what that gap means and what was done to close as much of it as
possible statically.

Test script: `apps/android/qa/android_qa.mjs`. Reproduce with:

```bash
cd apps/web && CAPACITOR_BUILD=1 npm run build && cd ..
python3 android/qa/static_server.py web/out 4173 &
# with the backend running on :8000 and CORS_ORIGINS including
# http://127.0.0.1:4173 and https://stromex.local
node android/qa/android_qa.mjs
```

## Results — final run

**26 of 28 automated checks passed.** The 2 that show as "failed" are a
blanket "zero console errors" assertion tripping on *expected* signals
(a `403` when a non-admin user's client calls the admin API, and a
`net::ERR_INTERNET_DISCONNECTED` from the deliberate offline test) — not
defects. See the annotated list below.

| # | Check | Light | Dark | Notes |
|---|---|---|---|---|
| 1 | Home page loads | PASS | PASS | |
| 2 | Registration submits and logs in (→ `/chat`) | PASS | PASS | |
| 3 | Login redirects away from `/login` | PASS | PASS | Separate account per run, independent of registration auto-login |
| 4 | Session persists across full page reload | PASS | PASS | Confirms token persistence (`localStorage`), not just SPA state |
| 5 | Chat page usable (composer + send found) | PASS | PASS | |
| 6 | Chat page renders conversation content | PASS | PASS | |
| 7 | Qur'an tutor page loads | PASS | PASS | Spaced-repetition planner (surah/ayah numbers, SM-2 grading) — no rendered ayah text on this page, see note below |
| 8 | Arabic input triggers RTL layout | PASS | PASS | Typed Arabic into the chat composer's Arabic⇄English mode; confirmed `dir="rtl"` applied |
| 9 | Books page loads | PASS | PASS | |
| 10 | Admin page handles non-admin access gracefully | PASS | PASS | Shows "Admin privileges required", no crash |
| 11 | App does not crash when offline | PASS | PASS | `context.setOffline(true)`, navigate, confirm page still renders |
| 12 | No unhandled runtime error overlay | PASS | PASS | |
| 13 | No console errors | **FAIL*** | **FAIL*** | *403 (expected, non-admin) + offline network error (expected, intentional) — not defects |
| 14 | Tablet viewport: no horizontal overflow | PASS (n/a — single run) | | iPad (gen 7) profile |
| 15 | Low-end/throttled device: home page loads | PASS (n/a — single run) | | Galaxy S5 profile + CDP network throttling (400ms latency, 200kbps down / 100kbps up) |

\* Full console output for the "failed" checks:
`403 Forbidden` ×2 (admin API calls from a deliberately non-admin test
account), `ApiError: Admin privileges required` ×2 (the app's own handled
error message logged to console, not an unhandled exception), and one
`net::ERR_INTERNET_DISCONNECTED` (from check #11's own intentional
offline simulation). All five are the correct, intended behavior.

## Requirement-by-requirement coverage

| User requirement | Status |
|---|---|
| Installation testing | **Not verified on-device** — no emulator/device available. APK installability verified statically: `apksigner verify` passes, `aapt2 dump badging` parses a well-formed manifest, `bundletool build-apks` + resulting `universal.apk` verifies too (see verification report). |
| Login testing | Verified — real registration + real login against the real backend, both light and dark mode, both succeed and redirect correctly. |
| Registration testing | Verified — real `POST /api/v1/auth/register` → `201`, followed by real login. |
| Session persistence testing | Verified — full page reload (not just SPA navigation) preserves the authenticated session via `localStorage` tokens. |
| Offline handling | Verified — app does not crash or show a blank/broken screen when the network is cut. |
| API failure handling | Verified — a `403` from a real backend rejection (non-admin calling admin routes) is handled gracefully, no crash, no unhandled-exception overlay. |
| Arabic RTL testing | Verified — Arabic text entered into the chat composer's Arabic⇄English mode triggers `dir="rtl"`. The Qur'an tutor page itself is a numeric surah/ayah spaced-repetition scheduler with no rendered ayah text (a pre-existing product characteristic from the original MVP, not an Android-specific gap), so there is no RTL text to test *there* — RTL rendering was verified on the page that actually displays Arabic text. |
| Dark mode testing | Verified — full pass repeated under `colorScheme: 'dark'`; screenshots in `docs/assets/android/login-{light,dark}.png` confirm correct theming (brand ink/paper/brass colors both ways). |
| Tablet responsiveness testing | Verified — iPad-sized viewport, no horizontal overflow on the home page; screenshot in `docs/assets/android/tablet-home.png`. |
| Low-memory device testing | **Partially verified.** Simulated via CDP network throttling on an older/smaller device profile (Galaxy S5) — confirms the app still loads under slow-network conditions. This is not the same as testing actual RAM pressure/low-memory process eviction on real hardware, which requires a real device or device farm; not available here. |
| Android 10–16 compatibility testing | **Not verified across real OS versions** — no device farm or multiple real/emulated Android OS instances available. `minSdkVersion=29` (Android 10) / `targetSdkVersion=36` (Android 16) are declared and enforced by the manifest and confirmed via `aapt2 dump badging`; the app uses only stable, long-available `android.webkit.*`/`android.app.*` APIs (no version-gated features), which is the strongest static argument for cross-version compatibility, but is not a substitute for running on each OS version. |

## What genuinely was and wasn't tested

**Tested for real, against the real backend:** registration, login, session
persistence, chat (composer + send), Arabic RTL rendering, books page,
admin authorization enforcement, offline resilience, dark mode, tablet
viewport, network throttling.

**Not tested (explicitly, per the user's own instruction to disclose gaps
rather than claim false completeness):**
- Actual installation and launch of the compiled `.apk` on a real Android
  OS instance (emulator or device) — see the verification report for what
  static analysis was done instead.
- Native Android chrome (status bar, notifications, back-gesture nav, split
  screen, foldables) — the WebView content was tested, not the native
  Activity shell hosting it, since there is no way to launch that Activity
  in this environment.
- Real low-memory process eviction/restoration behavior.
- Behavior across actual distinct Android OS builds/versions 10 through 16.
- The PDF export feature's native download/share behavior inside a WebView
  (the feature itself — chapter → PDF generation — is exercised by the
  existing backend test suite from Phase 4/5; the client-side "does the
  file actually save/open correctly from an Android WebView download"
  interaction specifically was not verified here).
