package ai.sautiy.core.dsp

import ai.sautiy.core.audio.AudioBuffer
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sinh
import kotlin.math.sqrt

/**
 * A second-order IIR section — the building block of every filter in SAUTIY's studio chain.
 *
 * Coefficients follow the Audio EQ Cookbook's bilinear-transform designs, which is what
 * essentially every audio equaliser in existence uses, and the difference equation is
 * transposed direct form II: fewer state variables than direct form I, and better numerical
 * behaviour at low frequencies in floating point, which matters because a 60 Hz high-pass at
 * 48 kHz is exactly where a naive implementation loses precision.
 */
public class Biquad(
    private val b0: Double,
    private val b1: Double,
    private val b2: Double,
    private val a1: Double,
    private val a2: Double,
) {
    private var s1 = 0.0
    private var s2 = 0.0

    /** Resets the filter's memory. Called before processing a new, unrelated block. */
    public fun reset() {
        s1 = 0.0
        s2 = 0.0
    }

    public fun processSample(x: Double): Double {
        val y = b0 * x + s1
        s1 = b1 * x - a1 * y + s2
        s2 = b2 * x - a2 * y
        return y
    }

    /** Filters a channel in place. */
    public fun process(samples: FloatArray) {
        for (i in samples.indices) samples[i] = processSample(samples[i].toDouble()).toFloat()
    }

    /**
     * Magnitude response at [frequency], for drawing the EQ curve.
     *
     * Evaluated directly from the coefficients rather than measured by sweeping the filter, so
     * the curve the user sees is the filter they are hearing by construction — the two cannot
     * drift apart.
     */
    public fun magnitudeAt(frequency: Double, sampleRate: Int): Double {
        val w = 2.0 * PI * frequency / sampleRate
        val cosw = cos(w)
        val cos2w = cos(2 * w)
        val sinw = sin(w)
        val sin2w = sin(2 * w)

        val numeratorReal = b0 + b1 * cosw + b2 * cos2w
        val numeratorImaginary = -(b1 * sinw + b2 * sin2w)
        val denominatorReal = 1.0 + a1 * cosw + a2 * cos2w
        val denominatorImaginary = -(a1 * sinw + a2 * sin2w)

        val numerator = sqrt(numeratorReal * numeratorReal + numeratorImaginary * numeratorImaginary)
        val denominator = sqrt(denominatorReal * denominatorReal + denominatorImaginary * denominatorImaginary)
        return if (denominator == 0.0) 0.0 else numerator / denominator
    }

    public fun magnitudeDbAt(frequency: Double, sampleRate: Int): Double =
        20.0 * kotlin.math.log10(magnitudeAt(frequency, sampleRate).coerceAtLeast(1e-12))

    public companion object {
        /** The default Q for a filter with no resonance: 1/√2, the Butterworth response. */
        public const val BUTTERWORTH_Q: Double = 0.70710678118654752

        private fun normalised(b0: Double, b1: Double, b2: Double, a0: Double, a1: Double, a2: Double) =
            Biquad(b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0)

        public fun lowPass(frequency: Double, sampleRate: Int, q: Double = BUTTERWORTH_Q): Biquad {
            val w = 2.0 * PI * frequency / sampleRate
            val alpha = sin(w) / (2.0 * q)
            val cosw = cos(w)
            return normalised(
                b0 = (1 - cosw) / 2, b1 = 1 - cosw, b2 = (1 - cosw) / 2,
                a0 = 1 + alpha, a1 = -2 * cosw, a2 = 1 - alpha,
            )
        }

        public fun highPass(frequency: Double, sampleRate: Int, q: Double = BUTTERWORTH_Q): Biquad {
            val w = 2.0 * PI * frequency / sampleRate
            val alpha = sin(w) / (2.0 * q)
            val cosw = cos(w)
            return normalised(
                b0 = (1 + cosw) / 2, b1 = -(1 + cosw), b2 = (1 + cosw) / 2,
                a0 = 1 + alpha, a1 = -2 * cosw, a2 = 1 - alpha,
            )
        }

        public fun bandPass(frequency: Double, sampleRate: Int, q: Double = 1.0): Biquad {
            val w = 2.0 * PI * frequency / sampleRate
            val alpha = sin(w) / (2.0 * q)
            val cosw = cos(w)
            return normalised(
                b0 = alpha, b1 = 0.0, b2 = -alpha,
                a0 = 1 + alpha, a1 = -2 * cosw, a2 = 1 - alpha,
            )
        }

        public fun notch(frequency: Double, sampleRate: Int, q: Double = 8.0): Biquad {
            val w = 2.0 * PI * frequency / sampleRate
            val alpha = sin(w) / (2.0 * q)
            val cosw = cos(w)
            return normalised(
                b0 = 1.0, b1 = -2 * cosw, b2 = 1.0,
                a0 = 1 + alpha, a1 = -2 * cosw, a2 = 1 - alpha,
            )
        }

        /** A bell. The workhorse of the parametric equaliser. */
        public fun peaking(frequency: Double, sampleRate: Int, gainDb: Double, q: Double = 1.0): Biquad {
            val a = Math.pow(10.0, gainDb / 40.0)
            val w = 2.0 * PI * frequency / sampleRate
            val alpha = sin(w) / (2.0 * q)
            val cosw = cos(w)
            return normalised(
                b0 = 1 + alpha * a, b1 = -2 * cosw, b2 = 1 - alpha * a,
                a0 = 1 + alpha / a, a1 = -2 * cosw, a2 = 1 - alpha / a,
            )
        }

        public fun lowShelf(frequency: Double, sampleRate: Int, gainDb: Double, slope: Double = 1.0): Biquad {
            val a = Math.pow(10.0, gainDb / 40.0)
            val w = 2.0 * PI * frequency / sampleRate
            val cosw = cos(w)
            val alpha = sin(w) / 2.0 * sqrt((a + 1 / a) * (1 / slope - 1) + 2)
            val twoSqrtAAlpha = 2 * sqrt(a) * alpha
            return normalised(
                b0 = a * ((a + 1) - (a - 1) * cosw + twoSqrtAAlpha),
                b1 = 2 * a * ((a - 1) - (a + 1) * cosw),
                b2 = a * ((a + 1) - (a - 1) * cosw - twoSqrtAAlpha),
                a0 = (a + 1) + (a - 1) * cosw + twoSqrtAAlpha,
                a1 = -2 * ((a - 1) + (a + 1) * cosw),
                a2 = (a + 1) + (a - 1) * cosw - twoSqrtAAlpha,
            )
        }

        public fun highShelf(frequency: Double, sampleRate: Int, gainDb: Double, slope: Double = 1.0): Biquad {
            val a = Math.pow(10.0, gainDb / 40.0)
            val w = 2.0 * PI * frequency / sampleRate
            val cosw = cos(w)
            val alpha = sin(w) / 2.0 * sqrt((a + 1 / a) * (1 / slope - 1) + 2)
            val twoSqrtAAlpha = 2 * sqrt(a) * alpha
            return normalised(
                b0 = a * ((a + 1) + (a - 1) * cosw + twoSqrtAAlpha),
                b1 = -2 * a * ((a - 1) + (a + 1) * cosw),
                b2 = a * ((a + 1) + (a - 1) * cosw - twoSqrtAAlpha),
                a0 = (a + 1) - (a - 1) * cosw + twoSqrtAAlpha,
                a1 = 2 * ((a - 1) - (a + 1) * cosw),
                a2 = (a + 1) - (a - 1) * cosw - twoSqrtAAlpha,
            )
        }

        /** Raw coefficients, for filters defined by a standard rather than by a design formula. */
        public fun of(b0: Double, b1: Double, b2: Double, a1: Double, a2: Double): Biquad =
            Biquad(b0, b1, b2, a1, a2)

        /** Bandwidth in octaves converted to Q, for interfaces that speak in octaves. */
        public fun qFromBandwidth(octaves: Double): Double {
            val ln2Half = 0.5 * kotlin.math.ln(2.0) * octaves
            return 1.0 / (2.0 * sinh(ln2Half))
        }
    }
}

/** One band of the parametric equaliser. */
public data class EqBand(
    val type: Type,
    val frequency: Double,
    val gainDb: Double = 0.0,
    val q: Double = 1.0,
    val enabled: Boolean = true,
) {
    public enum class Type { HIGH_PASS, LOW_SHELF, PEAKING, HIGH_SHELF, LOW_PASS, NOTCH }

    public fun build(sampleRate: Int): Biquad = when (type) {
        Type.HIGH_PASS -> Biquad.highPass(frequency, sampleRate, q)
        Type.LOW_SHELF -> Biquad.lowShelf(frequency, sampleRate, gainDb)
        Type.PEAKING -> Biquad.peaking(frequency, sampleRate, gainDb, q)
        Type.HIGH_SHELF -> Biquad.highShelf(frequency, sampleRate, gainDb)
        Type.LOW_PASS -> Biquad.lowPass(frequency, sampleRate, q)
        Type.NOTCH -> Biquad.notch(frequency, sampleRate, q)
    }
}

/**
 * A parametric equaliser: bands in series, each an independent biquad per channel.
 *
 * Per-channel filter state is what keeps stereo from smearing — sharing one filter across
 * channels sums their histories and collapses the image.
 */
public class Equaliser(public val bands: List<EqBand>, public val sampleRate: Int) {

    private val active = bands.filter { it.enabled }

    /** Filters a buffer in place. */
    public fun process(buffer: AudioBuffer): AudioBuffer {
        require(buffer.sampleRate == sampleRate) {
            "Equaliser built for $sampleRate Hz, given ${buffer.sampleRate} Hz"
        }
        for (channel in buffer.channels) {
            for (band in active) {
                band.build(sampleRate).process(channel)
            }
        }
        return buffer
    }

    /** The combined response, for drawing the curve. */
    public fun magnitudeDbAt(frequency: Double): Double =
        active.sumOf { it.build(sampleRate).magnitudeDbAt(frequency, sampleRate) }

    /** The curve sampled logarithmically from 20 Hz to 20 kHz, ready to plot. */
    public fun curve(points: Int = 128): DoubleArray {
        val lowest = kotlin.math.ln(20.0)
        val highest = kotlin.math.ln(20_000.0)
        return DoubleArray(points) { i ->
            val frequency = kotlin.math.exp(lowest + (highest - lowest) * i / (points - 1))
            magnitudeDbAt(frequency)
        }
    }
}
