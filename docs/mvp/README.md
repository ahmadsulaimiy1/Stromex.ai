# TASMIM Flagship MVP — Phase 4 Implementation

> Phase 4: a real, installable Android app — not a mockup, not another strategy document. This folder is the delivery record: what was built, how it was verified, how to build the APK yourself, and — held to the same "ruthless objectivity" standard as Phase 3 — exactly what is not yet real.

## Where the code lives

The Flutter app is at [`/app`](../../app) in this repository, built on branch `claude/tasmim-product-strategy-togu4q`.

## A structural note before anything else

The sandbox this app was built in blocks outbound access to `dl.google.com` and `maven.google.com` — the hosts the Android SDK, Android Gradle Plugin, and AndroidX Maven artifacts are served from. That means the Android release APK could not be compiled inside this development session. Every other verification step *was* run directly and is reported honestly below: `flutter analyze`, `flutter test` (9 tests, including a full onboarding-to-dashboard widget test), and a `flutter build web --release` compile, driven end-to-end through real screens with a headless Chromium browser to produce the screenshots in [`screenshots/`](./screenshots).

The actual Android compile happens in [`.github/workflows/build-apk.yml`](../../.github/workflows/build-apk.yml) — a GitHub Actions workflow that runs on GitHub's own infrastructure (unrestricted internet, Android SDK preinstalled), builds the release APK, and attaches it to a GitHub Release on this repository. That is the real, reproducible source of the installable APK — see [`02-build-instructions.md`](./02-build-instructions.md) for exactly how to get it.

## Documents in This Set

1. **[Architecture Summary](./01-architecture-summary.md)** — the actual technical structure of the shipped app: folder layout, state management, the canvas engine, AI integration, storage, and how this MVP maps back to (and deliberately narrows) the Phase 2/3 architecture.
2. **[Build Instructions](./02-build-instructions.md)** — how to get the compiled APK (via GitHub Actions) and how to build it yourself locally on a machine with normal internet access.
3. **[Feature Verification Checklist](./03-feature-verification-checklist.md)** — every feature the Phase 4 brief asked for, marked against what actually works, with the specific verification evidence for each (test, screenshot, or code path).
4. **[Known Limitations](./04-known-limitations.md)** — stated as plainly as the rest of this project's strategy documents: what's scoped out, what's reduced, and what would need to change before this is more than an MVP.

## Screenshots

Real captures from a running build of this exact app (Flutter web target, driven through actual user interaction with Playwright/Chromium — not mockups), in [`screenshots/`](./screenshots):

| Screenshot | What it shows |
|---|---|
| `onboarding.png` | First onboarding screen |
| `welcome.png` | Guest-or-profile choice screen |
| `dashboard-light.png` | Dashboard, guest session, light theme, empty project state |
| `template-gallery-islamic-suite.png` | Template gallery — real rendered Islamic Suite templates (Ramadan Iftar, Eid Mubarak, Friday Lecture, Community Iftar) with live Arabic typography |
| `editor-arabic-typography.png` | The canvas editor open on the Ramadan Iftar Invitation template — real RTL Arabic text (Amiri/NotoNaskhArabic), icons, and layered objects |
| `editor-selection-toolbar.png` | An object selected on canvas — resize handle, rotate handle, and the contextual Fill/Stroke toolbar |
| `inspiration-gallery.png` | The inspiration mood-board gallery |
| `ai-assistant-key-gate.png` | The AI Design Assistant's honest "add your API key" gate — no fake AI response, a real required setup step |
| `settings-arabic-rtl.png` | Settings screen with the app switched to Arabic — note the fully mirrored RTL layout (radio buttons, bottom nav order) and correctly rendered Arabic glyphs |

## The One-Paragraph Summary

This MVP is deliberately narrower than the full Phase 2/3 vision, on purpose, per the Feature Prioritization Framework's own "20 excellent features over 200 incomplete" instruction: a real canvas editor (text, shapes, icons, color, layers, undo/redo, PNG/JPG export, local save/load), a curated template gallery anchored by genuine Islamic Suite content (Arabic typography, calligraphic display type, Islamic iconography, Ramadan/Eid/mosque/da'wah templates), a curated inspiration gallery, guest and local-profile modes, dark/light theme, English/Arabic UI with real RTL mirroring, and AI features that are honestly gated behind a user-supplied API key rather than faked. Nothing in the shipped app is a placeholder button, a dead screen, or a "coming soon" — what exists, works; what doesn't exist yet is named directly in the Known Limitations document, not hidden behind a non-functional UI element.
