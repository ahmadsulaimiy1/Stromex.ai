# Chapter 7 — Recording Experience

> One tap. From cold. Every time.

---

## 7.1 The Promise

| Promise | Standard |
|---|---|
| Taps from cold launch to capturing | **1** |
| Tap to first sample committed | ≤ 300 ms |
| Decisions required before recording | **0** — no name, no format, no destination |
| Audio lost if the process is killed | ≤ 2 s, and offered back on next launch |
| Screen off, 90 minutes, in a bag | Survives |

There is no welcome screen, no onboarding, no account and no arm step. The app opens into the
workspace with the record control already under the thumb.

## 7.2 Permission

The microphone is requested **at the moment of the first record tap** — never on launch.

A permission dialog before the user has expressed any intent is a wall in front of a product
they have not seen, and it is the most common reason a first-time user never reaches the record
control at all. One line in SAUTIY's own words precedes the system dialog: *"SAUTIY needs the
microphone to record. Nothing is uploaded."*

If permission is refused, the workspace does not simply fail. It states the fact, the
consequence, and offers the single control that fixes it (chapter 3.2.6).

## 7.3 The Signal Path

| Decision | Choice | Why |
|---|---|---|
| Source | `VOICE_PERFORMANCE` | Least platform processing, lowest latency. `MIC` gives whatever the vendor decided; `VOICE_RECOGNITION` is tuned for speech engines, not for listening. |
| Platform noise suppression | **Off** | Tuned for telephony, not defeatable once applied, and sits ahead of SAUTIY's chain |
| Platform echo cancellation | **Off** | Same |
| Platform AGC | **Off** | Same — and it would fight SAUTIY's compressor |
| Working format | 32-bit float, planar | Chapter 7's engine format |
| Storage format | WAV, 16 or 24-bit | The only common container that can be written incrementally and safely |

A user who turns noise reduction off must actually get no noise reduction. Leaving the
platform's on would mean they were still getting somebody's.

## 7.4 Durability

Capture writes continuously and forces bytes to disk every **1 second**.

Because the capture format is WAV written incrementally, **the file on disk is a complete,
playable recording at every moment** — not a fragment needing repair. A process kill costs at
most the samples since the last flush. On next launch, any take on disk that no project claims
is offered back, once, with its real duration stated. Fragments under a second are discarded
silently rather than spending one of the four permitted interruptions on nothing.

## 7.5 What The User Sees While Recording

| Region | Shows |
|---|---|
| Status rail | Project, quality, **minutes of storage remaining**, and the word "Clipped" if it has |
| Canvas | The live waveform in **ember**, the timer in ember, the level meter |
| Layer strip | The layer being captured into |
| Context bar | Marker · Layer · Input · Noise — **and nothing destructive** |
| Transport dock | Unchanged, as always |

Storage is stated in **minutes at the bitrate actually in use**, never in megabytes free.
Nobody can convert 412 MB into "will this last the lecture?"

## 7.6 The Meter Tells The Truth

Instant attack, 20 dB/second release, peak hold with a 1.2 s dwell. Both peak and RMS are
shown: peak is what will clip, RMS is what it will sound like, and a meter showing only one of
them is lying by omission. Clipping is counted at capture, where it happens, and reported —
it cannot be undone later, so the user must see it now.

## 7.7 Pause, Resume, Discard

- **Pause** stays inside the same take. Resuming continues the same file.
- **Discard take** exists only while paused — never while recording — so it cannot be a slip.
- Losing the microphone to another app **pauses**; it never stops. The take survives and the
  user resumes when the other app lets go.

## 7.8 Layers

A layer cannot be added mid-take: it would require a second simultaneous capture stream, which
the hardware does not provide. Layers are added between takes, and each take lands as a clip on
the selected layer at the end of what is already there.

---

### Implementation

| Clause | Code |
|--------|------|
| 7.1 Transitions | `sautiy-core/.../record/RecordingSession.kt` (`RecordingMachine`) |
| 7.4 Durability | `CapturePolicy`, `WavCodec.StreamingWriter`, `CrashRecovery` |
| 7.3 Signal path | `app/.../record/AudioCapture.kt` |
| 7.5 Foreground survival | `app/.../record/RecordingService.kt` |
| 7.2 Permission timing | `app/.../SautiyActivity.kt` |
| 7.6 Meter | `app/.../ui/components/Meters.kt` |

**Verified by test:** recording begins in one tap from idle; losing the microphone pauses rather
than stops; illegal transitions are refused rather than half-performed; the flush cadence is
inside the constitutional loss ceiling; storage becomes critical at exactly two minutes and not
sooner; a sub-second fragment is not offered for recovery.
