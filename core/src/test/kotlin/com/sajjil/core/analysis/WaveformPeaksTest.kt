package com.sajjil.core.analysis

import kotlin.math.PI
import kotlin.math.sin
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class WaveformPeaksTest {
    @Test
    fun `returns the requested number of buckets`() {
        val samples = FloatArray(4800) { 0.1f }
        val peaks = WaveformPeaks.compute(samples, 120)
        assertEquals(120, peaks.size)
    }

    @Test
    fun `empty input yields all-silent buckets, not a crash`() {
        val peaks = WaveformPeaks.compute(FloatArray(0), 50)
        assertEquals(50, peaks.size)
        assertTrue(peaks.all { it == 0f })
    }

    @Test
    fun `louder region produces a higher peak than a silent region`() {
        val sampleRate = 48000
        val silentHalf = FloatArray(sampleRate)
        val loudHalf = FloatArray(sampleRate) { (0.8 * sin(2.0 * PI * 440 * it / sampleRate)).toFloat() }
        val samples = silentHalf + loudHalf

        val peaks = WaveformPeaks.compute(samples, 10)

        val firstHalfPeak = peaks.take(5).max()
        val secondHalfPeak = peaks.drop(5).max()
        assertTrue(secondHalfPeak > firstHalfPeak, "expected the loud half's buckets to peak higher: $peaks")
    }

    @Test
    fun `peaks are always within 0 to 1`() {
        val samples = FloatArray(48000) { (2.0 * sin(2.0 * PI * 440 * it / 48000)).toFloat() } // deliberately out-of-range input
        val peaks = WaveformPeaks.compute(samples, 30)
        assertTrue(peaks.all { it in 0f..1f }, "peaks must be clamped: $peaks")
    }

    @Test
    fun `fewer samples than buckets does not crash and stays in range`() {
        val samples = FloatArray(5) { 0.5f }
        val peaks = WaveformPeaks.compute(samples, 40)
        assertEquals(40, peaks.size)
        assertTrue(peaks.all { it in 0f..1f })
    }
}
