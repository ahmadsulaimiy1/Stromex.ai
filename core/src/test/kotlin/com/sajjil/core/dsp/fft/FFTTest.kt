package com.sajjil.core.dsp.fft

import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.sin
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class FFTTest {
    @Test
    fun `forward then inverse reconstructs the original signal`() {
        val n = 1024
        val original = DoubleArray(n) { sin(2.0 * PI * 5 * it / n) + 0.5 * sin(2.0 * PI * 40 * it / n) }
        val real = original.copyOf()
        val imag = DoubleArray(n)

        FFT.transform(real, imag, inverse = false)
        FFT.transform(real, imag, inverse = true)

        for (i in original.indices) {
            assertTrue(abs(real[i] - original[i]) < 1e-9, "mismatch at $i: ${real[i]} vs ${original[i]}")
        }
    }

    @Test
    fun `pure sine produces energy concentrated at the expected bin`() {
        val n = 1024
        val binIndex = 32
        val real = DoubleArray(n) { sin(2.0 * PI * binIndex * it / n) }
        val imag = DoubleArray(n)

        FFT.transform(real, imag, inverse = false)

        val magnitudes = DoubleArray(n) { kotlin.math.sqrt(real[it] * real[it] + imag[it] * imag[it]) }
        val peakBin = magnitudes.indices.maxByOrNull { magnitudes[it] }!!
        assertTrue(peakBin == binIndex || peakBin == n - binIndex, "expected peak near bin $binIndex, got $peakBin")
    }

    @Test
    fun `nextPowerOfTwo rounds up correctly`() {
        assertEquals(1024, FFT.nextPowerOfTwo(1000))
        assertEquals(1024, FFT.nextPowerOfTwo(1024))
        assertEquals(2048, FFT.nextPowerOfTwo(1025))
    }
}
