# StromeX Auth Entry Paths — Fix & Verification Report

## What was reported

"Sign Up and Sign In flows are preventing access to the application," with
a requirement to add a prominent, network-independent Guest option and to
verify all three entry paths end to end with evidence.

## Root-cause investigation

Re-tested Sign Up and Sign In fresh, against the real backend, before
changing anything: **both worked correctly** — no regression in the
registration/login/session code itself (see the "Evidence" section below
for the same test passing cleanly). That ruled out a broken auth endpoint.

The real, confirmed gap was architectural, not a broken endpoint: **every
entry path — including "Continue as Guest" — depended on successfully
reaching the backend to let a user in at all.** On a real Android device
where the installed build's backend URL isn't reachable (the disclosed,
standing limitation from the original delivery — see
`docs/09-STROMEX-ANDROID-VERIFICATION-REPORT.md`), *every* entry path would
fail identically: Sign Up, Sign In, and even Guest mode, because Guest mode
called `POST /auth/guest` over the network just like everything else. From
a real device tester's point of view — no working entry path, whichever
button they tried — this looks exactly like "the whole app is broken,"
which matches the report.

This is now fixed at the architecture level, not papered over: **Guest
mode no longer depends on the backend being reachable at all.**

## What changed

- `apps/web/src/lib/api.ts`: added a distinct `NetworkError` (backend
  unreachable/timed out) separate from `ApiError` (backend responded but
  rejected the request) — callers can now tell "there's no server to ask"
  apart from "the server said no," and a request no longer hangs forever
  (8s timeout).
- `apps/web/src/hooks/useAuth.ts`: `loginAsGuest()` now falls back to a
  local-only guest identity when the backend is unreachable — real chats
  need a real backend regardless (there's no offline data layer in this
  product), but **entry into the app itself is never blocked by
  connectivity**. `hydrate()` similarly no longer treats a network failure
  the same as "you're signed out" — an existing session is trusted (from a
  newly-added local cache of the last-known account) rather than forced
  back to a sign-in screen just because of a connectivity blip.
- `apps/web/src/components/layout/{RequireAuth,AppShell}.tsx`: an
  unauthenticated visitor to any protected page now lands on `/welcome`
  (all three choices), not straight into `/login`; a persistent banner
  explains *why* when running in a degraded/offline session, satisfying
  "display a clear explanation" rather than failing silently.
- `apps/web/src/app/welcome/page.tsx`: "Continue as Guest" is now the
  **primary** (most visually prominent) button, not the least — directly
  answering "must be clearly visible."
- `apps/web/src/app/{login,register}/page.tsx`: a `NetworkError` now shows
  "Could not reach the StromeX server" plus a direct link to continue as a
  guest, instead of a generic "something went wrong."
- `apps/web/src/app/chat/page.tsx`: a failed conversations/messages fetch
  now shows an inline message instead of an unhandled rejection.

## Evidence

All of the following ran against the real FastAPI backend (or with only
the backend host specifically blocked, to simulate real-world
unreachability precisely — see the note below on methodology), using the
exact static bundle the Android WebView loads, via
`apps/android/qa/entry_paths_test.mjs`. **13 of 13 checks passed.**

| # | Check | Result |
|---|---|---|
| 1 | **Sign Up**: registration creates a real account and lands in `/chat` | PASS |
| 2 | Sign Up: chat shell renders with the new account's name | PASS |
| 3 | Sign Up: duplicate-email validation error displays clearly ("Email is already registered") | PASS |
| 4 | **Sign In**: login succeeds and leaves the login screen | PASS |
| 5 | Sign In: access token is stored client-side | PASS |
| 6 | Sign In: **session persists after a simulated app restart** (fresh browser context, same localStorage) | PASS |
| 7 | **Guest (online)**: button visible on the welcome screen | PASS |
| 8 | Guest (online): lands in `/chat` immediately | PASS |
| 9 | **Guest (backend unreachable)**: entry is NOT blocked — still lands in `/chat` | PASS |
| 10 | Guest (backend unreachable): offline banner explains why | PASS |
| 11 | Guest (backend unreachable): chat composer still renders — a usable shell, not a blank/broken screen | PASS |
| 12 | Sign In (backend unreachable): shows a clear "can't reach server" message, not a crash | PASS |
| 13 | Sign In (backend unreachable): offers "continue as a guest" as an immediate way forward | PASS |

```
$ node entry_paths_test.mjs
PASS - SIGN UP: registration creates account and lands in /chat
PASS - SIGN UP: chat shell renders after registration
PASS - SIGN UP: duplicate-email validation error displays clearly
PASS - SIGN IN: login succeeds and leaves /login
PASS - SIGN IN: access token stored client-side
PASS - SIGN IN: session persists after simulated app restart
PASS - GUEST (online): button is visible on welcome screen
PASS - GUEST (online): lands in /chat immediately
PASS - GUEST (OFFLINE): entry is NOT blocked when the backend is unreachable
PASS - GUEST (OFFLINE): offline banner explains why
PASS - GUEST (OFFLINE): chat composer still renders (app is usable, not blank)
PASS - SIGN IN (backend unreachable): shows a clear "can't reach server" message, not a crash
PASS - SIGN IN (backend unreachable): offers "continue as a guest" as a way forward

=== SUMMARY ===
13/13 checks passed
```

Screenshots (`docs/assets/android/`):
`evidence-signup-success.png`, `evidence-signup-validation-error.png`,
`evidence-signin-success.png`, `evidence-session-persistence.png`,
`evidence-guest-online-success.png`, `evidence-guest-offline-success.png`
(shows the offline banner + full chat shell), `evidence-signin-offline-message.png`.

The full pre-existing 36-check Android QA suite
(`apps/android/qa/android_qa.mjs`, covering dark mode, RTL, tablet,
password reset, email verification, logout-all, etc.) was also re-run in
full to confirm no regression: **36/38 still passing**, same 2 expected
non-issues as previously documented in `docs/08-STROMEX-ANDROID-BUGFIX-REPORT.md`.
Backend suite: **66/66 passing**, unchanged this round.

### A methodology note, in the interest of not overstating the result

"Backend unreachable" above was simulated by blocking network requests to
the backend host specifically (`localhost:8000`), not the whole browsing
context. That distinction matters and is deliberate: the real Android
app's own screens are served by `MainActivity.shouldInterceptRequest`,
which answers requests for the app's own assets in-process and never
touches a real network socket at all — so on a real device with no
internet, the app's own UI still renders exactly as it does here, and only
calls to the actual backend fail. Simulating "offline" by blocking the
entire browser context (tried first, and it's what a naive test would do)
incorrectly also blocks this test's own local stand-in file server for the
web bundle, which has no equivalent failure mode on the real device — that
approach produced a false failure during development of this fix, and
switching to backend-only blocking is what actually verifies the real
condition. See `apps/android/qa/entry_paths_test.mjs` for the exact
implementation.

## Still true, unchanged from before

Real chat/Qur'an/Books functionality still requires a reachable backend —
there is no offline data layer in this product (no cached conversations,
no local LLM). What changed is that **connectivity failures no longer
block getting into the app at all**, and failures inside the app now say
so clearly instead of failing silently or bouncing to a sign-in wall. The
standing limitation that this sandbox's shipped build points at
`http://localhost:8000` (not a publicly reachable production backend) is
unchanged — see `docs/09-STROMEX-ANDROID-VERIFICATION-REPORT.md`.
