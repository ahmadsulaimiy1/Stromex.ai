# Chapter 14 — Export & Sharing

> Three taps from a finished recording to a file. Two in the common case.

---

## 14.1 The Guarantee

`Commit` → choose the format → `Export`.

The last-used format is pre-selected, so the common case is two taps. Chapter 3.2.2 allows the
user exactly **one decision** at export — the format — so everything else is decided for them
and stated, never asked:

| Decided | Value |
|---|---|
| Sample rate | The project's, unless the format requires otherwise |
| Bit depth | 24-bit for lossless, appropriate for lossy |
| Quality | Standard, unless the user has changed it in settings |
| Loudness | Whatever the applied chain produced — export never silently re-normalises |
| Metadata | Title, date and `ENCODER=SAUTIY`, so a file can be traced to what made it |

## 14.2 The Formats

Described in terms a person can choose between, never by codec name:

| Format | Said as | Lossless |
|---|---|---|
| **MP3** | "Plays everywhere. The right choice for sharing and publishing." | no |
| **M4A** | "Smaller than MP3 at the same quality. Best for Apple devices and modern players." | no |
| **WAV** | "Uncompressed and exact. For sending to an editor or an archive." | yes |
| **FLAC** | "Exact like WAV, at about half the size. For keeping." | yes |

**A format is never listed unless an encoder for it is actually registered.** Offering an export
that silently produces no file is the worst available outcome, so the panel reads a registry
rather than a hard-coded list, and asking for an unregistered format fails loudly.

## 14.3 Destinations

| Destination | Mechanism |
|---|---|
| Internal storage, SD card, cloud provider | Android's document picker (`CreateDocument`) — the user chooses, and SAUTIY writes where told |
| Another app | The share sheet, with a granted per-file URI |
| Back into SAUTIY | Never leaves; nothing to do |

SAUTIY never writes to a public directory on its own initiative and never asks for broad
storage permissions. It holds no permission that would let it read anyone else's files.

## 14.4 Export Never Blocks

Export runs off the interaction path. The user keeps recording, editing and listening while it
proceeds. Progress is **real** — driven by bytes actually encoded, not by a timer — and the
panel shows it as a determinate bar. An indeterminate spinner is an admission that the code
does not know how far along it is.

Failure states the fact, the consequence and the remedy, and leaves the recording untouched.

## 14.5 Encoders

| Format | How | Status |
|---|---|---|
| WAV | SAUTIY's own RIFF writer | Implemented, tested |
| FLAC | SAUTIY's own encoder — fixed predictors, partitioned Rice coding | Implemented, tested bit-exact against SAUTIY's own decoder |
| M4A | Platform `MediaCodec`, AAC-LC in ADTS | Implemented; registered only if the device has an AAC encoder |
| MP3 | — | **Not yet implemented. See 14.6.** |

ADTS rather than an MP4 container for AAC, because ADTS frames carry their own headers — so the
encode is a straight pipe to an output stream and never needs to seek, which matters when
writing into a document URI that may not be seekable.

## 14.6 MP3 — Stated Plainly

MP3 export is **not implemented yet**, and this is recorded here rather than papered over.

Android's `MediaCodec` decodes MP3 but has never encoded it, and no configuration changes that.
A real MP3 export therefore needs one of:

1. The NDK plus LAME — a native build dependency; or
2. An MPEG-1 Layer III encoder written in Kotlin — roughly 1,500 entries of exactly-correct
   Huffman table data, where a single wrong code produces a file that no decoder will open.

The second is the right answer for SAUTIY, because it keeps the product free of native
dependencies and consistent with the rest of the engine. It is worth building correctly rather
than half-building.

Until then the format is **absent from the export panel** rather than present and broken. Under
chapter 1.10 that is the correct behaviour: no placeholder, no "coming soon", and no encoder
that quietly writes something else.

## 14.7 Batch Export

Multiple recordings export in one operation, to one destination, with one progress figure. Each
file is written independently, so a failure on one does not lose the others, and the summary
states exactly which succeeded.

---

### Implementation

`sautiy-core/.../codec/AudioEncoder.kt` (the contract and the registry),
`WavCodec.kt`, `FlacCodec.kt` (encoder **and** decoder, so losslessness is proven rather than
claimed), `app/.../export/PlatformEncoders.kt` (AAC, registered conditionally).

**Verified by test:** bit-exact FLAC round trips on tones, noise, stereo, partial final blocks
and alternating full-scale material; two seconds of silence encode to under 2 KB; speech-like
material lands under 75% of the equivalent WAV; the registry refuses an unregistered format
loudly; every format carries a summary a person can choose on.
