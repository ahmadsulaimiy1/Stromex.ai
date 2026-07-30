# Speech Intelligence: What's Real, Updated for Phase 4

Phase 3's version of this document investigated offline transcription and
concluded, honestly, that no third-party ASR model (Whisper, Vosk, or
similar) could be sourced, bundled, or verified in this sandbox — so Phase 3
shipped title/notes/tag search instead of transcript search, and left
transcription as a documented recommendation.

Phase 4's directive asked for something different and genuinely achievable
without a bundled model: **wrap Android's own speech APIs**. That doesn't
require training or sourcing a model — `android.speech.SpeechRecognizer` and
`android.speech.tts.TextToSpeech` are public OS services. This phase does
that for real. What still isn't implemented, and why, is below.

## What's implemented this phase

- **`AndroidNativeSpeechRecognizer`** (`app/.../speech/`) — a real
  `SpeechRecognizer` + `RecognitionListener` wrapper. Requests
  `EXTRA_PREFER_OFFLINE`, taps `onBufferReceived` to simultaneously capture
  a reference WAV so a Voice Studio session doesn't need two competing
  microphone sessions (SAJJIL's own `AudioRecordEngine`, and
  `SpeechRecognizer`'s own capture, cannot both own the mic reliably).
- **`OfflineArabicRecognizer` / `OfflineEnglishRecognizer`** — named,
  stable extension points (Kotlin interface delegation over the recognizer
  above) so a future Priority-2 engine can be swapped in without touching
  anything that calls them. Today both delegate straight to Priority 1.
- **`TTSManager`** — wraps `TextToSpeech`, checks `Voice.isNetworkConnectionRequired()`
  before claiming a voice is offline, exposes rate/pitch control.
- **`VoiceCatalog`** — turns the raw voice set from a `TextToSpeech` engine
  into a sorted, human-readable list (offline voices first).
- **`AndroidSpeechBridge`** — the single place capability detection lives:
  is a recognition service installed, is a TTS engine installed, is there
  an offline voice per language. Feeds the Speech & Language Packs settings
  screen and Voice Studio's warning banner. It does **not** claim to know
  in advance whether a specific language will succeed at recognition time —
  see the limitation below.
- **`TranscriptSegment` / `Transcript` / `TranscriptSearchEngine`** (`core`,
  pure Kotlin, unit tested) — the data model transcripts are stored and
  searched with, including Arabic diacritic-insensitive matching.
  `TranscriptSegmentEntity` + `TranscriptDao` persist them (Room, DB
  version 3); `TranscriptRepository` bridges entities to the core domain
  types `TranscriptSearchEngine` operates on.
- **Voice Studio** (`ui/screens/voicestudio/`) — record → live offline
  transcription → search saved transcripts → read a result back with TTS,
  in one screen, per the directive. Confidence, when the recognizer
  reports one, is shown next to each segment rather than presented as
  certainty.
- **Speech & Language Packs settings screen** — per-language recognition
  and TTS status with an honest three-tier explanation (below), plus
  buttons that open the real Android system settings for voice input and
  TTS — SAJJIL cannot install a language pack itself, so it doesn't
  pretend to.

## A real platform limitation, worked around rather than hidden

`SpeechRecognizer` has no public API to transcribe a pre-existing audio
file — it is a **live microphone** API only (`startListening()`). Voice
Studio is therefore built as a live transcription session, not a
"transcribe this old recording" button; that's a constraint of the Android
platform, not a shortcut taken here. It's also single-shot: one
`startListening()` call yields exactly one final result, so a longer
session is built by automatically starting a new session each time the
previous one finalizes (`VoiceStudioViewModel.listenLoop`), with segment
timestamps offset to stay continuous across restarts. Because reopening
the same file mid-session would corrupt it (`WavStreamWriter` rewrites the
header from byte zero on open), only the most recent restart's audio is
kept as a reference clip when a session is saved — the transcript itself
covers the full session, the saved audio deliberately does not, and the UI
says so.

Similarly, there is no public API to ask "is Arabic available offline for
recognition" before starting a session — the only way to find out is to
try, and read back `ERROR_LANGUAGE_UNAVAILABLE` if it fails.
`AndroidSpeechBridge` reports recognition as "installed, confirmed on
first use" rather than a false green checkmark it can't actually back up.

## The Smart Fallback Hierarchy, honestly scoped

1. **Installed Android offline speech services** — implemented, described
   above.
2. **A SAJJIL-branded downloadable Offline Speech Pack** — **not
   implemented**. This is the same call Phase 3 made and for the same
   reason: there is no way in this sandbox to source, bundle, or verify a
   real ASR/TTS model. Shipping one unverified would risk silently
   mis-transcribing Qur'anic recitation, which is worse than not shipping
   it. The architecture reserves the slot — `OfflineArabicRecognizer` /
   `OfflineEnglishRecognizer` are exactly where a real Priority-2 engine
   would plug in — but nothing is downloaded, and the Speech & Language
   Packs screen says so rather than showing a fake "Download" button.
3. **Optional cloud processing** — **not implemented**. SAJJIL never sends
   audio to a network service, on-device or otherwise, and there is no
   code path that would.

## Recommended path for Priority 2, unchanged from Phase 3's reasoning

Whisper (small/base, quantized) remains the strongest candidate for
Arabic/English coverage; Vosk remains the lighter-footprint alternative.
Either needs real device testing across RAM tiers, and — critically —
verification against actual Qur'anic tajweed recitation and English
lecture speech before it ships, neither of which is possible without a
device and a model registry this environment doesn't have access to.
