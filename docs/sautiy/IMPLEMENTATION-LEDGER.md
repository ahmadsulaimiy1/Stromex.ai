# SAUTIY™ — Implementation Ledger

**This document does not round up.**

The record distinguishes what is *built*, what is *tested*, what is *verified by an executed
test run*, and what is *source-complete but unproven*. Overstating would be worse than saying
nothing, because the next person builds on it.

Branch `claude/sautiy-editorial-bible-app-nhdku6`.

---

## The Build Environment

The development sandbox blocks `dl.google.com` and `maven.google.com`, so `:app` cannot be
compiled there. **The build runs on GitHub Actions**, whose runners ship the Android SDK and
reach Google's Maven without restriction. `.github/workflows/sautiy-apk.yml` runs the engine
tests, builds the debug APK, lints it, uploads the artifact, and then **installs it on an
emulator and launches it**. That workflow is the source of truth for anything claimed about the
Android layer.

---

## Verified — tests written and executed, passing

**331 tests, 0 failures.** Reproduce with `cd apps/sautiy && gradle :sautiy-core:test`.

| Area | Tests | What was actually measured |
|---|---|---|
| **Ch.1 no-placeholder clause** | 6 | Source scan fails the build on placeholder tokens; proven not to false-positive on `toDouble` and proven to catch real ones |
| **Ch.2 colour** | 7 | WCAG contrast for every text and status role against every legal surface, both themes |
| **Ch.2/5/6 design system** | 10 | 4 dp grid, tabular figures, line heights, Qur'anic leading, motion tiers, no overshoot, meter ballistics |
| **Ch.3/4 workspace law** | 26 | Asserted over **224 enumerated states**: one destination, immovable dock, ≤6 context tools, exactly one primary action, no destructive control while recording, no panel over the dock, 3-word labels, errors with remedies, exactly four interruptions |
| **Ch.7 PCM/format** | 15 | All six encodings round-trip within a quantisation step; +1.0 never wraps negative; capture hot path matches the byte path |
| **Ch.7 WAV** | 14 | Chunk-tolerant reading; **after every flush the file is a complete playable WAV**; a process kill recovers every flushed frame |
| **WAV stream reader** | 12 | Every block matches the reference reader sample for sample; reads independent of order; stale scratch bytes never leak into a short read; both edges padded; streamed peaks equal in-memory peaks exactly |
| **Ch.7/8 transport** | 22 | Both state machines; illegal transitions refused; flush cadence inside the loss ceiling; storage critical at exactly two minutes |
| **Resampling** | 12 | 20 kHz → 32 kHz alias below −60 dBFS; per-tier rejection floors; no edge fade; channel independence |
| **Ch.15 waveform** | 13 | Decimation preserves extremes exactly; the loudest sample survives full zoom-out; incremental build matches one-shot |
| **Ch.9 edit engine** | 35 | Invariants unconstructable when violated; ripple law; 5 ms seam fades; equal-power crossfades hold power where linear provably dips; exact undo/redo/time-travel |
| **Ch.9.7 silence** | 10 | Threshold follows the room; sub-350 ms pauses preserved as rhythm |
| **Ch.10 DSP** | 29 | 4:1 means 4:1; continuous knee; limiter holds its ceiling and stays time-aligned; noise profile in real signal RMS |
| **Ambience engine** | 15 | **Measured T30 matches the stated RT60 within 25% at 0.5, 1, 2 and 3 seconds**; pre-delay is a real gap and never delays the dry voice; width 0 gives one room in both ears and width 1 two; warmth cuts the 8 kHz tail by more than half while leaving 200 Hz alone; a larger room answers later; **137-frame blocks are bit-identical to one pass**; every space finite and within ±18/+6 dB of dry |
| **Voice Studio** | 30 | **Preview output is sample-identical to the render**, and identical at 97-frame blocks as at 4 096; the stages a preview cannot run are named rather than faked; each of the eight controls moves its own range >2 dB in both directions and a centred control is bit-transparent; tone provably cannot reach the compressor's detector; the de-esser cuts 7 kHz >3 dB while moving a 300 Hz vowel <1 dB; hum removal takes the fundamental *and* two harmonics >20 dB; all twelve spaces render finite and unclipped; every stated delivery standard is reached within 2 LU and every ceiling respected |
| **Ch.10.4 loudness** | 15 | **−20 dBFS 1 kHz reads −23.0 LUFS at 44.1, 48, 32 and 96 kHz**; 20 s silences do not shift programme loudness; true peak exceeds sample peak on inter-sample material |
| **Ch.14 FLAC** | 12 | **Bit-exact round trips** through SAUTIY's own decoder; 2 s silence under 2 KB; speech under 75% of WAV |
| **Ch.14 export registry** | 5 | Unregistered formats fail loudly; platform encoders register without core knowledge |
| **Ch.13 library store** | 28 | Save survives restart; delete goes to trash with a stated date; atomic write leaves no temp file; a corrupt index does not take the recordings with it |
| **Ch.4.6 search** | 13 | Full ranking order title > tag > marker > transcript > date; trashed entries never appear; an unrecognised phrase matches nothing rather than guessing |
| **Ch.14 export pipeline** | 12 | What is exported is what was heard; progress is monotonic 0→1; a format that cannot carry the project rate is resampled to the nearest legal rate at or above it |

---

## Compiles, lints and launches — verified on CI

The APK builds, lints clean, installs on an emulator and **the app opens**. The smoke job boots
an x86_64 emulator (API 30), installs the APK, starts the activity and checks it 20 seconds
later; it fails the build on anything in the crash buffer or if the activity is not the resumed
one. This is a permanent gate on every push, not a one-off.

**The launch crash that reached the first APK:** `splash_background.xml` wrapped a
VectorDrawable in `<bitmap>`. That drawable was the window background, so the framework
inflated it while creating the window — before `onCreate`. It crashed on every device, every
launch, and both the compiler and lint were silent, because it is a runtime resource-inflation
failure.

---

## Fixed under the executive reset

Each of these was a control that looked complete and carried out no work. All were found by
reading the code against the reported symptoms.

| Reported symptom | Actual cause | State |
|---|---|---|
| Enhancement is ineffective | `applyPreset()` was `_state.update { it.copy(appliedPreset = preset) }` — the card highlighted and no sample was ever processed | Applies to playback and export |
| Reverb and echo do not work | Same cause; the Space panel was a read-only list of the preset's numbers | Nine live ambience controls |
| No graphs or waveform | `openRecording()` never rebuilt the peaks, so a saved recording opened against whatever the last recording left in the builder | Streamed from the file off the main thread |
| Playback is slow | `FileSourceProvider` called `WavCodec.readRange` per block — twenty-five file opens and header walks per second of audio, on the thread feeding the speaker | One open reader per take |
| Delete and file management broken | The library panel had no rename and no delete at all | Both on the row; delete confirmed in place |
| — | `onExport` was `{}` | Runs `ExportJob`, reports progress, deletes part-written files and states failures |
| — | `onShare` was `{}` | Exports first if needed, then a `content://` URI through the FileProvider |
| — | A/B compare flipped a boolean and never told the player | Reaches the audio |
| — | Playback and export assumed mono regardless of the material | Carries the project's channel count |

**Removed rather than left in place**, per the directive: the previous `Reverb` (allocated its
comb bank per call, so it restarted the tail at every block boundary — usable offline,
impossible to preview live), `Echo`, and `StudioChain` with its nine presets. Two space engines
would be exactly the disconnected-sliders problem the reset rejects.

---

## What remains unproven, precisely

CI has no microphone and no audio output, so what a compiling, launching APK still does **not**
prove is that recording captures audio, that playback is audible, that the waveform draws under
a finger, that edits apply, or that export writes a file another player will open. Each needs a
human with a phone.

| Item | Why | Where recorded |
|---|---|---|
| **MP3 export** | Optional native component over LAME, built only when the workflow is dispatched with `withMp3=true`. Android has no MP3 encoder. The default APK ships without it, and MP3 is then absent from the export panel rather than present and broken. The native build has not yet been run. | Ch. 14.6 |
| **On-device transcription** | Depends on a platform recogniser; where none is present the capability is absent rather than degraded. | Ch. 11.4 |
| **Qur'an Studio project store** | Model complete; persistence and panel not written. | Ch. 12 |
| **Spectrogram rendering** | The FFT is implemented and tested; the drawing is not written. | Ch. 15.2 |
| **Media session / lock screen** | Not implemented. | Ch. 8.7 |
| **SAF document picker** | Export writes to app storage and shares from there; the picker is not wired, so "save to SD card" is not yet available. | Ch. 14.3 |
| **Settings and About screens** | Not built. | Ch. 4.1.2, 22.3 |
| **Instrumented UI tests** | Require a device. | Ch. 19.7 |

---

## The Voice Studio

The signal chain is fixed: `Input → Cleanup → Dynamics → Tone → Ambience → Loudness → Output`.

**Twelve spaces**, each a complete voice rather than a reverb setting: Dry Studio, Natural
Presence, Vocal Booth, Podcast Studio, Broadcast Studio, Warm Studio, Lecture Hall, Prestige
Recitation, Auditorium, Cinematic Voice, Large Hall, Majestic Recitation.

**Nine ambience controls**: amount, wet/dry mix, room size, decay time (RT60 in seconds),
pre-delay, early reflections, width, warmth, brightness.

**Eight refinement controls**, each −1 to +1 with 0 exactly transparent: clarity, warmth,
richness, presence, body, air, brightness, depth. Warmth and brightness appear in both groups
because they are not the same control — one shapes the voice, the other the room it is in.
Depth drives the room rather than the equaliser, because depth is distance and distance is a
room; with no space selected the panel says so instead of pretending.

**Two one-taps**: ✨ Enhance Voice (clean, even, clear; adds no room) and 🎙 Studio Voice (the
finished production, room and all).

**Live preview is the same processing as the export.** `render()` drives the same streaming
chain `live()` returns, so preview output is sample-identical for every setting except noise
reduction and loudness normalisation — which cannot exist under a playback callback and are
therefore named in `deferredStages` and displayed, rather than silently differing.
