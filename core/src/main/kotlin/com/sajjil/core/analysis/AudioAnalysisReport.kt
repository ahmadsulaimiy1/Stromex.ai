package com.sajjil.core.analysis

import kotlin.math.roundToInt

data class AudioAnalysisReport(
    val loudness: LoudnessMetrics,
    val clarityScore: Int,
    val noiseScore: Int,
    val loudnessScore: Int,
    val dynamicsScore: Int,
    val echoScore: Int?,
    val studioReadinessScore: Int,
    val broadcastReadinessScore: Int,
    val archiveReadinessScore: Int,
)

/**
 * Converts raw loudness/noise/echo measurements into the 0-100 scores shown
 * on the Executive Dashboard. Heuristic, not a certified compliance metric.
 */
object AudioQualityScorer {

    /**
     * [rt60Seconds] is optional — pass `AcousticAnalyzer.estimateRt60(...)`
     * when an echo/reverb measurement is available. Without it, `echoScore`
     * is null and excluded from the readiness averages rather than silently
     * assumed to be perfect.
     */
    fun score(metrics: LoudnessMetrics, rt60Seconds: Double? = null): AudioAnalysisReport {
        val noiseScore = scaleClamp(metrics.noiseFloorDb, from = -70.0, to = -30.0, invert = true)
        val clarityScore = scaleClamp(metrics.dynamicRangeDb, from = 4.0, to = 24.0)
        val loudnessScore = scaleClamp(metrics.integratedLoudnessLufs, from = -30.0, to = -12.0)
        val dynamicsScore = scaleClamp(metrics.crestFactorDb, from = 4.0, to = 18.0)
        val echoScore = rt60Seconds?.let { scaleClamp(it, from = 1.2, to = 0.2, invert = false) }

        val clippingPenalty = if (metrics.peakDb > -0.1) 25 else 0
        val studioComponents = listOfNotNull(noiseScore, clarityScore, dynamicsScore, echoScore)
        val studioReadiness = (studioComponents.average().roundToInt() - clippingPenalty).coerceIn(0, 100)
        val broadcastReadiness = (listOfNotNull(loudnessScore, noiseScore, echoScore).average().roundToInt() - clippingPenalty)
            .coerceIn(0, 100)
        val archiveReadiness = (listOfNotNull(noiseScore, clarityScore, loudnessScore, dynamicsScore, echoScore).average().roundToInt() - clippingPenalty)
            .coerceIn(0, 100)

        return AudioAnalysisReport(
            loudness = metrics,
            clarityScore = clarityScore,
            noiseScore = noiseScore,
            loudnessScore = loudnessScore,
            dynamicsScore = dynamicsScore,
            echoScore = echoScore,
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
