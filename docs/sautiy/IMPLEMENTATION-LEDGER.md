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

## Verified on a running Android — 24 instrumented tests, all passing

`AudioRecord`, `AudioTrack` and `MediaCodec` have no meaningful stand-in on the JVM, so every
claim about them is earned here: the CI emulator job installs the APK, launches it, and then
runs the instrumented suite. **All 24 pass**; the task fails on a single failing test, so a
green job is every test passing.

| Phase | What the device confirmed |
|---|---|
| **A — recording** | The microphone opens and reports no failure; frames arrive and reach the waveform callback; the file on disk is a real WAV whose header agrees with what capture reported; **the file is complete and readable while recording is still running** — the crash-recovery guarantee observed rather than argued; pause stops promptly and stays stopped, and resume continues the same take; a second take opens after the first is stopped, which is the only way a leaked `AudioEffect` ever shows itself |
| **B — playback** | Playback starts and the head advances; a take recorded on the device plays back on it; playback through a Voice Space does not stall and changing the space mid-playback does not stop it; **starting and immediately stopping six times over does not take the process with it** |
| **MP3** | **The encoder is in the APK and loads** — asserted, not skipped when absent. Android's own `MediaExtractor`/`MediaCodec` — the code every other application uses to open an audio file — reports `audio/mpeg`, the right rate and channel count; the duration survives within 150 ms declared *and* decoded; the file decodes to real audio rather than silence; the ID3v2 synchsafe size lands exactly on an MPEG frame sync; 44.1 and 48 kHz in mono and stereo all round-trip; the file survives being handed to another application as a `content://` URI; two minutes encodes with monotonic progress in under 30 seconds |
| **Latency** | **Measured, not asserted.** The clock starts on the call a tap makes and stops when the playhead moves — which only happens once a block has been accepted by `AudioTrack`, so it times audio genuinely leaving the application. The median of five runs on a five-minute recording is inside the constitution's 100 ms tap-to-audible budget; starting deep inside a long recording costs no more than starting at the top; the largest Voice Space does not cost the instant start; and opening a five-minute recording and hearing it is under a second, with the peaks built afterwards rather than on the way |
| **E — export** | Every format the panel offers writes bytes and reports the length it wrote; an exported WAV re-probes as the same project; progress runs 0→1 without going backwards; M4A comes back from MediaCodec; a format with no encoder refuses loudly rather than writing a broken file |

**What the device tests found, which is the point of them.**

`lame_encode_buffer_interleaved` is documented for stereo, and its `num_samples` parameter means
samples *per channel* — it reads `num_samples × 2` shorts whatever the encoder is configured for.
Handing it mono audio makes it read twice the data that exists: a native overrun that killed the
process with no Java exception, no stack and nothing to act on. Mono now goes through
`lame_encode_buffer`. The bridge also refuses an out-of-range read rather than performing it, so
a wrong frame count is a returned error code with a sentence attached instead of a dead
application.

Two earlier failures in the same sequence were harness faults, not product faults, and are
recorded as such: the device-test job rebuilt the app without the LAME sources, so it tested a
build that was not the one shipped; and `Mp3Encoder` discarded the reason `System.loadLibrary`
failed, making "library missing" and "library failed to link" indistinguishable.

And earlier still:

`AudioTrack.write` with `WRITE_BLOCKING` does not respond to coroutine cancellation — it
returns when the track is paused, flushed or drained, and not before. `stop()` cancelled the
render loop and released the track while a write was still in flight, the native pointer went
away underneath it, and the uncaught `IllegalStateException` **killed the process**. Stopping
playback at that moment is the ordinary case, not an edge, and no amount of reading the code
was going to surface it. The ordering is now pause → flush → cancel, with the loop owning the
release on its way out.

A second defect fell out of the same reading: a cancelled loop invoked `onFinished`, so
stopping playback reported reaching the end and moved the transport to STOPPED behind the back
of whatever had just stopped it.

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

The emulator has no microphone in front of it and no speaker behind it. So the device tests
establish that the platform objects open, that frames flow, that files are written and reopen
correctly, and that nothing crashes — but **not** that the captured audio sounds like the room,
that playback is audible, that the twelve spaces sound like their names, that the waveform draws
under a finger, or that a gesture selects what the user meant. Those need a human with a phone.

The Voice Studio's *arithmetic* is proven on the JVM to a measured standard; its *sound* is a
judgement only a listener can make.

A CI emulator is also slower and jerkier than a phone, so the latency figures are a floor rather
than a measurement of real hardware. A failure there would be real anywhere; a pass means the
budget is met on something slower than the target device.

| Item | Why | Where recorded |
|---|---|---|
| **On-device transcription** | Depends on a platform recogniser; where none is present the capability is absent rather than degraded. | Ch. 11.4 |
| **Qur'an Studio project store** | Model complete; persistence and panel not written. | Ch. 12 |
| **Spectrogram rendering** | The FFT is implemented and tested; the drawing is not written. | Ch. 15.2 |
| **Media session / lock screen** | Not implemented. | Ch. 8.7 |
| **Settings and About screens** | Not built. | Ch. 4.1.2, 22.3 |
| **Instrumented UI tests** | Require a device. | Ch. 19.7 |

---

## Voice Space 2.0 — what was fixed, and what is still unknown

**Four causes of an artificial-sounding room, each removed and each measured:**

| Cause | What was done | How it is checked |
|---|---|---|
| Static comb delays ring at fixed frequencies — the metallic sound that makes a recording seem to *have reverb on it* | Every comb's read position wanders ~½ ms on a slow, mutually detuned LFO, fractionally interpolated | Spectral crest inside narrow sub-bands is lower with the tail moving than still |
| Thin echo density is heard as separate ticks | Diffusion drives both the number of all-pass sections and their coefficient | Tail density rises measurably with the control |
| Low frequencies turn a large room to mud | The reverb send is high-passed at 190 Hz; the dry voice keeps its weight | 70 Hz reaches the room at under half the level of 1 kHz |
| The room masks consonants | Speech priority ducks the wet by the dry envelope, so the room recedes while a word is spoken and blooms in the gaps | The room is measurably quieter during speech and still present in the gaps |

**Two real gain bugs, both of which would have made tuning by ear impossible:**

The all-pass sections were Freeverb's simplified form, which is **not** all-pass — its gain rises
with the feedback coefficient, so raising diffusion raised the volume and no two presets could be
compared. Replaced with the textbook unity-gain Schroeder structure. Removing that accidental
gain then exposed a second: the comb-bank normalisation used the textbook formula, which ignores
that the damping filter sits *inside* the loop and cuts effective feedback everywhere except DC.
On a damped hall it understated the loop gain by around 17 dB.

**Four of the measurements were themselves wrong** and had to be fixed before they measured
anything — recorded because they are the kind of error that produces confident nonsense: crest
over one wide band confuses ringing with tone (a darker tail reads as more metallic); RMS across
windows of different lengths measures how long the tail is, not how loud it is; and ducking
measured on the mixture confuses "the room got quieter" with "everything got quieter".

**Fifteen spaces, three modes.** Natural, Studio and Immersive are one control over *how much*
room, separate from *which* room. Immersive raises the mix and also raises the floor under speech
priority, so turning the room up cannot quietly cost intelligibility.

**Not tuned by ear, and not claimed to be.** The numbers are derived from the acoustics of the
places the presets are named for — a plastered room absorbs less treble than a carpeted one, a
larger space answers later and needs more diffusion to stop sounding grainy, a longer tail needs
more speech priority to stay intelligible. That reasoning gets a preset close. Only listening
gets it right, and no one has listened to these yet. **Hear every space** exists for exactly that:
it loops one five-second passage, starts on the original, and changes the room underneath the
same phrase every five seconds, so the whole roster is one tap and seventy-five seconds instead
of fifteen separate manual comparisons.

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
