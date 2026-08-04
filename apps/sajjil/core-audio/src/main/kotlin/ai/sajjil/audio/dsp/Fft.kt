package ai.sajjil.audio.dsp

import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * In-place iterative radix-2 complex FFT.
 *
 * Instances cache twiddle factors and the bit-reversal permutation for one size, so the STFT
 * loops in [ai.sajjil.audio.dsp.SpectralNoiseReducer] can run thousands of transforms without
 * reallocating anything.
 */
class Fft(val size: Int) {

    init {
        require(size >= 2 && (size and (size - 1)) == 0) {
            "FFT size must be a power of two >= 2, was $size"
        }
    }

    private val levels = Integer.numberOfTrailingZeros(size)
    private val cosTable = DoubleArray(size / 2) { cos(2.0 * PI * it / size) }
    private val sinTable = DoubleArray(size / 2) { sin(2.0 * PI * it / size) }
    private val reversed = IntArray(size) { Integer.reverse(it) ushr (32 - levels) }

    /** Forward transform. [re] and [im] are modified in place and must both be [size] long. */
    fun forward(re: DoubleArray, im: DoubleArray) {
        require(re.size == size && im.size == size) { "arrays must be $size long" }
        transform(re, im)
    }

    /**
     * Inverse transform, scaled by 1/N so `inverse(forward(x)) == x`.
     * [re] and [im] are modified in place.
     */
    fun inverse(re: DoubleArray, im: DoubleArray) {
        require(re.size == size && im.size == size) { "arrays must be $size long" }
        // Swapping the real and imaginary parts around a forward transform yields the inverse.
        transform(im, re)
        val scale = 1.0 / size
        for (i in 0 until size) {
            re[i] *= scale
            im[i] *= scale
        }
    }

    private fun transform(re: DoubleArray, im: DoubleArray) {
        for (i in 0 until size) {
            val j = reversed[i]
            if (j > i) {
                var t = re[i]; re[i] = re[j]; re[j] = t
                t = im[i]; im[i] = im[j]; im[j] = t
            }
        }
        var span = 2
        while (span <= size) {
            val half = span / 2
            val step = size / span
            var i = 0
            while (i < size) {
                var j = i
                var k = 0
                while (j < i + half) {
                    val l = j + half
                    val c = cosTable[k]
                    val s = sinTable[k]
                    val tre = re[l] * c + im[l] * s
                    val tim = -re[l] * s + im[l] * c
                    re[l] = re[j] - tre
                    im[l] = im[j] - tim
                    re[j] += tre
                    im[j] += tim
                    j++
                    k += step
                }
                i += span
            }
            if (span == size) break
            span *= 2
        }
    }

    /** Magnitude spectrum for bins `0..size/2`, given a transformed pair. */
    fun magnitudes(re: DoubleArray, im: DoubleArray, out: DoubleArray = DoubleArray(size / 2 + 1)): DoubleArray {
        for (i in 0..size / 2) out[i] = sqrt(re[i] * re[i] + im[i] * im[i])
        return out
    }
}

/** Window functions. All are periodic (not symmetric), which is what STFT overlap-add wants. */
object Windows {

    /** Hann window. With 75% overlap-add this sums to a constant, so resynthesis is transparent. */
    fun hann(size: Int): DoubleArray = DoubleArray(size) { 0.5 - 0.5 * cos(2.0 * PI * it / size) }

    /** Square-root Hann, for analysis/synthesis windowing on both ends of an STFT. */
    fun sqrtHann(size: Int): DoubleArray = hann(size).map { sqrt(it) }.toDoubleArray()

    fun hamming(size: Int): DoubleArray = DoubleArray(size) { 0.54 - 0.46 * cos(2.0 * PI * it / size) }
}
