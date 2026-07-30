package com.sajjil.core.analysis

import com.sajjil.core.dsp.fft.FFT
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.log10
import kotlin.math.max
import kotlin.math.sqrt

/**
 * A time x frequency magnitude-in-dB grid, ready to hand to a waterfall or
 * heatmap renderer. `frames[t][bin]` is the dB level of `binFrequencyHz[bin]`
 * at time `t * frameHopSeconds`.
 */
data class Spectrogram(
    val frames: List<DoubleArray>,
    val frameHopSeconds: Double,
    val binFrequencyHz: DoubleArray,
    val floorDb: Double = -100.0,
)

data class LoudnessSample(val timeSeconds: Double, val rmsDb: Double)

/** Powers SAJJIL's real-time spectrogram / waterfall / loudness-history views. */
object SpectrogramAnalyzer {

    fun compute(samples: FloatArray, sampleRate: Int, fftSize: Int = 1024, hopSize: Int = fftSize / 4): Spectrogram {
        require(FFT.isPowerOfTwo(fftSize)) { "fftSize must be a power of two" }
        val window = DoubleArray(fftSize) { i -> 0.5 - 0.5 * cos(2.0 * PI * i / fftSize) }
        val coherentGain = window.sum().coerceAtLeast(1.0)
        val half = fftSize / 2 + 1
        val binFrequencyHz = DoubleArray(half) { k -> k * sampleRate.toDouble() / fftSize }

        val frames = mutableListOf<DoubleArray>()
        var start = 0
        while (start + fftSize <= samples.size) {
            val real = DoubleArray(fftSize)
            val imag = DoubleArray(fftSize)
            for (i in 0 until fftSize) real[i] = samples[start + i] * window[i]
            FFT.transform(real, imag, inverse = false)

            val frameDb = DoubleArray(half)
            for (k in 0 until half) {
                // Single-sided amplitude spectrum: bins other than DC/Nyquist split their
                // energy between the positive and negative frequency, so double them back
                // to read a full-scale tone as ~0 dBFS instead of ~-6 dBFS.
                val sidedCorrection = if (k == 0 || k == fftSize / 2) 1.0 else 2.0
                val magnitude = sidedCorrection * sqrt(real[k] * real[k] + imag[k] * imag[k]) / coherentGain
                frameDb[k] = max(20.0 * log10(max(magnitude, 1e-9)), -100.0)
            }
            frames.add(frameDb)
            start += hopSize
        }

        return Spectrogram(frames, hopSize.toDouble() / sampleRate, binFrequencyHz)
    }

    fun loudnessHistory(
        samples: FloatArray,
        sampleRate: Int,
        windowSeconds: Double = 0.4,
        hopSeconds: Double = 0.1,
    ): List<LoudnessSample> {
        val windowSize = max(1, (sampleRate * windowSeconds).toInt())
        val hopSize = max(1, (sampleRate * hopSeconds).toInt())
        val result = mutableListOf<LoudnessSample>()
        var start = 0
        while (start + windowSize <= samples.size) {
            var sum = 0.0
            for (i in start until start + windowSize) sum += samples[i].toDouble() * samples[i]
            val rms = sqrt(sum / windowSize)
            result.add(LoudnessSample(start.toDouble() / sampleRate, 20.0 * log10(max(rms, 1e-9))))
            start += hopSize
        }
        return result
    }
}
