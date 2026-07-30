package com.sajjil.core.dsp

import kotlin.math.PI
import kotlin.math.sin
import kotlin.random.Random
import kotlin.test.Test
import kotlin.test.assertTrue

class AdaptiveMasteringEngineTest {
    private val sampleRate = 16000

    /** A tone that glides between two frequencies — stands in for sung/melodic pitch movement. */
    private fun melodicSweep(durationSeconds: Double = 3.0): FloatArray {
        val n = (sampleRate * durationSeconds).toInt()
        var phase = 0.0
        return FloatArray(n) { i ->
            val t = i.toDouble() / sampleRate
            val freq = 180.0 + 80.0 * sin(2.0 * PI * 0.5 * t) // glides 100-260Hz over ~2s cycles
            phase += 2.0 * PI * freq / sampleRate
            (0.5 * sin(phase)).toFloat()
        }
    }

    /** A constant-pitch tone with no vibrato — stands in for flat, monotone speech. */
    private fun monotone(durationSeconds: Double = 3.0, freq: Double = 150.0) =
        FloatArray((sampleRate * durationSeconds).toInt()) { i -> (0.5 * sin(2.0 * PI * freq * i / sampleRate)).toFloat() }

    private fun whiteNoise(durationSeconds: Double = 2.0): FloatArray {
        val random = Random(3)
        return FloatArray((sampleRate * durationSeconds).toInt()) { (random.nextFloat() - 0.5f) * 0.4f }
    }

    /** Long tone bursts separated by long silences — stands in for a lecture's deliberate pauses. */
    private fun longPausedSpeech(): FloatArray {
        val burst = monotone(durationSeconds = 1.0)
        val silence = FloatArray(sampleRate) { 0.0005f }
        return burst + silence + burst + silence + burst
    }

    @Test
    fun `melodic pitch movement scores higher variability than a monotone signal`() {
        val melodicFeatures = AdaptiveMasteringEngine.analyzeContent(melodicSweep(), sampleRate)
        val monotoneFeatures = AdaptiveMasteringEngine.analyzeContent(monotone(), sampleRate)
        assertTrue(
            melodicFeatures.pitchVariabilitySemitones > monotoneFeatures.pitchVariabilitySemitones,
            "expected melodic sweep (${melodicFeatures.pitchVariabilitySemitones}) to vary more than a monotone (${monotoneFeatures.pitchVariabilitySemitones})",
        )
    }

    @Test
    fun `long deliberate pauses are distinguished from a continuous tone`() {
        val paused = AdaptiveMasteringEngine.analyzeContent(longPausedSpeech(), sampleRate)
        val continuous = AdaptiveMasteringEngine.analyzeContent(monotone(durationSeconds = 3.0), sampleRate)
        assertTrue(
            paused.longPauseFraction > continuous.longPauseFraction,
            "expected the paused signal to show more long-pause structure",
        )
    }

    @Test
    fun `white noise reads as mostly unvoiced`() {
        val features = AdaptiveMasteringEngine.analyzeContent(whiteNoise(), sampleRate)
        assertTrue(features.voicedFraction < 0.3, "expected low voiced fraction for noise, got ${features.voicedFraction}")
    }

    @Test
    fun `a very short buffer degrades gracefully instead of crashing`() {
        val features = AdaptiveMasteringEngine.analyzeContent(FloatArray(50), sampleRate)
        assertTrue(features.pauseRatio == 0.0 && features.pitchVariabilitySemitones == 0.0)
    }

    @Test
    fun `classify always returns a normalized-ish confidence and a valid feature set`() {
        val classification = AdaptiveMasteringEngine.classify(melodicSweep(), sampleRate)
        assertTrue(classification.confidence in 0.0..1.0)
        assertTrue(ContentType.entries.contains(classification.type))
    }

    @Test
    fun `recommend produces a stable, usable processing chain`() {
        val config = AdaptiveMasteringEngine.recommend(longPausedSpeech(), sampleRate)
        assertTrue(config.compressorRatio in 1.5..6.0)

        val chain = AudioProcessingChain(sampleRate, config)
        val probe = monotone(durationSeconds = 0.5)
        for (s in probe) {
            val y = chain.process(s)
            assertTrue(!y.isNaN() && y.isFinite())
        }
    }
}
