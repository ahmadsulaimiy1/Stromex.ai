# SAJJIL™

An AI-assisted voice recording, enhancement and mastering studio for Android, purpose-built for
Qur'an recitation, Nasheed, lectures, khutbahs, podcasts and voiceover work.

This repository is being built in phases against the SAJJIL product vision, which describes a
multi-year product surface. Rather than stub all of it, each phase builds a **smaller set of
things for real** — genuine DSP, genuine tests, a coherent architecture — and leaves the rest as
an explicit, documented roadmap.

- **Phase 1 — DSP Foundation Layer:** the core signal-processing engine, recording pipeline, and
  the six primary screens.
- **Phase 2 — World-Class Audio Intelligence Layer:** pre-recording acoustic intelligence, a
  professional spectrogram, echo removal, voice restoration, USB microphone support,
  reference-track mastering, an Echo Score, batch Qur'an production, a plugin architecture, and
  the Royal Navy Deep identity.
- **Phase 3 — Intelligence & Production Ecosystem**: explicitly *not* more filters —
  per-Surah progress tracking and take-version management (the "killer feature"), continuous live
  recording guidance, seven genuinely-distinct flagship mastering chains, one-click adaptive
  mastering, A/B/C instant comparison, executive-level library analytics, and a formal design
  system.
- **Phase 4 — Flagship Platform & Speech Intelligence** (this pass): a Production Readiness Center
  (a single 0–100 score plus a concrete checklist — missing ayat, clipping, noise, loudness
  consistency, metadata, naming collisions), a rule-based Project Assistant, and — the phase's
  non-negotiable requirement — real offline speech recognition and text-to-speech built on
  Android's own platform APIs, wrapped in a new **Voice Studio** workflow. See "Most important
  instruction" below for how this phase was scoped against a much larger wishlist.

## Modules

- **`core`** — pure Kotlin/JVM, zero Android dependencies, fully unit tested (**135 tests**).
  Every DSP algorithm, acoustic analysis, Qur'an production-suite logic, the recording
  mode/voice-profile/microphone presets, WAV I/O, loudness analysis, batch processing, executive
  analytics, production readiness, the project assistant, transcript search, and the plugin
  architecture all live here — the parts actually verified in this sandbox.
- **`app`** — the Android application (Jetpack Compose + Material3). Wires `core`'s logic into a
  live `AudioRecord` capture chain, a Room-backed recording library, WAV/AAC export, and fourteen
  screens (Record, Enhance, Master, Archive, Qur'an Studio, Surah Project, Batch Production,
  Comparison Lab, Executive Analytics, Production Readiness, Voice Studio, Speech & Language
  Packs, Dashboard, Settings).

`core` is verified in this environment with `gradle :core:test` (no Android SDK required — see
"Building" below for why `app` couldn't be compiled here). `app` was written carefully against the
same API surfaces but has **not** been compiled or run on-device in this session; treat it as a
strong draft to build and smoke-test on a real checkout.

## Most important instruction for this phase

The Phase 3 brief was explicit: *"Do not chase hundreds of effects. Focus on making SAJJIL the
easiest professional Qur'an and voice-production platform in the world. Every feature should help
users produce cleaner, clearer, more beautiful recordings with fewer steps."* Concretely, that
shaped three decisions:
- **Qur'an targeting moved to the front of Record**, not after. Set a Surah/Ayah range before
  hitting record and the take is tagged automatically on save — no separate trip to Qur'an Studio
  to tag it afterward.
- **Enhance/Master results can be saved back to the library** as alternate takes on the same
  Surah/Ayah range, which is what makes take-version management, Executive Analytics, and the
  Comparison Lab actually have real data to work with instead of being disconnected demos.
- **Adaptive Mastering is a toggle, not a wizard** — flip it on, and content classification +
  chain selection happens in one pass inside the existing Master flow.

## How Phase 4 was scoped

Phase 4 arrived as three stacked directives: a 10-item flagship-platform wishlist, then a
"non-negotiable" offline speech/TTS requirement stated to supersede it, then a follow-up
"permanent offline model download" directive on top of that. Chasing all of it in one pass would
have meant building thin, half-verified stubs — the opposite of every prior phase's approach. So:
- **The speech/TTS directive was treated as primary**, per its own "supersedes lower-priority
  roadmap items" framing, and built as far as it can honestly go: real Android-native
  `SpeechRecognizer`/`TextToSpeech` integration, a full Voice Studio workflow, capability
  detection, and a Speech & Language Packs settings screen. The directive's second tier — a
  downloadable SAJJIL-branded model — is architecturally reserved but not implemented, for the
  same reason Phase 3 didn't implement transcription: no way to source or verify a real ASR/TTS
  model in this sandbox. See [`docs/SPEECH_INTELLIGENCE.md`](docs/SPEECH_INTELLIGENCE.md).
- **From the 10-item wishlist, two items were built for real**: the Production Readiness Center
  and the Intelligent Project Assistant — both cheap to build honestly on top of Phase 3's
  `SurahProgressCalculator`/`JuzProgressCalculator`/`AnalyticsCalculator`/`AudioQualityScorer`, and
  both non-generative/rule-based, matching the phase's own "no fabricated AI claims" principle.
- **The rest of the wishlist was scoped out explicitly, not silently dropped** — see "Deliberately
  out of scope" below: the Mushaf/Archive visual browser, the Brand Identity Package (logo assets),
  Performance Certification (needs a real device), and PDF/XLSX report export (needs dependencies
  this sandbox can't fetch or verify).

## What's real in `core` (not stubs)

### Phase 1 — DSP Foundation
- **`BiquadFilter`** — RBJ Audio EQ Cookbook peaking/shelf/low-pass/high-pass filters.
- **`ParametricEqualizer`** — 4-band tone control and a full 31-band ISO graphic EQ, with every
  fixed/parametric band clamped below Nyquist.
- **`Compressor`**, **`Limiter`/`LoudnessMaximizer`**, **`NoiseGate`**, **`DeEsser`** — RMS
  feed-forward compression, lookahead brickwall limiting, Tajweed-safe gating, dynamic sibilance
  control.
- **`FFT`** — iterative radix-2 Cooley-Tukey, forward/inverse.
- **`SpectralNoiseReducer`** — real STFT spectral subtraction (Boll 1979).
- **`LoudnessAnalyzer`** — peak/RMS/dynamic-range/noise-floor and a simplified BS.1770-style LUFS.
- **`WavIO`/`WavStreamWriter`** — full PCM16/PCM24/Float32 WAV read/write with a streaming writer.
- **`RecordingMode`** and **`QuranMetadata`** (114 Surahs, 30 Juz boundaries).

### Phase 2 — Audio Intelligence
- **`AcousticAnalyzer`** — blind RT60 estimation, clipping-risk detection, a proximity heuristic,
  plain-language pre-recording recommendations.
- **`Spectrogram`/`SpectrogramAnalyzer`** — calibrated time × frequency dB matrix + loudness
  history.
- **`Dereverberator`** — RT60-informed spectral-subtraction dereverberation.
- **`Declipper`/`AudioRestoration`** — cubic-Hermite clip reconstruction, declip → denoise →
  level-rescue pipeline, damage scoring.
- **`ReferenceMatcher`** — 1/3-octave spectral-envelope matching against a reference take.
- **`MicrophoneProfile`** — generic *character* correction curves, not fabricated per-brand data.
- **`AudioQualityScorer`** Echo Score, **`plugin/`** architecture, **`batch/BatchProcessor`**.

### Phase 3 — Intelligence & Production Ecosystem
- **`quran/SurahProgress.kt`** (`SurahProgressCalculator`) — the Qur'an Production Suite's core
  algorithm: merges every recorded take's ayah range, reports exactly which ayahs are still
  missing ("you've recorded 1–40 and 45–60, ayahs 41–44 and 61–88 are left"), and an
  ayah-count-weighted average quality score across takes.
- **`quran/QuranMetadata.juzSpan`** + **`JuzProgressCalculator`** — a Juz frequently starts partway
  through one Surah and ends partway through another; this computes the exact multi-Surah segments
  each of the 30 Juz spans and checks *every* segment is fully recorded before calling a Juz
  complete — not just "some recording exists somewhere in it." Verified with a seamlessness test
  across all 30 Juz boundaries.
- **`analysis/LiveDirector`** — the Intelligent Recording Director: a fast (no-FFT), continuous
  peak/RMS pass over a rolling window, producing "lower gain by 3 dB" / "levels look good, ready to
  record" guidance a few times a second — the live counterpart to `AcousticAnalyzer`'s deeper
  one-shot Room Check.
- **`modes/VoiceProfile`** — renamed and re-built into seven Haramain-inspired flagship chains
  (Haramain Broadcast, Makkah Studio, Madinah Studio, Qari Prestige, Lecture Authority, Royal
  Podcast, Executive Voice), each with its own custom EQ *curve* (not just gain offsets on shared
  points) plus distinct compressor knee/ratio and limiter drive — verified sonically distinct from
  each other by a pairwise RMS-difference test, not just distinctly labeled.
- **`dsp/AdaptiveMasteringEngine`** — measures pause structure, autocorrelation-based pitch
  movement, dynamic range, and spectral tilt to classify a take (Recitation/Lecture/Nasheed/Speech)
  and build a mastering chain automatically. An honest heuristic — see "On honesty" below.
- **`analysis/AnalyticsCalculator`** — Executive Analytics: recording hours, distinct Surahs
  recorded, true Juz-completed count (via `JuzProgressCalculator`), ayah-weighted average quality,
  an improvement trend (recent-window vs. prior-window average score), library size, storage usage.

### Phase 4 — Flagship Platform & Speech Intelligence
- **`readiness/ProductionReadinessCalculator`** — the Production Readiness Center's core algorithm:
  aggregates missing-ayah coverage (via `SurahProgressCalculator`), clipping, low noise scores,
  cross-take loudness inconsistency (standard deviation across integrated LUFS), missing
  Surah/Ayah/title metadata, overlapping-range duplicate takes, and title collisions into one
  0–100 score plus a severity-ranked issue list (`"Production Readiness: 94/100"`). A heuristic
  aggregator over numbers computed elsewhere, not a re-analysis of audio itself.
- **`assistant/ProjectAssistant`** — the Intelligent Project Assistant: turns
  `SurahProgress`/`JuzProgress`/`ExecutiveAnalytics` into plain-sentence insights ("112 of 114
  Surahs recorded, remaining: 2 Juz and 15 Surahs", "quality in Al-Mulk is below your average,
  consider re-recording it"). Every rule is arithmetic over an existing score — nothing here is
  generated that a screen couldn't already show on its own; it's non-generative by design, per the
  phase's own instruction.
- **`speech/TranscriptSegment`/`Transcript`/`TranscriptSearchEngine`** — the transcript data model
  and search, including Arabic diacritic-insensitive matching (harakat/tashkeel are stripped
  before comparing, so a query typed without diacritics still matches recognizer output that
  includes them, and vice versa).

### Bugs found and fixed by the test suite
Three genuine bugs surfaced across the phases — proof the tests are pulling their weight:
1. **Phase 1:** spectral-subtraction noise reduction reconstructed audio incorrectly near buffer
   edges (dividing by a near-zero window-sum). Fixed via zero-padding before framing.
2. **Phase 2:** `ParametricEqualizer.basic()`'s fixed 9 kHz treble shelf exceeded Nyquist at lower
   capture sample rates (e.g. 16 kHz), producing an unstable filter pole that blew the signal up to
   `NaN` within a few hundred samples. Fixed by clamping every EQ frequency below Nyquist.
3. **Phase 3:** `AdaptiveMasteringEngine`'s pause detector used a noise-floor-percentile threshold
   that degenerated on a signal with little level variation (e.g. a sustained tone with no real
   silence) — nearly every frame sat close to that floor, so the whole signal was misclassified as
   "pause." Caught by a test asserting a melodic sweep should show *more* pitch variability than a
   monotone tone (it showed zero for both). Fixed by anchoring the threshold to the *median* frame
   level instead of a low percentile, which stays meaningful even without real silence in the
   buffer.

### On honesty: "AI" naming vs. what's implemented
The spec calls these features "AI Acoustic Intelligence," "AI Echo Removal," "Intelligent
Recording Director," "Adaptive Mastering." What's implemented is classic acoustics, DSP, and
feature-based heuristics — blind RT60 estimation, spectral-subtraction dereverberation/noise
reduction, autocorrelation pitch tracking, threshold-based pause detection — not trained models.
`AdaptiveMasteringEngine` in particular: it cannot tell Qur'an recitation from any other
rhythmically-paused speech in a language it doesn't parse. It measures acoustic features and maps
them to the closest flagship profile, which is a helpful starting point a user can always override
in Master, not an infallible content classifier. `MicrophoneProfile` ships generic character
curves, not measured per-brand hardware data. Offline speech recognition and TTS are implemented
for real this phase, but as a wrapper around Android's own platform services, not a bundled
SAJJIL model — see [`docs/SPEECH_INTELLIGENCE.md`](docs/SPEECH_INTELLIGENCE.md) for exactly what
that means and what's still not implemented (a downloadable SAJJIL-branded model, and any cloud
fallback). Voice Studio's transcript confidence is shown as whatever the recognizer reports, never
presented as certainty — and nothing here claims automatic Qur'anic recitation accuracy.

## What's in `app`

- **Qur'an Production Suite**: set a Surah/Ayah target before recording (auto-tags on save); the
  **Surah Project** screen shows live progress, exactly which ayahs are missing, and lets you
  browse every recorded *version* of a given ayah range with a star to mark the primary take and
  per-take notes.
- **Intelligent Recording Director**: continuous live guidance (`LivePreviewMonitor` +
  `LiveDirector`) shown on the Record screen whenever the mic is live but not yet recording, plus
  the deeper one-shot **Room Check** (`AcousticProbeRecorder` + `AcousticAnalyzer`) for
  echo/noise/clipping analysis and a one-tap "use the suggested profile."
- USB/wired/Bluetooth input-device picker (`AudioInputDevices`) and a microphone character profile
  picker, both wired into the live capture chain.
- `SAJJIL Enhance`: spectral noise reduction at four strengths, A/B preview, and **Save to
  Library** to file the result as an alternate take.
- `SAJJIL Master`: seven flagship Voice Profiles *or* one-tap **Adaptive Mastering**
  (auto-detects content and builds the chain), optional damage repair, echo removal, reference-take
  matching, Executive Dashboard scores including Echo Score, a spectrogram and loudness history,
  export to WAV/AAC, and **Save to Library**.
- `SAJJIL Archive`: searchable (title, notes, Surah/Ayah tags) Room-backed library, favorites,
  delete, per-recording Dashboard. Transcript search now exists too — see Voice Studio below.
- **Batch Production**: master an entire tagged selection (a Surah, a Juz, the whole library) in
  one pass.
- **Comparison Laboratory**: load up to three takes into slots and switch playback between them at
  the same elapsed position — genuine position-preserving A/B/C, with an honest caveat about the
  small gap a source switch introduces (documented in `ComparisonPlayer`).
- **Executive Analytics**: recording hours, Surahs recorded, true Juz completed, average quality,
  improvement trend, library size, storage usage — computed from real persisted scores (Dashboard
  and Master now write `studioReadinessScore` back to the library instead of leaving it null
  forever).
- **Design system**: `SajjilColorTokens`/`SajjilSpacing`/`SajjilRadius`/`SajjilElevation`/
  `SajjilFonts` formalize the Royal Navy `#082A66` + Premium Gold + Platinum White + Obsidian Black
  palette and an "executive sans + Arabic companion" typography role split — see the font honesty
  note in `DesignTokens.kt` for why the actual typefaces resolve to the platform default rather
  than a fabricated downloadable-fonts certificate.
- Nine luxury Material3 themes, **Royal Navy Deep** as flagship default, `GlassCard` for restrained
  glassmorphism on Executive surfaces specifically.
- **Production Readiness Center**: a "Run Readiness Check" pass that reads every primary Qur'an
  take's actual audio (not a cached composite score) for clipping and noise, plus missing-ayah
  coverage, loudness consistency, and metadata/naming checks — one score
  (`"Production Readiness: 94/100"`) and a severity-ranked issue list, with the Project Assistant's
  insights surfaced on the same screen.
- **Voice Studio**: live offline speech-to-text (Arabic or English) via Android's own recognizer,
  with a simultaneous reference-audio capture, search across every saved transcript
  (diacritic-insensitive for Arabic), and text-to-speech readback — record, transcribe, search,
  and listen without leaving the screen.
- **Speech & Language Packs** (in Settings): per-language offline recognition/TTS status, checked
  fresh each time rather than assumed, an honest explanation of the three-tier fallback hierarchy,
  and buttons that open the real Android system settings to install a language pack — SAJJIL
  cannot install one itself, so it doesn't pretend it can.

### Deliberately out of scope for this pass

- FLAC / MP3 / OGG / OPUS / ALAC / AIFF export, video-audio extraction — unchanged from Phase 2.
- Hardware acceleration — investigated in Phase 2, still not implemented; see
  [`docs/HARDWARE_ACCELERATION.md`](docs/HARDWARE_ACCELERATION.md).
- A downloadable SAJJIL-branded offline speech/TTS model, and any cloud-based speech fallback —
  see [`docs/SPEECH_INTELLIGENCE.md`](docs/SPEECH_INTELLIGENCE.md) for why (same reasoning as
  hardware acceleration: nothing to bundle here that could be verified). Android's own offline
  speech services are implemented and real.
- Recitation *sessions* as a separate tracked entity — deliberately not built; Recording Notes +
  Surah Project progress covers the same need with one fewer concept for the user to manage,
  matching Phase 3's "fewer steps" instruction.
- Real per-microphone-model AI calibration, voice cloning protection, a DAW/mixer/plugin
  marketplace (the plugin architecture itself is real), multi-track recording, cloud sync.
- Truly gapless (sample-accurate, zero-gap) A/B switching in the Comparison Lab — today's version
  stops and restarts at the matched position, not a simultaneous dual-source mix.
- **Flagship Qur'an Archive** (Mushaf/Surah/Juz visual browser, completion map) — Surah Project and
  Executive Analytics already surface this data; a dedicated Mushaf-style visual browser is a UI
  investment, not a data problem, and wasn't built this pass to keep the speech directive primary.
- **Brand Identity Package** (logo system, app icon, splash mark, dark/light variants) — this is
  graphic-design asset production, not something to fabricate as placeholder files; needs a real
  designer or image-generation pass, not code.
- **Performance Certification** (processing speed, memory, battery, startup time dashboard) — same
  reasoning as Hardware Acceleration: these are real-device measurements. Nothing runs in this
  sandbox to measure honestly, so nothing is claimed.
- **PDF/XLSX production reports** — needs a document-generation dependency this sandbox has no
  network path to fetch or verify; the same data (hours, sessions, quality, completion) is already
  real and visible in Executive Analytics and Production Readiness today.
- **Enterprise Metadata Engine** as a separate system — `RecordingEntity` already carries Surah,
  Ayah range, Juz, timestamps, readiness scores, and notes; a distinct metadata layer would
  duplicate it for no new capability.

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
