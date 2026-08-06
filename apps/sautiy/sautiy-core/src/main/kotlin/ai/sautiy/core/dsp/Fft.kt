package ai.sautiy.core.dsp

import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * In-place iterative radix-2 FFT.
 *
 * Used by the spectrogram, the frequency analyser and the spectral noise reducer. Written
 * without recursion and with the twiddle factors precomputed per instance, because on the
 * spectrogram path this runs a few hundred times per second on a phone and a per-call
 * `sin`/`cos` would dominate the cost.
 */
public class Fft(public val size: Int) {

    init {
        require(size >= 2 && size and (size - 1) == 0) { "FFT size must be a power of two, was $size" }
    }

    private val levels = Integer.numberOfTrailingZeros(size)
    private val cosTable = DoubleArray(size / 2) { cos(2.0 * PI * it / size) }
    private val sinTable = DoubleArray(size / 2) { sin(2.0 * PI * it / size) }
    private val reversed = IntArray(size) { Integer.reverse(it) ushr (32 - levels) }

    /** Forward transform, in place. */
    public fun forward(real: DoubleArray, imaginary: DoubleArray) {
        require(real.size == size && imaginary.size == size) { "Buffers must be $size long" }

        for (i in 0 until size) {
            val j = reversed[i]
            if (j > i) {
                var t = real[i]; real[i] = real[j]; real[j] = t
                t = imaginary[i]; imaginary[i] = imaginary[j]; imaginary[j] = t
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
                    val partner = j + half
                    val wr = cosTable[k]
                    val wi = -sinTable[k]
                    val tr = real[partner] * wr - imaginary[partner] * wi
                    val ti = real[partner] * wi + imaginary[partner] * wr
                    real[partner] = real[j] - tr
                    imaginary[partner] = imaginary[j] - ti
                    real[j] += tr
                    imaginary[j] += ti
                    j++
                    k += step
                }
                i += span
            }
            span *= 2
        }
    }

    /** Inverse transform, in place, correctly scaled so `inverse(forward(x)) == x`. */
    public fun inverse(real: DoubleArray, imaginary: DoubleArray) {
        // The conjugate trick: swapping real and imaginary either side of a forward transform
        // performs the inverse, without a second twiddle table.
        forward(imaginary, real)
        val scale = 1.0 / size
        for (i in 0 until size) {
            real[i] *= scale
            imaginary[i] *= scale
        }
    }

    /** Magnitude spectrum of a real signal, bins `0..size/2`. */
    public fun magnitudeSpectrum(samples: FloatArray, window: Window = Window.HANN): DoubleArray {
        val real = DoubleArray(size)
        val imaginary = DoubleArray(size)
        val weights = window.coefficients(size)
        val count = minOf(samples.size, size)
        for (i in 0 until count) real[i] = samples[i] * weights[i]

        forward(real, imaginary)

        val bins = size / 2 + 1
        val out = DoubleArray(bins)
        val gain = window.coherentGain(size)
        for (i in 0 until bins) {
            val magnitude = sqrt(real[i] * real[i] + imaginary[i] * imaginary[i])
            // Scaled so a full-scale sine reads as its own amplitude, whatever the window.
            out[i] = if (i == 0 || i == size / 2) magnitude / (size * gain) else 2.0 * magnitude / (size * gain)
        }
        return out
    }

    /** Frequency of bin [index] at [sampleRate]. */
    public fun binFrequency(index: Int, sampleRate: Int): Double = index.toDouble() * sampleRate / size
}

/** Analysis windows. */
public enum class Window {
    /** No window. Only correct when the block is exactly periodic. */
    RECTANGULAR,

    /**
     * The default for everything in SAUTIY. Sidelobes fall at 18 dB per octave, so a loud tone
     * cannot masquerade as content several hundred hertz away — the failure that makes an
     * unwindowed analyser report noise that is not there.
     */
    HANN,

    /** Slightly wider main lobe than Hann, lower nearest sidelobe. For the spectrogram. */
    HAMMING,

    /** Very low sidelobes, for measuring something quiet next to something loud. */
    BLACKMAN_HARRIS,
    ;

    public fun coefficients(size: Int): DoubleArray = DoubleArray(size) { i ->
        val t = i.toDouble() / (size - 1)
        when (this) {
            RECTANGULAR -> 1.0
            HANN -> 0.5 - 0.5 * cos(2.0 * PI * t)
            HAMMING -> 0.54 - 0.46 * cos(2.0 * PI * t)
            BLACKMAN_HARRIS ->
                0.35875 - 0.48829 * cos(2.0 * PI * t) +
                    0.14128 * cos(4.0 * PI * t) - 0.01168 * cos(6.0 * PI * t)
        }
    }

    /** Mean of the window, by which a spectrum must be divided to read true amplitudes. */
    public fun coherentGain(size: Int): Double = coefficients(size).average()
}
