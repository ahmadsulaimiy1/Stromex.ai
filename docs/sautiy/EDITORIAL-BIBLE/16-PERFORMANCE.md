# Chapter 16 — Performance Standards

> Every budget here is a ceiling, not a target. Exceeding one is a defect with a bug number,
> not a trade-off to be discussed.

---

## 16.1 The Budgets

| Measure | Ceiling |
|---|---|
| Cold start to armed workspace | 700 ms |
| Tap to first sample captured | 300 ms |
| Tap to audible playback | 100 ms |
| Frame budget during live recording | 16.67 ms — 60 fps, zero dropped frames on the waveform |
| Panel open to interactive | 220 ms, with no spinner inside it |
| Audio lost to a process kill | 2,000 ms |
| Capture flush interval | 1,000 ms — half the loss ceiling, leaving room for one in-flight buffer |
| Capture buffer | 20 ms |
| Playback output buffer | 40 ms |
| In-memory audio before streaming | 128 MiB |

These live in code as `PerformanceBudget`, are read by the engine to size its buffers, and are
asserted by test — including that the flush cadence is arithmetically inside the loss ceiling.

## 16.2 The Rules That Make Them Achievable

**Nothing expensive happens on the interaction path.** Waveform column resolution, pyramid
level choice and formatting are done before the draw phase runs; the draw loop reads
pre-computed float arrays and does nothing else.

**Nothing allocates per audio buffer.** The capture read loop reuses one array for the life of
the recording. A ninety-minute lecture at 20 ms per read is 270,000 buffers, and a per-read
allocation is 270,000 chances for a collection to land inside a read.

**Nothing decodes a whole file.** Playback, the waveform and the editor all read ranges. A
two-hour project opens as fast as a two-minute one.

**Nothing waits on analysis.** Chapter 1.3.4, enforced structurally: the playback state holds no
reference to any analysis result.

**Nothing blocks on I/O in a composable.** File probing, rendering and encoding run on the IO
dispatcher; the UI observes state.

## 16.3 Memory

- Audio is 32-bit float, planar. Above the 128 MiB ceiling — about 12 minutes of 48 kHz mono —
  the engine reads from disk in windows rather than growing the heap.
- Peaks cost about 8 MB per hour at the base bucket size, which is why a whole recording's
  waveform can live in memory while its audio does not.
- A timeline is metadata: a few hundred bytes per clip. That is what makes 200 history states
  affordable (chapter 9.5).

## 16.4 Battery

- **Partial wake lock only.** The CPU must run to service the audio callback; the screen must
  not, because a lecture recorded with the display on ends when the battery does.
- No polling. No background work while idle. No periodic jobs. No network — there is no network
  permission.
- The waveform stops redrawing when the workspace is not visible. Capture continues; drawing
  does not.
- DSP runs on demand, not continuously. A preset is applied when asked and rendered when played.

## 16.5 Storage

- Capture is written once, straight through, with no intermediate copy.
- Editing writes nothing at all until export (chapter 9.1).
- Export staging is pruned after 24 hours.
- Remaining time is computed from the bitrate actually in use, never estimated.

## 16.6 Offline

Every core capability — capture, playback, the full edit engine, the entire DSP chain, WAV and
FLAC export — runs with no network, no account and no server. This is not a degraded mode; it
is the only mode. The application has no internet permission.

## 16.7 Measuring

A budget nobody measures is a wish. Before release:

- Cold start, tap-to-record and tap-to-play measured on a mid-range device, not a flagship.
- A 90-minute capture run to completion with the screen off, with the file verified afterwards.
- Frame timing captured during live recording with the waveform at full width.
- A forced process kill mid-recording, and the recovery verified.

---

### Implementation

`sautiy-core/.../SautiyConstitution.kt` (`PerformanceBudget`),
`record/RecordingSession.kt` (`CapturePolicy`), `play/PlaybackSession.kt` (`PlaybackPolicy` —
which checks its own buffer against the tap-to-audible budget at class initialisation, so an
incompatible change fails at load rather than in the field).
