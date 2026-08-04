package ai.sautiy.core.analysis

import ai.sautiy.core.audio.AudioBuffer
import ai.sautiy.core.dsp.Biquad
import ai.sautiy.core.dsp.Resampler
import kotlin.math.PI
import kotlin.math.log10
import kotlin.math.sqrt
import kotlin.math.tan

/**
 * Loudness measurement to **ITU-R BS.1770-4** and EBU R128.
 *
 * This is implemented to the published specification rather than approximated, because it is
 * the number a podcaster hands to a distributor and a broadcaster is held to by a regulator.
 * Chapter 1.4 principle 5 requires the meter to tell the truth, and "roughly LUFS" is not a
 * truth anyone can act on.
 *
 * Three quantities, all of which the analysis panel shows:
 *
 * - **Momentary** — 400 ms window. What is happening now.
 * - **Short-term** — 3 s window. What the last few seconds sounded like.
 * - **Integrated** — the whole programme, gated. The number a platform normalises against.
 *
 * The gating is the part most naive implementations omit and the reason their numbers are
 * wrong: silence between sentences would otherwise drag the average down, so BS.1770 discards
 * blocks below an absolute −70 LUFS, computes a provisional mean from what remains, and then
 * discards everything more than 10 LU below *that*.
 */
public object Loudness {

    /** Block length for the integrated measurement, per BS.1770. */
    public const val BLOCK_MS: Long = 400

    /** Blocks overlap by 75%, so a new block starts every 100 ms. */
    public const val BLOCK_OVERLAP: Double = 0.75

    public const val ABSOLUTE_GATE_LUFS: Double = -70.0

    public const val RELATIVE_GATE_LU: Double = -10.0

    /** The offset in the BS.1770 loudness equation. */
    private const val LOUDNESS_OFFSET = -0.691

    public const val SHORT_TERM_MS: Long = 3_000
    public const val MOMENTARY_MS: Long = 400

    /** Common delivery targets, offered as one-tap choices in the export panel. */
    public enum class Target(public val displayName: String, public val lufs: Double, public val truePeakCeilingDb: Double) {
        STREAMING("Streaming", -14.0, -1.0),
        PODCAST("Podcast", -16.0, -1.0),
        BROADCAST("Broadcast", -23.0, -1.0),
        SPOKEN_WORD("Spoken word", -19.0, -1.5),
    }

    public data class Measurement(
        val integratedLufs: Double,
        val loudnessRangeLu: Double,
        val truePeakDb: Double,
        val momentaryMaxLufs: Double,
        val shortTermMaxLufs: Double,
    ) {
        /** Gain in dB needed to hit [target]'s loudness. */
        public fun gainToReach(target: Target): Double = target.lufs - integratedLufs

        /** True if applying [gainToReach] would push the true peak past the target's ceiling. */
        public fun wouldClip(target: Target): Boolean =
            truePeakDb + gainToReach(target) > target.truePeakCeilingDb
    }

    /**
     * The K-weighting pre-filter: a high shelf approximating the acoustic effect of a head,
     * followed by a high-pass that removes the rumble the ear does not weigh.
     *
     * BS.1770 tabulates its coefficients at 48 kHz only. Using those numbers at any other rate
     * — which a surprising amount of code does — silently mis-weights the measurement, so
     * SAUTIY derives them from the specified analogue prototypes at whatever rate it is given.
     */
    internal fun kWeightingFilters(sampleRate: Int): List<Biquad> {
        // Stage 1: high shelf, +3.9998 dB, f0 = 1681.97 Hz, Q = 0.7071752.
        val shelfF0 = 1681.9744509555319
        val shelfGain = 3.999843853973347
        val shelfQ = 0.7071752369554193
        val k1 = tan(PI * shelfF0 / sampleRate)
        val vh = Math.pow(10.0, shelfGain / 20.0)
        val vb = Math.pow(vh, 0.4996667741545416)
        val a0Shelf = 1.0 + k1 / shelfQ + k1 * k1
        val shelf = Biquad.of(
            b0 = (vh + vb * k1 / shelfQ + k1 * k1) / a0Shelf,
            b1 = 2.0 * (k1 * k1 - vh) / a0Shelf,
            b2 = (vh - vb * k1 / shelfQ + k1 * k1) / a0Shelf,
            a1 = 2.0 * (k1 * k1 - 1.0) / a0Shelf,
            a2 = (1.0 - k1 / shelfQ + k1 * k1) / a0Shelf,
        )

        // Stage 2: RLB high-pass, f0 = 38.135 Hz, Q = 0.5003270.
        val hpF0 = 38.13547087602444
        val hpQ = 0.5003270373238773
        val k2 = tan(PI * hpF0 / sampleRate)
        val a0Hp = 1.0 + k2 / hpQ + k2 * k2
        val highPass = Biquad.of(
            b0 = 1.0,
            b1 = -2.0,
            b2 = 1.0,
            a1 = 2.0 * (k2 * k2 - 1.0) / a0Hp,
            a2 = (1.0 - k2 / hpQ + k2 * k2) / a0Hp,
        )
        return listOf(shelf, highPass)
    }

    /** Applies K-weighting to a copy of [buffer]. */
    internal fun kWeight(buffer: AudioBuffer): AudioBuffer {
        val weighted = buffer.copy()
        for (channel in weighted.channels) {
            for (filter in kWeightingFilters(buffer.sampleRate)) {
                filter.process(channel)
            }
        }
        return weighted
    }

    /** Mean square of each 400 ms block, K-weighted and channel-summed. */
    private fun blockMeanSquares(buffer: AudioBuffer): DoubleArray {
        val weighted = kWeight(buffer)
        val blockFrames = (BLOCK_MS * buffer.sampleRate / 1000).toInt()
        val stepFrames = (blockFrames * (1.0 - BLOCK_OVERLAP)).toInt().coerceAtLeast(1)
        if (weighted.frameCount < blockFrames) return DoubleArray(0)

        val count = (weighted.frameCount - blockFrames) / stepFrames + 1
        val out = DoubleArray(count)
        for (b in 0 until count) {
            val from = b * stepFrames
            var sum = 0.0
            // BS.1770 sums the per-channel mean squares with channel weights; for mono and
            // stereo every weight is 1.0.
            for (channel in weighted.channels) {
                var channelSum = 0.0
                for (i in from until from + blockFrames) {
                    channelSum += channel[i].toDouble() * channel[i]
                }
                sum += channelSum / blockFrames
            }
            out[b] = sum
        }
        return out
    }

    private fun toLufs(meanSquare: Double): Double =
        if (meanSquare <= 0.0) Double.NEGATIVE_INFINITY else LOUDNESS_OFFSET + 10.0 * log10(meanSquare)

    /**
     * Integrated loudness with both gates applied, exactly as the standard specifies.
     */
    public fun integrated(buffer: AudioBuffer): Double {
        val blocks = blockMeanSquares(buffer)
        if (blocks.isEmpty()) return Double.NEGATIVE_INFINITY

        // Absolute gate.
        val aboveAbsolute = blocks.filter { toLufs(it) > ABSOLUTE_GATE_LUFS }
        if (aboveAbsolute.isEmpty()) return Double.NEGATIVE_INFINITY

        // Relative gate, computed from the blocks that survived the absolute one.
        val provisional = toLufs(aboveAbsolute.average())
        val relativeThreshold = provisional + RELATIVE_GATE_LU
        val gated = aboveAbsolute.filter { toLufs(it) > relativeThreshold }
        if (gated.isEmpty()) return Double.NEGATIVE_INFINITY

        return toLufs(gated.average())
    }

    /** Loudness over a sliding window, one value per 100 ms step. */
    public fun windowed(buffer: AudioBuffer, windowMs: Long): DoubleArray {
        val weighted = kWeight(buffer)
        val windowFrames = (windowMs * buffer.sampleRate / 1000).toInt()
        val stepFrames = (buffer.sampleRate / 10).coerceAtLeast(1)
        if (weighted.frameCount < windowFrames) return DoubleArray(0)

        val count = (weighted.frameCount - windowFrames) / stepFrames + 1
        return DoubleArray(count) { w ->
            val from = w * stepFrames
            var sum = 0.0
            for (channel in weighted.channels) {
                var channelSum = 0.0
                for (i in from until from + windowFrames) {
                    channelSum += channel[i].toDouble() * channel[i]
                }
                sum += channelSum / windowFrames
            }
            toLufs(sum)
        }
    }

    public fun momentary(buffer: AudioBuffer): DoubleArray = windowed(buffer, MOMENTARY_MS)

    public fun shortTerm(buffer: AudioBuffer): DoubleArray = windowed(buffer, SHORT_TERM_MS)

    /**
     * Loudness range (EBU Tech 3342): the spread between the 10th and 95th percentiles of the
     * short-term loudness, above a relative gate of −20 LU.
     *
     * This is the number that says whether a lecture needs compression: a large range means the
     * quiet passages will be inaudible in a car, however loud the peaks are.
     */
    public fun loudnessRange(buffer: AudioBuffer): Double {
        val values = shortTerm(buffer).filter { it.isFinite() && it > ABSOLUTE_GATE_LUFS }
        if (values.size < 2) return 0.0

        val powerMean = values.map { Math.pow(10.0, it / 10.0) }.average()
        val gate = 10.0 * log10(powerMean) - 20.0
        val gated = values.filter { it > gate }.sorted()
        if (gated.size < 2) return 0.0

        val low = gated[(gated.size * 0.10).toInt().coerceIn(0, gated.lastIndex)]
        val high = gated[(gated.size * 0.95).toInt().coerceIn(0, gated.lastIndex)]
        return high - low
    }

    /**
     * True peak in dBTP, per BS.1770's 4× oversampling.
     *
     * A sample peak is not the peak: the analogue waveform reconstructed between two samples
     * can and does exceed both of them. A file that reads −0.1 dBFS on a sample meter can clip
     * a consumer D/A converter or an MP3 decoder outright, which is why every delivery
     * specification is written in dBTP and why SAUTIY measures it properly.
     */
    public fun truePeakDb(buffer: AudioBuffer): Double {
        if (buffer.frameCount == 0) return ai.sautiy.core.audio.Decibels.FLOOR_DB
        val oversampled = Resampler.resample(buffer, buffer.sampleRate * 4, Resampler.Quality.TRANSPARENT)
        val peak = maxOf(oversampled.peak(), buffer.peak())
        return ai.sautiy.core.audio.Decibels.fromLinear(peak.toDouble())
    }

    /** Everything the analysis panel shows, in one pass over the audio. */
    public fun measure(buffer: AudioBuffer): Measurement {
        val momentaryValues = momentary(buffer).filter { it.isFinite() }
        val shortTermValues = shortTerm(buffer).filter { it.isFinite() }
        return Measurement(
            integratedLufs = integrated(buffer),
            loudnessRangeLu = loudnessRange(buffer),
            truePeakDb = truePeakDb(buffer),
            momentaryMaxLufs = momentaryValues.maxOrNull() ?: Double.NEGATIVE_INFINITY,
            shortTermMaxLufs = shortTermValues.maxOrNull() ?: Double.NEGATIVE_INFINITY,
        )
    }

    /** Peak normalisation: the gain that brings the sample peak to [targetDb]. */
    public fun peakNormalisationGain(buffer: AudioBuffer, targetDb: Double = -1.0): Double {
        val peak = buffer.peak()
        if (peak <= 0f) return 0.0
        return targetDb - 20.0 * log10(peak.toDouble())
    }

    /**
     * The gain to reach a loudness target, reduced if necessary so the true peak stays under
     * the target's ceiling.
     *
     * Returning a gain that would clip and leaving the caller to notice is how loudness
     * normalisation ends up distorting the very material it was meant to fix. Where the two
     * constraints conflict the ceiling wins, and the shortfall is reported so the user can be
     * offered a limiter rather than silently given the wrong loudness.
     */
    public data class NormalisationPlan(
        val gainDb: Double,
        val achievedLufs: Double,
        val limitedByTruePeak: Boolean,
        val shortfallDb: Double,
    )

    public fun planNormalisation(buffer: AudioBuffer, target: Target): NormalisationPlan {
        val measurement = measure(buffer)
        if (!measurement.integratedLufs.isFinite()) {
            return NormalisationPlan(0.0, measurement.integratedLufs, false, 0.0)
        }
        val wanted = target.lufs - measurement.integratedLufs
        val headroom = target.truePeakCeilingDb - measurement.truePeakDb
        val allowed = minOf(wanted, headroom)
        return NormalisationPlan(
            gainDb = allowed,
            achievedLufs = measurement.integratedLufs + allowed,
            limitedByTruePeak = allowed < wanted - 1e-9,
            shortfallDb = (wanted - allowed).coerceAtLeast(0.0),
        )
    }

    /** Root-mean-square of a buffer in dBFS. Not loudness; used only for quick level checks. */
    public fun rmsDb(buffer: AudioBuffer): Double {
        val rms = buffer.rms()
        return if (rms <= 0.0) ai.sautiy.core.audio.Decibels.FLOOR_DB else 20.0 * log10(rms)
    }

    /** Crest factor in dB: how peaky the material is, and therefore how much a limiter can win. */
    public fun crestFactorDb(buffer: AudioBuffer): Double {
        val rms = buffer.rms()
        val peak = buffer.peak().toDouble()
        if (rms <= 0.0 || peak <= 0.0) return 0.0
        return 20.0 * log10(peak / rms)
    }

    internal fun meanSquareOf(samples: FloatArray): Double {
        var sum = 0.0
        for (s in samples) sum += s.toDouble() * s
        return sqrt(sum / samples.size)
    }
}
