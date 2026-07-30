package com.sajjil.core.dsp

import kotlin.math.abs
import kotlin.math.exp
import kotlin.math.ln
import kotlin.math.log10
import kotlin.math.max
import kotlin.math.pow

/**
 * Feed-forward RMS-detector dynamic range compressor with soft knee,
 * attack/release time constants and makeup gain. All levels in dBFS.
 */
class Compressor(
    private val sampleRate: Int,
    var thresholdDb: Double = -18.0,
    var ratio: Double = 3.0,
    var attackMs: Double = 8.0,
    var releaseMs: Double = 120.0,
    var kneeDb: Double = 6.0,
    var makeupGainDb: Double = 0.0,
) {
    private var envelopeDb = -100.0
    private var rmsSquared = 0.0
    private val rmsCoeff = exp(-1.0 / (sampleRate * 0.005))

    var lastGainReductionDb: Double = 0.0
        private set

    fun reset() {
        envelopeDb = -100.0
        rmsSquared = 0.0
        lastGainReductionDb = 0.0
    }

    private fun attackCoeff() = exp(-1.0 / (sampleRate * (attackMs / 1000.0).coerceAtLeast(1e-4)))
    private fun releaseCoeff() = exp(-1.0 / (sampleRate * (releaseMs / 1000.0).coerceAtLeast(1e-4)))

    private fun gainComputer(inputDb: Double): Double {
        val overshoot = inputDb - thresholdDb
        return when {
            2 * overshoot < -kneeDb -> inputDb
            2 * abs(overshoot) <= kneeDb ->
                inputDb + (1.0 / ratio - 1.0) * (overshoot + kneeDb / 2.0).pow(2) / (2.0 * kneeDb)
            else -> thresholdDb + overshoot / ratio
        }
    }

    fun process(sample: Float): Float {
        val x = sample.toDouble()
        rmsSquared = rmsCoeff * rmsSquared + (1 - rmsCoeff) * x * x
        val rms = kotlin.math.sqrt(max(rmsSquared, 1e-12))
        val inputDb = 20.0 * log10(rms).coerceAtLeast(-100.0)

        val targetDb = gainComputer(inputDb)
        val gainReductionTargetDb = targetDb - inputDb

        val coeff = if (gainReductionTargetDb < lastGainReductionDb) attackCoeff() else releaseCoeff()
        lastGainReductionDb = coeff * lastGainReductionDb + (1 - coeff) * gainReductionTargetDb
        envelopeDb = inputDb

        val totalGainDb = lastGainReductionDb + makeupGainDb
        val linearGain = 10.0.pow(totalGainDb / 20.0)
        return (x * linearGain).toFloat()
    }

    fun processBlock(samples: FloatArray) {
        for (i in samples.indices) samples[i] = process(samples[i])
    }

    /** Suggested makeup gain to restore average level lost to compression, in dB. */
    fun autoMakeupGain(): Double = -thresholdDb * (1.0 - 1.0 / ratio) / 2.0

    companion object {
        fun ln10() = ln(10.0)
    }
}
