package com.sajjil.core.dsp

import kotlin.math.PI
import kotlin.math.log10
import kotlin.math.sin
import kotlin.math.sqrt
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class AudioRestorationTest {
    private val sampleRate = 8000

    @Test
    fun `normalizePeak brings a quiet buffer up to the target peak`() {
        val quiet = FloatArray(4000) { i -> (0.02 * sin(i * 0.1)).toFloat() }
        val normalized = AudioRestoration.normalizePeak(quiet, targetPeakDb = -1.0)
        val peak = normalized.maxOf { kotlin.math.abs(it) }
        val peakDb = 20.0 * log10(peak.toDouble())
        assertTrue(kotlin.math.abs(peakDb - -1.0) < 0.5, "expected peak near -1dB, got $peakDb")
    }

    @Test
    fun `normalizePeak on silence is a no-op, not a divide-by-zero crash`() {
        val silence = FloatArray(1000)
        val result = AudioRestoration.normalizePeak(silence)
        assertTrue(result.all { it == 0f })
    }

    @Test
    fun `damage score is zero for clean audio and positive for heavily clipped audio`() {
        val clean = FloatArray(4000) { i -> (0.3 * sin(i * 0.1)).toFloat() }
        assertEquals(0, AudioRestoration.estimateDamageScore(clean))

        val clipped = FloatArray(4000) { i -> (2.0 * sin(i * 0.1)).toFloat().coerceIn(-1f, 1f) }
        assertTrue(AudioRestoration.estimateDamageScore(clipped) > 20)
    }

    @Test
    fun `restore pipeline returns a buffer of the same length`() {
        val damaged = FloatArray(sampleRate) { i -> (1.5 * sin(2.0 * PI * 300 * i / sampleRate)).toFloat().coerceIn(-1f, 1f) }
        val restored = AudioRestoration.restore(damaged, sampleRate)
        assertEquals(damaged.size, restored.size)
    }
}
