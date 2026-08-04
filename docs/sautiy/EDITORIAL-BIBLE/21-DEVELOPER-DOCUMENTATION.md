# Chapter 21 — Developer Documentation

---

## 21.1 Module Map

```
apps/sautiy/
├── settings.gradle.kts        Two-tier build; :app included when an SDK is present
├── gradle/libs.versions.toml  Every version, in one place
├── sautiy-core/               Pure JVM Kotlin — no Android
│   └── src/main/kotlin/ai/sautiy/core/
│       ├── SautiyConstitution.kt   Chapter 1 as constants + PerformanceBudget
│       ├── design/                 Palette, contrast, spacing, motion, type scale
│       ├── workspace/              The one-canvas law, errors, interruptions
│       ├── audio/                  AudioFormat, AudioBuffer, PcmCodec, Decibels
│       ├── codec/                  WavCodec, FlacCodec (+decoder), encoder registry
│       ├── dsp/                    Fft, Biquad, Dynamics, NoiseReduction, Reverb,
│       │                           Resampler, StudioChain + the nine presets
│       ├── analysis/               WaveformPeaks, Loudness (BS.1770), SilenceDetector
│       ├── edit/                   Timeline, operations, history, renderer
│       ├── record/                 Capture state machine, policy, crash recovery
│       └── play/                   Playback state machine, policy, bookmarks
└── app/                       Android
    └── src/main/
        ├── AndroidManifest.xml     Note the absent INTERNET permission
        ├── res/font/               Archivo, Fraunces, Amiri, Cairo — bundled
        └── java/ai/sautiy/
            ├── SautiyActivity.kt   The only Activity
            ├── ui/theme/           Compose bindings for the core design system
            ├── ui/icons/           The drawn icon set
            ├── ui/workspace/       The canvas, dock, context bar, ViewModel
            ├── ui/components/      Meters, gauges
            ├── ui/panels/          The twelve panels
            ├── record/             AudioCapture, RecordingService
            ├── play/               AudioPlayer
            ├── export/             Platform encoders
            └── data/               Storage paths
```

## 21.2 Building

**Core only** — works on any machine with a JDK 17+, no Android SDK required:

```bash
cd apps/sautiy
gradle :sautiy-core:test        # 248 tests
gradle :sautiy-core:build
```

**The Android app** — needs an Android SDK:

```bash
export ANDROID_HOME=/path/to/android-sdk      # or set sdk.dir in local.properties
cd apps/sautiy
gradle :app:assembleDebug
gradle :app:installDebug
```

`:app` is included automatically once an SDK is detected. Force the decision either way with
`-PsautiyAndroid=true|false`.

## 21.3 Where To Put A Change

| Change | Goes in |
|---|---|
| A new tool in the context bar | `WorkspaceState.contextActions()` — the law, then the icon mapping |
| A new panel | `Panel` enum, then `PanelHost` |
| A new DSP stage | `dsp/`, then `StudioChain.apply`, in the chapter 10.2 order |
| A new export format | An `AudioEncoder`, registered in `Encoders` |
| A new edit operation | `EditOperation`, as a pure `Timeline → Timeline` function |
| A colour, a size, a duration | `sautiy-core/design/` — **never** at a call site |
| A user-facing string | `res/values/strings.xml`, in the chapter 2.9 voice |

**The test for where something belongs:** if it decides *what should happen*, it goes in
`sautiy-core`. If it decides *how to talk to a device*, it goes in `app`.

## 21.4 Conventions

- British English everywhere, identifiers included.
- Explicit API mode in `sautiy-core`.
- Comments explain **why**. A comment restating the code is noise.
- Every public type carries a KDoc naming the Bible chapter it implements.
- Domain names: `frames`, `dBFS`, `take`, `clip`, `layer` — not `count`, `level`, `item`.

## 21.5 Extension Points

Named interfaces with **working default implementations** — never empty promises (chapter 1.10):

| Interface | Default | Extend for |
|---|---|---|
| `AudioEncoder` | WAV, FLAC | A new format, including MP3 |
| `SourceProvider` | `InMemorySourceProvider` | Streaming from disk, network, anywhere |
| `RecordingAnalyst` (ch. 11.7) | Measured analysis of chapters 10 and 15 | An on-device model |

## 21.6 Adding A Bible Chapter

The execution protocol is not optional:

1. Write the chapter.
2. Implement it — completely — in the same commit.
3. Add the tests that hold it.
4. Run the suite.
5. Update the implementation ledger with what was **actually verified**.

Documentation and implementation move together. A chapter written without its code is the one
unrecoverable defect (chapter 1.11).

## 21.7 Contributing

- Every commit states what was verified and how, and does not round up.
- A commit that changes behaviour changes a test.
- A commit that diverges from the Bible either fixes the code or amends the Bible, in the same
  commit, with the reason recorded.
- No commit adds a placeholder. The build will reject it.

---

### Implementation

This chapter is the repository. See also `apps/sautiy/THIRD-PARTY-NOTICES.md` and
`docs/sautiy/IMPLEMENTATION-LEDGER.md`.
