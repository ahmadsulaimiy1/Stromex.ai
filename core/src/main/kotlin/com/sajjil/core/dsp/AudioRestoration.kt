package com.sajjil.core.dsp

import kotlin.math.abs
import kotlin.math.log10
import kotlin.math.max
import kotlin.math.pow

/** SAJJIL Audio Restoration Laboratory: repair pipelines for damaged recordings. */
object AudioRestoration {

    /** Applies gain so the buffer's peak sits at [targetPeakDb] (default -1 dBFS). Fixes low-volume takes. */
    fun normalizePeak(samples: FloatArray, targetPeakDb: Double = -1.0): FloatArray {
        val peak = samples.maxOfOrNull { abs(it) } ?: return samples.copyOf()
        if (peak < 1e-9f) return samples.copyOf()
        val currentPeakDb = 20.0 * log10(peak.toDouble())
        val gain = 10.0.pow((targetPeakDb - currentPeakDb) / 20.0).toFloat()
        return FloatArray(samples.size) { i -> (samples[i] * gain).coerceIn(-1f, 1f) }
    }

    /**
     * Full restoration pass for a damaged archive: declip, denoise, then
     * bring the level back up to a usable reference peak. Order matters —
     * declipping first gives the noise reducer a cleaner spectrum to learn
     * a noise profile from; normalizing last avoids re-clipping partially
     * repaired peaks.
     */
    fun restore(
        samples: FloatArray,
        sampleRate: Int,
        noiseReductionStrength: NoiseReductionStrength = NoiseReductionStrength.MODERATE,
        targetPeakDb: Double = -1.0,
    ): FloatArray {
        val declipped = Declipper.repair(samples)
        val denoised = SpectralNoiseReducer(sampleRate).process(declipped, noiseReductionStrength)
        return normalizePeak(denoised, targetPeakDb)
    }

    /** Fraction of samples that look clipped — useful as a "damage" indicator before running [restore]. */
    fun estimateDamageScore(samples: FloatArray): Int {
        if (samples.isEmpty()) return 0
        val clippedSamples = Declipper.findClipSegments(samples).sumOf { it.endIndexExclusive - it.startIndex }
        val clippedFraction = clippedSamples.toDouble() / samples.size
        return (clippedFraction * 100).toInt().coerceIn(0, 100).let { max(it, 0) }
    }
}
