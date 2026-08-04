package ai.sajjil.audio.dsp

import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Normalised biquad coefficients (a0 divided out), in the usual direct-form-I ordering:
 *
 *     y[n] = b0*x[n] + b1*x[n-1] + b2*x[n-2] - a1*y[n-1] - a2*y[n-2]
 */
data class BiquadCoefficients(
    val b0: Double,
    val b1: Double,
    val b2: Double,
    val a1: Double,
    val a2: Double,
) {
    /**
     * Magnitude response at [frequency] Hz for a filter running at [sampleRate].
     * Used by the tests to assert that each design actually does what its name says.
     */
    fun magnitudeAt(frequency: Double, sampleRate: Int): Double {
        val w = 2.0 * PI * frequency / sampleRate
        val cw = cos(w)
        val c2w = cos(2 * w)
        val sw = sin(w)
        val s2w = sin(2 * w)
        val numRe = b0 + b1 * cw + b2 * c2w
        val numIm = -(b1 * sw + b2 * s2w)
        val denRe = 1.0 + a1 * cw + a2 * c2w
        val denIm = -(a1 * sw + a2 * s2w)
        val num = sqrt(numRe * numRe + numIm * numIm)
        val den = sqrt(denRe * denRe + denIm * denIm)
        return if (den == 0.0) Double.POSITIVE_INFINITY else num / den
    }

    companion object {
        val PASSTHROUGH = BiquadCoefficients(1.0, 0.0, 0.0, 0.0, 0.0)
    }
}

/**
 * Robert Bristow-Johnson's audio EQ cookbook designs.
 *
 * These are the standard formulas; they are here rather than pulled from a library so the whole
 * signal path stays dependency-free and unit-testable on a plain JVM.
 */
object BiquadDesign {

    private fun omega(frequency: Double, sampleRate: Int): Double {
        // Clamp just below Nyquist: the bilinear transform blows up as w -> pi.
        val nyquist = sampleRate / 2.0
        val f = frequency.coerceIn(1.0, nyquist * 0.999)
        return 2.0 * PI * f / sampleRate
    }

    fun lowPass(frequency: Double, sampleRate: Int, q: Double = 0.7071): BiquadCoefficients {
        val w = omega(frequency, sampleRate)
        val cw = cos(w)
        val alpha = sin(w) / (2.0 * q)
        val a0 = 1.0 + alpha
        return BiquadCoefficients(
            b0 = ((1.0 - cw) / 2.0) / a0,
            b1 = (1.0 - cw) / a0,
            b2 = ((1.0 - cw) / 2.0) / a0,
            a1 = (-2.0 * cw) / a0,
            a2 = (1.0 - alpha) / a0,
        )
    }

    fun highPass(frequency: Double, sampleRate: Int, q: Double = 0.7071): BiquadCoefficients {
        val w = omega(frequency, sampleRate)
        val cw = cos(w)
        val alpha = sin(w) / (2.0 * q)
        val a0 = 1.0 + alpha
        return BiquadCoefficients(
            b0 = ((1.0 + cw) / 2.0) / a0,
            b1 = (-(1.0 + cw)) / a0,
            b2 = ((1.0 + cw) / 2.0) / a0,
            a1 = (-2.0 * cw) / a0,
            a2 = (1.0 - alpha) / a0,
        )
    }

    fun bandPass(frequency: Double, sampleRate: Int, q: Double = 1.0): BiquadCoefficients {
        val w = omega(frequency, sampleRate)
        val cw = cos(w)
        val alpha = sin(w) / (2.0 * q)
        val a0 = 1.0 + alpha
        return BiquadCoefficients(
            b0 = alpha / a0,
            b1 = 0.0,
            b2 = -alpha / a0,
            a1 = (-2.0 * cw) / a0,
            a2 = (1.0 - alpha) / a0,
        )
    }

    /**
     * Notch with the width expressed as a bandwidth in Hz, which is how hum removal wants to
     * think about it (a 50 Hz harmonic needs a fixed-Hz notch, not a fixed-Q one).
     */
    fun notch(frequency: Double, sampleRate: Int, bandwidthHz: Double): BiquadCoefficients {
        val w = omega(frequency, sampleRate)
        val cw = cos(w)
        // Q and -3 dB bandwidth are related by Q = f0 / bandwidth.
        val q = (frequency / bandwidthHz.coerceAtLeast(0.1)).coerceIn(0.1, 1000.0)
        val alpha = sin(w) / (2.0 * q)
        val a0 = 1.0 + alpha
        return BiquadCoefficients(
            b0 = 1.0 / a0,
            b1 = (-2.0 * cw) / a0,
            b2 = 1.0 / a0,
            a1 = (-2.0 * cw) / a0,
            a2 = (1.0 - alpha) / a0,
        )
    }

    fun peaking(frequency: Double, sampleRate: Int, gainDb: Double, q: Double = 1.0): BiquadCoefficients {
        if (abs(gainDb) < 1e-6) return BiquadCoefficients.PASSTHROUGH
        val a = Math.pow(10.0, gainDb / 40.0)
        val w = omega(frequency, sampleRate)
        val cw = cos(w)
        val alpha = sin(w) / (2.0 * q)
        val a0 = 1.0 + alpha / a
        return BiquadCoefficients(
            b0 = (1.0 + alpha * a) / a0,
            b1 = (-2.0 * cw) / a0,
            b2 = (1.0 - alpha * a) / a0,
            a1 = (-2.0 * cw) / a0,
            a2 = (1.0 - alpha / a) / a0,
        )
    }

    fun lowShelf(frequency: Double, sampleRate: Int, gainDb: Double, slope: Double = 1.0): BiquadCoefficients {
        if (abs(gainDb) < 1e-6) return BiquadCoefficients.PASSTHROUGH
        val a = Math.pow(10.0, gainDb / 40.0)
        val w = omega(frequency, sampleRate)
        val cw = cos(w)
        val alpha = sin(w) / 2.0 * sqrt((a + 1 / a) * (1 / slope - 1) + 2)
        val twoSqrtAAlpha = 2.0 * sqrt(a) * alpha
        val a0 = (a + 1) + (a - 1) * cw + twoSqrtAAlpha
        return BiquadCoefficients(
            b0 = (a * ((a + 1) - (a - 1) * cw + twoSqrtAAlpha)) / a0,
            b1 = (2 * a * ((a - 1) - (a + 1) * cw)) / a0,
            b2 = (a * ((a + 1) - (a - 1) * cw - twoSqrtAAlpha)) / a0,
            a1 = (-2 * ((a - 1) + (a + 1) * cw)) / a0,
            a2 = ((a + 1) + (a - 1) * cw - twoSqrtAAlpha) / a0,
        )
    }

    fun highShelf(frequency: Double, sampleRate: Int, gainDb: Double, slope: Double = 1.0): BiquadCoefficients {
        if (abs(gainDb) < 1e-6) return BiquadCoefficients.PASSTHROUGH
        val a = Math.pow(10.0, gainDb / 40.0)
        val w = omega(frequency, sampleRate)
        val cw = cos(w)
        val alpha = sin(w) / 2.0 * sqrt((a + 1 / a) * (1 / slope - 1) + 2)
        val twoSqrtAAlpha = 2.0 * sqrt(a) * alpha
        val a0 = (a + 1) - (a - 1) * cw + twoSqrtAAlpha
        return BiquadCoefficients(
            b0 = (a * ((a + 1) + (a - 1) * cw + twoSqrtAAlpha)) / a0,
            b1 = (-2 * a * ((a - 1) + (a + 1) * cw)) / a0,
            b2 = (a * ((a + 1) + (a - 1) * cw - twoSqrtAAlpha)) / a0,
            a1 = (2 * ((a - 1) - (a + 1) * cw)) / a0,
            a2 = ((a + 1) - (a - 1) * cw - twoSqrtAAlpha) / a0,
        )
    }
}

/**
 * A single biquad section holding its own delay line, processed in transposed direct form II
 * (better numerical behaviour at low frequencies than direct form I, and only two state words).
 */
class Biquad(coefficients: BiquadCoefficients = BiquadCoefficients.PASSTHROUGH) {

    var coefficients: BiquadCoefficients = coefficients
        set(value) {
            field = value
            // Deliberately does NOT reset state: presets are re-applied between blocks and
            // zeroing here would click on every parameter change.
        }

    private var z1 = 0.0
    private var z2 = 0.0

    fun reset() {
        z1 = 0.0
        z2 = 0.0
    }

    fun processSample(x: Double): Double {
        val c = coefficients
        val y = c.b0 * x + z1
        z1 = c.b1 * x - c.a1 * y + z2
        z2 = c.b2 * x - c.a2 * y
        return y
    }

    fun process(samples: FloatArray, from: Int = 0, until: Int = samples.size) {
        for (i in from until until) {
            samples[i] = processSample(samples[i].toDouble()).toFloat()
        }
    }
}

/** A cascade of biquads sharing one input, applied in order. */
class BiquadChain(sections: List<BiquadCoefficients>) {
    private val stages = sections.map { Biquad(it) }

    val stageCount: Int get() = stages.size

    fun reset() = stages.forEach { it.reset() }

    fun processSample(x: Double): Double {
        var y = x
        for (stage in stages) y = stage.processSample(y)
        return y
    }

    fun process(samples: FloatArray) {
        for (i in samples.indices) {
            samples[i] = processSample(samples[i].toDouble()).toFloat()
        }
    }
}
