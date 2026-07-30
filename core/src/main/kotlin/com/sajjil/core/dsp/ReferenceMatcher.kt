package com.sajjil.core.dsp

import com.sajjil.core.dsp.fft.FFT
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.log10
import kotlin.math.max
import kotlin.math.pow
import kotlin.math.sqrt

/**
 * SAJJIL Reference Mastering Engine's spectral-matching stage: measures the
 * smoothed (1/3-octave) spectral envelope of a take against a reference
 * recording — a target Haramain/broadcast take, say — and builds a 31-band
 * graphic EQ correction that nudges the take's tonal balance toward the
 * reference. This is a *tonal* match only (frequency balance); it says
 * nothing about the reference's dynamics/loudness, which the mastering
 * chain's compressor/limiter stages handle separately.
 */
object ReferenceMatcher {

    fun buildMatchingEq(
        sampleRate: Int,
        source: FloatArray,
        reference: FloatArray,
        maxCorrectionDb: Double = 8.0,
        fftSize: Int = 2048,
    ): ParametricEqualizer {
        val sourceBands = bandLevelsDb(source, sampleRate, fftSize)
        val referenceBands = bandLevelsDb(reference, sampleRate, fftSize)

        val correction = DoubleArray(GRAPHIC_EQ_31_BAND_FREQUENCIES.size) { i ->
            (referenceBands[i] - sourceBands[i]).coerceIn(-maxCorrectionDb, maxCorrectionDb)
        }
        return ParametricEqualizer.graphic31Band(sampleRate, correction)
    }

    fun matchToReference(
        sampleRate: Int,
        source: FloatArray,
        reference: FloatArray,
        maxCorrectionDb: Double = 8.0,
    ): FloatArray {
        val eq = buildMatchingEq(sampleRate, source, reference, maxCorrectionDb)
        val output = source.copyOf()
        eq.processBlock(output)
        return output
    }

    /** Average dB level at each ISO 1/3-octave band center, smoothed across the whole buffer. */
    private fun bandLevelsDb(samples: FloatArray, sampleRate: Int, fftSize: Int): DoubleArray {
        if (samples.size < fftSize) return DoubleArray(GRAPHIC_EQ_31_BAND_FREQUENCIES.size) { -100.0 }

        val window = DoubleArray(fftSize) { i -> 0.5 - 0.5 * cos(2.0 * PI * i / fftSize) }
        val half = fftSize / 2 + 1
        val hopSize = fftSize / 2
        val accum = DoubleArray(half)
        var frameCount = 0

        var start = 0
        while (start + fftSize <= samples.size) {
            val real = DoubleArray(fftSize)
            val imag = DoubleArray(fftSize)
            for (i in 0 until fftSize) real[i] = samples[start + i] * window[i]
            FFT.transform(real, imag, inverse = false)
            for (k in 0 until half) accum[k] += sqrt(real[k] * real[k] + imag[k] * imag[k])
            frameCount++
            start += hopSize
        }
        if (frameCount == 0) return DoubleArray(GRAPHIC_EQ_31_BAND_FREQUENCIES.size) { -100.0 }
        val frameCountDouble = frameCount.toDouble()
        for (k in 0 until half) accum[k] = accum[k] / frameCountDouble

        val binFreqs = DoubleArray(half) { k -> k * sampleRate.toDouble() / fftSize }
        return DoubleArray(GRAPHIC_EQ_31_BAND_FREQUENCIES.size) { i ->
            val center = GRAPHIC_EQ_31_BAND_FREQUENCIES[i]
            val low = center / THIRD_OCTAVE_RATIO
            val high = center * THIRD_OCTAVE_RATIO
            var sum = 0.0
            var count = 0
            for (k in 0 until half) {
                if (binFreqs[k] in low..high) {
                    sum += accum[k]
                    count++
                }
            }
            if (count == 0) -100.0 else max(20.0 * log10(max(sum / count, 1e-9)), -100.0)
        }
    }

    private val THIRD_OCTAVE_RATIO = 2.0.pow(1.0 / 6.0)
}
