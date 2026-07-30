package com.sajjil.core.analysis

import kotlin.math.exp
import kotlin.math.ln
import kotlin.random.Random
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

class AcousticAnalyzerTest {
    private val sampleRate = 16000

    /** A noise burst whose envelope decays exponentially to a known RT60. */
    private fun decayBurst(targetRt60: Double, durationSeconds: Double, floor: Float = 0.001f): FloatArray {
        val random = Random(7)
        val tau = targetRt60 / ln(1000.0) // -60dB = amplitude ratio 1/1000
        val n = (sampleRate * durationSeconds).toInt()
        return FloatArray(n) { i ->
            val t = i.toDouble() / sampleRate
            val envelope = exp(-t / tau).toFloat()
            (random.nextFloat() - 0.5f) * 2f * (envelope.coerceAtLeast(floor))
        }
    }

    @Test
    fun `estimates RT60 within a reasonable margin for a synthetic decay`() {
        val burst = decayBurst(targetRt60 = 0.8, durationSeconds = 1.5)
        val silenceGap = FloatArray((sampleRate * 0.3).toInt()) { (Random(1).nextFloat() - 0.5f) * 0.0005f }
        val signal = burst + silenceGap + burst + silenceGap + burst

        val estimate = AcousticAnalyzer.estimateRt60(signal, sampleRate)
        assertTrue(estimate != null, "expected a non-null RT60 estimate")
        assertTrue(estimate in 0.3..1.6, "expected estimate near 0.8s, got $estimate")
    }

    @Test
    fun `returns null RT60 for near-silent buffers with no usable decay`() {
        val silence = FloatArray(sampleRate) { (Random(3).nextFloat() - 0.5f) * 0.0005f }
        assertNull(AcousticAnalyzer.estimateRt60(silence, sampleRate))
    }

    @Test
    fun `flags clipping risk when many samples sit at full scale`() {
        val clipped = FloatArray(1000) { if (it % 3 == 0) 1.0f else 0.1f }
        val profile = AcousticAnalyzer.analyze(clipped, sampleRate)
        assertTrue(profile.clippingRiskPercent > 20.0, "expected high clipping risk, got ${profile.clippingRiskPercent}")
    }

    @Test
    fun `reports no clipping risk for a clean quiet signal`() {
        val clean = FloatArray(sampleRate) { i -> (0.1 * kotlin.math.sin(i * 0.05)).toFloat() }
        val profile = AcousticAnalyzer.analyze(clean, sampleRate)
        assertEquals(0.0, profile.clippingRiskPercent)
    }

    @Test
    fun `classifies severe echo and recommends a large-space profile for long decay`() {
        val burst = decayBurst(targetRt60 = 1.8, durationSeconds = 2.5)
        val profile = AcousticAnalyzer.analyze(burst, sampleRate)
        assertTrue(
            profile.echoSeverity == EchoSeverity.HIGH || profile.echoSeverity == EchoSeverity.SEVERE,
            "expected high/severe echo classification, got ${profile.echoSeverity}",
        )
        assertTrue(profile.recommendations.isNotEmpty())
    }

    @Test
    fun `quiet clean short room gives a ready-to-record recommendation`() {
        val clean = FloatArray(sampleRate) { i -> (0.2 * kotlin.math.sin(i * 0.05)).toFloat() }
        val profile = AcousticAnalyzer.analyze(clean, sampleRate)
        assertTrue(profile.recommendations.isNotEmpty())
    }
}
