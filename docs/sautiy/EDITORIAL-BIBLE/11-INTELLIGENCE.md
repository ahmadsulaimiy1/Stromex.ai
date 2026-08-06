# Chapter 11 — Intelligence

> AI never takes over. It suggests, predicts, repairs and improves — and it stays invisible.

---

## 11.1 The Rules

1. **Intelligence never acts on its own.** Nothing is applied, deleted, renamed or normalised
   without the user asking. A suggestion is offered once, quietly, in place; it is never a
   dialog and never repeats.
2. **Intelligence never blocks.** Every analysis runs after the audio is safe and off the path
   of anything the user is doing. Playback outranks it (chapter 1.3.4); so does recording.
3. **Intelligence is always inspectable.** Every conclusion states the measurement it came
   from. "Quality 62" is useless; "62 — very quiet, peak −34 dBFS" is actionable.
4. **Intelligence is always defeatable.** Every suggestion has a visible "no", and refusing one
   twice stops it being offered for that recording.
5. **Intelligence stays on the device.** No audio, no transcript and no derived feature leaves
   the phone. The application has no internet permission (chapter 1.3.7).

## 11.2 Automatic Quality Analysis

Runs once when a take ends. Produces a 0–100 score built only from **measured** faults, each
mapping to one sentence the user can act on:

| Fault | Deduction | Sentence |
|---|---|---|
| Clipping | −40 | "Clipped. Move further from the microphone." |
| Peak above −1 dBFS | −20 | "Close to clipping. Ease back a little." |
| Peak below −30 dBFS | −35 | "Very quiet. Move closer to the microphone." |
| Peak below −18 dBFS | −10 | "A little quiet." |
| Signal-to-noise under 20 dB | −30 | "A quieter room would help." |
| Signal-to-noise under 35 dB | −15 | " " |

Nothing speculative contributes. A score the user cannot explain is a score they ignore.

## 11.3 Smart Suggestions

Offered at most **one per recording**, in the analysis panel, never as an interruption:

| Observed | Suggested |
|---|---|
| Loudness range above 15 LU | "Compression would even this out." → applies Lecture |
| Noise floor above −45 dBFS | "There is room noise. Reduce it?" |
| More than 8 s of leading or trailing silence | "Trim the silence at the start and end?" |
| Integrated loudness more than 6 LU from a delivery target | "Normalise to −16 LUFS for publishing?" |
| Clipping present | No suggestion — it cannot be repaired, and offering a fix that is not one is dishonest |

That last row is the important one. Where nothing can genuinely be done, SAUTIY says nothing.

## 11.4 Transcription

On-device speech recognition, run **after** a take ends and never during. The transcript is a
**search index first and a document second**: its primary job is making "find where I said
'balance sheet'" work.

- Tap a word to seek to it.
- Transcription failing is not an error — most recordings do not need one. It is simply absent.
- Where no on-device recogniser exists, the capability is absent rather than degraded, and the
  transcript panel says what it is for rather than pretending to be loading.

## 11.5 Intelligent Tagging

Tags are **proposed**, never applied: time of day, detected language, duration band, and whether
the material looks like speech, recitation or music. The user accepts or ignores. A tag SAUTIY
applied by itself is a tag the user has to audit.

## 11.6 Search By Meaning

Search (chapter 4.6) ranks across title, tags, marker labels, transcript and spoken-date
phrases — "last Tuesday", "Ramadan", "this morning". Date phrases are resolved locally against
the device clock and calendar; there is no service involved.

## 11.7 The Extension Point

Intelligence is defined as an interface with a working default, not as a promise:

```
interface RecordingAnalyst {
    fun analyse(recording): Analysis   // quality, loudness, noise, suggestions
    fun transcribe(recording): Transcript?   // null where no recogniser exists
}
```

The default implementation is the measured analysis of chapters 10 and 15 — real, complete and
shipped. A future model implements the same interface. Nothing in the product waits on one.

---

### Implementation

`sautiy-core/.../record/RecordingSession.kt` (`RecordingState.qualityScore`),
`sautiy-core/.../analysis/Loudness.kt`, `SilenceDetector.kt`, `NoiseReduction.Profile.levelDb`,
`app/.../ui/workspace/WorkspaceViewModel.kt` (`qualityReason`).
