# SAUTIY™ — Implementation Ledger

**This document does not round up.**

Chapter 20.8 requires that the record distinguishes what is *built*, what is *tested*, what is
*verified by an executed test run*, and what is *source-complete but not executable in the
current build environment*. Overstating would be worse than saying nothing, because the next
person builds on it.

Last updated against commit on branch `claude/sautiy-editorial-bible-app-nhdku6`.

---

## The Build Environment

The development sandbox blocks `dl.google.com` and `maven.google.com`, so `:app` cannot be
compiled there. **The build was therefore moved to GitHub Actions**, whose runners ship the
Android SDK and reach Google's Maven without restriction.

`.github/workflows/sautiy-apk.yml` runs the engine tests, builds the debug APK, lints it and
uploads the artifact. That workflow is now the source of truth for anything claimed about the
Android layer.

**The APK builds.** Run 4 (`310ecfb`) — every step green:

| Step | Result |
|---|---|
| Verify the audio engine (`:sautiy-core:test`) | success, 289 tests |
| Build the debug APK (`:app:assembleDebug`) | **success** |
| Lint the Android layer (`:app:lintDebug`) | success |
| Upload artifact | `sautiy-debug-apk`, 12,923,919 bytes |

Four compile-stage defects were found and fixed to get there — two Gradle plugin-classloader
problems and two missing Compose imports. They are listed in the git history.

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
| **Ch.13 library store** | 28 | Save survives restart; rename keeps titles unique; delete goes to trash with a stated date; expired trash purges and nothing else does; atomic write leaves no temp file; a corrupt index does not take the recordings with it; file names never contain a separator or wildcard |
| **Ch.4.6 search** | 13 | Full ranking order title > tag > marker > transcript > date; transcript hits show why they matched; trashed entries never appear; "last week" excludes this week; an unrecognised phrase matches nothing rather than guessing |
| **Ch.14 export pipeline** | 12 | What is exported is what was heard (same renderer, same edits); progress is monotonic 0→1 across render/enhance/encode; encoding never reported before rendering finishes; a format that cannot carry the project rate is resampled to the nearest legal rate at or above it; clipping reported; the caller's stream is never closed |

**Total: 289 tests, 0 failures.** Reproduce with `cd apps/sautiy && gradle :sautiy-core:test`.

---

## Launches — verified on an emulator

The APK installs and **the app opens**. Run 7's smoke job booted an x86_64 emulator (API 30),
installed the APK, started the activity and checked it 20 seconds later:

```
ResumedActivity: ActivityRecord{ai.sautiy.debug/ai.sautiy.SautiyActivity t9}
SAUTIY launched, is alive, and its activity is resumed.
```

Crash buffer empty. This is now a permanent CI gate, not a one-off: every push runs it, and it
fails the build on anything in the crash buffer or if the activity is not the resumed one.

**The launch crash that reached the first APK:** `splash_background.xml` wrapped a
VectorDrawable in `<bitmap>`. That drawable was the window background, so the framework
inflated it while creating the window — before `onCreate`. It crashed on every device, every
launch, and both the compiler and lint were silent, because it is a runtime resource-inflation
failure. Fixed by using `<item android:drawable=...>`, which accepts a vector.

Everything in `apps/sautiy/app/` compiles, links, lints clean and launches. What that still does
**not** prove is that it *works*: CI has no microphone and no audio output.

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
| `FileSourceProvider` — range reads with a small LRU | Source complete |
| `Mp3Encoder` + JNI bridge + CMake (LAME) | Source complete; needs NDK |
| Manifest, resources, adaptive icon, splash, strings | Source complete |

**What remains unproven, precisely:** that recording captures audio, that playback is audible,
that the waveform draws under a finger, that edits apply, and that export writes a file another
player will open. Each needs a human with a phone. Launch stability is no longer on this list.

---

## Not implemented, stated plainly

| Item | Why | Where recorded |
|---|---|---|
| **MP3 export** | Optional native component: JNI bridge + CMake over LAME, built by the CI workflow when dispatched with `withMp3=true`. Android has no MP3 encoder, so this is the only route. The default APK ships without it, and MP3 is then absent from the export panel rather than present and broken. | Ch. 14.6 |
| **On-device transcription** | Depends on a platform recogniser. The interface and the panel exist; where no recogniser is present the capability is absent rather than degraded. | Ch. 11.4, 11.7 |
| **Qur'an Studio project store** | The model and the chapter are complete; the persistence layer and its panel UI are not written. | Ch. 12 |
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
