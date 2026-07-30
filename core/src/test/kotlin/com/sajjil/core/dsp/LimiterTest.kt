package com.sajjil.core.dsp

import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.pow
import kotlin.math.sin
import kotlin.test.Test
import kotlin.test.assertTrue

class LimiterTest {
    private val sampleRate = 48000

    @Test
    fun `output never exceeds the configured ceiling`() {
        val limiter = Limiter(sampleRate, ceilingDb = -1.0)
        val ceilingLinear = 10.0.pow(-1.0 / 20.0).toFloat()
        var maxAbs = 0f
        for (i in 0 until sampleRate) {
            val x = (1.6 * sin(2.0 * PI * 440.0 * i / sampleRate)).toFloat() // intentionally over 0dBFS
            val y = limiter.process(x)
            if (abs(y) > maxAbs) maxAbs = abs(y)
        }
        assertTrue(maxAbs <= ceilingLinear + 1e-4f, "output peak $maxAbs exceeded ceiling $ceilingLinear")
    }

    @Test
    fun `signal well under ceiling passes through near unity`() {
        val limiter = Limiter(sampleRate, ceilingDb = -0.3)
        var maxAbs = 0f
        for (i in 0 until sampleRate / 10) {
            val x = (0.1 * sin(2.0 * PI * 440.0 * i / sampleRate)).toFloat()
            val y = limiter.process(x)
            if (abs(y) > maxAbs) maxAbs = abs(y)
        }
        assertTrue(maxAbs in 0.08f..0.11f, "expected near-unity passthrough, got peak $maxAbs")
    }

    @Test
    fun `loudness maximizer raises level of a quiet signal while respecting ceiling`() {
        val maximizer = LoudnessMaximizer(sampleRate, driveDb = 12.0, ceilingDb = -0.3)
        val ceilingLinear = 10.0.pow(-0.3 / 20.0).toFloat()
        var maxAbs = 0f
        for (i in 0 until sampleRate) {
            val x = (0.05 * sin(2.0 * PI * 440.0 * i / sampleRate)).toFloat()
            val y = maximizer.process(x)
            if (abs(y) > maxAbs) maxAbs = abs(y)
        }
        assertTrue(maxAbs > 0.1f, "expected boosted level, got peak $maxAbs")
        assertTrue(maxAbs <= ceilingLinear + 1e-4f, "output exceeded ceiling: $maxAbs")
    }
}
