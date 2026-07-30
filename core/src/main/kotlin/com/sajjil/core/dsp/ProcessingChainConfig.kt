package com.sajjil.core.dsp

/** Full set of tunable parameters for one recording/mastering signal chain. */
data class ProcessingChainConfig(
    val label: String,
    val description: String,
    val eqBassDb: Double = 0.0,
    val eqMidDb: Double = 0.0,
    val eqPresenceDb: Double = 0.0,
    val eqTrebleDb: Double = 0.0,
    val gateEnabled: Boolean = true,
    val gateThresholdDb: Double = -45.0,
    val gateRangeDb: Double = -18.0,
    val gateHoldMs: Double = 80.0,
    val gateReleaseMs: Double = 250.0,
    val deEsserEnabled: Boolean = true,
    val deEsserThresholdDb: Double = -24.0,
    val deEsserRatio: Double = 4.0,
    val compressorThresholdDb: Double = -18.0,
    val compressorRatio: Double = 2.5,
    val compressorAttackMs: Double = 10.0,
    val compressorReleaseMs: Double = 140.0,
    val limiterCeilingDb: Double = -0.3,
    val limiterDriveDb: Double = 5.0,
    val noiseReductionStrength: NoiseReductionStrength = NoiseReductionStrength.MODERATE,
)

/**
 * A complete per-sample signal chain assembled from a [ProcessingChainConfig]:
 * noise gate -> equalizer -> de-esser -> compressor -> loudness maximizer.
 * Frequency-domain broadband noise reduction ([SpectralNoiseReducer]) runs as
 * a separate offline pass over a full buffer, not inside this real-time chain.
 */
class AudioProcessingChain(sampleRate: Int, val config: ProcessingChainConfig) {
    private val gate = NoiseGate(
        sampleRate,
        thresholdDb = config.gateThresholdDb,
        rangeDb = config.gateRangeDb,
        holdMs = config.gateHoldMs,
        releaseMs = config.gateReleaseMs,
    )
    private val eq = ParametricEqualizer.basic(
        sampleRate,
        bassDb = config.eqBassDb,
        midDb = config.eqMidDb,
        trebleDb = config.eqTrebleDb,
        presenceDb = config.eqPresenceDb,
    )
    private val deEsser = DeEsser(
        sampleRate,
        thresholdDb = config.deEsserThresholdDb,
        ratio = config.deEsserRatio,
    )
    private val compressor = Compressor(
        sampleRate,
        thresholdDb = config.compressorThresholdDb,
        ratio = config.compressorRatio,
        attackMs = config.compressorAttackMs,
        releaseMs = config.compressorReleaseMs,
    ).apply { makeupGainDb = autoMakeupGain() }
    private val maximizer = LoudnessMaximizer(
        sampleRate,
        driveDb = config.limiterDriveDb,
        ceilingDb = config.limiterCeilingDb,
    )

    fun reset() {
        gate.reset(); eq.reset(); deEsser.reset(); compressor.reset(); maximizer.reset()
    }

    fun process(sample: Float): Float {
        var s = sample
        if (config.gateEnabled) s = gate.process(s)
        s = eq.process(s)
        if (config.deEsserEnabled) s = deEsser.process(s)
        s = compressor.process(s)
        s = maximizer.process(s)
        return s
    }

    fun processBlock(samples: FloatArray) {
        for (i in samples.indices) samples[i] = process(samples[i])
    }
}
