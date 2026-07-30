# Offline Speech Intelligence Investigation

Phase 3 asked for Arabic/English transcription, speaker segmentation, and
searchable recordings, "offline-first where possible." This is that
investigation. As with hardware acceleration in Phase 2, it ends in a
recommendation rather than a bundled model — see "Why not implemented now."

## What shipped instead: real text search over what SAJJIL already knows

Recordings are searchable today by **title, notes, Surah tag, and Ayah
range** (`RecordingDao.search`, `RecordingRepository.search`, wired into
the Archive screen's search field). That's a genuine, working search
feature — just not a transcript search, since there's no transcript yet.
Recording Notes (Phase 3's Qur'an Production Suite) doubles as a practical
stand-in: a Qari can note what a take covers or contains, and search finds
it.

## Why transcription wasn't attempted

Offline ASR needs an actual trained acoustic/language model — there is no
shortcut equivalent to how the DSP features in this project were built
(genuine signal processing implemented from first principles). Whisper,
Vosk, and similar are trained on enormous multilingual speech corpora;
reproducing one from scratch here is not realistic, and I have no way in
this sandbox to bundle, download, verify, or test a real model file — no
Android runtime, no device, no network path to a model registry, and
critically, no way to confirm a bundled model actually transcribes Arabic
tajweed recitation or English lecture speech correctly rather than just
returning plausible-looking garbage. Shipping an untested transcription
path would be worse than not shipping one.

## Recommended path, phased

### 1. Pick an on-device ASR runtime
- **Whisper (small/base, quantized, via whisper.cpp or an ONNX Runtime
  Mobile / TensorFlow Lite port)** — multilingual, has meaningfully strong
  Modern Standard Arabic support, runs on-device with a quantized model in
  the 40-150MB range depending on size chosen. This is the strongest
  candidate specifically because Qur'anic Arabic and MSA lecture speech are
  both well inside Whisper's training distribution; expect it to do
  noticeably worse on Tajweed-specific pronunciation nuances than on plain
  MSA, since Tajweed rules aren't something a general-purpose ASR model was
  trained to represent.
- **Vosk** — smaller footprint, fully offline, weaker accuracy than
  Whisper in most published comparisons, includes Arabic language models.
  Worth a look if Whisper's model size is a problem for low-end target
  devices.
- Either way: budget real device testing across a range of RAM tiers before
  committing — a model that runs fine on a flagship can be unusable on a
  budget phone.

### 2. Integration shape
- A `TranscriptionEngine` interface in `core` (pure Kotlin, mirroring the
  `AudioEffectPlugin` pattern already in this codebase) wrapping whichever
  runtime is chosen behind a narrow contract: `transcribe(samples,
  sampleRate, languageHint): TranscriptResult`.
- The actual model inference is NDK/JNI-bound (native runtimes, not pure
  Kotlin), so it lives in `app`, not `core` — same boundary reasoning as
  hardware acceleration.
- Run transcription as an explicit, user-initiated background job (like
  Batch Production), not automatically on every recording — it's
  computationally expensive and the user should decide when it's worth the
  battery/time cost.

### 3. Data model
- A `TranscriptEntity` (Room): recordingId, language, segments (start/end
  timestamp + text), confidence. Store segment-level, not just full-text,
  so the UI can eventually jump playback to a matched phrase.
- Extend `RecordingDao.search` to also match transcript segments once they
  exist — the search infrastructure built this phase (title/notes/tags)
  extends naturally rather than needing a rewrite.

### 4. Speaker segmentation
- A materially harder, separate problem from transcription — diarization
  (who spoke when) typically needs its own model (e.g. pyannote-style
  embedding + clustering), largely irrelevant for single-Qari recitation
  but genuinely useful for multi-speaker lectures/Q&A sessions. Treat as a
  distinct, lower-priority roadmap item after transcription ships and
  proves out on real devices — don't bundle it speculatively.

### 5. What "offline-first" means in practice here
- Ship the model as a downloadable asset fetched once (not bundled in the
  APK, which would bloat every install for a feature not everyone uses),
  cached locally, and run entirely on-device thereafter with no network
  dependency — genuinely offline after the one-time download, consistent
  with the rest of SAJJIL's offline-first posture.

## Why not implemented now

No Android runtime, device, or model registry access in this sandbox to
select, bundle, and — critically — *verify* an ASR model actually works on
Arabic recitation and English lecture speech. A wrong transcript that looks
plausible is worse than no transcript; shipping that risk without any way
to test it here would violate the same honesty standard the rest of this
project has held to (spectral subtraction called DSP, not "AI"; generic mic
profiles instead of fabricated brand curves). The search feature that *did*
ship this phase (title/notes/tag search) is real, tested by inspection
against the DAO query, and immediately useful.
