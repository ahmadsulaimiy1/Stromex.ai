# StromeX Modern Mobile Authentication

## What this replaces

Before this phase, the only way into StromeX was: create an account with
email + password against whatever backend URL happened to be baked into the
build, with no password reset, no email verification, and no way to sign
out everywhere at once. This phase replaces that with the three entry
points a mobile app is expected to offer today — Google Sign-In, email
(now with reset + verification), and a frictionless Guest mode — plus the
account-security controls (sign out everywhere, delete account) that go
with them, and moves the backend URL from a single hardcoded value to a
per-environment build setting.

## What's real right now vs. what needs your action

Everything in this feature is fully implemented, tested, and working
**except the one piece that fundamentally requires you, personally, to do
something Google requires of the account owner, not the developer**:
Google itself will not authenticate against a client ID nobody registered.
Here is exactly what's done and exactly what's left:

| Piece | Status |
|---|---|
| Guest mode (instant account, upgrade later) | **Done, tested end-to-end** |
| Email: register/login/reset/verify | **Done, tested end-to-end** |
| Sign out of all devices | **Done, tested end-to-end** |
| Delete account | **Done, tested end-to-end** |
| Environment-based backend URL | **Done** (build-time selection — see below for why not runtime) |
| Google Sign-In: backend + Android code | **Done, code-complete, structurally tested** |
| Google Sign-In: actually signing in with a real Google account | **Blocked on you creating a Google Cloud OAuth Client** — see steps below |

## Activating Google Sign-In

1. Go to [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials), create an OAuth 2.0 Client ID of type **Web application** (not Android — see "Why a Web client, not the Android client type" below).
2. Add an **Authorized redirect URI**: `https://<your-backend-domain>/api/v1/auth/google/callback`.
3. Set three environment variables on the backend (see `apps/api/.env.example`):
   ```
   GOOGLE_CLIENT_ID=<the client id>
   GOOGLE_CLIENT_SECRET=<the client secret>
   GOOGLE_REDIRECT_URI=https://<your-backend-domain>/api/v1/auth/google/callback
   ```
4. Restart the backend. `GET /api/v1/auth/google/authorize` will now redirect into Google's real consent screen instead of returning `503`.
5. Rebuild the Android app pointed at that backend (`apps/android/build-for-env.sh production`, once `environments/production.env` points at your real domain).

Until step 3 is done, "Continue with Google" takes the user to a page
Google itself would reject anyway — the backend fails fast with `503
Service Unavailable` rather than pretending it works. This was confirmed
directly: `GET /api/v1/auth/google/authorize` in this repo's own test/dev
environment (no credentials set) returns `503` today, and the Android QA
suite (`apps/android/qa/android_qa.mjs`) asserts exactly that.

### Why a Web client, not the Android client type

Google's own terms prohibit completing sign-in inside an embedded WebView
— which is what renders every other screen of this app — so this doesn't
use Google's native Android SDK (Credential Manager/One Tap) at all. It
uses the standard OAuth "authorization code" flow instead: tapping
"Continue with Google" opens the **system browser** (not the WebView) to
Google's consent screen, and Google redirects back to a backend route
(`/auth/google/callback`) that exchanges the code for an identity and hands
the resulting tokens to the Android app via a custom-scheme deep link
(`ai.stromex.app://auth-callback`, registered in
`apps/android/AndroidManifest.xml` and handled in
`MainActivity.onNewIntent`). That's a server-driven flow, so the
credential type Google expects is "Web application," even though an
Android app is what's using it.

This also happens to be why no AndroidX/Play Services dependency was
needed for this at all: everything on the Android side is
`android.content.Intent`/`android.net.Uri` (open a URL, catch a deep
link) — plain framework APIs, consistent with why the rest of this app
avoids AndroidX (see `docs/05-STROMEX-ANDROID-BUILD.md`).

## Guest mode

`POST /api/v1/auth/guest` creates a real account — not a client-only
placeholder — with no email or password, so its chats, memory, and Qur'an
plans are ordinary rows tied to a real user id from the first message
onward, not something that only lives in the browser and gets lost. It's
given a generated, never-emailed address
(`guest-<uuid>@guest.stromex.ai`) purely so the database schema doesn't
need a separate nullable-email code path for one auth mode.

`POST /api/v1/auth/guest/upgrade` (Settings → "Create a full account")
attaches a real email + password to that same account — same id, same
conversations, same everything — and kicks off normal email verification.
Nothing is migrated or copied; it's the same row.

## Email: reset and verification

Both use the same single-use, expiring, hashed-token mechanism
(`app/core/auth_tokens.py` — SHA-256 hash stored, raw token only ever
lives in the link itself, same shape as the refresh-token-revocation
denylist from the earlier security audit). Password reset additionally
bumps the account's `token_version`, signing out every existing session —
the assumption being that a reset usually follows a compromise or a
forgotten password, either way a moment to not trust old sessions.

**Email delivery is dev-mode by default**: with no `SMTP_*` settings
configured, the reset/verify link is logged (`app/core/email.py`) instead
of sent — the entire flow, including confirming via the link, works and is
tested this way (see the test report), it just doesn't leave your
terminal until you configure a real provider. Set `SMTP_HOST` /
`SMTP_PORT` / `SMTP_USERNAME` / `SMTP_PASSWORD` /
`SMTP_FROM_ADDRESS` (see `apps/api/.env.example`) to send real email
through any standard SMTP provider — no code change required either way.

## Sign out everywhere / delete account

`POST /api/v1/auth/logout-all` bumps a per-user `token_version` counter;
every access and refresh token embeds the version it was issued under, and
both `get_current_user` and `/auth/refresh` reject a token whose version
doesn't match the account's current one. This invalidates every
outstanding token in one step without needing to enumerate or individually
revoke them.

`DELETE /api/v1/auth/me` permanently deletes the account and everything it
owns (conversations, memory, Qur'an plans, books — all
`cascade="all, delete-orphan"`). Confirmation depends on how the account
authenticates: a guest account needs only a live session (nothing
irreplaceable to protect), a password account must re-enter its current
password, and a Google-only account (no password set) must re-present a
fresh Google ID token for the same account — a bare access token alone can
never delete an account on its own.

## Environment-based backend configuration

`NEXT_PUBLIC_API_URL` is a Next.js **build-time** constant — it gets
compiled into the static JS bundle, the same way it always has been; there
is no legitimate way for a *shipped* app to detect "which environment am I
in" at runtime without a server round-trip to ask, which is circular (you'd
need to already know a URL to ask). So, same as native mobile apps
generally handle this (build flavors, schemes, release channels), StromeX
now has three prebuilt environment profiles —
`apps/android/environments/{development,staging,production}.env` — and
`apps/android/build-for-env.sh <environment>` rebuilds the web bundle with
that environment's URL and produces a build tagged with a matching version
suffix (`1.0.0-dev`, `1.0.0-staging`, `1.0.0`). Switching environments is a
rebuild, not a runtime setting — exactly like a debug vs. release build of
any native app.

`staging.env` and `production.env` currently hold placeholder domains
(`https://staging-api.stromex.ai`, `https://api.stromex.ai`) since no such
deployments exist yet — replace them with real URLs once they do (see
`infra/DEPLOYMENT.md`).

## Files touched

Backend: `app/db/models/user.py` (guest/verified/google_sub/token_version
+ new `AuthToken` model), `alembic/versions/1d754ab2dadd_*.py`,
`app/core/{email,google_oauth,auth_tokens}.py` (new),
`app/api/v1/auth.py` (rewritten), `app/schemas/{auth,user}.py`,
`app/core/{security,deps,config}.py`, `app/tests/test_auth_modern.py` (new,
16 tests).
Web: `src/app/{welcome,reset-password,verify-email,auth/google-callback,settings}/page.tsx`
(new), `src/hooks/useAuth.ts`, `src/lib/{api,types}.ts`,
`src/components/layout/AppShell.tsx`, `src/app/{login,page}.tsx`.
Android: `AndroidManifest.xml` (deep-link intent-filter,
`launchMode="singleTask"`), `MainActivity.java` (`onNewIntent` handling),
`build-for-env.sh` + `environments/*.env` (new).
