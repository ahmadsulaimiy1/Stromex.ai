package com.sajjil.core.dsp

import kotlin.math.sqrt
import kotlin.random.Random
import kotlin.test.Test
import kotlin.test.assertTrue

class ReferenceMatcherTest {
    private val sampleRate = 48000

    private fun highBandEnergy(samples: FloatArray): Double {
        val hp = BiquadFilter.highPass(6000.0, sampleRate.toDouble())
        var sum = 0.0
        for (s in samples) {
            val y = hp.process(s)
            sum += y.toDouble() * y
        }
        return sqrt(sum / samples.size)
    }

    @Test
    fun `matching a dark source to a bright reference restores high-frequency energy`() {
        val random = Random(21)
        val n = sampleRate * 2
        val whiteNoise = FloatArray(n) { (random.nextFloat() - 0.5f) * 0.5f }

        // "Dark" source: same noise with highs rolled off.
        val darkFilter = BiquadFilter.lowPass(1500.0, sampleRate.toDouble())
        val darkSource = whiteNoise.copyOf()
        darkFilter.processBlock(darkSource)

        val matched = ReferenceMatcher.matchToReference(sampleRate, darkSource, whiteNoise, maxCorrectionDb = 12.0)

        val darkHighEnergy = highBandEnergy(darkSource)
        val matchedHighEnergy = highBandEnergy(matched)

        assertTrue(
            matchedHighEnergy > darkHighEnergy * 2,
            "expected matching to noticeably restore high-frequency energy: dark=$darkHighEnergy matched=$matchedHighEnergy",
        )
    }

    @Test
    fun `matching a source to itself yields a near-flat correction`() {
        val random = Random(5)
        val samples = FloatArray(sampleRate * 2) { (random.nextFloat() - 0.5f) * 0.4f }
        val matched = ReferenceMatcher.matchToReference(sampleRate, samples, samples)

        var sumSquareDiff = 0.0
        for (i in samples.indices) sumSquareDiff += (matched[i] - samples[i]).toDouble().let { it * it }
        val rmsDiff = sqrt(sumSquareDiff / samples.size)
        assertTrue(rmsDiff < 0.05, "expected near-identity when matching a signal to itself, got rmsDiff=$rmsDiff")
    }
}
