# SAJJIL — What is verified, and what is not

This document exists so nobody has to guess which claims in
[`15-SAJJIL-ARCHITECTURE.md`](15-SAJJIL-ARCHITECTURE.md) are backed by evidence.

Three tiers are used throughout:

- **Verified** — proven by an automated test that runs on every push, or by an independent tool.
- **Compiles** — the code builds and is reviewed, but its runtime behaviour has not been exercised.
- **Not implemented** — deliberately absent, with the reason stated.

---

## Verified

### The audio engine

142 unit tests in `core-audio`, run by CI on every push and by `./gradlew :core-audio:test` locally.
No Android SDK is needed. They cover:

| Area | What is actually asserted |
|---|---|
| FFT | Round-trip accuracy to 1e-9; a pure tone lands in a single bin with negligible leakage. |
| Filter design | Every design's magnitude response, measured: −3 dB at cutoff, peaking filters delivering their requested gain to within 0.05 dB, shelves reaching their gain, notches attenuating >40 dB at centre while leaving 200 Hz untouched. |
| Filter processing | A running filter's measured output matches its designed response to within 0.3 dB. |
| Compressor | Below threshold is bit-identical; above threshold the gain reduction follows the ratio; a soft knee acts below the threshold where a hard knee does not; makeup gain applies. |
| Limiter | Nothing exceeds the ceiling at four ceiling settings; quiet material passes through unchanged apart from the look-ahead delay; a 0.98 transient is contained. |
| Gate | Speech passes, noise in the gaps drops below −56 dB, and hysteresis prevents chatter at the threshold. |
| De-esser | Sibilant band drops >40% while the fundamental retains >80% — i.e. it is not ducking broadband. |
| **Loudness** | **K-weighting coefficients reproduce BS.1770-4's tabulated 48 kHz values to 1e-12.** EBU Tech 3341 case 1 (−23 dBFS → −23.0 LUFS) and case 2 (−33 → −33.0) pass to ±0.1 LU. Loudness tracks amplitude dB-for-dB. Readings agree across 44.1 and 48 kHz. Gating makes a recording that is half silence read the same as continuous speech. |
| True peak | A full-scale sine reads ≈0 dBTP; inter-sample overshoot invisible to sample-peak measurement is detected. |
| Normalisation | Four delivery targets hit to ±0.3 LU; the true-peak ceiling wins when it conflicts with the target; gain is bounded; silence is left alone. |
| Noise reduction | Speech survives while off-band noise drops >30%; the noise floor in pauses halves; length is preserved exactly for four input lengths; zero strength is a bit-exact bypass. |
| Hum removal | 50 Hz fundamental and its third harmonic removed while a 500 Hz voice retains >85%; 50 vs 60 Hz detection is correct; detection declines to guess on clean audio. |
| De-click / de-clip | Injected clicks are repaired to within 0.2 amplitude; clean audio is left alone; flat tops are reconstructed; unclipped audio is bit-identical. |
| Reverb | Impulse produces a decaying tail; longer decay settings produce longer tails; zero amount is a bit-exact bypass; the FDN stays bounded under 8 s of sustained input; all seven ambience profiles are stable. |
| **Edit engine** | **Undo restores audio bit-for-bit** (`maxAbsoluteDifference == 0.0`), including through a six-step mixed chain of delete, insert, paste, gain and fade, and back again via redo. Split markers and the selection track the audio they refer to across edits. History is bounded. Joins are softened enough that the largest sample-to-sample step across a splice is under 0.05. |
| Enhancement chain | All five presets and all 35 preset × voice-style combinations produce finite audio within full scale; the source buffer is never modified; presets never leave peaks above their ceiling; progress is monotonic; loudness is stable when a recording is enhanced twice. |
| Quality analysis | A clean recording scores ≥70; a noisy one scores lower and names noise; clipping is flagged as a problem; continuous material is not misread as noise; enhancement raises the score of a poor recording. |
| WAV | Round-trips at 16/24/32-bit and float; 24-bit is >100× more accurate than 16-bit; float is exactly lossless; unknown chunks are skipped; a truncated file still yields its audio; overshoot clamps rather than wraps. |
| **FLAC** | **Bit-exactness verified by libsndfile**, an independent implementation — see below. |

### FLAC, verified against an independent decoder

A self-round-trip would pass just as happily if the bitstream were wrong in a self-consistent way.
So `FlacFixtureTest` writes five `.flac` files exercising different coding paths, and
`tools/verify-flac.py` decodes them with **libsndfile** and compares against the source PCM.

Result on the current build:

```
OK   bursts.flac:  153600 frames x 1ch bit-exact,  12% of WAV size
OK   noise.flac:    48000 frames x 1ch bit-exact, 100% of WAV size
OK   partial.flac:   8329 frames x 1ch bit-exact,  18% of WAV size
OK   stereo.flac:   48000 frames x 2ch bit-exact,  28% of WAV size
OK   tone.flac:     96000 frames x 1ch bit-exact,  22% of WAV size

All 5 fixtures decoded bit-exactly by libsndfile
```

"Bit-exact" means every sample matched, not that they were close. This runs in CI.

### The build

CI assembles the debug APK, runs the app module's unit tests, and runs lint on every push, and
uploads the APK as a build artifact.

Observed on the `claude/sajjil-ux-design-directive-7sdieb` branch:

| Run | Commit | Engine tests | FLAC vs libsndfile | `assembleDebug` | App unit tests | Lint | Conclusion |
|---|---|---|---|---|---|---|---|
| 1 | `19b57a0` | pass | pass | **fail** — 9 Kotlin errors | not reached | not reached | failure |
| 2 | `5423f9e` | pass | pass | **pass** (3 m 46 s) | **pass** | superseded | cancelled |
| 3 | `f431820` | pass | pass | **pass** (4 m 02 s) | **pass** | pass | **success** |

Run 1's failures were two real defects, both fixed in `5423f9e`: `animateFloat` was used without
its import, and `AnimatedVisibility` inside a `Box` nested in a `Row` resolved to the `RowScope`
overload, which cannot be called with an implicit receiver there.

**Run 3 is green end to end** — both jobs, every step. It produced two artifacts:

```
sajjil-debug-apk     20,592,169 bytes   (~19.6 MB installable APK)
sajjil-lint-report       49,639 bytes
```

The `Upload APK` step is configured with `if-no-files-found: error`, so the run could only have
succeeded if a real APK was present. **The application builds and packages.**

(Run 2 was cancelled part-way through lint by the push that created run 3; its `assembleDebug` and
unit-test steps had already passed, which is why they are recorded above.)

### App module

`FormatTest` covers the formatting shared by every screen — durations, the recording timer, spoken
durations for screen readers, file sizes, relative dates, remaining-recording-time phrasing, and
the cases that exist to avoid embarrassing output (a negative duration never renders as
`-1:-30`; unmeasured loudness shows a dash rather than a fabricated number; silence reads as
`−∞ dB`).

This is the only part of the app module under test. Everything else in it depends on Android
platform services — see the next section.

---

## Compiles, but not exercised at runtime

Everything in this section is code that builds and has been reviewed, but whose behaviour depends on
Android platform services that no automated test in this project touches. **None of it has been run
on a physical device.**

| Area | What is unverified |
|---|---|
| Microphone capture | `AudioRecord` configuration, the capture thread's timing, and behaviour when the system starves it. Buffer sizing (4× the reported minimum) is a considered choice, not a measured one. |
| Crash recovery | The header-repair logic is unit-tested against synthetically truncated files. Recovery from a *real* process kill mid-recording has not been observed. |
| Foreground service | Notification actions, behaviour across Android's foreground-service restrictions, and survival under Doze. |
| Lock-screen controls | Media3 session integration, audio focus, headset buttons. |
| MediaCodec export | AAC and M4A encoding paths. The ADTS header construction in particular is written from the specification and has not been played back. |
| MP3 availability | The `MediaCodecList` query is straightforward, but no device has been checked. |
| Room | Schema generation and queries compile; no migration has been written or tested because there is only version 1. |
| Compose UI | Every screen renders in principle; none has been seen. Gesture handling on the waveform — pinch-zoom interacting with drag-select in particular — is the most likely place for a real problem. |
| Performance | No claim is made about frame timing, startup, or memory on a mid-range device, because none has been measured. The design choices made *for* performance (visible-range-only waveform extraction, gated true-peak measurement, SQL-side sorting) are reasoned, not benchmarked. |

The honest summary: **the audio is proven, the app around it is not.** A device test pass is the
next thing this project needs, and no amount of code review substitutes for it.

---

## Not implemented

### MP3 export on devices without an MP3 encoder

Android guarantees an MP3 **decoder** on every device. It does not guarantee an **encoder**, and
AOSP does not ship one. Some vendor devices expose one; most do not.

The options were:

1. Bundle LAME through the NDK. Adds a native toolchain, an LGPL dependency, and several MB to the
   APK, for a format that M4A matches in size and compatibility.
2. Offer MP3 and let it fail on devices that cannot do it.
3. Query the device and only offer what it can produce.

The app does (3). `ExportFormat.availableOn()` checks `MediaCodecList`, and where MP3 is absent the
export sheet says so in a sentence and points to M4A. The architecture takes a `LameMp3Encoder`
without restructuring if bundling LAME is ever chosen.

Option (2) was rejected outright: shipping a format button that fails on most devices is exactly the
"claim capabilities that are not implemented" failure the brief rules out.

### Transcription

The Assistant screen describes what transcription would use — Android's `SpeechRecognizer`, which is
offline on devices with a language pack and online otherwise. **The recognition itself is not
wired up.** The database schema, the search join and the Library's transcript indicator are all in
place and tested; the engine call is not.

This is stated on the screen rather than implied. No button offers transcription and then fails.

### Multi-layer editing

The reference interface shared during this work shows layered tracks ("Add Layer", "Vocals 1"). The
edit engine is single-buffer. Multi-track is a different data model — not a feature to bolt onto
`EditSession` — and adding a half-working version would have compromised the single-track editing
that does work.

### Cloud enhancement and online transcription

Offline-first is implemented; the optional cloud path is not. There is no network code in the app at
all, and no permission for it in the manifest.

### Signed release builds

CI produces a **debug-signed APK** (~19.6 MB), which installs on a device but is not a release
build. Release signing needs a keystore, which is credential material and does not belong in a
repository. `app/build.gradle.kts` falls back to debug signing so a release build does not fail;
wiring a real keystore is a deployment step.

---

## Reproducing the verification

```bash
cd apps/sajjil

# The audio engine. No Android SDK required.
./gradlew :core-audio:test

# FLAC bit-exactness against libsndfile.
pip install soundfile
./gradlew :core-audio:test --tests '*FlacFixtureTest*'
python3 tools/verify-flac.py

# The APK. Requires the Android SDK.
./gradlew :app:assembleDebug
```

The engine tests and the FLAC check are the two worth running before trusting any change to audio
behaviour. Both are fast.

---

## A note on the development environment

This app was built in an environment where `dl.google.com` is blocked by network policy — which is
both the Android SDK and the AndroidX/AGP Maven repository. The Android module therefore could not
be compiled locally at any point during development; it is built and tested only by CI, on a runner
that has the SDK.

That constraint shaped the module split for the better: `core-audio` was made platform-free partly
so that the part of the system where correctness is hardest to eyeball could be developed against a
real, fast test loop rather than against a compiler that was not available.
