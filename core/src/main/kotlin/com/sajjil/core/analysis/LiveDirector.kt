package com.sajjil.core.analysis

import kotlin.math.abs
import kotlin.math.log10
import kotlin.math.max
import kotlin.math.round
import kotlin.math.sqrt

enum class GuidanceSeverity { GOOD, INFO, WARNING }

data class DirectorGuidance(
    val message: String,
    /** Positive = raise input gain, negative = lower it. Null when there isn't enough signal to judge yet. */
    val suggestedGainAdjustmentDb: Double?,
    val severity: GuidanceSeverity,
    val isClipping: Boolean,
    val peakDb: Double,
    val rmsDb: Double,
)

/**
 * SAJJIL Intelligent Recording Director: the fast, continuous counterpart
 * to `AcousticAnalyzer`'s deeper one-shot Room Check. Where Room Check
 * spends ~3 seconds estimating RT60 and echo severity, `LiveDirector` costs
 * a peak/RMS pass over whatever's in the ring buffer right now (no FFT) so
 * the UI can call it every fraction of a second while the user adjusts mic
 * position and input gain before hitting record — "engineer looking over
 * your shoulder," not a one-time report card.
 */
object LiveDirector {

    /**
     * @param recentSamples a short rolling window (e.g. the last 0.5-1s) of live input.
     * @param targetPeakDb the peak level a healthy take should sit at (default -6 dBFS: headroom
     *   for plosives/dynamics without inviting clipping).
     */
    fun assess(
        recentSamples: FloatArray,
        targetPeakDb: Double = -6.0,
        clippingThreshold: Float = 0.98f,
    ): DirectorGuidance {
        if (recentSamples.isEmpty()) {
            return DirectorGuidance("Listening…", null, GuidanceSeverity.INFO, isClipping = false, peakDb = -100.0, rmsDb = -100.0)
        }

        var peak = 0f
        var sumSquares = 0.0
        var clippedCount = 0
        for (s in recentSamples) {
            val a = abs(s)
            if (a > peak) peak = a
            if (a >= clippingThreshold) clippedCount++
            sumSquares += s.toDouble() * s
        }
        val peakDb = 20.0 * log10(max(peak.toDouble(), 1e-6))
        val rmsDb = 20.0 * log10(max(sqrt(sumSquares / recentSamples.size), 1e-6))
        val isClipping = clippedCount > 0
        val gainDelta = round((targetPeakDb - peakDb) * 2.0) / 2.0 // nearest 0.5 dB

        return when {
            isClipping -> DirectorGuidance(
                message = "Clipping detected — lower your input gain now.",
                suggestedGainAdjustmentDb = gainDelta.coerceAtMost(-1.0),
                severity = GuidanceSeverity.WARNING,
                isClipping = true,
                peakDb = peakDb,
                rmsDb = rmsDb,
            )
            peakDb > targetPeakDb + 3.0 -> DirectorGuidance(
                message = "Signal is a little hot — lower gain by ${fmt(-gainDelta)} dB.",
                suggestedGainAdjustmentDb = gainDelta,
                severity = GuidanceSeverity.WARNING,
                isClipping = false,
                peakDb = peakDb,
                rmsDb = rmsDb,
            )
            peakDb < targetPeakDb - 15.0 -> DirectorGuidance(
                message = "Signal is very low — raise gain by ${fmt(gainDelta)} dB or move closer to the microphone.",
                suggestedGainAdjustmentDb = gainDelta,
                severity = GuidanceSeverity.WARNING,
                isClipping = false,
                peakDb = peakDb,
                rmsDb = rmsDb,
            )
            peakDb < targetPeakDb - 6.0 -> DirectorGuidance(
                message = "A touch quiet — raise gain by ${fmt(gainDelta)} dB.",
                suggestedGainAdjustmentDb = gainDelta,
                severity = GuidanceSeverity.INFO,
                isClipping = false,
                peakDb = peakDb,
                rmsDb = rmsDb,
            )
            else -> DirectorGuidance(
                message = "Levels look good — ready to record.",
                suggestedGainAdjustmentDb = 0.0,
                severity = GuidanceSeverity.GOOD,
                isClipping = false,
                peakDb = peakDb,
                rmsDb = rmsDb,
            )
        }
    }

    private fun fmt(db: Double): String {
        val magnitude = abs(db)
        return if (magnitude == magnitude.toLong().toDouble()) magnitude.toLong().toString() else "%.1f".format(magnitude)
    }
}
