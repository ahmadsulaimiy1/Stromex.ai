package com.sajjil.core.dsp.fft

import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

/**
 * Iterative radix-2 Cooley-Tukey FFT, in place, for power-of-two sizes.
 * `real`/`imag` are overwritten with the transform result.
 */
object FFT {
    fun isPowerOfTwo(n: Int) = n > 0 && (n and (n - 1)) == 0

    fun transform(real: DoubleArray, imag: DoubleArray, inverse: Boolean) {
        val n = real.size
        require(n == imag.size) { "real/imag size mismatch" }
        require(isPowerOfTwo(n)) { "FFT size must be a power of two, got $n" }

        // Bit-reversal permutation.
        var j = 0
        for (i in 0 until n - 1) {
            if (i < j) {
                var tmp = real[i]; real[i] = real[j]; real[j] = tmp
                tmp = imag[i]; imag[i] = imag[j]; imag[j] = tmp
            }
            var m = n shr 1
            while (m in 1..j) {
                j -= m
                m = m shr 1
            }
            j += m
        }

        val sign = if (inverse) 1.0 else -1.0
        var size = 2
        while (size <= n) {
            val half = size shr 1
            val angleStep = sign * 2.0 * PI / size
            var start = 0
            while (start < n) {
                for (k in 0 until half) {
                    val angle = angleStep * k
                    val wr = cos(angle)
                    val wi = sin(angle)
                    val evenIdx = start + k
                    val oddIdx = start + k + half
                    val tr = wr * real[oddIdx] - wi * imag[oddIdx]
                    val ti = wr * imag[oddIdx] + wi * real[oddIdx]
                    real[oddIdx] = real[evenIdx] - tr
                    imag[oddIdx] = imag[evenIdx] - ti
                    real[evenIdx] += tr
                    imag[evenIdx] += ti
                }
                start += size
            }
            size = size shl 1
        }

        if (inverse) {
            val nDouble = n.toDouble()
            for (i in 0 until n) {
                real[i] = real[i] / nDouble
                imag[i] = imag[i] / nDouble
            }
        }
    }

    /** Smallest power-of-two >= n. */
    fun nextPowerOfTwo(n: Int): Int {
        var p = 1
        while (p < n) p = p shl 1
        return p
    }
}
