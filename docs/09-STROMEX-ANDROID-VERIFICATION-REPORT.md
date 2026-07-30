# StromeX Android — Verification Report

## Honesty statement, up front

This environment has **no Android emulator** (no `/dev/kvm`, no VMX/SVM CPU
flags — checked directly, confirmed absent) and **no physical Android
device**. So the literal instruction "install and run the generated Android
application" on an Android OS instance could not be carried out here. What
follows is every verification that *was* genuinely possible without one —
static analysis of the actual signed build artifacts, plus functional
testing of the exact code the APK ships (see the test report) — stated
plainly as a substitute, not a disguise, for on-device installation.
Anyone with access to a device or emulator can complete that last step in
minutes using the installation instructions doc; this report tells you
exactly what's already been confirmed and what specifically still needs
that final check.

## 1. Build reproducibility

`apps/android/build.sh`, run non-interactively end to end, produces both
artifacts from source with no manual intervention, and self-checks its own
output (`apksigner verify`, `jarsigner -verify`, `bundletool validate`) as
its last steps — a broken build fails the script rather than shipping a bad
artifact silently.

```
$ ./build.sh
== Compiling Java sources ==
== Dexing (D8) ==
== Compiling resources (aapt2 compile) ==
== Linking binary APK (aapt2 link) ==
== Merging classes.dex, zipaligning, signing (APK) ==
APK -> .../build/apk-out/stromex-release.apk
== Building proto-format resources for the App Bundle ==
== Assembling the base module ==
== Building and signing the App Bundle (bundletool) ==
jar signed.
AAB -> .../build/aab/stromex-release.aab
== Deriving a universal APK from the AAB as an end-to-end sanity check ==
== Copying deliverables to release/ ==
Done.
```

## 2. APK static verification

```
$ aapt2 dump badging release/stromex-v1.0.0.apk
package: name='ai.stromex.app' versionCode='1' versionName='1.0.0' ...
sdkVersion:'29'
targetSdkVersion:'36'
uses-permission: name='android.permission.INTERNET'
uses-permission: name='android.permission.ACCESS_NETWORK_STATE'
application-label:'StromeX'
application-icon-160:'res/mipmap-anydpi-v26/ic_launcher.xml'
launchable-activity: name='ai.stromex.app.MainActivity'  label='StromeX'
supports-screens: 'small' 'normal' 'large' 'xlarge'
supports-any-density: 'true'
```

Confirms: correct package ID, correct min/target SDK, correct declared
permissions (only the two expected — no unnecessary permissions), correct
launcher activity, adaptive icon present, screen-size support declared for
phones and tablets alike.

```
$ apksigner verify --verbose --print-certs release/stromex-v1.0.0.apk
Verifies
Verified using v3 scheme (APK Signature Scheme v3): true
Number of signers: 1
Signer #1 certificate DN: CN=StromeX, OU=Engineering, O=StromeX, ...
Signer #1 key algorithm: RSA
Signer #1 key size (bits): 2048
```

v3-only signing is correct and sufficient for `minSdkVersion=29` (v3 is
supported from API 28 onward); v1/v2 are intentionally not required at this
floor.

`unzip -l` confirms the archive contains a real `AndroidManifest.xml`,
`resources.arsc`, `classes.dex`, and the full `assets/` tree (the static web
bundle) — not an empty or truncated package.

## 3. AAB static verification

```
$ jarsigner -verify release/stromex-v1.0.0.aab
jar verified.
(expected warnings only: self-signed certificate, no timestamp —
 both normal for a self-managed release/upload key, not a defect)

$ bundletool validate --bundle=release/stromex-v1.0.0.aab
App Bundle information
------------
Feature modules:
	Feature module: base
		File: assets/index.html, assets/chat.html, assets/quran.html, ...
		File: res/mipmap-anydpi-v26/ic_launcher.xml
		File: dex/classes.dex
```

`bundletool validate` parses the bundle successfully — a malformed bundle
would fail this step outright.

## 4. End-to-end proof the AAB is installable (not just well-formed)

The strongest available proof that the `.aab` is genuinely usable, short of
an actual Play Store upload or device install, is deriving and re-verifying
a real installable APK *from* it — exactly what Google Play's own backend
does at install time:

```
$ bundletool build-apks --bundle=release/stromex-v1.0.0.aab \
    --output=stromex.apks --ks=... --mode=universal
$ unzip stromex.apks   # -> universal.apk

$ apksigner verify --verbose universal.apk
Verifies
Verified using v3 scheme (APK Signature Scheme v3): true
Number of signers: 1
```

This round-trip (AAB → bundletool → derived APK → re-verified signature)
succeeded, confirming the AAB is not just schema-valid but produces a
correctly signed, installable APK.

## 5. Checksums (for anyone verifying the exact committed files)

```
4c3a59f8d342055dc5b007d610d52853638e806d137261c0adbca6be0edbc19d  release/stromex-v1.0.0.apk
98a096628ef5cfef428234c47f8bee8b697e97d5c555252415dcb47be7a01521  release/stromex-v1.0.0.aab
```

## 6. Functional verification

See [07-STROMEX-ANDROID-TEST-REPORT.md](./07-STROMEX-ANDROID-TEST-REPORT.md)
in full. Summary: the exact static bundle inside the APK/AAB
(`apps/android/assets` ≡ `apps/web/out`) was exercised in real Chromium via
Playwright, under mobile device emulation, against the real running FastAPI
backend — registration, login, session persistence, chat, Arabic RTL, books,
admin-access enforcement, offline handling, dark mode, tablet viewport, and
network throttling all passed. Screenshots: `docs/assets/android/`.

## 7. What remains unverified — explicitly, per the user's own instruction

- **Actual installation and launch on a real Android OS instance** (emulator
  or physical device). Everything above is the strongest available
  substitute in this environment, but it is not the same thing, and this
  report does not claim otherwise. Anyone with a device can complete this in
  under a minute: `adb install apps/android/release/stromex-v1.0.0.apk` (or
  sideload directly), then walk through the same user journeys described in
  the test report.
- **Cross-version testing across real Android 10 through 16 OS builds.** No
  device farm (Firebase Test Lab, BrowserStack) or multiple real/emulated OS
  instances were available. `minSdkVersion`/`targetSdkVersion` are correctly
  declared and the app avoids any version-gated API, which is the strongest
  static argument available, but real per-version testing was not performed.
- **Real low-memory process eviction behavior** on actual constrained
  hardware (only network-throttling was simulated, not RAM pressure).
- **The backend the shipped build points at is `http://localhost:8000`** —
  the device's own localhost, not a publicly reachable production backend.
  This sandbox could not expose a public URL for the running backend by any
  method tried (Cloudflare Quick Tunnel, ngrok, raw SSH tunnels — all
  blocked by network policy), so a build baked with a real public backend
  URL could not be produced or tested end-to-end here. To use the shipped
  build against a real backend, see
  [06-STROMEX-ANDROID-INSTALL.md](./06-STROMEX-ANDROID-INSTALL.md).
- **Native WebView chrome/interaction specifics** not observable from a
  browser stand-in: Android back-gesture navigation inside the WebView,
  system share-sheet behavior for PDF export downloads, notification
  permission prompts (none currently requested by this app), and split-
  screen/foldable behavior.

None of the above were skipped by omission — each is called out because it
requires infrastructure (a device, a device farm, a public network egress
path) that this environment does not have, not because it was judged
unimportant.
