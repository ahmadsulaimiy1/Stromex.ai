package com.sajjil.core.analysis

import kotlin.math.abs

/**
 * Downsamples a full sample buffer into a small, fixed number of peak-amplitude buckets for a
 * scrubber-style waveform visualization -- the classic "bars that show how loud each stretch of
 * the recording was" view, distinct from [Spectrogram] (frequency-domain) or a loudness-over-time
 * curve. Cheap: one linear pass, no FFT.
 */
object WaveformPeaks {
    fun compute(samples: FloatArray, bucketCount: Int): FloatArray {
        require(bucketCount > 0) { "bucketCount must be positive" }
        val peaks = FloatArray(bucketCount)
        if (samples.isEmpty()) return peaks

        val bucketSize = samples.size.toDouble() / bucketCount
        for (bucket in 0 until bucketCount) {
            val start = (bucket * bucketSize).toInt()
            val end = (((bucket + 1) * bucketSize).toInt()).coerceAtMost(samples.size)
            var peak = 0f
            for (i in start until end) {
                val magnitude = abs(samples[i])
                if (magnitude > peak) peak = magnitude
            }
            peaks[bucket] = peak.coerceIn(0f, 1f)
        }
        return peaks
    }
}
