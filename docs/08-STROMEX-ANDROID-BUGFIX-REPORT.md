# StromeX Android — Bug-Fix Report

Real defects found and fixed during this phase, in the order discovered.

## 1. Missing CORS origin for the app's virtual host (fixed — product)

**Symptom:** every `fetch()` the WebView makes would fail CORS preflight.
**Cause:** `MainActivity` serves the app's own bundle from
`https://stromex.local` (a virtual origin, chosen over `file://` because
WebView's `fetch()` from `file://` sends `Origin: null`, which most CORS
configurations — including this backend's — reject). The backend's
`CORS_ORIGINS` allowlist didn't include that origin.
**Fix:** added `https://stromex.local` to `CORS_ORIGINS` in
`apps/api/.env` (dev) and documented it in `apps/api/.env.example` for any
real deployment. Verified with a direct `OPTIONS` preflight request
returning the correct `access-control-allow-origin: https://stromex.local`.

## 2. Missing favicon → spurious 404 (fixed — product)

**Symptom:** every page load logged a `404` console error for
`/favicon.ico`.
**Cause:** the web app (`apps/web`) never had a favicon/icon file — a
pre-existing gap from the original MVP build (Phase 4), not something the
Android work introduced, but surfaced by this QA pass's console-error
check.
**Fix:** added `apps/web/src/app/icon.svg` — the same "Index" mark (ring +
settling index line) used for the Android adaptive icon, on the brand's
brass background — using Next.js's App Router icon-file convention, which
auto-generates the correct `<link rel="icon">` tag and route. Rebuilt the
static export and regenerated the Android APK/AAB to include it. Verified
`GET /icon.svg` now returns `200` and no `/favicon.ico` 404 appears in a
fresh QA run.

## 3. Test-server couldn't resolve extensionless SPA routes (fixed — test tooling)

**Symptom:** navigating to `https://.../chat` (no `.html`) after a
client-side login redirect returned `404` from the QA test's static file
server, even though the real Android WebView would have served it fine.
**Cause:** Next.js's static export writes one `.html` file per route
(`chat.html`, not `chat/`), and `MainActivity.serveAsset()` was written
specifically to try `path.html` → `path/index.html` → raw `path` for any
extensionless request — but the first test server used
(`python3 -m http.server`) has no such fallback, so it 404'd on exactly the
path shape a post-login client-side redirect produces.
**Fix:** wrote `apps/android/qa/static_server.py`, a ~20-line
`http.server` subclass that implements the identical fallback order, so the
browser-based functional test exercises the same asset-resolution logic the
shipped app actually uses. This was a test-infrastructure fix, not a change
to `MainActivity.java` (whose logic was already correct — this bug was in
the stand-in test server, not the product).

## 4. QA script defects that produced false negatives (fixed — test tooling)

Three issues in the first draft of `apps/android/qa/android_qa.mjs` itself,
found while investigating apparent login failures that turned out not to be
real:

- **Required "Name" field never filled.** The registration form has a
  required `displayName` input the first draft of the script never
  populated, so the browser's own HTML5 validation silently blocked
  submission. Fixed by filling `#displayName` before submit.
- **`waitForLoadState('networkidle')` right after a login/register button
  click doesn't reliably wait for the SPA's client-side route change** —
  Next.js navigates via the History API (`router.push`) after a successful
  auth call, not a full page load, so `networkidle` can resolve before the
  route actually changes, making a successful login look like a failed one.
  Fixed with an explicit `waitForURL` for "no longer on this route" instead.
- **Shared `email` constant across the light/dark test iterations** caused
  the second (dark-mode) registration attempt to collide with the first,
  surfacing as a `409 Conflict` that looked like a real bug. Fixed by
  generating a fresh email per iteration.

None of these were product defects — they were testing artifacts that, left
unfixed, would have produced a false "login is broken" report. Documented
here because finding and correcting them was necessary to get a trustworthy
signal, and because a testing bug that hides a real one (or invents a fake
one) is worth being explicit about.

## Confirmed *not* a bug: registration rate limiting

During repeated test runs, registration attempts started returning
`429 Too Many Requests`. This is the per-IP registration rate limiter
(`5 requests / hour`, `apps/api/app/api/v1/auth.py`) added during the Phase 5
security audit, working exactly as designed — it was only tripped because
automated re-runs from the same test-harness IP exceeded it well outside
normal usage patterns. Resolved for testing purposes by clearing the
relevant Redis keys (`ratelimit:register:ip:127.0.0.1` etc.) between runs;
no code change was made or needed.

## Not a bug, disclosed as a scope boundary: Qur'an tutor page has no RTL markup

The automated test initially flagged the Qur'an tutor page (`/quran`) for
having zero `dir="rtl"`/`lang="ar"` elements. Investigation
(`apps/web/src/app/quran/page.tsx`) showed this page is a spaced-repetition
memorization *scheduler* — it shows surah/ayah numbers and SM-2 recall-grade
buttons, not rendered Qur'anic text — so there is genuinely no Arabic text
on this page to apply RTL styling to. This is a pre-existing characteristic
of the feature as built in Phase 4, not an Android-specific defect. RTL
rendering was confirmed correct where the product actually displays Arabic
text: the chat composer's Arabic⇄English mode (`dir="rtl"` applied on
Arabic input, per `apps/web/src/lib/textDirection.ts`).

## Outstanding — not fixed, disclosed

None of the above required leaving any known-broken behavior unfixed. The
items listed as "not verified" in
[07-STROMEX-ANDROID-TEST-REPORT.md](./07-STROMEX-ANDROID-TEST-REPORT.md) are
coverage gaps caused by the lack of a real device/emulator/device farm in
this environment, not known bugs being left in place.
