# Known Limitations

> Written in the same spirit as the Phase 3 Red Team Review: stated plainly, not softened. Everything here is a disclosed, deliberate scope decision or an honestly-flagged gap — not something hidden behind a working-looking UI element.

## Infrastructure

- **The APK was not compiled inside this development session.** This sandbox's network policy blocks `dl.google.com` and `maven.google.com` (the Android SDK / Android Gradle Plugin's hosts). The app was fully written, statically analyzed, unit- and widget-tested, and compiled to a working web build inside this session — but the actual Android binary is produced by the GitHub Actions workflow added at `.github/workflows/build-apk.yml`, which runs on infrastructure that isn't network-restricted. This is a sound and common CI pattern, not a workaround of unknown reliability — but it does mean the specific APK binary has not been installed and manually tapped through on a physical Android device by the author of this MVP. Do that check before treating this as fully device-verified.
- **The release APK is debug-signed.** `android/app/build.gradle.kts` signs release builds with the default debug keystore (Flutter's scaffolded default), which is exactly right for direct install/testing but is not appropriate for Play Store submission. Proper release signing (a real keystore, ideally enrolled in Play App Signing) is a pre-launch task, not an MVP task.
- **No physical-device performance profiling has been done.** "Fast performance" was verified qualitatively (no dropped frames observed in browser-based manual testing) but not profiled with `flutter run --profile` on real Android hardware, which is where GPU/memory characteristics actually diverge from a desktop browser.

## Authentication and accounts

- **"Optional authentication" is a local, on-device profile — not a cloud account.** There is no backend, no server-side user record, and no cross-device sync. A passcode-protected profile is stored via `flutter_secure_storage`, salted and hashed (SHA-256) — appropriate protection for what it actually is (a local device lock), but explicitly not a security model designed to resist a networked attacker, because there's no network component to attack. This matches the Phase 3 Engineering Specification's own scoping of Phase 1 authentication, and is disclosed to the user directly in-app ("Profiles are stored securely on this device only").

## AI features

- **AI features require the user's own Anthropic API key.** TASMIM does not ship with, proxy, or subsidize a shared key — this is the responsible MVP posture given the Phase 3 Technology Stack Decision Report's cost-control reasoning, and it's disclosed honestly in-app (a real "Add your API key" screen, not a fake response or hidden failure).
- **AI generation is text and palette, not image synthesis.** "AI Design Assistant," "Prompt-to-design," the flyer generator, and the social post generator all generate structured copy and a color direction, then apply that to one of TASMIM's own hand-crafted templates. This was a deliberate scope decision (see the Phase 3 Technology Stack Decision Report) — it is not the full "AI Designer" agent described in the Phase 2 Creative Intelligence Engine, which implies genuine layout generation and eventually image synthesis. Only 1 of the Phase 2 architecture's 10 specialist AI agents is meaningfully represented here (a simplified AI Designer); the other 9 (Art Director, Layout Expert, Typography Expert, Brand Strategist, Presentation Designer, Publishing Assistant, Social Media Creator, Marketing Assistant, Design Critic) do not exist in this MVP.
- **No AI cost/rate-limit handling beyond basic error messages.** A 429 or network failure surfaces a plain error string; there's no retry-with-backoff, no usage tracking, and no cost estimate shown to the user before a call is made.

## Inspiration Ecosystem

- **The Inspiration gallery is a curated, static set of 8 color/typography mood boards — not a live feed.** It is real, useful content (not a mockup), but it is not the Pinterest-class discovery engine, trend feed, creator community, or Inspiration-to-Design conversion pipeline described in the Phase 2/3 architecture. That system requires infrastructure (a backend, a content corpus, vector search) this local-first MVP does not have and was never scoped to build in Phase 4.

## Islamic Creative Suite

- **Only a curated MVP subset of the full Islamic Suite exists.** Arabic typography, Islamic iconography, and four categories of hand-crafted templates (Islamic flyers, mosque events, da'wah posters, plus general/social) are real and functional. The calligraphy tools, the Islamic geometric pattern generator, and Mushaf publishing tools described in the Phase 2 architecture are **not implemented** — this is intentional, since the Phase 2/3 documents explicitly require a scholarly governance board before any Mushaf-adjacent feature ships, and no such board exists for this MVP. The AI system is explicitly instructed never to generate or paraphrase Qur'anic text, and defers to human review for anything liturgical, per that same governance requirement.

## Collaboration and platform reach

- **No real-time collaboration.** Every document is single-user, single-device. This matches the Phase 3 Feature Prioritization Framework's explicit Tier B placement (deferred past MVP due to being the highest-engineering-risk item in the whole roadmap).
- **No cloud sync between devices.** A project saved on one device does not appear on another.
- **Android only.** No iOS, desktop, or (beyond the local web build used for verification) a supported web deployment. This matches the Phase 4 brief's own "Android first" instruction.
- **No marketplace, no plugin/API ecosystem, no video/motion tooling.** All explicitly out of scope per the Phase 3 Feature Prioritization Framework's Tier C.

## Editor capability gaps

- **No CMYK or print-resolution preflight.** Exports are RGB, screen-resolution-appropriate (PNG/JPG at the document's native design resolution) — not print-production-ready.
- **No multi-page / multi-artboard documents.** Each project is a single canvas; there is no Publishing Studio (books, long-document layout) in this MVP.
- **Resize/rotate handles are axis-aligned regardless of an object's current rotation.** Resizing a rotated object works, but the handle position doesn't visually re-orient with the object — a minor interaction polish gap, not a functional one.
- **Template gallery thumbnails for non-square/portrait-heavy templates (e.g., the wide "Clean Corporate Update" banner) render with visible letterboxing** in the portrait-oriented grid card — a cosmetic layout detail in the thumbnail view only; the underlying template itself is correctly proportioned when opened in the editor.

## Localization

- **Only the four highest-traffic screens (onboarding, welcome, dashboard, settings) are translated into Arabic.** Secondary screens and dialogs (e.g., some Settings sub-labels, dialog button text, diagnostics screen) remain English-only even when the app language is set to Arabic. RTL layout mirroring and Arabic *font rendering* are universal across the whole app regardless of translation coverage — only some UI *copy* is still English. This was a disclosed, deliberate scope trade-off given the size of the full app's string surface versus the time available, not an oversight discovered after the fact — see the Phase 4 build log for the reasoning.

## Testing depth

- **Automated test coverage is real but not exhaustive.** Nine tests cover canvas document serialization, controller mutation/undo/redo logic, and the onboarding-to-dashboard golden path. Export, AI integration, project save/load, and the full settings/localization surface are verified manually (via the web build and screenshots) rather than by automated tests, and have not been exercised via `integration_test` against a real Android device or emulator.
