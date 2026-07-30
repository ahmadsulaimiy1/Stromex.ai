package com.sajjil.core.analysis

import kotlin.math.roundToInt

data class AudioAnalysisReport(
    val loudness: LoudnessMetrics,
    val clarityScore: Int,
    val noiseScore: Int,
    val loudnessScore: Int,
    val dynamicsScore: Int,
    val studioReadinessScore: Int,
    val broadcastReadinessScore: Int,
    val archiveReadinessScore: Int,
)

/**
 * Converts raw loudness/noise measurements into the 0-100 scores shown on
 * the Executive Dashboard. Heuristic, not a certified compliance metric.
 */
object AudioQualityScorer {

    fun score(metrics: LoudnessMetrics): AudioAnalysisReport {
        val noiseScore = scaleClamp(metrics.noiseFloorDb, from = -70.0, to = -30.0, invert = true)
        val clarityScore = scaleClamp(metrics.dynamicRangeDb, from = 4.0, to = 24.0)
        val loudnessScore = scaleClamp(metrics.integratedLoudnessLufs, from = -30.0, to = -12.0)
        val dynamicsScore = scaleClamp(metrics.crestFactorDb, from = 4.0, to = 18.0)

        val clippingPenalty = if (metrics.peakDb > -0.1) 25 else 0
        val studioReadiness = (listOf(noiseScore, clarityScore, dynamicsScore).average().roundToInt() - clippingPenalty)
            .coerceIn(0, 100)
        val broadcastReadiness = (listOf(loudnessScore, noiseScore).average().roundToInt() - clippingPenalty)
            .coerceIn(0, 100)
        val archiveReadiness = (listOf(noiseScore, clarityScore, loudnessScore, dynamicsScore).average().roundToInt() - clippingPenalty)
            .coerceIn(0, 100)

        return AudioAnalysisReport(
            loudness = metrics,
            clarityScore = clarityScore,
            noiseScore = noiseScore,
            loudnessScore = loudnessScore,
            dynamicsScore = dynamicsScore,
            studioReadinessScore = studioReadiness,
            broadcastReadinessScore = broadcastReadiness,
            archiveReadinessScore = archiveReadiness,
        )
    }

    private fun scaleClamp(value: Double, from: Double, to: Double, invert: Boolean = false): Int {
        val t = ((value - from) / (to - from)).coerceIn(0.0, 1.0)
        val normalized = if (invert) 1.0 - t else t
        return (normalized * 100).roundToInt()
    }
}
