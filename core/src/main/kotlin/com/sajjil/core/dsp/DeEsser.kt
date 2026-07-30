package com.sajjil.core.dsp

import kotlin.math.exp
import kotlin.math.log10
import kotlin.math.max
import kotlin.math.sqrt

/**
 * Split-band de-esser: isolates the sibilance band (4-9 kHz by default),
 * detects its envelope, and applies frequency-selective gain reduction
 * only in that band when it exceeds threshold — controlling harsh "s"/"sh"
 * sounds (sibilance control) without dulling overall clarity.
 */
class DeEsser(
    private val sampleRate: Int,
    var centerFreqHz: Double = 6500.0,
    var thresholdDb: Double = -24.0,
    var ratio: Double = 4.0,
    var attackMs: Double = 1.0,
    var releaseMs: Double = 60.0,
) {
    private val detectorFilter = BiquadFilter.highPass(centerFreqHz - 2000.0, sampleRate.toDouble(), 0.7071)
    private var dynamicBand = BiquadFilter.peaking(centerFreqHz, sampleRate.toDouble(), 2.0, 0.0)
    private var envelopeSquared = 0.0
    private var currentReductionDb = 0.0
    private val envCoeff = exp(-1.0 / (sampleRate * 0.002))

    fun reset() {
        detectorFilter.reset()
        dynamicBand.reset()
        envelopeSquared = 0.0
        currentReductionDb = 0.0
    }

    fun process(sample: Float): Float {
        val sideChain = detectorFilter.process(sample)
        val sc = sideChain.toDouble()
        envelopeSquared = envCoeff * envelopeSquared + (1 - envCoeff) * sc * sc
        val envelopeDb = 20.0 * log10(sqrt(max(envelopeSquared, 1e-12)))

        val overshoot = envelopeDb - thresholdDb
        val targetReductionDb = if (overshoot > 0) -overshoot * (1.0 - 1.0 / ratio) else 0.0

        val coeff = if (targetReductionDb < 0) {
            exp(-1.0 / (sampleRate * (attackMs / 1000.0)))
        } else {
            exp(-1.0 / (sampleRate * (releaseMs / 1000.0)))
        }
        currentReductionDb = coeff * currentReductionDb + (1 - coeff) * targetReductionDb

        dynamicBand.updateAsPeaking(centerFreqHz, sampleRate.toDouble(), 2.0, currentReductionDb)
        return dynamicBand.process(sample)
    }

    fun processBlock(samples: FloatArray) {
        for (i in samples.indices) samples[i] = process(samples[i])
    }
}
