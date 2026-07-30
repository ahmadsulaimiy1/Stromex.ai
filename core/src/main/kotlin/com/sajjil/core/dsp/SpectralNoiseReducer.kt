package com.sajjil.core.dsp

import com.sajjil.core.dsp.fft.FFT
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.sqrt

enum class NoiseReductionStrength(val oversubtraction: Double, val spectralFloor: Double) {
    LIGHT(1.2, 0.10),
    MODERATE(1.8, 0.05),
    STRONG(2.5, 0.02),
    EXTREME(3.5, 0.005),
}

/**
 * Broadband noise reduction via spectral subtraction (Boll, 1979): an STFT
 * with 75%-overlap Hann windows, subtracting a learned noise magnitude
 * profile from each frame's spectrum with an oversubtraction factor and a
 * spectral floor to avoid musical-noise artifacts, then reconstructing with
 * weighted overlap-add. Removes steady-state noise (fans, AC hum, room
 * tone, hiss) while leaving transient speech/recitation content intact.
 *
 * The signal is zero-padded by one frame on each side before framing, so
 * every original sample sits inside the region with full 4x overlap
 * coverage. Without this, edge samples are reconstructed from a partial
 * window sum and the division in [reconstruct] blows up the residual.
 */
class SpectralNoiseReducer(
    private val sampleRate: Int,
    private val frameSize: Int = 1024,
    private val hopSize: Int = frameSize / 4,
) {
    private val window = DoubleArray(frameSize) { i -> 0.5 - 0.5 * cos(2.0 * PI * i / frameSize) }
    private var noiseProfile: DoubleArray? = null

    /** Learns the noise floor spectrum from a segment known to contain only background noise. */
    fun learnNoiseProfile(noiseOnlySamples: FloatArray) {
        noiseProfile = averageMagnitudeSpectrum(noiseOnlySamples)
    }

    /**
     * Processes a full buffer, auto-estimating the noise profile from its
     * quietest frames when none has been explicitly learned.
     */
    fun process(samples: FloatArray, strength: NoiseReductionStrength = NoiseReductionStrength.MODERATE): FloatArray {
        if (samples.size < frameSize) return samples.copyOf()
        val profile = noiseProfile ?: estimateNoiseFromQuietestFrames(samples)

        val padded = FloatArray(samples.size + 2 * frameSize)
        samples.copyInto(padded, frameSize)

        val cleaned = reconstruct(padded, profile, strength)
        return cleaned.copyOfRange(frameSize, frameSize + samples.size)
    }

    private fun reconstruct(padded: FloatArray, profile: DoubleArray, strength: NoiseReductionStrength): FloatArray {
        val output = DoubleArray(padded.size)
        val windowSum = DoubleArray(padded.size)
        val half = frameSize / 2 + 1

        var start = 0
        while (start + frameSize <= padded.size) {
            val real = DoubleArray(frameSize)
            val imag = DoubleArray(frameSize)
            for (i in 0 until frameSize) real[i] = padded[start + i] * window[i]

            FFT.transform(real, imag, inverse = false)

            for (k in 0 until half) {
                val mag = sqrt(real[k] * real[k] + imag[k] * imag[k])
                val phaseR = if (mag > 1e-12) real[k] / mag else 1.0
                val phaseI = if (mag > 1e-12) imag[k] / mag else 0.0

                val noiseMag = profile[k] * strength.oversubtraction
                val floor = profile[k] * strength.spectralFloor
                val cleanMag = max(mag - noiseMag, floor)

                real[k] = cleanMag * phaseR
                imag[k] = cleanMag * phaseI
                if (k in 1 until frameSize - k) {
                    val mirror = frameSize - k
                    real[mirror] = real[k]
                    imag[mirror] = -imag[k]
                }
            }

            FFT.transform(real, imag, inverse = true)

            for (i in 0 until frameSize) {
                output[start + i] += real[i] * window[i]
                windowSum[start + i] += window[i] * window[i]
            }
            start += hopSize
        }

        val result = FloatArray(padded.size)
        for (i in padded.indices) {
            result[i] = if (windowSum[i] > 1e-6) (output[i] / windowSum[i]).toFloat() else 0f
        }
        return result
    }

    private fun estimateNoiseFromQuietestFrames(samples: FloatArray, fraction: Double = 0.15): DoubleArray {
        val half = frameSize / 2 + 1
        data class Frame(val start: Int, val rms: Double)
        val frames = mutableListOf<Frame>()
        var start = 0
        while (start + frameSize <= samples.size) {
            var sum = 0.0
            for (i in 0 until frameSize) sum += samples[start + i].toDouble() * samples[start + i]
            frames.add(Frame(start, sqrt(sum / frameSize)))
            start += hopSize
        }
        if (frames.isEmpty()) return DoubleArray(half)

        val quietCount = max(1, (frames.size * fraction).toInt())
        val quietest = frames.sortedBy { it.rms }.take(quietCount)

        val accum = DoubleArray(half)
        for (frame in quietest) {
            val real = DoubleArray(frameSize)
            val imag = DoubleArray(frameSize)
            for (i in 0 until frameSize) real[i] = samples[frame.start + i] * window[i]
            FFT.transform(real, imag, inverse = false)
            for (k in 0 until half) accum[k] += sqrt(real[k] * real[k] + imag[k] * imag[k])
        }
        val quietCountDouble = quietest.size.toDouble()
        for (k in 0 until half) accum[k] = accum[k] / quietCountDouble
        return accum
    }

    private fun averageMagnitudeSpectrum(samples: FloatArray): DoubleArray {
        val half = frameSize / 2 + 1
        val accum = DoubleArray(half)
        var frames = 0
        var start = 0
        while (start + frameSize <= samples.size) {
            val real = DoubleArray(frameSize)
            val imag = DoubleArray(frameSize)
            for (i in 0 until frameSize) real[i] = samples[start + i] * window[i]
            FFT.transform(real, imag, inverse = false)
            for (k in 0 until half) accum[k] += sqrt(real[k] * real[k] + imag[k] * imag[k])
            frames++
            start += hopSize
        }
        if (frames > 0) {
            val framesDouble = frames.toDouble()
            for (k in 0 until half) accum[k] = accum[k] / framesDouble
        }
        return accum
    }
}
