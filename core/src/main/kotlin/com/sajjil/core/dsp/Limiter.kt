package com.sajjil.core.dsp

import kotlin.math.abs
import kotlin.math.exp
import kotlin.math.log10
import kotlin.math.max
import kotlin.math.pow

/**
 * Lookahead brickwall peak limiter used as the final stage of the loudness
 * maximizer. Guarantees output never exceeds [ceilingDb] while smoothing
 * gain reduction to avoid audible pumping.
 */
class Limiter(
    sampleRate: Int,
    var ceilingDb: Double = -0.3,
    lookaheadMs: Double = 5.0,
    var releaseMs: Double = 60.0,
) {
    private val lookaheadSamples = max(1, (sampleRate * lookaheadMs / 1000.0).toInt())
    private val delayLine = FloatArray(lookaheadSamples)
    private val peakWindow = FloatArray(lookaheadSamples)
    private var writeIndex = 0
    private var currentGain = 1.0
    private val releaseCoeff = exp(-1.0 / (sampleRate * (releaseMs / 1000.0)))
    private val ceilingLinear get() = 10.0.pow(ceilingDb / 20.0)

    var lastGainReductionDb: Double = 0.0
        private set

    fun reset() {
        delayLine.fill(0f)
        peakWindow.fill(0f)
        writeIndex = 0
        currentGain = 1.0
        lastGainReductionDb = 0.0
    }

    fun process(sample: Float): Float {
        val delayed = delayLine[writeIndex]
        delayLine[writeIndex] = sample
        peakWindow[writeIndex] = abs(sample)
        writeIndex = (writeIndex + 1) % lookaheadSamples

        var peak = 0f
        for (v in peakWindow) if (v > peak) peak = v

        val requiredGain = if (peak > ceilingLinear) ceilingLinear / peak else 1.0
        currentGain = if (requiredGain < currentGain) {
            requiredGain
        } else {
            releaseCoeff * currentGain + (1 - releaseCoeff) * requiredGain
        }
        currentGain = currentGain.coerceAtMost(1.0)
        lastGainReductionDb = 20.0 * log10(currentGain.coerceAtLeast(1e-9))

        val out = (delayed * currentGain).toFloat()
        return out.coerceIn(-ceilingLinear.toFloat(), ceilingLinear.toFloat())
    }

    fun processBlock(samples: FloatArray) {
        for (i in samples.indices) samples[i] = process(samples[i])
    }
}

/**
 * Combines input gain staging with a lookahead limiter to raise perceived
 * loudness toward a target without introducing audible distortion.
 */
class LoudnessMaximizer(
    sampleRate: Int,
    var driveDb: Double = 6.0,
    ceilingDb: Double = -0.3,
) {
    private val limiter = Limiter(sampleRate, ceilingDb = ceilingDb)

    fun reset() = limiter.reset()

    fun process(sample: Float): Float {
        val driven = (sample * 10.0.pow(driveDb / 20.0)).toFloat()
        return limiter.process(driven)
    }

    fun processBlock(samples: FloatArray) {
        for (i in samples.indices) samples[i] = process(samples[i])
    }
}
