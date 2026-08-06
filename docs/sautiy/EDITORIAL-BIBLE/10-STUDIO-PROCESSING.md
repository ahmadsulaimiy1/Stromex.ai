# Chapter 10 — Studio Processing

> Enhancement must feel intelligent and be completely inspectable. Nothing hidden, nothing
> magic, nothing the user cannot measure, defeat or undo.

---

## 10.1 The Enhancement Contract

1. **Nothing is applied without being asked.** SAUTIY never "improves" a recording on capture.
2. **Everything is a recipe.** A chain is a small serialisable value, not a rendering. Revert
   to original is therefore always available and always instant (chapter 3.2.8).
3. **Everything is measurable.** Every stage reports what it *actually did* — gain reduction in
   dB, loudness before and after, true peak — not what it was configured to do.
4. **Everything is defeatable.** Every preset expands to its real parameters. A professional is
   never limited (chapter 1.4 principle 6); a beginner never has to look (principle 2).
5. **The user is told when a target could not be met.** A loudness target that would clip is
   not silently missed; the shortfall is stated and a limiter is offered.

## 10.2 The Chain, and Why It Is In This Order

The order is fixed and is not a matter of taste.

| # | Stage | Why here |
|---|-------|----------|
| 1 | **High-pass** | Remove rumble first, so nothing downstream spends headroom on energy nobody will hear |
| 2 | **Noise reduction** | Before compression — a compressor turns up the gaps between words, and would otherwise amplify exactly the noise being removed |
| 3 | **Equalisation** | Shape the tone while the dynamics are still natural |
| 4 | **De-essing** | After EQ, because a presence lift is usually what made the sibilance sharp |
| 5 | **Compression** | Even out the level of the tone that now exists |
| 6 | **Space** | Put the finished voice in a room, rather than the room in the voice |
| 7 | **Loudness normalisation** | Measure the result and set the delivery level |
| 8 | **Limiting** | Last, so nothing after it can push a peak back over the ceiling |

## 10.3 The Presets

Nine cards, each named for a **situation** rather than a process. A user knows whether they
recorded a lecture; they do not know whether they want 3:1 at −18 dBFS with a 6 dB knee.

| Card | For | Notable |
|---|---|---|
| **Natural** | Anything | High-pass and a limiter. Nothing you can hear working. |
| **Studio** | A close microphone in a quiet room | Clean, controlled, present |
| **Podcast** | Publication | Hits −16 LUFS |
| **Lecture** | A hall, a lapel mic, ninety minutes | Heavy noise reduction, −19 LUFS |
| **Recitation** | Qur'anic recitation | **Deliberately light compression** — recitation lives on its dynamics |
| **Broadcast** | Delivery to a broadcaster | Hits −23 LUFS |
| **Warm** | A thin or distant recording | Low shelf up, presence down |
| **Deep** | Authority | Weight without losing words |
| **Bright** | A dull room | Presence up — and the de-esser is therefore not optional |

Each card expands, on touch, to the parameters underneath it. Advanced controls remain hidden
until then (chapter 3.2.3, tier 3).

## 10.4 Measurement Is To Standard

| Quantity | Standard |
|---|---|
| Integrated / short-term / momentary loudness | **ITU-R BS.1770-4**, with both gates |
| Loudness range | **EBU Tech 3342** |
| True peak | BS.1770 4× oversampling, reported in **dBTP** |
| Delivery targets | Streaming −14, Podcast −16, Spoken word −19, Broadcast −23 LUFS |

These are implemented to the published specification, not approximated, because they are the
numbers a podcaster hands to a distributor and a broadcaster is held to by a regulator.
"Roughly LUFS" is not a truth anyone can act on.

**K-weighting is re-derived at the working sample rate.** BS.1770 tabulates its coefficients at
48 kHz only; reusing those numbers at 44.1 kHz silently mis-weights the measurement.

**True peak, not sample peak.** The analogue waveform reconstructed between two samples can
exceed both of them. A file reading −0.1 dBFS on a sample meter can clip a consumer converter
or an MP3 decoder outright, which is why every delivery specification is written in dBTP.

## 10.5 Craft Rules

These are the details that separate processing that sounds professional from processing that
sounds processed. Each is implemented and each is held by a test.

- **A ratio is a straight line in dB.** Gain is computed in the decibel domain, so 4:1 means
  4:1 and the number on the panel is the number in the audio.
- **The knee is continuous.** A hard corner in the transfer curve is audible as a click on
  transients, so the knee interpolates quadratically and its first derivative is continuous.
- **A limiter has look-ahead.** Without it every transient passes through unattenuated for the
  length of the attack — which is precisely the distortion a limiter exists to prevent. The
  output is time-aligned, so a limited layer never drifts against an unlimited one.
- **A de-esser splits the band properly.** Signal-minus-high-pass is *not* a low band: a filter
  shifts phase as well as magnitude, and the remainder still holds most of the sibilance. SAUTIY
  uses a Linkwitz-Riley 4th-order crossover, whose halves sum flat.
- **A gate holds.** Without a hold time a gate chatters on every syllable boundary, and the
  chattering is more distracting than the noise. It also closes to −20 dB, not to silence:
  digital silence between words sounds like a dropout.
- **Noise reduction keeps a floor.** Subtracting to zero leaves isolated surviving bins that are
  heard as tones flickering in and out — "musical noise". A residual floor keeps a quiet, steady
  bed the ear reads as room.
- **The noise profile is a median, not a mean.** A mean absorbs the chair creak that crept into
  the learning passage, and then subtracts that creak's spectrum from the whole recording.
- **Detection is on the channel sum.** Compressing stereo channels independently pulls the loud
  side down on its own and the stereo image moves.
- **Reverb is not echo.** Echo is a repetition the listener can count; reverb is a space they
  cannot. They are two controls, not one slider with a blend.

## 10.6 Live Preview

Any preset can be auditioned instantly, because applying a chain to the *window being played*
costs a few milliseconds and requires no file to be written. A/B against the original is a
single control, and it is always available.

---

### Implementation

| Clause | Code |
|--------|------|
| 10.2 The chain | `sautiy-core/.../dsp/StudioChain.kt` |
| 10.3 The presets | `StudioPreset` — nine cards, each fully parameterised |
| 10.4 Loudness | `sautiy-core/.../analysis/Loudness.kt` |
| 10.5 Filters | `dsp/Biquad.kt` (Audio EQ Cookbook designs, transposed direct form II) |
| 10.5 Dynamics | `dsp/Dynamics.kt` — compressor, look-ahead limiter, gate, LR4 de-esser |
| 10.5 Noise reduction | `dsp/NoiseReduction.kt` — STFT spectral subtraction |
| 10.5 Space | `dsp/Reverb.kt` — Schroeder–Moorer reverb and a damped delay |
| Analysis primitives | `dsp/Fft.kt` |

**Verified by test**, among others: a −20 dBFS 1 kHz tone reads −23.0 LUFS at 44.1, 48, 32 and
96 kHz; twenty-second gaps of silence do not change programme loudness; a 4:1 compressor turns
20 dB over the threshold into exactly 5 dB over; the limiter's first transient is already
controlled and does not move in time; the de-esser reduces 7 kHz by more than 3 dB while moving
a 300 Hz vowel by less than 1 dB; and every preset that names a loudness target reaches it
within 2 LU without exceeding its own true-peak ceiling.
