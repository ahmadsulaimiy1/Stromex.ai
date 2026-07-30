package com.sajjil.core.analysis

import kotlin.math.PI
import kotlin.math.sin
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class LiveDirectorTest {
    private val sampleRate = 48000

    private fun tone(amplitude: Double, seconds: Double = 0.5) =
        FloatArray((sampleRate * seconds).toInt()) { i -> (amplitude * sin(2.0 * PI * 300 * i / sampleRate)).toFloat() }

    @Test
    fun `empty buffer returns a neutral listening state`() {
        val guidance = LiveDirector.assess(FloatArray(0))
        assertEquals(GuidanceSeverity.INFO, guidance.severity)
        assertTrue(guidance.suggestedGainAdjustmentDb == null)
    }

    @Test
    fun `clipping is flagged and suggests lowering gain`() {
        val samples = FloatArray(1000) { if (it % 2 == 0) 1.0f else -1.0f }
        val guidance = LiveDirector.assess(samples)
        assertTrue(guidance.isClipping)
        assertEquals(GuidanceSeverity.WARNING, guidance.severity)
        assertTrue(guidance.suggestedGainAdjustmentDb!! < 0)
    }

    @Test
    fun `a signal near the target peak reads as good`() {
        // -6 dBFS amplitude ~= 0.501
        val guidance = LiveDirector.assess(tone(amplitude = 0.501), targetPeakDb = -6.0)
        assertEquals(GuidanceSeverity.GOOD, guidance.severity)
        assertFalse(guidance.isClipping)
    }

    @Test
    fun `a very quiet signal suggests raising gain by roughly the right amount`() {
        // -40 dBFS amplitude
        val amplitude = 0.01
        val guidance = LiveDirector.assess(tone(amplitude), targetPeakDb = -6.0)
        assertTrue(guidance.severity == GuidanceSeverity.WARNING)
        assertTrue(guidance.suggestedGainAdjustmentDb!! > 20.0, "expected a large positive gain suggestion, got ${guidance.suggestedGainAdjustmentDb}")
    }

    @Test
    fun `a hot but non-clipping signal suggests lowering gain`() {
        // -1 dBFS amplitude, well above -6dB target but not clipping
        val guidance = LiveDirector.assess(tone(amplitude = 0.89), targetPeakDb = -6.0)
        assertFalse(guidance.isClipping)
        assertEquals(GuidanceSeverity.WARNING, guidance.severity)
        assertTrue(guidance.suggestedGainAdjustmentDb!! < 0)
    }
}
