package com.sajjil.core.dsp

import kotlin.math.exp
import kotlin.math.log10
import kotlin.math.max
import kotlin.math.pow
import kotlin.math.sqrt

/**
 * Envelope-follower noise gate with hysteresis and hold time, used to tame
 * steady background noise and breath sounds between phrases without
 * chopping off soft consonants (Tajweed-safe: generous hold/release avoid
 * clipping the tail of a recitation).
 */
class NoiseGate(
    private val sampleRate: Int,
    var thresholdDb: Double = -45.0,
    var rangeDb: Double = -18.0,
    var attackMs: Double = 2.0,
    var holdMs: Double = 80.0,
    var releaseMs: Double = 250.0,
) {
    private var envelopeSquared = 0.0
    private var holdCounter = 0
    private var currentGain = 1.0
    private val envCoeff = exp(-1.0 / (sampleRate * 0.003))

    fun reset() {
        envelopeSquared = 0.0
        holdCounter = 0
        currentGain = 1.0
    }

    fun process(sample: Float): Float {
        val x = sample.toDouble()
        envelopeSquared = envCoeff * envelopeSquared + (1 - envCoeff) * x * x
        val envelopeDb = 20.0 * log10(sqrt(max(envelopeSquared, 1e-12)))

        val floorGain = 10.0.pow(rangeDb / 20.0)
        val open = envelopeDb > thresholdDb
        val holdSamples = (sampleRate * holdMs / 1000.0).toInt()

        val targetGain: Double
        if (open) {
            holdCounter = holdSamples
            targetGain = 1.0
        } else if (holdCounter > 0) {
            holdCounter--
            targetGain = 1.0
        } else {
            targetGain = floorGain
        }

        val coeff = if (targetGain > currentGain) {
            exp(-1.0 / (sampleRate * (attackMs / 1000.0).coerceAtLeast(1e-4)))
        } else {
            exp(-1.0 / (sampleRate * (releaseMs / 1000.0).coerceAtLeast(1e-4)))
        }
        currentGain = coeff * currentGain + (1 - coeff) * targetGain
        return (x * currentGain).toFloat()
    }

    fun processBlock(samples: FloatArray) {
        for (i in samples.indices) samples[i] = process(samples[i])
    }
}
