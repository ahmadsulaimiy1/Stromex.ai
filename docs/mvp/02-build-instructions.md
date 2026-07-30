# Build Instructions

## Option A — Get the pre-built APK from GitHub Actions (recommended)

The release APK is compiled automatically by [`.github/workflows/build-apk.yml`](../../.github/workflows/build-apk.yml) on GitHub's own infrastructure, which has the Android SDK preinstalled and unrestricted internet access — the two things this development sandbox does not have.

1. Push (or merge) this branch to the repository — the workflow triggers automatically on any push touching `app/**`.
2. Alternatively, trigger it manually: on GitHub, go to **Actions → Build TASMIM Android APK → Run workflow**.
3. Once the run finishes (a few minutes), the APK is available two ways:
   - **Releases tab**: the workflow publishes a GitHub Release (tagged `mvp-build-<run-number>`) with the `.apk` file attached directly — the simplest way to download and sideload it.
   - **Workflow artifact**: every run also uploads the APK as a build artifact (`tasmim-release-apk`) under the run's summary page, retained for 90 days.
4. Download the `.apk` to an Android device (or transfer it), then install it directly (Android will prompt to allow installs from that source if it's the first time) — no Play Store submission involved.

**This is a debug-signed release build** — appropriate for direct install and testing, not for Play Store distribution (see Known Limitations).

## Option B — Build it yourself locally

Requires a machine with normal, unrestricted internet access (specifically to `dl.google.com`/`maven.google.com`, which this development sandbox could not reach).

### Prerequisites

- [Flutter SDK](https://docs.flutter.dev/get-started/install) 3.44.x, stable channel
- Android SDK with API 34+ platform and build-tools (installed automatically by Android Studio, or via `sdkmanager`)
- A JDK 17 (Temurin recommended)

### Steps

```bash
git clone <this repository>
cd Stromex.ai/app

flutter pub get
flutter analyze          # should report 0 errors
flutter test             # should report 9/9 passing

flutter build apk --release
# Output: build/app/outputs/flutter-apk/app-release.apk
```

Install directly to a connected device/emulator:

```bash
flutter install --release
# or
adb install build/app/outputs/flutter-apk/app-release.apk
```

### Running in debug mode (for development)

```bash
flutter run
```

### Regenerating localization files (after editing `lib/l10n/*.arb`)

```bash
flutter gen-l10n
```

### Regenerating the app icon (after editing `tool/generate_icon.dart`)

```bash
dart run tool/generate_icon.dart
dart run flutter_launcher_icons
```

## Verifying without the Android SDK

If you only want to verify the Dart/Flutter application logic (not produce an Android binary), everything below works with just the Flutter SDK — no Android SDK required:

```bash
flutter analyze
flutter test
flutter build web --release   # compiles the full app for a browser target
```

This is exactly the verification path used during this MVP's development, documented in [`03-feature-verification-checklist.md`](./03-feature-verification-checklist.md).
