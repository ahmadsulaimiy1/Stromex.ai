package com.sajjil.core.dsp

import com.sajjil.core.dsp.fft.FFT
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.pow
import kotlin.math.sqrt

/**
 * Spectral-subtraction speech dereverberation, informed by a measured or
 * estimated RT60 (see `AcousticAnalyzer.estimateRt60`). Models the late
 * reverberant tail per frequency bin as a single-pole leaky integrator of
 * past frame energy — decaying at the rate Polack's statistical
 * reverberation model predicts for the given RT60 — then subtracts that
 * estimate from each frame's energy before reconstructing.
 *
 * This targets late reflections (mosque/hall "boominess" and smear), the
 * same family of technique used in Lebart/Boucher/Denbigh-style
 * dereverberation. It is not a trained model, and it will not remove
 * discrete slap-back echo the way a delay-based echo canceller would —
 * that's a distinct, still-unimplemented feature (see README roadmap).
 */
class Dereverberator(
    private val sampleRate: Int,
    private val frameSize: Int = 1024,
    private val hopSize: Int = frameSize / 4,
) {
    private val window = DoubleArray(frameSize) { i -> 0.5 - 0.5 * cos(2.0 * PI * i / frameSize) }

    fun process(samples: FloatArray, rt60Seconds: Double, strength: Double = 1.0, spectralFloor: Double = 0.05): FloatArray {
        if (samples.size < frameSize || rt60Seconds <= 0.0) return samples.copyOf()

        val hopTime = hopSize.toDouble() / sampleRate
        val decayPerFrame = 10.0.pow(-6.0 * hopTime / rt60Seconds)

        val padded = FloatArray(samples.size + 2 * frameSize)
        samples.copyInto(padded, frameSize)

        val half = frameSize / 2 + 1
        val lateReverbEnergy = DoubleArray(half)

        val output = DoubleArray(padded.size)
        val windowSum = DoubleArray(padded.size)

        var start = 0
        while (start + frameSize <= padded.size) {
            val real = DoubleArray(frameSize)
            val imag = DoubleArray(frameSize)
            for (i in 0 until frameSize) real[i] = padded[start + i] * window[i]
            FFT.transform(real, imag, inverse = false)

            val frameEnergy = DoubleArray(half)
            for (k in 0 until half) frameEnergy[k] = real[k] * real[k] + imag[k] * imag[k]

            for (k in 0 until half) {
                val currentEnergy = frameEnergy[k]
                val mag = sqrt(currentEnergy)
                val phaseR = if (mag > 1e-12) real[k] / mag else 1.0
                val phaseI = if (mag > 1e-12) imag[k] / mag else 0.0

                val predictedLateEnergy = lateReverbEnergy[k] * strength
                val floorEnergy = currentEnergy * spectralFloor
                val cleanEnergy = max(currentEnergy - predictedLateEnergy, floorEnergy)
                val cleanMag = sqrt(cleanEnergy)

                real[k] = cleanMag * phaseR
                imag[k] = cleanMag * phaseI
                if (k in 1 until frameSize - k) {
                    val mirror = frameSize - k
                    real[mirror] = real[k]
                    imag[mirror] = -imag[k]
                }

                lateReverbEnergy[k] = decayPerFrame * (lateReverbEnergy[k] + currentEnergy)
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
        return result.copyOfRange(frameSize, frameSize + samples.size)
    }
}
