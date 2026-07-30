package com.sajjil.core.analysis

import kotlin.math.abs
import kotlin.math.log10
import kotlin.math.max
import kotlin.math.sqrt

enum class EchoSeverity { LOW, MODERATE, HIGH, SEVERE }
enum class ProximityEstimate { TOO_CLOSE, GOOD, TOO_FAR, UNKNOWN }

data class AcousticProfile(
    val noiseFloorDb: Double,
    val clippingRiskPercent: Double,
    val estimatedRt60Seconds: Double?,
    val echoSeverity: EchoSeverity,
    val proximity: ProximityEstimate,
    val recommendations: List<String>,
    val recommendedModeName: String?,
)

/**
 * SAJJIL AI Acoustic Intelligence: analyses a short probe recording (a few
 * seconds of room tone / a couple of test phrases) *before* the user
 * commits to a take, and turns it into plain-language guidance.
 *
 * Every measurement here is classic acoustics/DSP, not a trained model:
 * - RT60 is estimated blind, from naturally occurring "free decay" segments
 *   in the envelope (Ratnam et al.-style free-decay detection), not from a
 *   known excitation signal — so it's an estimate, not a lab measurement.
 * - "Proximity" is a direct-to-reverberant energy ratio proxy, not a
 *   calibrated distance in centimeters; the UI should phrase it as
 *   "move closer" / "you're a little far", not claim exact centimeters.
 */
object AcousticAnalyzer {

    fun analyze(samples: FloatArray, sampleRate: Int): AcousticProfile {
        val loudness = LoudnessAnalyzer.analyze(samples, sampleRate)
        val clippingRisk = clippingRiskPercent(samples)
        val rt60 = estimateRt60(samples, sampleRate)
        val echoSeverity = classifyEcho(rt60)
        val proximity = estimateProximity(samples, sampleRate, rt60)

        val recommendations = buildRecommendations(loudness.noiseFloorDb, clippingRisk, echoSeverity, proximity)
        val recommendedMode = recommendMode(loudness.noiseFloorDb, echoSeverity)

        return AcousticProfile(
            noiseFloorDb = loudness.noiseFloorDb,
            clippingRiskPercent = clippingRisk,
            estimatedRt60Seconds = rt60,
            echoSeverity = echoSeverity,
            proximity = proximity,
            recommendations = recommendations,
            recommendedModeName = recommendedMode,
        )
    }

    private fun clippingRiskPercent(samples: FloatArray): Double {
        if (samples.isEmpty()) return 0.0
        val nearFullScale = samples.count { abs(it) >= 0.98f }
        return 100.0 * nearFullScale / samples.size
    }

    /**
     * Blind RT60 estimate: finds envelope segments that decay monotonically
     * (within tolerance) by at least 15 dB over at least 150 ms, fits a
     * linear dB/second slope to each via least squares, and extrapolates
     * to a full 60 dB decay. Returns the median across segments found, or
     * null if the signal has no usable free-decay region (too short, too
     * noisy, or no natural pauses).
     */
    fun estimateRt60(samples: FloatArray, sampleRate: Int): Double? {
        val frameMs = 10.0
        val frameSize = max(1, (sampleRate * frameMs / 1000.0).toInt())
        val envelopeDb = frameEnergyDb(samples, frameSize)
        if (envelopeDb.size < 4) return null

        val decayRatesPerSecond = mutableListOf<Double>()
        var i = 1
        while (i < envelopeDb.size - 1) {
            val isPeak = envelopeDb[i] >= envelopeDb[i - 1] &&
                (i + 1 >= envelopeDb.size || envelopeDb[i] >= envelopeDb[i + 1] - 0.1)
            if (isPeak) {
                var j = i
                while (j + 1 < envelopeDb.size && envelopeDb[j + 1] <= envelopeDb[j] + 0.5) j++
                val decayDb = envelopeDb[i] - envelopeDb[j]
                val decaySpanMs = (j - i) * frameMs
                if (decaySpanMs >= 150.0 && decayDb >= 15.0) {
                    val xs = DoubleArray(j - i + 1) { k -> k * frameMs / 1000.0 }
                    val ys = DoubleArray(j - i + 1) { k -> envelopeDb[i + k] }
                    val slope = linearRegressionSlope(xs, ys)
                    if (slope < -0.5) decayRatesPerSecond.add(-60.0 / slope)
                }
                i = j + 1
            } else {
                i++
            }
        }

        if (decayRatesPerSecond.isEmpty()) return null
        val sorted = decayRatesPerSecond.sorted()
        return sorted[sorted.size / 2].coerceIn(0.05, 8.0)
    }

    private fun estimateProximity(samples: FloatArray, sampleRate: Int, rt60: Double?): ProximityEstimate {
        val loudness = LoudnessAnalyzer.analyze(samples, sampleRate)
        val headroomDb = loudness.peakDb - loudness.rmsDb // crest factor: sharp direct transients vs. sustained level

        return when {
            rt60 == null && headroomDb < 6.0 -> ProximityEstimate.UNKNOWN
            headroomDb > 20.0 -> ProximityEstimate.TOO_CLOSE // plosive/handling-heavy, very peaky
            (rt60 ?: 0.0) > 0.5 && headroomDb < 10.0 -> ProximityEstimate.TOO_FAR // smeared, reverberant-dominated
            else -> ProximityEstimate.GOOD
        }
    }

    private fun classifyEcho(rt60: Double?): EchoSeverity = when {
        rt60 == null -> EchoSeverity.LOW
        rt60 < 0.3 -> EchoSeverity.LOW
        rt60 < 0.6 -> EchoSeverity.MODERATE
        rt60 < 1.2 -> EchoSeverity.HIGH
        else -> EchoSeverity.SEVERE
    }

    private fun buildRecommendations(
        noiseFloorDb: Double,
        clippingRiskPercent: Double,
        echoSeverity: EchoSeverity,
        proximity: ProximityEstimate,
    ): List<String> {
        val notes = mutableListOf<String>()
        if (noiseFloorDb > -45.0) notes += "Background noise detected — find a quieter spot, or the Lecture profile's stronger suppression will help."
        if (clippingRiskPercent > 0.05) notes += "Clipping risk detected — lower the input gain or move back slightly from the microphone."
        when (echoSeverity) {
            EchoSeverity.HIGH -> notes += "Noticeable room reflections — soft furnishings nearby (rugs, curtains) will tighten the sound."
            EchoSeverity.SEVERE -> notes += "Strong hall/mosque-style reflections detected — switch to Imam Al-Haram or Qur'an Studio, which are tuned for this space."
            else -> {}
        }
        when (proximity) {
            ProximityEstimate.TOO_CLOSE -> notes += "You're very close to the microphone — ease back a little to reduce plosives and handling noise."
            ProximityEstimate.TOO_FAR -> notes += "Move closer to the microphone for clearer articulation."
            else -> {}
        }
        if (notes.isEmpty()) notes += "Conditions look good — you're ready to record."
        return notes
    }

    private fun recommendMode(noiseFloorDb: Double, echoSeverity: EchoSeverity): String? = when {
        echoSeverity == EchoSeverity.SEVERE -> "IMAM_AL_HARAM"
        echoSeverity == EchoSeverity.HIGH -> "QURAN_STUDIO"
        noiseFloorDb > -40.0 -> "LECTURE"
        else -> null
    }

    private fun frameEnergyDb(samples: FloatArray, frameSize: Int): List<Double> {
        val result = mutableListOf<Double>()
        var start = 0
        while (start + frameSize <= samples.size) {
            var sum = 0.0
            for (i in start until start + frameSize) sum += samples[i].toDouble() * samples[i]
            val rms = sqrt(sum / frameSize)
            result.add(20.0 * log10(max(rms, 1e-9)))
            start += frameSize
        }
        return result
    }

    private fun linearRegressionSlope(xs: DoubleArray, ys: DoubleArray): Double {
        val n = xs.size
        if (n < 2) return 0.0
        val meanX = xs.average()
        val meanY = ys.average()
        var num = 0.0
        var den = 0.0
        for (i in 0 until n) {
            num += (xs[i] - meanX) * (ys[i] - meanY)
            den += (xs[i] - meanX) * (xs[i] - meanX)
        }
        return if (den > 1e-12) num / den else 0.0
    }
}
