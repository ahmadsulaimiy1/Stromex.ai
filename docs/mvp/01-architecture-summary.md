# TASMIM MVP — Architecture Summary

> How the app in `/app` is actually built, mapped back to the Phase 2 Master Architecture and the Phase 3 Engineering Specification — including where this implementation deliberately narrows or diverges from those documents, and why.

## Stack

| Layer | Choice | Matches Phase 3 recommendation? |
|---|---|---|
| Framework | Flutter 3.44.8 (stable), Dart 3.12 | The user's Phase 4 brief explicitly requires Flutter/Android-first, which the Phase 3 Technology Stack Decision Report had actually recommended *against* for the long-term app shell (favoring native Swift/Kotlin over a shared Rust/WASM core). This MVP follows the Phase 4 instruction as given — see [`04-known-limitations.md`](./04-known-limitations.md) for the tension this creates with the Phase 3 recommendation. |
| State management | `provider` + `ChangeNotifier` | Lighter-weight than a full architecture like Riverpod/Bloc — appropriate for the MVP's actual state surface (app-wide session/theme/locale via `AppState`, per-document editing state via `CanvasController`). |
| Routing | `go_router` | Single centrally-defined route table (`core/router/app_router.dart`) with a redirect guard, so every navigable destination is enumerated in one place — the concrete mechanism behind "no broken navigation." |
| Local persistence | `shared_preferences` (non-secret prefs), `flutter_secure_storage` (API key, local profile credential hash), raw JSON files via `path_provider` (saved projects) | Local-first, matches the Engineering Specification's Phase 1 database decision in spirit (no backend, no network dependency for core editing) — simplified further since this MVP has no multi-device sync requirement at all. |
| AI | Direct HTTPS calls to the Anthropic Messages API, bring-your-own-key | Matches the Technology Stack Decision Report's "Anthropic for reasoning/agents" recommendation and the BYOK model explicitly named as the responsible MVP approach for AI cost/access. |
| Export | `dart:ui` `RenderRepaintBoundary.toImage()` (native PNG) + the `image` package (JPG encoding) | Renders the editor's real on-screen content at native document resolution, not display resolution — see `features/editor/export/export_service.dart`. |

## Folder structure

```
app/lib/
  main.dart              — process entry point, DI wiring, global error handlers
  app.dart               — MaterialApp.router, theme/locale binding
  core/
    theme/                — AppColors, AppTheme (light/dark, Arabic font fallback)
    state/                — AppState (session, theme, locale)
    storage/               — LocalStorageService, SecureStorageService, ProjectRepository
    router/                — the single app_router.dart route table
    logging/               — AppLogger (in-app diagnostics log)
    error/                 — AppErrorScreen (ErrorWidget.builder override)
  features/
    onboarding/
    auth/                  — welcome, create-profile, sign-in (local profile only)
    home/                  — HomeShell (bottom-nav shell: Home/Templates/Inspiration/AI/Settings)
    dashboard/
    editor/
      canvas/              — CanvasDocument/CanvasObject model, CanvasController, CanvasView, renderer
      widgets/             — toolbars, pickers, layers panel
      export/              — ExportService
    templates/             — DesignTemplate model + curated template library (incl. Islamic Suite)
    inspiration/           — curated mood-board data + gallery
    ai/                    — AiService (Anthropic client), prompt-to-design, assistant chat
    settings/
  l10n/                    — app_en.arb / app_ar.arb + generated AppLocalizations
  shared/widgets/          — IslamicIcon set + IconRegistry, shared UI kit pieces
```

## The canvas engine

This is the core of the MVP and the piece worth understanding in most depth.

- **Document model** (`canvas_model.dart`): a `CanvasDocument` is a size, a background color, and an ordered list of `CanvasObject`s (`TextObject`, `ShapeObject`, `IconObjectData`). Every object is independently JSON-serializable — the same structure backs saved projects, built-in templates, and (indirectly) AI-populated designs.
- **Controller** (`canvas_controller.dart`): a `ChangeNotifier` owning selection state and a bounded undo/redo history (60 entries). History snapshots are taken once per *gesture*, not once per frame — `beginTransform()` snapshots at drag-start, then `updateTransform()` mutates without pushing new history until the next `beginTransform()` call, so one undo reverts a whole drag rather than one pixel of it (covered by a unit test).
- **Rendering** (`canvas_renderer.dart`, `canvas_document_view.dart`, `canvas_view.dart`): one pure rendering function (`CanvasObjectRenderer`) is shared by three contexts — the live interactive editor, template gallery thumbnails, and saved-project cards — so a thumbnail is always a pixel-accurate preview of the real design, never a separately-maintained mock image.
- **Interaction**: the live `CanvasView` renders the real document inside a `RepaintBoundary` (used for export) and layers a *separate*, non-captured gesture layer on top for tap/select, drag-to-move, a resize handle, and a rotate handle — so selection UI never contaminates an exported image. Drag math uses raw global pointer-position deltas divided by the computed display scale, rather than relying on Flutter's ancestor-transform-dependent local delta semantics, specifically to keep dragging correct regardless of on-screen zoom level.
- **Export**: `ExportService` reads the *displayed* `RenderRepaintBoundary`'s size, computes the exact pixel ratio needed to reach the document's real (design-space) resolution, and calls `toImage(pixelRatio:)` — so a flyer designed at 1240×1748 exports at that resolution even though it's shown much smaller on a phone screen.

## AI integration

`AiService` calls the Anthropic Messages API directly from the device using a key the user enters in Settings (stored via `flutter_secure_storage`, Android Keystore-backed). Two capabilities are implemented:

1. **AI Design Assistant** — a conversational design-advice chat (`ai_assistant_screen.dart`), constrained by a system prompt to give concrete design feedback and to explicitly decline to generate or paraphrase Qur'anic text, deferring to scholarly review — a direct, code-level expression of the Islamic Creative Suite's governance requirement from the Phase 2 architecture.
2. **Prompt-to-design** (`prompt_to_design_screen.dart` + `design_brief_applier.dart`) — the model returns structured JSON (headline, subheadline, body copy, a color palette, and a suggested category), which `applyDesignBrief()` then uses to select the best-matching built-in template and populate it with that content. This is the MVP's honest scope for "AI Designer": real content and palette generation applied to real, hand-crafted templates — not image synthesis, and not a from-scratch AI layout engine, per the Phase 3 Technology Stack Decision Report's reasoning for what's realistic to ship first. Islamic Suite templates specifically are *not* recolored by AI suggestions — only general-category templates are, protecting the deliberately-curated Islamic Suite palette from being silently overridden (also enforced in code, not just by convention).

"Flyer generator" and "social post generator" are the same underlying flow with a different default canvas preset and prompt framing (`PromptToDesignMode.flyer` / `.socialPost`) — genuinely distinct entry points and defaults, not two copies of one screen pretending to be different features.

## Localization and RTL

`flutter_localizations` + generated `AppLocalizations` (from `lib/l10n/app_en.arb` / `app_ar.arb`) drive the four highest-traffic screens (onboarding, welcome, dashboard, settings) in both languages, with `MaterialApp.locale` bound to `AppState.locale` so switching language in Settings immediately re-renders the whole app in the new `Directionality` — verified in `settings-arabic-rtl.png`, where the bottom navigation bar, radio buttons, and text alignment all correctly mirror to RTL. Canvas *content* (template text, AI-generated headlines) sets its `TextDirection` and font family explicitly per-object regardless of app UI language, since a template's Arabic content should render RTL whether the app chrome is in English or Arabic.

A real bug was caught and fixed during verification: the app's default text theme originally specified only the Latin-only `Inter` font, which rendered Arabic UI strings (like the language toggle's own "العربية" label) as tofu boxes in this specific headless-browser test environment. The fix — adding `Cairo`/`NotoNaskhArabic` as `fontFamilyFallback` on every text style in `AppTheme` — is a general, correct solution (Flutter substitutes per-glyph from the fallback list) that also protects any future Arabic string in app chrome, not a one-off patch for that single label.

## What deliberately isn't here

Real-time collaboration, a live Pinterest-class inspiration feed, image-generation AI, cloud accounts/sync, native mobile beyond Android, and Mushaf/calligraphy tooling are all out of scope for this MVP by design — each is either explicitly Tier B/C/D in the Phase 3 Feature Prioritization Framework or requires infrastructure (a backend, a scholarly governance board) this local-first, single-session MVP doesn't have. See [`04-known-limitations.md`](./04-known-limitations.md) for the complete, honest list.
