package ai.sautiy.core.dsp

import ai.sautiy.core.audio.AudioBuffer
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.ceil
import kotlin.math.floor
import kotlin.math.min
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Band-limited sample rate conversion by windowed-sinc interpolation.
 *
 * SAUTIY needs this in three places: a device that refuses the requested capture rate, an
 * imported file at a foreign rate, and an MP3 export at 44.1 kHz from 48 kHz material. All
 * three are quality-critical — a naive linear or drop-sample conversion puts aliased images of
 * sibilance straight into the 4–8 kHz band where the ear is most sensitive, which is exactly
 * the "digital" harshness that makes phone recordings sound like phone recordings.
 *
 * The filter is a Kaiser-windowed sinc. When **downsampling**, the cutoff is scaled by the
 * conversion ratio so the anti-alias filter sits below the *new* Nyquist frequency — the step
 * that a surprising amount of resampling code omits, and the reason this one does not fold
 * high frequencies back into the audible band.
 */
public object Resampler {

    /**
     * @param zeroCrossings half-width of the kernel in sinc lobes. More lobes means a steeper
     *   transition and deeper stopband, at linear cost.
     * @param kaiserBeta shape of the Kaiser window; 8.6 gives roughly 90 dB of stopband
     *   attenuation, comfortably below the noise floor of any microphone on a phone.
     * @param cutoffSafety where the filter's cutoff is placed relative to the new Nyquist when
     *   downsampling. A filter with its cutoff *at* Nyquist has its entire transition band
     *   above it, so everything in that band aliases; pulling the cutoff down by this factor
     *   moves the transition below Nyquist, at the cost of a little air at the very top. The
     *   narrower the kernel, the wider its transition, so the faster tiers pull down further.
     */
    public enum class Quality(
        public val zeroCrossings: Int,
        public val kaiserBeta: Double,
        public val cutoffSafety: Double,
    ) {
        /** For scrubbing and previews, where the result is heard for a fraction of a second. */
        FAST(8, 6.0, 0.85),

        /** The default for playback and capture rate matching. */
        GOOD(16, 8.6, 0.92),

        /** For export and any conversion the user will keep. */
        TRANSPARENT(32, 10.0, 0.96),
    }

    /** Converts [buffer] to [targetRate]. Returns the same instance when no work is needed. */
    public fun resample(
        buffer: AudioBuffer,
        targetRate: Int,
        quality: Quality = Quality.GOOD,
    ): AudioBuffer {
        require(targetRate > 0) { "Target rate must be positive" }
        if (targetRate == buffer.sampleRate || buffer.frameCount == 0) return buffer

        val ratio = targetRate.toDouble() / buffer.sampleRate
        val outFrames = floor(buffer.frameCount * ratio).toInt().coerceAtLeast(1)

        val kernel = SincKernel(quality, cutoffScaleFor(ratio, quality))

        val outChannels = Array(buffer.channelCount) { FloatArray(outFrames) }
        for (c in 0 until buffer.channelCount) {
            val source = buffer.channels[c]
            val destination = outChannels[c]
            for (n in 0 until outFrames) {
                val sourcePosition = n / ratio
                destination[n] = kernel.interpolate(source, sourcePosition)
            }
        }
        return AudioBuffer(outChannels, targetRate)
    }

    /**
     * Resamples by a rate *factor* rather than to a target rate, keeping the nominal sample
     * rate unchanged. This is playback speed control (chapter 8): 1.5× makes the material
     * shorter and the voice higher, exactly as a tape machine would, and the pitch-preserving
     * variant lives in [TimeStretch].
     */
    public fun changeSpeed(
        buffer: AudioBuffer,
        speed: Double,
        quality: Quality = Quality.GOOD,
    ): AudioBuffer {
        require(speed > 0.0) { "Speed must be positive" }
        if (speed == 1.0 || buffer.frameCount == 0) return buffer

        val outFrames = floor(buffer.frameCount / speed).toInt().coerceAtLeast(1)
        val kernel = SincKernel(quality, cutoffScaleFor(1.0 / speed, quality))

        val outChannels = Array(buffer.channelCount) { FloatArray(outFrames) }
        for (c in 0 until buffer.channelCount) {
            val source = buffer.channels[c]
            val destination = outChannels[c]
            for (n in 0 until outFrames) {
                destination[n] = kernel.interpolate(source, n * speed)
            }
        }
        return AudioBuffer(outChannels, buffer.sampleRate)
    }

    /**
     * Where to place the filter cutoff, as a fraction of the source Nyquist.
     *
     * Downsampling pulls the cutoff down to the *new* Nyquist and then a little further, by the
     * tier's safety factor. Upsampling leaves it wide open: there is nothing above the source
     * Nyquist to alias, so narrowing there would only throw away treble the user recorded.
     */
    private fun cutoffScaleFor(ratio: Double, quality: Quality): Double =
        if (ratio < 1.0) ratio * quality.cutoffSafety else 1.0

    /**
     * A Kaiser-windowed sinc evaluated from a precomputed table with linear interpolation
     * between entries.
     *
     * The table is what makes this affordable on a phone: evaluating `sin(x)/x` and a Bessel
     * function per tap per sample would be tens of millions of transcendental calls for a
     * three-minute file. At 512 entries per lobe the interpolation error sits below −100 dB,
     * far under the resampler's own stopband.
     */
    private class SincKernel(quality: Quality, private val cutoffScale: Double) {
        private val zeroCrossings = quality.zeroCrossings
        private val table: DoubleArray
        private val entriesPerLobe = TABLE_ENTRIES_PER_LOBE

        init {
            val entries = zeroCrossings * entriesPerLobe + 2
            table = DoubleArray(entries)
            for (i in 0 until entries) {
                val x = i.toDouble() / entriesPerLobe
                table[i] = sinc(x) * kaiser(x / zeroCrossings, quality.kaiserBeta)
            }
        }

        /** Kernel weight at distance [x] lobes from the centre, by table lookup. */
        private fun weight(x: Double): Double {
            val magnitude = abs(x)
            if (magnitude >= zeroCrossings) return 0.0
            val position = magnitude * entriesPerLobe
            val index = position.toInt()
            val fraction = position - index
            return table[index] * (1.0 - fraction) + table[index + 1] * fraction
        }

        /**
         * Value of [source] at fractional position [position], band-limited.
         *
         * Two details here carry the whole quality of the resampler.
         *
         * **Normalisation is by the full window, not by the taps that happened to land inside
         * the array.** A truncated kernel has a slightly different sum at every fractional
         * phase; dividing by that realised sum makes the gain wobble at the phase rate, which
         * is amplitude modulation, which puts sidebands either side of every tone in the
         * recording. Normalising by the phase-correct full-window sum makes the gain exactly
         * unity for every phase and those sidebands disappear.
         *
         * **Out-of-range reads extend the edge sample rather than returning silence.** Treating
         * the outside of a recording as digital black puts a step discontinuity at each end,
         * and the filter rings on it — a converted file that fades in and out at its own
         * boundaries. Holding the edge value keeps a constant signal constant right to the
         * last sample.
         */
        fun interpolate(source: FloatArray, position: Double): Float {
            if (source.isEmpty()) return 0f
            val centre = floor(position)
            val fraction = position - centre
            val centreIndex = centre.toInt()
            val lastIndex = source.size - 1

            // The kernel widens by 1/cutoffScale when downsampling, because the filter is
            // stretched in time as its cutoff drops.
            val halfWidth = ceil(zeroCrossings / cutoffScale).toInt()

            var sum = 0.0
            var weightSum = 0.0
            for (i in -halfWidth..halfWidth) {
                val distance = (i - fraction) * cutoffScale
                val w = weight(distance)
                if (w == 0.0) continue
                val index = (centreIndex + i).coerceIn(0, lastIndex)
                sum += source[index] * w
                weightSum += w
            }
            return if (weightSum == 0.0) 0f else (sum / weightSum).toFloat()
        }

        companion object {
            const val TABLE_ENTRIES_PER_LOBE = 512
        }
    }

    private fun sinc(x: Double): Double {
        if (x == 0.0) return 1.0
        val pix = PI * x
        return sin(pix) / pix
    }

    /** Kaiser window over −1..+1. */
    private fun kaiser(x: Double, beta: Double): Double {
        if (abs(x) >= 1.0) return 0.0
        return besselI0(beta * sqrt(1.0 - x * x)) / besselI0(beta)
    }

    /** Zeroth-order modified Bessel function of the first kind, by series expansion. */
    private fun besselI0(x: Double): Double {
        var sum = 1.0
        var term = 1.0
        val halfSquared = (x / 2.0) * (x / 2.0)
        var k = 1
        while (k < 64) {
            term *= halfSquared / (k.toDouble() * k)
            sum += term
            if (term < sum * 1e-16) break
            k++
        }
        return sum
    }
}
