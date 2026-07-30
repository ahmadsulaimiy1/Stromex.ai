# Android Verification Report

Written against the QA checklist requested for SAJJIL's Android release.
Every line below states what was actually done and how — nothing here is
marked verified on the basis of "the code looks right." Where something
wasn't verified, it says so explicitly, per the "list it, don't mark it
complete" instruction.

## 0. Scope correction, made before anything else

The requested checklist includes login testing, registration testing,
session persistence, API failure handling, and a chat feature "connected
to the existing backend." **SAJJIL has none of these, by design, and never
has across any phase of this project.** Confirmed directly:
- `AndroidManifest.xml` declares no `INTERNET` permission — the app cannot
  make a network call even if code tried to.
- There is no authentication, account, session, or backend-client code
  anywhere in `core` or `app`.
- There is no chat feature. The "SAJJIL Assistant" (Phase 5–6) is a local,
  rule-based pattern matcher over the on-device Room database — see
  `docs/REALTIME_ASSISTANT.md`. It never leaves the device.

SAJJIL is a fully offline, local-storage Android app. Those five checklist
items are marked **N/A — feature does not exist** below, per the explicit
agreement to drop them rather than build a backend/auth/chat system from
scratch under this request.

## 1. What was actually verified, and how

| Item | Status | Evidence |
|---|---|---|
| `core` compiles and its logic is correct | **Verified** | `./gradlew :core:test` — 171 tests, all passing, run repeatedly across every phase in this repo (pure Kotlin/JVM, no Android SDK needed). |
| `app` compiles against a real Android SDK (first time ever, across 6 phases) | **Verified in CI** | `.github/workflows/android-build.yml` → `assembleDebug` step. This is the ground truth this report relies on — not a sandbox assumption. |
| APK installs on a device/emulator | **Verified in CI** | `emulator-smoke-test` job: boots an Android 14 (API 34) x86_64 emulator, runs `adb install`. |
| App launches without crashing or ANRing | **Verified in CI, launch window only** | Same job: launches `MainActivity`, waits 12s, scans logcat for `FATAL EXCEPTION`/ANR, confirms the activity is still running. This proves the app starts — it does not exercise any specific screen or feature. |
| No build errors, no unresolved dependencies | **Verified in CI** | A failed Gradle build fails the workflow; green means Gradle actually resolved every dependency and compiled every file. |
| Offline handling | **Trivially true by construction** | The app has no `INTERNET` permission and makes no network calls anywhere — there is nothing to fail offline, because nothing ever goes online. |

**Read the actual CI run before trusting this table** — a report is not a
substitute for the run: https://github.com/ahmadsulaimiy1/Stromex.ai/actions
(the "Android Build" workflow). If you're reading this before that
workflow has completed at least once on the current commit, none of the
"Verified in CI" rows above have executed yet against this exact code.

## 2. What was NOT verified — explicit, not glossed over

| Checklist item | Status | Why |
|---|---|---|
| Login testing | **N/A** | No login feature exists (see §0). |
| Registration testing | **N/A** | No registration feature exists. |
| Session persistence testing | **N/A** | No accounts/sessions exist to persist. |
| API failure handling | **N/A** | No APIs are called. |
| Chat feature verification | **N/A** | No chat/backend-connected feature exists; SAJJIL Assistant is local-only (see §0). |
| Arabic RTL testing | **Not performed** | No instrumented UI tests exist in this repo yet (`androidTest` dependencies are declared in `app/build.gradle.kts` but no test classes have been written), and no device/emulator screen-by-screen RTL check has been run. Arabic text rendering relies on Jetpack Compose's built-in bidi support, which is generally correct by default, but "generally correct by default" is not the same as verified against this app's specific screens. |
| Dark mode testing | **Not performed** | Nine Material3 theme variants exist (`SajjilTheme`), each defining light/dark-appropriate color schemes, but no visual verification has been done on a real screen. |
| Tablet responsiveness testing | **Not performed** | No tablet-specific layouts, breakpoints, or `WindowSizeClass` handling exist in the code — layouts are single-column Compose screens. On a tablet they will render, just not adaptively. |
| Low-memory device testing | **Not performed** | No `minSdk`-floor (Android 8.0/API 26) or low-RAM device testing has been run. `AudioRecordEngine`'s buffers and `TranscriptStabilizer`'s history are small and bounded by design, but that's a code-review observation, not a measurement. |
| Android 10–16 compatibility | **Partially addressable, not verified** | `minSdk 26` (Android 8.0) and `targetSdk`/`compileSdk 34` (Android 14) — this covers Android 10 (API 29) through 14 (API 34) as configured. **Android 15 (API 35) and 16 (API 36) are not currently targeted** — `compileSdk`/`targetSdk` would need bumping to 35/36 first, which itself has not been attempted or verified against this codebase (a compileSdk bump can surface new lint/behavior-change issues that haven't been checked). No testing across this range has been run on real devices or multiple emulator API levels — the CI smoke test currently boots one API level (34) only. |
| Every screen/workflow/button/form/search feature exercised individually | **Not performed** | This would require either a full instrumented Espresso/Compose UI test suite (none exists yet) or manual testing on a real device (none available in any environment used for this project). The emulator smoke test confirms the app *starts*; it does not click through Record, Enhance, Master, Archive, Qur'an Studio, Voice Studio, the Assistant, or Settings. |

## 3. Bug-fix report

None yet, because real compilation has not happened as of writing this
document — this report is being committed alongside the CI workflow that
performs the first real build. If the CI run attached to this commit (or
the next one) fails, that failure and its fix will be recorded here as a
follow-up, against the actual compiler output, not a guess.

## 4. What "complete" actually means for this deliverable

A downloadable, installable **debug APK** that installs and launches
without crashing, built and verified by GitHub Actions against a real
Android SDK, is achievable and is what this change delivers. A **signed
release APK/AAB** additionally requires a signing key only the app owner
should generate (see `docs/ANDROID_BUILD.md`) and is not produced until
that's supplied. A **full manual/automated QA pass across every screen,
RTL, dark mode, tablet, low-memory, and the full Android 10–16 range** is
a substantial follow-on testing effort — real device/emulator time and,
for full coverage, a written instrumented test suite — that has not been
done and should not be represented as done.
