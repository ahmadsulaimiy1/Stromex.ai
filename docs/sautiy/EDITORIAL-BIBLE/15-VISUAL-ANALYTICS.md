# Chapter 15 — Visual Analytics

> Where a picture is faster than a sentence, draw. Where a number is the truth, print the number.

---

## 15.1 The Rule

A visualisation earns its place only if it is **faster to read than the sentence it replaces**.
A chart that takes longer to interpret than "peak −6.2 dB" is decoration, and decoration is
forbidden (chapter 2.5).

Every visualisation in SAUTIY also carries its number, because a picture cannot be quoted to a
distributor.

## 15.2 The Set

| Visualisation | Answers | Where |
|---|---|---|
| **Waveform** | Where is the sound, and where is the silence? | Canvas — the centre of the product |
| **Live waveform** | Is it working, right now? | Canvas, in ember, while recording |
| **Level meter** | Will this clip? | Canvas, during capture and monitoring |
| **Quality gauge** | Is this take usable? | Analysis panel, plus a canvas tap target |
| **Loudness graph** | Which passages will be too quiet in a car? | Analysis panel |
| **Spectrogram** | Where is the hum, the hiss, the ring? | Analysis panel, on demand |
| **Frequency analyser** | What am I about to equalise? | Behind the EQ curve |
| **Noise readout** | How bad is this room? | Status rail during capture; Analysis panel after |
| **Storage ring** | How much longer can I record? | Status rail, as **minutes** |
| **Progress bar** | How far through this export? | Export panel, determinate, driven by real bytes |

## 15.3 Waveform Drawing Law

- **Peak *and* RMS envelopes, both.** A peak-only waveform makes a plosive and a sustained
  vowel look identical; an RMS-only one hides the transient that will clip.
- **Minima and maxima are drawn separately**, never as a mirrored magnitude. Speech is
  asymmetric, and a symmetric drawing lies about it.
- **The loudest sample survives every zoom level.** A zoomed-out waveform that loses a transient
  is worse than useless — it tells the user there is no click at the exact moment they are
  hunting for one. This is a tested property of the pyramid, not an intention.
- Beyond the end of the material the canvas draws silence rather than nothing, because during
  recording the view legitimately runs ahead.

## 15.4 Meter Law

Broadcast ballistics, always (chapter 2.6): instant attack, 20 dB/second release, peak hold with
a 1.2 second dwell then a 12 dB/second fall.

The scale is **non-linear**: the top 20 dB take half the width. A meter linear in decibels
spends most of its length on levels nobody watches and compresses the region between "good" and
"clipped" into a few pixels.

## 15.5 Colour Encodes Data, Or Nothing

The only gradients in SAUTIY are the meter ramp (`safe → caution → critical`) and the
spectrogram colour map. Both encode data. No surface anywhere carries a gradient for effect
(chapter 2.3.4 clause 4).

Every colour-carried state also carries a shape, an icon, a number or a word — clipping shows
as red *and* as the word "Clipped" (chapter 2.3.4 clause 2).

## 15.6 Progressive Rendering

Analysis renders into a laid-out shell as it completes, never behind a spinner. The panel's
structure appears immediately with its numbers filling in, so the user can see what is coming
and can leave if it is not what they wanted.

Nothing in this chapter may delay playback (chapter 1.3.4).

## 15.7 Statistics

The Project panel states only what is genuinely known: recorded duration, take count, layer
count, sample rate, and date of the most recent take. No projections, no averages presented as
insight, no trends drawn from four data points.

---

### Implementation

`sautiy-core/.../analysis/WaveformPeaks.kt` (pyramid, columns, instant level),
`Loudness.kt` (BS.1770-4, EBU R128, true peak), `dsp/Fft.kt` (spectrogram and analyser),
`app/.../ui/workspace/WaveformCanvas.kt`, `app/.../ui/components/Meters.kt`.

**Verified by test:** decimation preserves extremes exactly; a full-recording view still shows
the loudest single sample; `columns()` returns exactly one entry per pixel at every width;
columns past the end are silent rather than an error; incremental building matches building all
at once, so the waveform does not visibly change on save.
