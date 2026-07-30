package com.sajjil.core.analysis

import com.sajjil.core.dsp.BiquadFilter
import kotlin.math.abs
import kotlin.math.log10
import kotlin.math.max
import kotlin.math.sqrt

data class LoudnessMetrics(
    val peakDb: Double,
    val rmsDb: Double,
    val integratedLoudnessLufs: Double,
    val dynamicRangeDb: Double,
    val noiseFloorDb: Double,
    val crestFactorDb: Double,
)

/**
 * Measures level and dynamics from a full PCM buffer. Integrated loudness
 * uses a simplified ITU-R BS.1770-style K-weighting pre-filter (high-shelf
 * + high-pass) followed by mean-square gating, giving an LUFS approximation
 * suitable for on-device guidance (not certified broadcast-loudness metrology).
 */
object LoudnessAnalyzer {

    fun analyze(samples: FloatArray, sampleRate: Int): LoudnessMetrics {
        if (samples.isEmpty()) {
            return LoudnessMetrics(-100.0, -100.0, -100.0, 0.0, -100.0, 0.0)
        }

        var peak = 0f
        var sumSquares = 0.0
        for (s in samples) {
            val a = abs(s)
            if (a > peak) peak = a
            sumSquares += s.toDouble() * s
        }
        val rms = sqrt(sumSquares / samples.size)
        val peakDb = 20.0 * log10(max(peak.toDouble(), 1e-9))
        val rmsDb = 20.0 * log10(max(rms, 1e-9))

        val weighted = kWeight(samples, sampleRate)
        val lufs = integratedLoudness(weighted, sampleRate)

        val frameRmsDb = frameRmsDbValues(samples, sampleRate)
        val sorted = frameRmsDb.sorted()
        val noiseFloorDb = if (sorted.isNotEmpty()) sorted[(sorted.size * 0.10).toInt().coerceIn(0, sorted.size - 1)] else rmsDb
        val loudFloorDb = if (sorted.isNotEmpty()) sorted[(sorted.size * 0.90).toInt().coerceIn(0, sorted.size - 1)] else rmsDb
        val dynamicRangeDb = loudFloorDb - noiseFloorDb

        return LoudnessMetrics(
            peakDb = peakDb,
            rmsDb = rmsDb,
            integratedLoudnessLufs = lufs,
            dynamicRangeDb = dynamicRangeDb,
            noiseFloorDb = noiseFloorDb,
            crestFactorDb = peakDb - rmsDb,
        )
    }

    private fun kWeight(samples: FloatArray, sampleRate: Int): FloatArray {
        val stage1 = BiquadFilter.highShelf(1500.0, sampleRate.toDouble(), 4.0)
        val stage2 = BiquadFilter.highPass(60.0, sampleRate.toDouble(), 0.5)
        val out = samples.copyOf()
        stage1.processBlock(out)
        stage2.processBlock(out)
        return out
    }

    private fun integratedLoudness(weighted: FloatArray, sampleRate: Int): Double {
        val blockSize = (sampleRate * 0.4).toInt().coerceAtLeast(1)
        val hop = (blockSize * 0.25).toInt().coerceAtLeast(1)
        val blockLoudnessLufs = mutableListOf<Double>()
        var start = 0
        while (start + blockSize <= weighted.size) {
            var sum = 0.0
            for (i in 0 until blockSize) sum += weighted[start + i].toDouble() * weighted[start + i]
            val meanSquare = sum / blockSize
            val lufs = -0.691 + 10.0 * log10(max(meanSquare, 1e-12))
            blockLoudnessLufs.add(lufs)
            start += hop
        }
        if (blockLoudnessLufs.isEmpty()) return -100.0
        val gated = blockLoudnessLufs.filter { it > -70.0 }
        if (gated.isEmpty()) return -100.0
        val meanSquareLinear = gated.map { Math.pow(10.0, (it + 0.691) / 10.0) }.average()
        return -0.691 + 10.0 * log10(max(meanSquareLinear, 1e-12))
    }

    private fun frameRmsDbValues(samples: FloatArray, sampleRate: Int): List<Double> {
        val frameSize = (sampleRate * 0.05).toInt().coerceAtLeast(1)
        val result = mutableListOf<Double>()
        var start = 0
        while (start + frameSize <= samples.size) {
            var sum = 0.0
            for (i in 0 until frameSize) sum += samples[start + i].toDouble() * samples[start + i]
            val rms = sqrt(sum / frameSize)
            result.add(20.0 * log10(max(rms, 1e-9)))
            start += frameSize
        }
        return result
    }
}
