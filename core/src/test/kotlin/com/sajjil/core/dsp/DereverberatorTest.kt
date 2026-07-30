package com.sajjil.core.dsp

import kotlin.math.PI
import kotlin.math.exp
import kotlin.math.ln
import kotlin.math.sin
import kotlin.math.sqrt
import kotlin.random.Random
import kotlin.test.Test
import kotlin.test.assertTrue

class DereverberatorTest {
    private val sampleRate = 8000

    private fun rms(samples: FloatArray, from: Int, to: Int): Double {
        var sum = 0.0
        for (i in from until to) sum += samples[i].toDouble() * samples[i]
        return sqrt(sum / (to - from))
    }

    private fun convolve(dry: FloatArray, ir: FloatArray): FloatArray {
        val out = FloatArray(dry.size)
        for (n in dry.indices) {
            var sum = 0.0
            val maxK = minOf(ir.size, n + 1)
            for (k in 0 until maxK) sum += dry[n - k] * ir[k]
            out[n] = sum.toFloat()
        }
        return out
    }

    @Test
    fun `reduces reverberant tail energy left after a burst ends`() {
        val random = Random(11)
        val rt60 = 0.35
        val tau = rt60 / ln(1000.0)
        val irLength = (sampleRate * 0.3).toInt()
        val ir = FloatArray(irLength) { n ->
            val t = n.toDouble() / sampleRate
            ((random.nextFloat() - 0.5f) * 2f) * exp(-t / tau).toFloat()
        }
        // Normalize the IR so the convolution doesn't blow up amplitude.
        val irPeak = ir.maxOf { kotlin.math.abs(it) }.coerceAtLeast(1e-6f)
        for (i in ir.indices) ir[i] = ir[i] / irPeak * 0.6f

        val burstLength = (sampleRate * 0.1).toInt()
        val silenceLength = (sampleRate * 0.4).toInt()
        val dry = FloatArray(burstLength + silenceLength) { i ->
            if (i < burstLength) (0.8 * sin(2.0 * PI * 300.0 * i / sampleRate)).toFloat() else 0f
        }

        val reverberant = convolve(dry, ir)

        val dereverberator = Dereverberator(sampleRate)
        val cleaned = dereverberator.process(reverberant, rt60Seconds = rt60, strength = 1.5, spectralFloor = 0.02)

        val tailStart = burstLength + (sampleRate * 0.05).toInt()
        val tailEnd = burstLength + (sampleRate * 0.35).toInt()
        val tailBefore = rms(reverberant, tailStart, tailEnd)
        val tailAfter = rms(cleaned, tailStart, tailEnd)

        assertTrue(tailAfter < tailBefore, "expected tail energy reduced: before=$tailBefore after=$tailAfter")
    }

    @Test
    fun `passes short buffers through unchanged`() {
        val samples = FloatArray(100) { 0.1f }
        val result = Dereverberator(sampleRate).process(samples, rt60Seconds = 0.5)
        assertTrue(result.contentEquals(samples))
    }

    @Test
    fun `zero or negative RT60 is a no-op`() {
        val samples = FloatArray(4000) { 0.1f }
        val result = Dereverberator(sampleRate).process(samples, rt60Seconds = 0.0)
        assertTrue(result.contentEquals(samples))
    }
}
