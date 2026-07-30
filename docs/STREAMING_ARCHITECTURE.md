# Streaming Architecture Investigation: Can One Mic Capture Fan Out to Everything?

Phase 6 asked directly: *"investigate whether Android's audio pipeline can
be redesigned so a single microphone capture fans out to recording, live
transcript, quality analysis, and waveform."* This is that investigation.
Short answer: **half of this is already true and now more fully built out;
the other half is a hard platform ceiling, not a design problem SAJJIL can
architect its way around.**

## Fan-out point 1: `AudioRecordEngine` — real, and now extended

`AudioRecordEngine` was already a fan-out point before this phase: its
`while (_isRecording.value)` loop reads one `AudioRecord` buffer at a time,
runs it through the DSP chain, and from that single pass already produced
two outputs — the WAV file (`WavStreamWriter`) and the live level meter
(`RecordingLevel`). Phase 6 added two more consumers of that same loop at
essentially no new capture cost, because the audio is already being
iterated sample-by-sample for the DSP chain:

- **`waveformHistory`** — a rolling buffer of recent peak levels, for a
  live scrolling waveform view (`LiveWaveformView`).
- **`clippingDetected`** — flips true the moment any buffer touches the
  same clipping threshold `AudioQualityScorer` uses, surfaced immediately
  on the Record screen instead of only after the take is analyzed.

This is genuine fan-out, not a simulation of it: one `AudioRecord` session,
one processing loop, multiple independent consumers reading from it. A
future phase could add more consumers the same way — e.g. a lightweight
running noise-floor estimate — since the marginal cost of one more
computation per already-iterated sample is small.

## Fan-out point 2: `SpeechRecognizer` — a hard platform wall

This is the piece that does **not** redesign away. `android.speech.
SpeechRecognizer.startListening(Intent)` does not accept externally
captured audio — it owns its own capture session internally (its own
`AudioRecord`/`MediaRecorder.AudioSource` under the hood, run by the
recognizer service, not by SAJJIL). The public API surface —
`SpeechRecognizer`, `RecognitionListener`, `RecognitionService`,
`RecognizerIntent` — has no method to hand it a buffer, a stream, or an
existing `AudioRecord` instance instead of letting it record. The one
audio-adjacent callback that does exist, `RecognitionListener.
onBufferReceived(ByteArray)`, is one-way and read-only — Voice Studio
already uses it (Phase 4) to *tap* what `SpeechRecognizer` is hearing for
a reference WAV, but there is no equivalent to *feed* it anything.

This is consistent across the platform's design intent, not an oversight:
the recognizer service typically wants exclusive, low-latency control of
capture for its own echo-cancellation and endpointing, which is part of
why voice-input APIs across mobile platforms are generally exclusive-mic
by design. It's a ceiling this sandbox — or any app without a private ASR
engine — cannot design around.

## What this means for "one experience" (Priority 1)

Record (`AudioRecordEngine`, owns the mic via raw `AudioRecord`) and Voice
Studio (`SpeechRecognizer`, owns the mic itself) are two different
pipelines **because they are built on two different, mutually exclusive
Android capture APIs** — not because SAJJIL chose to keep them separate.
Merging them into a single button has exactly two honest paths, both
already ruled out for reasons documented elsewhere in this project:

1. Make the *studio* take use `SpeechRecognizer`'s own capture so
   transcription and recording share one session — but that means every
   recording drops to whatever format/quality the recognizer captures at
   (observed ~16kHz mono, undocumented as a guaranteed contract), which
   is a real fidelity regression for a platform whose whole premise is
   studio-quality Qur'an recitation capture.
2. Bundle a private ASR engine SAJJIL feeds `AudioRecordEngine`'s own
   buffers to directly, bypassing `SpeechRecognizer` — this is exactly
   the Priority-6 "Download Once" model this sandbox has no way to
   source, bundle, or verify (see `docs/SPEECH_INTELLIGENCE.md`).

Neither is implemented, for the same honesty reasons already established
across this project. What's real instead: two purpose-built pipelines,
each fanning out for real within its own capture session — Record for
studio-quality takes with a live waveform and clipping warning, Voice
Studio for live-transcribed sessions with a reference clip. A future
*sequencing* idea for a real device to try — not built here, and worth
flagging as a roadmap idea rather than a claim of what exists — is
presenting the two as one guided flow ("record with live transcription,
then optionally re-take at full studio quality") rather than pretending
they can run simultaneously on one mic session.

## Background Intelligence (Priority 2) is a more tractable version of "no waiting"

The concurrent, non-mic-contended part of the "unified pipeline" ask is
already achievable and is what Phase 6 actually built: every save path
(Record, Enhance/Master save-to-library, Voice Studio) now triggers
`RecordingAutoAnalyzer` in the background the moment a take is saved,
instead of a recording sitting at a permanent null quality score until
someone opens its Dashboard. This is real background intelligence, just
scoped to what doesn't require the mic to still be open.
