# Phase 5: Real-Time Feel and the SAJJIL Assistant — What's Real, What Isn't

Phase 5's directive set two goals: the app should never feel like it's
waiting/loading/processing/thinking, and there should eventually be a
"SAJJIL Assistant" the user can talk to naturally. Both goals are legitimate
product direction. This document is the same kind of honest accounting as
`docs/HARDWARE_ACCELERATION.md` and `docs/SPEECH_INTELLIGENCE.md`: what
shipped for real this phase, what's a genuine platform constraint rather
than a shortcut, and what would need capabilities this sandbox doesn't have
to build honestly.

## What's implemented this phase

- **`TranscriptStabilizer`** (`core/speech`) — the "Smart Transcript
  Stabilisation" requirement, built for real. Voice Studio already showed
  live partial results (Phase 4); this phase splits each partial hypothesis
  into a *stable* prefix (unchanged across the last few updates — safe to
  render without flicker) and a *draft* tail (still being revised),
  rendered as normal-weight vs. dimmed text in `VoiceStudioScreen`. Pure
  word-history comparison, unit tested, no dependency on any specific
  recognizer's internals.
- **Zero-wait, where it was already achievable** — Voice Studio's
  transcript was already live (Phase 4: partial results streamed as you
  spoke, final segments appended immediately on each `onResults()`). There
  was no "Loading transcript…"/"Generating transcript…" step to remove
  because none existed; this phase's contribution is making the *live* text
  stop flickering, not inventing zero-wait where it wasn't already true.
- **A real instance of "run concurrently, not sequentially"** —
  `DashboardViewModel.load` used to run RT60 estimation, loudness/quality
  scoring, and spectrogram computation one after another inside a single
  `withContext` block. They're three independent read-only passes over the
  same decoded audio, so they now run concurrently via `coroutineScope` +
  `async`/`await`, cutting Dashboard analysis wall-clock time to roughly the
  slowest of the three instead of the sum of all three. This is genuinely
  correct — no shared mutable state between the three passes — but it is
  post-hoc analysis of an already-recorded file, not the live recording
  pipeline; see the mic-contention constraint below for why those are
  different problems.
- **`AssistantIntentParser`** (`core/assistant`) and the new **SAJJIL
  Assistant** screen — a fixed, small set of request patterns (find by
  Surah, find by keyword across titles/notes/transcripts, read the current
  transcript aloud via TTS, filter the library by quality) matched against
  typed or spoken text, executed against real repository data, with results
  you can tap to select as "current" for a follow-up "read this
  transcript." Unmatched phrasing returns `Unrecognized` with a plain
  explanation and examples, rather than a wrong guess dressed up as
  understanding.

## What "SAJJIL Assistant" is not, and why

The directive's own examples — "Find the lecture where I explained
fasting," "Read this transcript" — describe natural-language
understanding: an assistant that parses arbitrary phrasing into intent and
carries conversational context. **That requires a language model.** This
sandbox has no way to bundle, fine-tune, or verify one — no network path to
a model registry, no device to test inference latency or accuracy on, and
critically no way to confirm it wouldn't quietly misunderstand a Qur'an- or
fiqh-related request and act on the wrong thing. Shipping a fake "AI
understands you" experience built on regex would be a worse outcome than
building a scoped tool and labeling it honestly — the same call made for
`AdaptiveMasteringEngine` (Phase 3) and offline transcription (Phase 3/4).

So what shipped is **keyword/pattern matching over four request shapes**,
clearly labeled as such in the screen's own subtitle and in
`AssistantIntentParser`'s doc comment. It will correctly handle "Show me
Surah Al-Kahf recordings" and reasonably close phrasings. It will not
understand "did I ever mention how Umar handled that one dispute during the
lecture on jurisprudence" — and it says so, rather than pretending.

**Natural Conversation Layer, Context Awareness, sub-1-2s response
guarantees** — all depend on the same missing ingredient (a real language
model) and are not implemented for the same reason. The architecture keeps
its options open for a real one later: `AssistantIntentParser` is a single,
swappable module behind `AssistantIntent`, matching the directive's own
"separate Speech Recognition / NLU / Assistant Logic / Response Generation
/ TTS into independent modules" requirement — a future NLU implementation
replaces `AssistantIntentParser.parse()`'s body without touching
`AssistantViewModel` or the screen.

## The mic-contention constraint, still real

"Record → transcript appears while speaking" is fully true for Voice
Studio, because Voice Studio's recording chain *is* `SpeechRecognizer` —
one mic owner, live partials, done. It is **not** true for the main
Record screen's studio-quality pipeline (`AudioRecordEngine`: gate → EQ →
de-esser → compressor → limiter → WAV), because that pipeline and
`SpeechRecognizer` both want to own the microphone, and Android does not
support two apps' components reliably sharing one `AudioRecord` session at
once (documented in `docs/SPEECH_INTELLIGENCE.md`). Fusing live
transcription into the main Record flow would mean either degrading the
studio recording to `SpeechRecognizer`'s own (lower-fidelity, ~16kHz)
capture, or attempting simultaneous dual-mic-session capture that is
unreliable across OEM devices and impossible to verify without physical
hardware. Neither was done silently — this is a real platform boundary
between "the highest-fidelity take" and "live transcription while
recording it," and Voice Studio exists specifically as the workflow that
picks transcription. A user who wants both today: record in Voice Studio.

## Arabic-English code-switching, and response-time targets

Both depend entirely on the OS recognizer's own capability, which varies by
device and is outside SAJJIL's control — SAJJIL passes whichever language
locale is selected to `SpeechRecognizer`; it does not implement recognition
itself. The directive's ~1-2 second assistant response target is not
something this sandbox can measure or certify (same reasoning as
`docs/HARDWARE_ACCELERATION.md`'s stance on performance claims): the rule-
based `AssistantIntentParser` itself resolves in microseconds, so on real
hardware the bottleneck would be the repository query, not parsing —  but
"on real hardware" is exactly the part this environment can't verify.
