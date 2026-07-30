package com.sajjil.core.dsp

import kotlin.math.PI
import kotlin.math.pow
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Direct Form I biquad, coefficients per Robert Bristow-Johnson's Audio EQ Cookbook.
 * Operates on normalized float samples in [-1, 1].
 */
class BiquadFilter private constructor(
    private var b0: Double,
    private var b1: Double,
    private var b2: Double,
    private var a1: Double,
    private var a2: Double,
) {
    private var x1 = 0.0
    private var x2 = 0.0
    private var y1 = 0.0
    private var y2 = 0.0

    fun reset() {
        x1 = 0.0; x2 = 0.0; y1 = 0.0; y2 = 0.0
    }

    fun setCoefficients(b0: Double, b1: Double, b2: Double, a1: Double, a2: Double) {
        this.b0 = b0; this.b1 = b1; this.b2 = b2; this.a1 = a1; this.a2 = a2
    }

    /** Recomputes this filter as a peaking (bell) stage, preserving its delay-line state. */
    fun updateAsPeaking(freqHz: Double, sampleRate: Double, q: Double, gainDb: Double) {
        val a = 10.0.pow(gainDb / 40.0)
        val w0 = omega(freqHz, sampleRate)
        val alpha = alphaFromQ(w0, q)
        val cosW0 = kotlin.math.cos(w0)
        val a0 = 1 + alpha / a
        setCoefficients(
            b0 = (1 + alpha * a) / a0,
            b1 = (-2 * cosW0) / a0,
            b2 = (1 - alpha * a) / a0,
            a1 = (-2 * cosW0) / a0,
            a2 = (1 - alpha / a) / a0,
        )
    }

    fun process(sample: Float): Float {
        val x0 = sample.toDouble()
        val y0 = b0 * x0 + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2 = x1; x1 = x0
        y2 = y1; y1 = y0
        return y0.toFloat()
    }

    fun processBlock(samples: FloatArray) {
        for (i in samples.indices) samples[i] = process(samples[i])
    }

    companion object {
        internal fun omega(freqHz: Double, sampleRate: Double) = 2.0 * PI * freqHz / sampleRate
        internal fun alphaFromQ(w0: Double, q: Double) = sin(w0) / (2.0 * q)

        fun peaking(freqHz: Double, sampleRate: Double, q: Double, gainDb: Double): BiquadFilter {
            val a = 10.0.pow(gainDb / 40.0)
            val w0 = omega(freqHz, sampleRate)
            val alpha = alphaFromQ(w0, q)
            val cosW0 = kotlin.math.cos(w0)
            val a0 = 1 + alpha / a
            val b0 = (1 + alpha * a) / a0
            val b1 = (-2 * cosW0) / a0
            val b2 = (1 - alpha * a) / a0
            val a1 = (-2 * cosW0) / a0
            val a2 = (1 - alpha / a) / a0
            return BiquadFilter(b0, b1, b2, a1, a2)
        }

        fun lowShelf(freqHz: Double, sampleRate: Double, gainDb: Double, slope: Double = 1.0): BiquadFilter {
            val a = 10.0.pow(gainDb / 40.0)
            val w0 = omega(freqHz, sampleRate)
            val cosW0 = kotlin.math.cos(w0)
            val sinW0 = sin(w0)
            val alpha = sinW0 / 2.0 * sqrt((a + 1 / a) * (1 / slope - 1) + 2)
            val twoSqrtAAlpha = 2 * sqrt(a) * alpha
            val a0 = (a + 1) + (a - 1) * cosW0 + twoSqrtAAlpha
            val b0 = a * ((a + 1) - (a - 1) * cosW0 + twoSqrtAAlpha) / a0
            val b1 = 2 * a * ((a - 1) - (a + 1) * cosW0) / a0
            val b2 = a * ((a + 1) - (a - 1) * cosW0 - twoSqrtAAlpha) / a0
            val a1 = -2 * ((a - 1) + (a + 1) * cosW0) / a0
            val a2 = ((a + 1) + (a - 1) * cosW0 - twoSqrtAAlpha) / a0
            return BiquadFilter(b0, b1, b2, a1, a2)
        }

        fun highShelf(freqHz: Double, sampleRate: Double, gainDb: Double, slope: Double = 1.0): BiquadFilter {
            val a = 10.0.pow(gainDb / 40.0)
            val w0 = omega(freqHz, sampleRate)
            val cosW0 = kotlin.math.cos(w0)
            val sinW0 = sin(w0)
            val alpha = sinW0 / 2.0 * sqrt((a + 1 / a) * (1 / slope - 1) + 2)
            val twoSqrtAAlpha = 2 * sqrt(a) * alpha
            val a0 = (a + 1) - (a - 1) * cosW0 + twoSqrtAAlpha
            val b0 = a * ((a + 1) + (a - 1) * cosW0 + twoSqrtAAlpha) / a0
            val b1 = -2 * a * ((a - 1) + (a + 1) * cosW0) / a0
            val b2 = a * ((a + 1) + (a - 1) * cosW0 - twoSqrtAAlpha) / a0
            val a1 = 2 * ((a - 1) - (a + 1) * cosW0) / a0
            val a2 = ((a + 1) - (a - 1) * cosW0 - twoSqrtAAlpha) / a0
            return BiquadFilter(b0, b1, b2, a1, a2)
        }

        fun lowPass(freqHz: Double, sampleRate: Double, q: Double = 0.7071): BiquadFilter {
            val w0 = omega(freqHz, sampleRate)
            val alpha = alphaFromQ(w0, q)
            val cosW0 = kotlin.math.cos(w0)
            val a0 = 1 + alpha
            val b1 = (1 - cosW0) / a0
            val b0 = b1 / 2.0
            val b2 = b0
            val a1 = (-2 * cosW0) / a0
            val a2 = (1 - alpha) / a0
            return BiquadFilter(b0, b1, b2, a1, a2)
        }

        fun highPass(freqHz: Double, sampleRate: Double, q: Double = 0.7071): BiquadFilter {
            val w0 = omega(freqHz, sampleRate)
            val alpha = alphaFromQ(w0, q)
            val cosW0 = kotlin.math.cos(w0)
            val a0 = 1 + alpha
            val b0 = (1 + cosW0) / 2.0 / a0
            val b1 = -(1 + cosW0) / a0
            val b2 = b0
            val a1 = (-2 * cosW0) / a0
            val a2 = (1 - alpha) / a0
            return BiquadFilter(b0, b1, b2, a1, a2)
        }
    }
}
