# SAUTIY™ — Implementation Ledger

**This document does not round up.**

Chapter 20.8 requires that the record distinguishes what is *built*, what is *tested*, what is
*verified by an executed test run*, and what is *source-complete but not executable in the
current build environment*. Overstating would be worse than saying nothing, because the next
person builds on it.

Last updated against commit on branch `claude/sautiy-editorial-bible-app-nhdku6`.

---

## The Build Environment, Stated First

This work was produced in a sandbox whose network policy blocks `dl.google.com` and
`maven.google.com`. Maven Central is reachable; the Google Maven repository is not.

**Consequence:** the Android SDK, AndroidX, Jetpack Compose and the Android Gradle Plugin could
not be downloaded, so the `:app` module **has never been compiled**. Nothing in the Android
layer below is claimed as verified.

**Response:** the architecture was chosen so this constraint costs as little truth as possible.
Every product rule, the whole audio engine, every codec, the entire DSP chain and both transport
state machines live in `sautiy-core`, a pure-JVM module that compiles and tests on a bare JDK.
That is why 248 tests could actually be run.

---

## Verified — tests written and executed, passing

| Area | Tests | What was actually measured |
|---|---|---|
| **Ch.1 no-placeholder clause** | 6 | Source scan fails the build on placeholder tokens; proven not to false-positive on `toDouble` and proven to catch real ones |
| **Ch.2 colour** | 7 | WCAG contrast for every text and status role against every legal surface, both themes |
| **Ch.2/5/6 design system** | 10 | 4 dp grid, tabular figures, line heights, Qur'anic leading, motion tiers, no overshoot, meter ballistics |
| **Ch.3/4 workspace law** | 26 | Asserted over **224 enumerated states**: one destination, immovable dock, ≤6 context tools, exactly one primary action, no destructive control while recording, no panel over the dock, 3-word labels, errors with remedies, exactly four interruptions |
| **Ch.7 PCM/format** | 15 | All six encodings round-trip within a quantisation step; +1.0 never wraps negative; capture hot path matches the byte path |
| **Ch.7 WAV** | 14 | Chunk-tolerant reading; **after every flush the file is a complete playable WAV**; a process kill recovers every flushed frame; an unpatched header still yields all audio |
| **Ch.7/8 transport** | 22 | Both state machines; illegal transitions refused; flush cadence inside the loss ceiling; storage critical at exactly two minutes; crash-recovery fragments not offered |
| **Resampling** | 12 | 20 kHz → 32 kHz alias below −60 dBFS; per-tier rejection floors; no edge fade; channel independence |
| **Ch.15 waveform** | 13 | Decimation preserves extremes exactly; the loudest sample survives full zoom-out; incremental build matches one-shot |
| **Ch.9 edit engine** | 35 | Invariants unconstructable when violated; ripple law; 5 ms seam fades; equal-power crossfades hold power where linear provably dips; per-sample fade ramps; exact undo/redo/time-travel |
| **Ch.9.7 silence** | 10 | Threshold follows the room; sub-350 ms pauses preserved as rhythm; padding symmetric |
| **Ch.10 DSP** | 40 | 4:1 means 4:1; continuous knee; limiter holds its ceiling and stays time-aligned; de-esser cuts 7 kHz >3 dB while moving a 300 Hz vowel <1 dB; every preset finite, unclipped, hitting its loudness target within 2 LU |
| **Ch.10.4 loudness** | 15 | **−20 dBFS 1 kHz reads −23.0 LUFS at 44.1, 48, 32 and 96 kHz**; 20 s silences do not shift programme loudness; relative gating; true peak exceeds sample peak on inter-sample material |
| **Ch.14 FLAC** | 12 | **Bit-exact round trips** through SAUTIY's own decoder on tones, noise, stereo, partial blocks and alternating full-scale; 2 s silence under 2 KB; speech under 75% of WAV |
| **Ch.14 export registry** | 5 | Unregistered formats fail loudly; platform encoders register without core knowledge |

**Total: 248 tests, 0 failures.** Reproduce with `cd apps/sautiy && gradle :sautiy-core:test`.

---

## Source-complete but NOT compiled or run

Everything in `apps/sautiy/app/`. Written as production source, reviewed by hand, **never
compiled**, because the Android toolchain is unreachable here.

| Component | State |
|---|---|
| `SautiyWorkspace` — the one canvas, four regions, panel host | Source complete |
| `WaveformCanvas` — drawing, gestures, semantics | Source complete |
| `TransportDock` — the immovable five | Source complete |
| `PanelHost` — all twelve panels | Source complete |
| `Meters` — level meter, quality gauge, storage | Source complete |
| `SautiyIcons` — 28 icons drawn on the 24 dp grid | Source complete |
| Theme — colour, type, motion, shape bound to the core | Source complete |
| `AudioCapture` — `AudioRecord`, platform processing disabled | Source complete |
| `RecordingService` — foreground service, wake lock | Source complete |
| `AudioPlayer` — `AudioTrack`, timeline rendering | Source complete |
| `PlatformEncoders` — AAC/ADTS via `MediaCodec` | Source complete |
| `WorkspaceViewModel` | Source complete |
| Manifest, resources, adaptive icon, splash, strings | Source complete |

**Expect compilation errors on first build.** Roughly 4,000 lines of Compose and Android code
have never seen a compiler. The correct next step on a machine with an SDK is
`gradle :app:assembleDebug` and a fix-forward pass.

---

## Not implemented, stated plainly

| Item | Why | Where recorded |
|---|---|---|
| **MP3 export** | Android's `MediaCodec` cannot encode MP3. A real implementation needs the NDK with LAME, or ~1,500 entries of exactly-correct Huffman table data for a Layer III encoder — worth building correctly rather than half-building. The format is **absent from the panel** rather than present and broken. | Ch. 14.6 |
| **On-device transcription** | Depends on a platform recogniser. The interface and the panel exist; where no recogniser is present the capability is absent rather than degraded. | Ch. 11.4, 11.7 |
| **Qur'an Studio project store** | The model and the chapter are complete; the persistence layer and its panel UI are not written. | Ch. 12 |
| **Library persistence** | The panel renders from state; the on-disk project store is not written. | Ch. 13 |
| **Spectrogram rendering** | The FFT is implemented and tested; the drawing is not written. | Ch. 15.2 |
| **Media session / lock screen** | Declared in chapter 8.7; not implemented. | Ch. 8.7 |
| **SAF document picker wiring** | The export contract and encoders exist; the picker launch is not wired. | Ch. 14.3 |
| **Settings and About screens** | Chapters written; the two full destinations are not built. | Ch. 4.1.2, 22.3 |
| **Instrumented UI tests** | Require a device. | Ch. 19.7 |

---

## Chapter Status

| # | Chapter | Written | Implemented | Verified |
|---|---|---|---|---|
| 01 | Constitution | ✓ | ✓ | ✓ |
| 02 | Brand Identity | ✓ | ✓ | ✓ colour/type; icon & splash source-only |
| 03 | Human Experience | ✓ | ✓ | ✓ |
| 04 | Information Architecture | ✓ | ✓ | ✓ |
| 05 | Design System | ✓ | ✓ | ✓ tokens; components source-only |
| 06 | Interaction Design | ✓ | ✓ | ✓ motion law; gestures source-only |
| 07 | Recording Experience | ✓ | ✓ | ✓ engine/policy; device layer source-only |
| 08 | Playback Experience | ✓ | ✓ | ✓ engine/policy; device layer source-only |
| 09 | Editing Studio | ✓ | ✓ | ✓ |
| 10 | Studio Processing | ✓ | ✓ | ✓ |
| 11 | Intelligence | ✓ | partial | ✓ quality analysis; transcription absent |
| 12 | Qur'an Studio | ✓ | partial | model only |
| 13 | Library | ✓ | partial | panel source-only |
| 14 | Export & Sharing | ✓ | partial | ✓ WAV/FLAC/registry; MP3 absent |
| 15 | Visual Analytics | ✓ | partial | ✓ waveform/meters/loudness; spectrogram absent |
| 16 | Performance | ✓ | ✓ | budgets asserted; field measurement pending a device |
| 17 | Accessibility | ✓ | ✓ | ✓ contrast; screen-reader pass pending a device |
| 18 | Component States | ✓ | ✓ | ✓ error type; states source-only |
| 19 | Engineering Standards | ✓ | ✓ | ✓ |
| 20 | Quality Assurance | ✓ | ✓ | ✓ build-enforced rules |
| 21 | Developer Documentation | ✓ | ✓ | — |
| 22 | About SAUTIY | ✓ | partial | screen not built |

---

## The Honest Summary

**What exists and is proven:** a complete, tested audio engine — capture policy, WAV, FLAC
(encoder *and* decoder), band-limited resampling, a non-destructive sample-accurate edit engine
with real undo, a full DSP chain measured to ITU-R BS.1770-4, and the entire product law of the
Editorial Bible expressed as code that fails the build when violated. 248 tests.

**What exists and is unproven:** the Android application — around 4,000 lines of Compose and
platform code implementing the one-canvas workspace, written carefully but never compiled.

**What does not exist:** MP3 encoding, transcription, persistence, and the items listed above.

The right next step is an Android SDK, `gradle :app:assembleDebug`, and a fix-forward pass —
then the device checklists of chapter 20.
