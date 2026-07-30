# SAJJIL™

An AI-assisted voice recording, enhancement and mastering studio for Android, purpose-built for
Qur'an recitation, Nasheed, lectures, khutbahs, podcasts and voiceover work.

This repository is being built in phases against the SAJJIL product vision, which describes a
multi-year product surface (dozens of AI features, nine luxury themes, dedicated Qur'an tooling,
executive dashboards, a plugin ecosystem). Rather than stub all of it, each phase builds a
**smaller set of things for real** — genuine DSP, genuine tests, a coherent architecture — and
leaves the rest as an explicit, documented roadmap.

- **Phase 1 — DSP Foundation Layer:** the core signal-processing engine, recording pipeline, and
  the six primary screens.
- **Phase 2 — World-Class Audio Intelligence Layer** (this pass): pre-recording acoustic
  intelligence, a professional spectrogram, echo removal (dereverberation), voice restoration
  (declipping), USB microphone support, reference-track mastering, an Echo Score, batch Qur'an
  production, a plugin architecture, and a UI pass toward the Royal Navy Deep identity.

## Modules

- **`core`** — pure Kotlin/JVM, zero Android dependencies, fully unit tested (**65 tests**).
  Every DSP algorithm, acoustic analysis, the recording mode/voice profile/microphone presets,
  WAV I/O, loudness analysis, batch processing, the plugin architecture, and Qur'an reference
  metadata (Surah/Ayah/Juz) all live here — and are the parts actually verified in this sandbox.
- **`app`** — the Android application (Jetpack Compose + Material3). Wires `core`'s DSP into a live
  `AudioRecord` capture chain, a Room-backed recording library, WAV/AAC export, USB/input-device
  selection, and seven screens (Record, Enhance, Master, Archive, Qur'an Studio, Batch Production,
  Settings) plus an Executive Dashboard.

`core` is verified in this environment with `gradle :core:test` (no Android SDK required — see
"Building" below for why `app` couldn't be compiled here). `app` was written carefully against the
same API surfaces but has **not** been compiled or run on-device in this session; treat it as a
strong draft to build and smoke-test on a real checkout.

## What's real in `core` (not stubs)

### Phase 1 — DSP Foundation
- **`BiquadFilter`** — RBJ Audio EQ Cookbook peaking/shelf/low-pass/high-pass filters.
- **`ParametricEqualizer`** — 4-band tone control and a full 31-band ISO graphic EQ, with every
  fixed/parametric band clamped below Nyquist (see "Bugs found" below for why that matters).
- **`Compressor`** — RMS-detector feed-forward compressor, soft knee, auto makeup gain.
- **`Limiter` / `LoudnessMaximizer`** — lookahead brickwall peak limiter for loudness maximization.
- **`NoiseGate`** — envelope-follower gate with hold/hysteresis (Tajweed-safe: long hold avoids
  clipping soft letters).
- **`DeEsser`** — dynamic sibilance-band peaking filter.
- **`FFT`** — iterative radix-2 Cooley-Tukey, forward/inverse.
- **`SpectralNoiseReducer`** — real STFT spectral subtraction (Boll 1979) with Hann windows and
  overlap-add reconstruction.
- **`LoudnessAnalyzer`** — peak/RMS/dynamic-range/noise-floor and a simplified BS.1770-style
  integrated loudness (LUFS) estimate.
- **`WavIO` / `WavStreamWriter`** — full PCM16/PCM24/Float32 WAV read/write, including a streaming
  writer so multi-hour recordings never have to sit fully in memory.
- **`RecordingMode`** (Qur'an Studio, Imam Al-Haram, Lecture, Nasheed, Podcast) and **`VoiceProfile`**
  (Haramain, Madinah, Makkah, Studio Qari, Lecture Hall, Broadcast, Podcast) — concrete DSP-chain
  presets, not just labels.
- **`QuranMetadata`** — all 114 Surahs with ayah counts and the 30 Juz start boundaries.

### Phase 2 — Audio Intelligence
- **`AcousticAnalyzer`** (AI Acoustic Intelligence) — blind RT60 estimation via free-decay
  detection in the envelope (Ratnam et al.-style), clipping-risk detection, a direct-to-reverberant
  proximity heuristic, and plain-language recommendations before the user commits to a take.
- **`Spectrogram` / `SpectrogramAnalyzer`** — time × frequency dB matrix (single-sided, calibrated
  so a full-scale tone reads ~0 dBFS) for a professional spectrogram/waterfall view, plus a
  loudness-history time series.
- **`Dereverberator`** (AI Echo Removal) — RT60-informed spectral-subtraction dereverberation
  (Lebart/Boucher/Denbigh-style), targeting late-reflection "boominess" in mosque/hall recordings.
- **`Declipper` / `AudioRestoration`** (AI Voice Restoration) — cubic-Hermite clip reconstruction,
  a declip → denoise → level-rescue restoration pipeline, and a 0–100 damage score.
- **`ReferenceMatcher`** (Reference Mastering Engine) — 1/3-octave spectral-envelope matching
  against a reference take, building a 31-band correction EQ.
- **`MicrophoneProfile`** — generic *character* correction curves (Phone Built-in, USB Condenser —
  Bright, USB Dynamic — Warm, Wireless Lavalier, Flat/Reference), not fabricated per-model curves
  (see "On honesty" below).
- **`AudioQualityScorer`** — now includes an **Echo Score** (0–100 from RT60), folded into Studio/
  Broadcast/Archive Readiness only when a measurement is actually available (null, not a fake 100,
  otherwise).
- **`plugin/AudioEffectPlugin`, `PluginRegistry`, `BuiltinPlugins`** — the plugin architecture
  requested "ahead of a full marketplace": a narrow, real contract (describe yourself, produce a
  processor), with SAJJIL's own gate/compressor/limiter/de-esser/EQ registered as the first five
  plugins, proving the contract is load-bearing rather than a paper design.
- **`batch/BatchProcessor`** (Batch Qur'an Production) — masters a list of files with one chain
  config in one pass (an entire Surah, Juz, or full library selection), per-item pass/fail
  reporting, one item's failure never aborting the batch.

### Bugs found and fixed by the test suite
Two genuine bugs surfaced while building this, in both phases — proof the tests are pulling their
weight rather than just padding a count:
1. **Phase 1:** the first spectral-subtraction implementation reconstructed audio incorrectly near
   buffer edges (dividing by a near-zero window-sum), audible as retained noise a casual listen
   might miss. Fixed via zero-padding before framing.
2. **Phase 2:** `ParametricEqualizer.basic()`'s fixed 9 kHz treble shelf exceeds Nyquist at lower
   capture sample rates (e.g. 16 kHz), which — per the RBJ cookbook's own assumptions — produces an
   unstable filter pole and blows the signal up to `NaN` within a few hundred samples. Caught when
   `BatchProcessor`'s test threw "Cannot round NaN value"; root-caused by bisecting the processing
   chain stage by stage. Fixed by clamping every fixed/parametric EQ frequency below Nyquist
   (`ParametricEqualizer`, `DeEsser`), with a regression test that reproduces the exact failing
   configuration.

### On honesty: "AI" naming vs. what's implemented
The spec calls these features "AI Acoustic Intelligence," "AI Echo Removal," "AI Voice
Restoration," "SAJJIL AI Studio." What's implemented is classic, well-understood **acoustics and
digital signal processing** — blind RT60 estimation, spectral-subtraction dereverberation,
spectral-subtraction noise reduction, interpolation-based declipping — not trained models. These
are honestly effective for what they target (steady-state noise, statistically-modeled late
reverberation, short clip runs) and honestly limited where a neural model would do better (complex
non-stationary noise, discrete echo/slap-back, heavily/long-clipped material with no surviving
waveform to reconstruct from). `MicrophoneProfile` ships generic character curves, not measured
per-model frequency-response data for the named hardware brands — SAJJIL has no lab measurements
of them, and shipping fabricated "exact" curves would be actively misleading. On-device trained-
model noise/echo removal remains a roadmap item, not something silently claimed.

## What's in `app`

- Live recording through `AudioRecordEngine`: mic capture → optional microphone-character EQ →
  gate → EQ → de-esser → compressor → loudness maximizer → streamed straight to WAV.
- **Room Check**: a 3-second pre-recording probe (`AcousticProbeRecorder` + `AcousticAnalyzer`) on
  the Record screen, surfacing noise/echo/clipping guidance and a one-tap "use the suggested
  profile" before the take even starts — the single highest-leverage feature in this phase, per
  the brief's own framing ("capture the cleanest possible source before enhancement").
- Input-device picker (`AudioInputDevices`) for USB/wired/Bluetooth microphones, wired to
  `AudioRecord.setPreferredDevice`, plus the microphone character profile picker.
- `SAJJIL Enhance`: pick a recording, run spectral noise reduction at Light/Moderate/Strong/Extreme,
  A/B preview original vs. enhanced.
- `SAJJIL Master`: apply a Voice Profile, optionally repair damage (declip/denoise/rescue level),
  remove echo (dereverberate using a fresh RT60 estimate), match tonal balance to another take,
  see Executive Dashboard scores (now including Echo Score) plus a spectrogram and loudness
  history, export to WAV or AAC/M4A.
- `SAJJIL Archive`: searchable Room-backed library, favorites, delete, tap-through to a
  per-recording Executive Dashboard (loudness metrics, 0–100 readiness scores including Echo
  Score, and a spectrogram).
- `SAJJIL Qur'an Studio`: tag any recording with Surah/Ayah range (Juz derived automatically),
  browse the resulting Qur'an library, and jump into **Batch Production** to master an entire
  selection (a Surah, a Juz, the whole tagged library) in one pass.
- Nine luxury Material3 themes — **Royal Navy Deep** (new flagship default: deep navy `#082A66`
  with restrained gold accents, Vision 2030/NEOM-publication styled) plus Royal Gold, Midnight
  Black, Emerald Prestige, Sapphire Blue, Makkah Night, Madinah Green, Platinum White, Executive
  Dark — persisted via DataStore. A `GlassCard` component applies restrained glassmorphism to the
  Executive Dashboard specifically, not as the default card style everywhere.
- Export: WAV (any bit depth) and AAC/M4A via `MediaCodec`/`MediaMuxer` — no third-party codec
  dependency.

### Deliberately out of scope for this pass

The spec's own **"Future Roadmap"** and **"Future AI Features"** sections are treated as out of
scope, plus a few practical additions:

- FLAC / MP3 / OGG / OPUS / ALAC / AIFF export — these need licensed or NDK-cross-compiled codecs
  (`libFLAC`, `libmp3lame`, `libopus`); WAV and AAC/M4A cover the two formats Android's SDK supports
  natively.
- Trained-model noise/echo removal, voice cloning protection, an AI mastering *assistant* (as
  opposed to the rule-based mastering chains shipped today), true per-microphone-model AI
  calibration, room correction, a DAW/mixer/plugin *marketplace* (the plugin *architecture* is
  real — see above), transcription, speaker separation, multi-track recording, cloud sync.
- Hardware acceleration (NDK/SIMD/NEON/GPU) — investigated, not implemented; see
  [`docs/HARDWARE_ACCELERATION.md`](docs/HARDWARE_ACCELERATION.md) for the findings and recommended
  path. Short version: profile on real hardware first, NEON-accelerate the STFT hot path if it's
  actually the bottleneck, skip GPU for the real-time path entirely.
- Video-audio extraction (MP4/MOV/MKV/AVI) — same MediaCodec path as AAC export, just not wired up
  yet.
- Real-time (continuous, during capture) spectrogram — today's spectrogram renders from a completed
  recording (Master/Dashboard), not a live streaming view during capture.

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
