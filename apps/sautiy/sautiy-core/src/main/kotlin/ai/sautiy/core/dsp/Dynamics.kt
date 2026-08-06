package ai.sautiy.core.dsp

import ai.sautiy.core.audio.AudioBuffer
import kotlin.math.abs
import kotlin.math.exp
import kotlin.math.log10
import kotlin.math.max

/**
 * Dynamics processing — Editorial Bible chapter 10.
 *
 * Everything here computes gain in the **decibel domain** and applies it in the linear domain.
 * That is not a stylistic choice: a ratio is a straight line in dB and a curve in amplitude, so
 * a compressor whose knee is built on linear values does not have the ratio printed on its
 * front panel. Chapter 1.4 principle 6 promises a professional real compression, and a real
 * compressor is one where 4:1 means 4:1.
 */

/**
 * A one-pole envelope follower with independent attack and release.
 *
 * The coefficient is `exp(−1 / (time · rate))`, the standard analogue-equivalent single-pole
 * response, so a stated 10 ms attack really is a 10 ms time constant rather than a number that
 * happens to sound about right.
 */
public class EnvelopeFollower(
    attackMs: Double,
    releaseMs: Double,
    sampleRate: Int,
    /**
     * RMS detection is smoother and matches perceived loudness; peak detection catches
     * transients a compressor must not miss. A limiter is always peak.
     */
    private val rms: Boolean = false,
) {
    private val attackCoefficient = coefficient(attackMs, sampleRate)
    private val releaseCoefficient = coefficient(releaseMs, sampleRate)
    private var envelope = 0.0

    public fun reset() {
        envelope = 0.0
    }

    public fun process(sample: Double): Double {
        val input = if (rms) sample * sample else abs(sample)
        val coefficient = if (input > envelope) attackCoefficient else releaseCoefficient
        envelope = coefficient * envelope + (1.0 - coefficient) * input
        return if (rms) kotlin.math.sqrt(max(envelope, 0.0)) else envelope
    }

    public companion object {
        internal fun coefficient(timeMs: Double, sampleRate: Int): Double =
            if (timeMs <= 0.0) 0.0 else exp(-1.0 / (timeMs / 1000.0 * sampleRate))
    }
}

/**
 * A feed-forward compressor with a soft knee.
 *
 * @param thresholdDb level above which gain reduction begins
 * @param ratio 4.0 means 4:1 — for every 4 dB above the threshold, 1 dB comes out
 * @param kneeDb width of the transition, centred on the threshold. A hard knee is 0.
 * @param makeupDb applied after compression. `null` computes automatic makeup that restores
 *   the level a steady signal at the threshold would have lost, which is what makes a
 *   compressor comparable by ear at different settings instead of just quieter.
 */
public class Compressor(
    public val thresholdDb: Double = -18.0,
    public val ratio: Double = 3.0,
    public val attackMs: Double = 10.0,
    public val releaseMs: Double = 120.0,
    public val kneeDb: Double = 6.0,
    public val makeupDb: Double? = null,
    public val detectRms: Boolean = true,
) {
    init {
        require(ratio >= 1.0) { "A ratio below 1:1 is an expander, not a compressor" }
        require(kneeDb >= 0.0)
    }

    /** The static curve: output level in dB for an input level in dB. */
    public fun outputLevelDb(inputDb: Double): Double {
        val over = inputDb - thresholdDb
        return when {
            kneeDb > 0 && over > -kneeDb / 2 && over < kneeDb / 2 -> {
                // Quadratic interpolation across the knee, which makes the curve and its first
                // derivative continuous — a hard corner is audible as a click on transients.
                val x = over + kneeDb / 2
                inputDb + (1.0 / ratio - 1.0) * x * x / (2.0 * kneeDb)
            }

            over <= -kneeDb / 2 -> inputDb
            else -> thresholdDb + over / ratio
        }
    }

    /** Gain reduction in dB (negative) for an input level in dB. */
    public fun gainReductionDb(inputDb: Double): Double = outputLevelDb(inputDb) - inputDb

    /** Makeup that restores unity for material sitting at the threshold. */
    public fun automaticMakeupDb(): Double = -gainReductionDb(0.0) * 0.5

    /**
     * Compresses in place, returning the peak gain reduction applied, so the meter can show
     * what the compressor actually did rather than what it was configured to do.
     */
    public fun process(buffer: AudioBuffer): Double {
        val follower = EnvelopeFollower(attackMs, releaseMs, buffer.sampleRate, rms = detectRms)
        val makeup = makeupDb ?: automaticMakeupDb()
        val makeupLinear = Math.pow(10.0, makeup / 20.0)
        var maxReduction = 0.0

        // Detection is on the channel sum so stereo material keeps its image: compressing the
        // two channels independently pulls the loud side down on its own and the picture moves.
        val frames = buffer.frameCount
        for (i in 0 until frames) {
            var detector = 0.0
            for (channel in buffer.channels) detector = max(detector, abs(channel[i].toDouble()))

            val envelope = follower.process(detector)
            val levelDb = if (envelope <= 0.0) -120.0 else 20.0 * log10(envelope)
            val reduction = gainReductionDb(levelDb)
            if (reduction < maxReduction) maxReduction = reduction

            val gain = (Math.pow(10.0, reduction / 20.0) * makeupLinear).toFloat()
            for (channel in buffer.channels) channel[i] *= gain
        }
        return maxReduction
    }
}

/**
 * A look-ahead peak limiter.
 *
 * The look-ahead is what separates a limiter from a fast compressor: the signal is delayed by
 * the look-ahead time while the detector runs ahead of it, so the gain is already down *before*
 * the transient arrives instead of catching up after it. Without that, every peak passes
 * through unattenuated for the length of the attack, which is exactly the distortion a limiter
 * exists to prevent.
 *
 * The gain envelope is smoothed by a running minimum over the look-ahead window followed by a
 * one-pole release, so gain never steps.
 */
public class Limiter(
    public val ceilingDb: Double = -1.0,
    public val lookAheadMs: Double = 5.0,
    public val releaseMs: Double = 50.0,
) {
    /**
     * Limits in place, returning the peak gain reduction applied.
     *
     * The output is time-aligned with the input: the look-ahead delay is absorbed internally
     * by running the gain computation `lookAhead` frames past the end, so a caller never has to
     * compensate and a limited file never drifts against an unlimited one.
     */
    public fun process(buffer: AudioBuffer): Double {
        val sampleRate = buffer.sampleRate
        val lookAhead = (lookAheadMs * sampleRate / 1000.0).toInt().coerceAtLeast(1)
        val ceiling = Math.pow(10.0, ceilingDb / 20.0)
        val frames = buffer.frameCount
        if (frames == 0) return 0.0

        // The gain each frame would need on its own to sit under the ceiling.
        val required = DoubleArray(frames)
        for (i in 0 until frames) {
            var peak = 0.0
            for (channel in buffer.channels) peak = max(peak, abs(channel[i].toDouble()))
            required[i] = if (peak > ceiling) ceiling / peak else 1.0
        }

        val original = Array(buffer.channelCount) { buffer.channels[it].copyOf() }
        val releaseCoefficient = EnvelopeFollower.coefficient(releaseMs, sampleRate)

        // A monotonic deque gives the minimum of `required` over a trailing window of
        // `lookAhead` frames in amortised O(1) per sample. Paired with emitting the signal
        // delayed by the same amount, that is exactly a leading window on the audio: the gain
        // is already down before the transient is emitted, rather than catching up after it.
        val window = java.util.ArrayDeque<Int>()
        var gain = 1.0
        var maxReduction = 0.0

        for (n in 0 until frames + lookAhead) {
            val incoming = if (n < frames) required[n] else 1.0
            while (window.isNotEmpty() && requiredAt(required, window.peekLast(), frames) >= incoming) {
                window.removeLast()
            }
            window.addLast(n)
            while (window.peekFirst() < n - lookAhead) window.removeFirst()
            val target = requiredAt(required, window.peekFirst(), frames)

            // Instant attack, smoothed release: gain never steps upward.
            gain = if (target < gain) target else releaseCoefficient * gain + (1.0 - releaseCoefficient) * target

            val emit = n - lookAhead
            if (emit >= 0) {
                val reductionDb = 20.0 * log10(gain.coerceAtLeast(1e-9))
                if (reductionDb < maxReduction) maxReduction = reductionDb
                for (c in 0 until buffer.channelCount) {
                    buffer.channels[c][emit] = (original[c][emit] * gain).toFloat()
                }
            }
        }
        return maxReduction
    }

    private fun requiredAt(required: DoubleArray, index: Int, frames: Int): Double =
        if (index < frames) required[index] else 1.0

    /** Frames of latency this limiter introduces, which the caller must compensate. */
    public fun latencyFrames(sampleRate: Int): Int = (lookAheadMs * sampleRate / 1000.0).toInt().coerceAtLeast(1)
}

/**
 * A noise gate with hold.
 *
 * The hold is not a refinement, it is the difference between usable and unusable: without it,
 * a gate chatters open and closed on every syllable boundary where the level crosses the
 * threshold, and the chattering is far more distracting than the noise it removes.
 */
public class NoiseGate(
    public val thresholdDb: Double = -45.0,
    public val attackMs: Double = 2.0,
    public val holdMs: Double = 120.0,
    public val releaseMs: Double = 200.0,
    /** How far down the gate closes. Full silence sounds like a dropout; −20 dB sounds natural. */
    public val rangeDb: Double = -20.0,
) {
    public fun process(buffer: AudioBuffer): AudioBuffer {
        val sampleRate = buffer.sampleRate
        val follower = EnvelopeFollower(attackMs, releaseMs, sampleRate, rms = true)
        val threshold = Math.pow(10.0, thresholdDb / 20.0)
        val floor = Math.pow(10.0, rangeDb / 20.0)
        val holdFrames = (holdMs * sampleRate / 1000.0).toInt()
        val attackCoefficient = EnvelopeFollower.coefficient(attackMs, sampleRate)
        val releaseCoefficient = EnvelopeFollower.coefficient(releaseMs, sampleRate)

        var gain = floor
        var holdCounter = 0

        for (i in 0 until buffer.frameCount) {
            var detector = 0.0
            for (channel in buffer.channels) detector = max(detector, abs(channel[i].toDouble()))
            val envelope = follower.process(detector)

            if (envelope > threshold) {
                holdCounter = holdFrames
            } else if (holdCounter > 0) {
                holdCounter--
            }

            val target = if (envelope > threshold || holdCounter > 0) 1.0 else floor
            val coefficient = if (target > gain) attackCoefficient else releaseCoefficient
            gain = coefficient * gain + (1.0 - coefficient) * target

            val g = gain.toFloat()
            for (channel in buffer.channels) channel[i] *= g
        }
        return buffer
    }
}

/**
 * A split-band de-esser.
 *
 * Sibilance is a band, not a level, so a full-band compressor triggered by an "s" ducks the
 * entire voice and produces the pumping that makes amateur podcasts recognisable. This one
 * splits the signal, compresses only the sibilant band, and sums the two back together — so an
 * "s" loses its edge while the vowel around it is untouched.
 */
public class DeEsser(
    public val frequencyHz: Double = 6_000.0,
    public val thresholdDb: Double = -28.0,
    public val ratio: Double = 4.0,
    public val attackMs: Double = 1.0,
    public val releaseMs: Double = 40.0,
) {
    public fun process(buffer: AudioBuffer): Double {
        val sampleRate = buffer.sampleRate
        var maxReduction = 0.0

        for (channel in buffer.channels) {
            // A Linkwitz-Riley 4th-order crossover: two cascaded Butterworth sections per side.
            //
            // The obvious shortcut — high-pass the signal and call the remainder the low band —
            // does not work, and does not fail loudly. A filter shifts phase as well as
            // magnitude, so `signal minus high-pass` still contains most of the sibilance: at
            // 1.4 times the corner frequency it retains about 79% of it. Pulling the high band
            // down then barely changes the total, and the de-esser appears to work while doing
            // almost nothing. LR4 is the standard crossover precisely because its two halves
            // sum to a flat magnitude response.
            val high = channel.copyOf()
            Biquad.highPass(frequencyHz, sampleRate, Biquad.BUTTERWORTH_Q).process(high)
            Biquad.highPass(frequencyHz, sampleRate, Biquad.BUTTERWORTH_Q).process(high)

            val low = channel.copyOf()
            Biquad.lowPass(frequencyHz, sampleRate, Biquad.BUTTERWORTH_Q).process(low)
            Biquad.lowPass(frequencyHz, sampleRate, Biquad.BUTTERWORTH_Q).process(low)

            val follower = EnvelopeFollower(attackMs, releaseMs, sampleRate, rms = false)
            val compressor = Compressor(
                thresholdDb = thresholdDb,
                ratio = ratio,
                attackMs = attackMs,
                releaseMs = releaseMs,
                kneeDb = 4.0,
                makeupDb = 0.0,
                detectRms = false,
            )

            for (i in high.indices) {
                val envelope = follower.process(abs(high[i].toDouble()))
                val levelDb = if (envelope <= 0.0) -120.0 else 20.0 * log10(envelope)
                val reduction = compressor.gainReductionDb(levelDb)
                if (reduction < maxReduction) maxReduction = reduction
                high[i] = (high[i] * Math.pow(10.0, reduction / 20.0)).toFloat()
                channel[i] = low[i] + high[i]
            }
        }
        return maxReduction
    }
}
