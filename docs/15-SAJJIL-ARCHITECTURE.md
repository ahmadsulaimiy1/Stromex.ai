# SAJJIL — Architecture

SAJJIL is a native Android audio recording, editing, enhancement and export application. It lives
in [`apps/sajjil`](../apps/sajjil) and is independent of the StromeX web client and API — it shares
the repository, not the runtime.

This document describes what was built and why the structure is the way it is. What is *not* built,
and why, is in [`16-SAJJIL-VERIFICATION.md`](16-SAJJIL-VERIFICATION.md). Read that one before
relying on any capability claimed here.

---

## The journey the app is built around

Every screen exists to serve one step of a single path:

```
Record  →  Review  →  Edit  →  Enhance  →  Export  →  Archive
```

The five sections map onto it directly. **Record** is the first step. **Studio** is the middle four
— review, edit, enhance and export all happen against one waveform, without changing screens.
**Library** is the archive. **Qur'an** is a project structure layered over the same recordings.
**Assistant** reports on what the app has measured across the archive.

There is no sixth section, and nothing nests more than one level deep.

---

## Modules

```
apps/sajjil/
├── core-audio/      Pure Kotlin. No Android dependency. All signal processing and editing.
└── app/             Android: Compose UI, capture, playback, persistence, export.
```

### Why `core-audio` has no Android in it

The split is not organisational tidiness. `core-audio` contains every claim the product makes about
audio quality — the loudness meter that decides an export's level, the noise reduction that decides
what a recording sounds like, the edit engine that decides whether undo loses your work. If those
lived in the app module they could only be tested on a device or an emulator, which means in
practice they would be tested by hand, occasionally.

Because the module is platform-free, all of it runs under a plain JVM test. 142 tests execute in
about forty seconds on a laptop, including the EBU R128 loudness compliance cases and a FLAC
encoder verified against an independent decoder.

The rule is enforced by the module's dependencies: `core-audio` depends on the Kotlin standard
library and nothing else. It cannot accidentally acquire an Android import.

---

## `core-audio`

### Signal processing (`dsp/`)

| Component | Notes |
|---|---|
| `Fft` | Iterative radix-2, cached twiddle factors and bit-reversal table. |
| `BiquadDesign` | RBJ cookbook: low/high pass, band pass, notch, peaking, low/high shelf. |
| `Biquad`, `BiquadChain` | Transposed direct form II. |
| `Compressor` | Feed-forward, soft knee, channel-linked detection. |
| `Limiter` | Look-ahead brick wall with a hard ceiling clamp. |
| `NoiseGate` | Downward expander with hold and hysteresis. |
| `DeEsser` | Split-band, so it ducks sibilance and not the whole voice. |
| `SpectralNoiseReducer` | STFT spectral subtraction, automatic noise profile. |
| `HumRemover` | Notch comb at 50/60 Hz harmonics, with detection. |
| `DeClicker` | Third-difference detection, cubic Hermite repair. |
| `DeClipper` | Flat-top detection, parabolic reconstruction. |
| `WindReducer` | Cascaded high-pass scaled by strength. |
| `Reverb` | Feedback delay network with early reflections and width. |
| `StereoWidener` | Mid/side. |

Three of these are worth explaining, because the obvious implementation is wrong.

**Noise reduction estimates its profile from whole frames, not per-bin percentiles.** The tempting
approach is, for each frequency bin, to take a low percentile of its magnitude across the recording
and call that the noise floor. It fails badly: in a bin where the voice is present in every frame,
that percentile *is* the voice, and subtracting it removes exactly what the user wanted to keep. So
frames are ranked by total energy, the quietest fifth are taken to be pauses, and the profile is
their average spectrum.

That still assumes the recording *has* pauses. Continuous material — a sustained note, unbroken
recitation — has none, and its quietest frames are as loud as the rest. The estimator measures that
directly and scales its confidence to zero when it detects it, degrading to a no-op rather than
gutting a recording that was never noisy. Failing safe is the only acceptable behaviour here.

**The limiter clamps as well as attenuates.** Floating-point gain reduction alone leaves samples a
fraction above the ceiling; those wrap rather than clip when converted to integers on export, which
turns a peak into a full-scale click in the opposite direction. The clamp costs nothing and closes
the case.

**The reverb is an FDN, not a Schroeder bank.** Four delay lines of mutually prime length, mixed
through a Householder matrix, reach a dense tail with far fewer operations than a comb/allpass
chain — which matters on a phone. Early reflections are a separate multi-tap delay, because the
tail alone sounds like an effect while the tail plus early reflections sounds like a room.

### Loudness (`loudness/`)

ITU-R BS.1770-4 K-weighting, EBU R128 gating, and 4× oversampled true-peak measurement.

The K-weighting coefficients are **derived from the standard's analog prototype at the actual sample
rate** rather than hard-coded for 48 kHz. Hard-coded 48 kHz coefficients are a common bug that
silently misreports at 44.1 and 16 kHz; the test suite pins the derivation against BS.1770-4's own
tabulated values at 48 kHz to prove it.

True peak measurement only runs the interpolation filter near samples already close to the sample
peak. Running it everywhere costs 48 multiply-accumulates per sample — minutes of work on a long
recording — and an inter-sample peak cannot occur anywhere else.

`LoudnessNormalizer` reports `gainLimited` when a recording was too quiet to reach its target within
the gain ceiling. Silently missing the target and reporting success would be worse than saying so.

### Editing (`edit/`)

`EditSession` models every operation as one reversible primitive: **replace a frame range with other
audio**. Cut, delete, paste, trim, insert silence, apply a fade, run a whole enhancement chain — all
of them are that.

Two consequences follow. Undo history is proportional to what was actually edited, not to the length
of the recording, so trimming a two-hour lecture does not hold two hours of audio in memory per
step. And every effect gets undo for free without knowing that history exists.

De-click fades at edit boundaries are folded *into* the replaced range rather than applied to the
buffer afterwards. Applied afterwards they would modify audio the inverse does not hold, and undo
would silently leave faded edges behind. The test suite asserts undo is bit-exact.

### Codecs (`codec/`)

`WavReader`/`WavWriter` handle 16/24/32-bit and 32-bit float. The reader skips unknown chunks rather
than rejecting files over them, and trusts the payload over the header — a file killed mid-recording
has a stale length field and perfectly good audio, and refusing to open it would be indefensible.

`FlacEncoder` is a Kotlin FLAC encoder (constant, verbatim and fixed subframes; partitioned Rice
residuals). It is written here rather than delegated to a platform codec because Android's FLAC
encoder availability varies by device and `MediaMuxer` cannot write a FLAC container at all — the
alternative was FLAC export working on some phones and not others. It does not implement LPC
prediction, so files run 3–8% larger than reference libFLAC; they are bit-exact lossless either way,
which is the property that matters.

---

## `app`

### Recording

`AudioRecorder` captures via `AudioRecord` straight to a WAV file, writing the header first with
placeholder lengths and finalising it on stop.

That ordering is the crash-recovery design. Samples reach disk continuously; only two integers in
the header are wrong if the process dies. `AudioFileStore.repairIncomplete` rewrites them, and
`RecordingSession.recoverInterrupted` runs it at startup for anything left marked incomplete. The
user is never asked what to do about it — there is one sensible answer and it should just have
happened.

`RecordingSession` is the single process-wide owner of a take, because there is one microphone. It
deliberately outlives the activity: a rotation or a trip to another app must not end a recording.
`RecordingService` is a foreground service that keeps the microphone open and presents the
notification; it holds no audio state of its own.

Capture uses `VOICE_RECOGNITION` as its audio source and leaves the platform's noise suppression and
AGC **off** by default. Those are tuned for phone calls and fight the enhancement chain — the
platform AGC in particular pumps the level under a compressor. Recording clean and processing
deliberately produces a better result than two processors guessing at each other.

### Playback

Media3's `MediaSessionService`, which is what puts controls on the lock screen, in the notification
shade, and on headsets and watches without building each of those separately.

`PlaybackController` queues commands issued before the controller connects and replays them on
connect, so tapping play the instant a screen opens starts audio rather than dropping the tap.

### Persistence

Room, with recordings, folders, transcripts and Qur'an projects/takes. Every column is a primitive
or a `String` — no type converters, which are a recurring source of migration surprises and are not
needed here.

There is no `fallbackToDestructiveMigration`. Losing a user's recording index because a schema
changed is not an acceptable failure mode.

Search joins transcripts, so a lecture can be found by a phrase spoken inside it. Sorting happens in
SQL rather than in Kotlin so the Library stays responsive with thousands of rows.

### Export

| Format | Encoder | Availability |
|---|---|---|
| WAV | `core-audio` | Always |
| FLAC | `core-audio` | Always |
| M4A | MediaCodec AAC + MediaMuxer | Always (AAC encoder is mandated on Android) |
| AAC | MediaCodec AAC + ADTS framing | Always |
| MP3 | MediaCodec, if present | **Device-dependent** |

Android guarantees an MP3 *decoder* but not an encoder. `ExportFormat.availableOn()` queries
`MediaCodecList` and the export sheet only offers formats the device can actually produce, with a
line of explanation where MP3 is absent. See the verification document for the full reasoning.

Destinations go through Android's share sheet, which already knows about the SD card, cloud
providers and messaging apps. Reimplementing a file browser would be worse and less capable.

---

## Design system

`ui/theme` holds the palette, type scale and spacing. Three rules do most of the work:

- **One accent colour** (brass) plus **one signal colour** (record red, used nowhere else). A single
  accent is what makes a primary action unmistakable.
- **A coarse spacing scale.** Steps far enough apart that arbitrary in-between values are not an
  option; the rhythm is what reads as considered.
- **The system font.** Bundling a typeface would add weight, cost a frame on first draw, and
  override the size and family a user chose in Accessibility settings.

Dynamic colour is deliberately not used. The waveform, level meters and quality signals must mean
the same thing on every device; letting the wallpaper retint them would break the one thing this
interface has to communicate reliably.

---

## Where to look

| Concern | File |
|---|---|
| Enhancement stage order and why | `core-audio/.../chain/EnhancementChain.kt` |
| Preset definitions | `core-audio/.../chain/EnhancementSettings.kt` |
| Undo model | `core-audio/.../edit/EditSession.kt` |
| Loudness | `core-audio/.../loudness/LoudnessMeter.kt` |
| Crash recovery | `app/.../audio/RecordingSession.kt`, `app/.../data/AudioFileStore.kt` |
| Waveform gestures | `app/.../ui/components/Waveform.kt` |
| Format availability | `app/.../audio/ExportFormat.kt` |
