# StromeX Android — Installation Instructions

## Installing the APK (sideload)

1. Download `apps/android/release/stromex-v1.0.0.apk` to your Android device
   (Android 10 / API 29, or newer — up to and including current Android
   releases; see the compatibility note below).
2. On the device, allow installs from the source you downloaded it with
   (Settings → Apps → Special access → Install unknown apps → pick your
   browser/file manager → allow), if not already allowed.
3. Open the downloaded file and tap **Install**.
4. Launch **StromeX** from the app drawer.

Or, from a computer with the device connected over USB (developer mode +
USB debugging enabled):

```bash
adb install apps/android/release/stromex-v1.0.0.apk
```

## Installing via the AAB (Google Play path)

`.aab` files are not directly installable — Google Play (or `bundletool`)
turns them into device-specific APKs at install time. To sideload from the
`.aab` for testing without a Play Console listing:

```bash
java -jar bundletool.jar build-apks \
  --bundle=apps/android/release/stromex-v1.0.0.aab \
  --output=stromex.apks \
  --ks=path/to/your/keystore --ks-key-alias=<alias> \
  --ks-pass=pass:<password> --key-pass=pass:<password> \
  --mode=universal

java -jar bundletool.jar install-apks --apks=stromex.apks
```

For an actual Play Store release, upload the `.aab` directly in Play
Console — that is exactly what it's for.

## Connecting to a backend

The shipped APK/AAB point at `http://localhost:8000` — i.e., **the device's
own localhost** — because this build environment could not expose a public
backend URL to bake in (see
[05-STROMEX-ANDROID-BUILD.md](./05-STROMEX-ANDROID-BUILD.md)). To use the app
against a real backend:

1. Deploy the backend per `infra/DEPLOYMENT.md`, or run it locally and note
   its reachable URL/IP.
2. Add that URL's origin to the backend's `CORS_ORIGINS` — the app also needs
   `https://stromex.local` in that list (see `apps/api/.env.example`).
3. Rebuild the web bundle with `NEXT_PUBLIC_API_URL` set to that URL, copy it
   into `apps/android/assets/`, and re-run `apps/android/build.sh` (see the
   build doc for exact commands).
4. Install the freshly built APK/AAB as above.

There is currently no in-app settings screen to change the API URL after
build time — it is baked in at web-build time, the same as the browser app's
`NEXT_PUBLIC_API_URL`.

## Compatibility

- `minSdkVersion=29` (Android 10) — `targetSdkVersion=36` (Android 16).
- Uses only `android.app.*`/`android.webkit.*` — no AndroidX, no Play
  Services dependency, no vendor-specific APIs — so it should behave
  identically across OEM Android builds.
- Requires `INTERNET` and `ACCESS_NETWORK_STATE` permissions only (both
  auto-granted, no runtime permission prompts).

See [07-STROMEX-ANDROID-TEST-REPORT.md](./07-STROMEX-ANDROID-TEST-REPORT.md)
and [09-STROMEX-ANDROID-VERIFICATION-REPORT.md](./09-STROMEX-ANDROID-VERIFICATION-REPORT.md)
for what was and wasn't actually verified on-device versus in an emulated
browser environment standing in for one.
