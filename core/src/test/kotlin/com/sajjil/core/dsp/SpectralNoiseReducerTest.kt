package com.sajjil.core.dsp

import kotlin.math.PI
import kotlin.math.sin
import kotlin.math.sqrt
import kotlin.random.Random
import kotlin.test.Test
import kotlin.test.assertTrue

class SpectralNoiseReducerTest {
    private val sampleRate = 48000

    private fun rms(samples: FloatArray): Double {
        var sum = 0.0
        for (s in samples) sum += s.toDouble() * s
        return sqrt(sum / samples.size)
    }

    @Test
    fun `reduces broadband noise floor while preserving a tone`() {
        val random = Random(42)
        val n = sampleRate * 2
        val noiseOnly = FloatArray(sampleRate) { (random.nextFloat() - 0.5f) * 0.08f }
        val toneWithNoise = FloatArray(n) { i ->
            val tone = 0.4f * sin(2.0 * PI * 300.0 * i / sampleRate).toFloat()
            val noise = (random.nextFloat() - 0.5f) * 0.08f
            tone + noise
        }

        val reducer = SpectralNoiseReducer(sampleRate)
        reducer.learnNoiseProfile(noiseOnly)
        val cleaned = reducer.process(toneWithNoise, NoiseReductionStrength.STRONG)

        val silentSegmentBefore = FloatArray(sampleRate) { (random.nextFloat() - 0.5f) * 0.08f }
        val silentSegmentAfter = reducer.process(silentSegmentBefore, NoiseReductionStrength.STRONG)

        val rmsBefore = rms(silentSegmentBefore)
        val rmsAfter = rms(silentSegmentAfter)
        assertTrue(rmsAfter < rmsBefore * 0.6, "expected noise floor reduced: before=$rmsBefore after=$rmsAfter")

        // Output should be the same length as input.
        assertTrue(cleaned.size == toneWithNoise.size)
    }

    @Test
    fun `short buffers below one frame are returned unchanged`() {
        val reducer = SpectralNoiseReducer(sampleRate, frameSize = 1024)
        val samples = FloatArray(100) { 0.1f }
        val result = reducer.process(samples)
        assertTrue(result.contentEquals(samples))
    }
}
