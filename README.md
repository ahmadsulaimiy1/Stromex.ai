# SAJJIL™

An AI-assisted voice recording, enhancement and mastering studio for Android, purpose-built for
Qur'an recitation, Nasheed, lectures, khutbahs, podcasts and voiceover work.

This repository is the first implementation pass toward the SAJJIL product vision. It is scoped
deliberately: the vision document describes a multi-year product surface (dozens of AI features,
eight luxury themes, dedicated Qur'an tooling, dashboards). Rather than stub all of it, this pass
builds a **smaller set of things for real** — genuine DSP, genuine tests, a coherent architecture —
and leaves the rest as an explicit roadmap.

## Modules

- **`core`** — pure Kotlin/JVM, zero Android dependencies, fully unit tested (31 tests). Contains
  every DSP algorithm, the recording mode/voice profile presets, WAV I/O, loudness analysis, and
  Qur'an reference metadata (Surah/Ayah/Juz).
- **`app`** — the Android application (Jetpack Compose + Material3). Wires `core`'s DSP into a live
  `AudioRecord` capture chain, a Room-backed recording library, WAV/AAC export, and six screens
  (Record, Enhance, Master, Archive, Qur'an Studio, Settings + an Executive Dashboard).

`core` is verified in this environment with `gradle :core:test` (no Android SDK required — see
"Building" below for why `app` couldn't be compiled here). `app` was written carefully against the
same API surfaces but has **not** been compiled or run on-device in this session; treat it as a
strong first draft to build and smoke-test on a real checkout.

## What's real in `core` (not stubs)

- **`BiquadFilter`** — RBJ Audio EQ Cookbook peaking/shelf/low-pass/high-pass filters.
- **`ParametricEqualizer`** — 4-band tone control and a full 31-band ISO graphic EQ.
- **`Compressor`** — RMS-detector feed-forward compressor, soft knee, auto makeup gain.
- **`Limiter` / `LoudnessMaximizer`** — lookahead brickwall peak limiter for loudness maximization.
- **`NoiseGate`** — envelope-follower gate with hold/hysteresis (Tajweed-safe: long hold avoids
  clipping soft letters).
- **`DeEsser`** — dynamic sibilance-band peaking filter.
- **`FFT`** — iterative radix-2 Cooley-Tukey, forward/inverse.
- **`SpectralNoiseReducer`** — real STFT spectral subtraction (Boll 1979) with Hann windows,
  overlap-add reconstruction, and edge-padding to avoid the boundary artifact a naive OLA
  implementation produces (this bug was caught and fixed via the test suite — see below).
- **`LoudnessAnalyzer`** — peak/RMS/dynamic-range/noise-floor and a simplified BS.1770-style
  integrated loudness (LUFS) estimate.
- **`WavIO` / `WavStreamWriter`** — full PCM16/PCM24/Float32 WAV read/write, including a streaming
  writer so multi-hour recordings never have to sit fully in memory.
- **`RecordingMode`** (Qur'an Studio, Imam Al-Haram, Lecture, Nasheed, Podcast) and **`VoiceProfile`**
  (Haramain, Madinah, Makkah, Studio Qari, Lecture Hall, Broadcast, Podcast) — concrete DSP-chain
  presets, not just labels.
- **`QuranMetadata`** — all 114 Surahs with ayah counts and the 30 Juz start boundaries.

A genuine bug was found and fixed while building this: the first spectral-subtraction
implementation reconstructed audio incorrectly near buffer edges (dividing by a near-zero
window-sum), which a naive listen-through would likely have missed but the noise-floor-reduction
unit test caught immediately. Fixed via zero-padding before framing.

### "AI Studio" naming vs. what's implemented

The spec calls the enhancement engine "SAJJIL AI Studio™." What's implemented today is classic,
well-understood **digital signal processing** — spectral subtraction, not a trained noise-removal
model. It's honestly effective for steady-state noise (fans, hiss, hum) but won't out-perform a
neural denoiser on complex non-stationary noise. On-device ML noise/echo removal is tracked as a
roadmap item, not silently claimed.

## What's in `app`

- Live recording through `AudioRecordEngine`: mic capture → per-sample gate → EQ → de-esser →
  compressor → loudness maximizer → streamed straight to WAV (no whole-file buffering).
- `SAJJIL Enhance`: pick a recording, run spectral noise reduction at Light/Moderate/Strong/Extreme,
  A/B preview original vs. enhanced.
- `SAJJIL Master`: apply a Voice Profile, see Executive Dashboard scores, export to WAV or AAC/M4A.
- `SAJJIL Archive`: searchable Room-backed library, favorites, delete, tap-through to a per-recording
  Executive Dashboard (loudness metrics + 0–100 readiness scores).
- `SAJJIL Qur'an Studio`: tag any recording with Surah/Ayah range (Juz is derived automatically) and
  browse the resulting Qur'an library.
- Eight luxury Material3 themes (Royal Gold, Midnight Black, Emerald Prestige, Sapphire Blue, Makkah
  Night, Madinah Green, Platinum White, Executive Dark), persisted via DataStore.
- Export: WAV (any bit depth) and AAC/M4A via `MediaCodec`/`MediaMuxer` — no third-party codec
  dependency.

### Deliberately out of scope for this pass

The spec's own **"Future Roadmap"** and **"Future AI Features"** sections are treated as out of
scope here, plus a few practical additions:

- FLAC / MP3 / OGG / OPUS / ALAC / AIFF export — these need licensed or NDK-cross-compiled codecs
  (`libFLAC`, `libmp3lame`, `libopus`); WAV and AAC/M4A cover the two formats Android's SDK supports
  natively.
- Trained-model noise/echo removal, voice cloning protection, AI mastering assistant, AI microphone
  simulation, room correction, DAW/mixer/plugin marketplace, transcription, speaker separation,
  multi-track recording, cloud sync.
- Batch processing of "entire Qur'an"/album-scale jobs — the single-file pipeline exists; a queue on
  top of it is straightforward follow-up work.
- Video-audio extraction (MP4/MOV/MKV/AVI) — same MediaCodec path as AAC export, just not wired up
  yet.

## Building

This sandboxed environment has a JDK and Gradle but **no Android SDK and no network path to
`dl.google.com`**, so the Android Gradle Plugin can't be resolved here — `app` could not be built
or run in this session. `core` has zero Android dependencies and was fully built and tested here:

```
gradle :core:test
```

On a normal Android development machine (Android SDK + network access), the whole project builds
with:

```
./gradlew assembleDebug
./gradlew :core:test
```

`minSdk 26`, `compileSdk 34`, Kotlin 1.9.24, Jetpack Compose (Material3), Room, DataStore.
