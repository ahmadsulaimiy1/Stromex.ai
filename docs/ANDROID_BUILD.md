# Building and Installing SAJJIL

This repo was developed inside a sandboxed environment with no Android SDK
and no network path to `dl.google.com` (Android's SDK component host is
blocked by that environment's egress policy — confirmed, not assumed; see
`docs/STREAMING_ARCHITECTURE.md` for the same constraint's earlier
context). That means every `app` module change across this project's phases
was written carefully against real Android/Compose/Room APIs but had never
been run through an actual Android build until the CI workflow below was
added. `core` (pure Kotlin/JVM) has been genuinely compiled and unit tested
throughout — see the README's test counts.

## Getting an installable APK: GitHub Actions (works today, no local setup)

`.github/workflows/android-build.yml` builds on GitHub's own runners, which
have full network access and a real Android SDK. On every push to this
branch (or via "Run workflow" in the Actions tab):

1. Runs `core`'s full unit test suite for real, as a gate.
2. Builds `app:assembleDebug` — a **debug-signed APK**, real and directly
   installable. Debug signing uses Android's own auto-generated debug
   keystore; no secrets or setup required.
3. Uploads it as a workflow artifact named `sajjil-debug-apk`.

To get the APK: open the **Actions** tab on GitHub → the latest
"Android Build" run → download the `sajjil-debug-apk` artifact (a zip
containing the `.apk`) from the run summary page.

**Installing it**: transfer the `.apk` to an Android device (minSdk 26 /
Android 8.0+), enable "Install unknown apps" for whichever app you used to
transfer it (Settings → Apps → Special access → Install unknown apps, on
stock Android; wording varies by OEM), then open the file to install.
Debug-signed APKs install and run identically to release ones — the
signature only affects update compatibility and Play Store eligibility,
not whether the app works.

## Getting a signed release APK + AAB (needs your own signing key)

A release build — the kind installable as an update-compatible app and
the only kind Google Play accepts — must be signed with a key **you
generate and keep forever**: losing it, or having someone else generate
one on your behalf and hand it over insecurely, permanently breaks your
ability to publish updates under the same app identity. Nothing in this
repo generates or stores that key.

To enable it:

1. Generate a keystore (do this once, keep the file and passwords safe,
   e.g. in a password manager — there is no recovery if you lose it):
   ```
   keytool -genkeypair -v -keystore release.keystore -alias sajjil \
     -keyalg RSA -keysize 2048 -validity 10000
   ```
2. In the GitHub repo → Settings → Secrets and variables → Actions, add:
   - `RELEASE_KEYSTORE_BASE64` — `base64 -w0 release.keystore` (its
     contents, base64-encoded, not the file path)
   - `RELEASE_KEYSTORE_PASSWORD`
   - `RELEASE_KEY_ALIAS` (`sajjil` if you used the command above)
   - `RELEASE_KEY_PASSWORD`
3. Push again (or re-run the workflow). The build now also runs
   `assembleRelease`/`bundleRelease` and uploads a `sajjil-release`
   artifact containing the signed `.apk` and Play-Store-ready `.aab`.

Without those secrets, the workflow builds the debug APK only and logs
that release signing was skipped — it does not fail, and it does not
fabricate an unsigned or fake-signed artifact.

## Building locally (Android Studio or command line)

On a machine with Android Studio (or the Android SDK + a network path to
Google's Maven repos):

```
git clone <this repo>
cd Stromex.ai
./gradlew :core:test          # pure-Kotlin unit tests, no SDK needed
./gradlew :app:assembleDebug  # installable debug APK
```

`app/build/outputs/apk/debug/app-debug.apk` is the result. Opening the
project root in Android Studio also works directly — it's a standard
Gradle multi-module project (`:core`, `:app`).

## What CI does and doesn't verify

The build succeeding proves the Kotlin compiles, resources link, and the
DSP/Qur'an-logic unit tests pass — it does **not** prove every screen
works correctly on a device. See `docs/ANDROID_VERIFICATION_REPORT.md` for
exactly what has and hasn't been verified, and why.
