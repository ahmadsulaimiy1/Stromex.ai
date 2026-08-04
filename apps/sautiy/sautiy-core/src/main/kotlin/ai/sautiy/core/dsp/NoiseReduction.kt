package ai.sautiy.core.dsp

import ai.sautiy.core.audio.AudioBuffer
import kotlin.math.max
import kotlin.math.sqrt

/**
 * Spectral noise reduction by overlap-add short-time Fourier transform.
 *
 * The method: learn the magnitude spectrum of the noise from a passage where nobody is
 * talking, then in every subsequent frame subtract that profile from the magnitude while
 * leaving the phase alone, and resynthesise.
 *
 * Two details are the difference between this and the underwater warble that gives noise
 * reduction its bad name:
 *
 * **A spectral floor.** Subtracting all the way to zero leaves isolated surviving bins
 * scattered across an otherwise empty spectrum, and those bins are heard as tones flickering
 * in and out — "musical noise". Holding the residual at a floor (default −18 dB relative to
 * the original bin) keeps a quiet, steady bed underneath that the ear reads as room rather
 * than as artefact.
 *
 * **Over-subtraction with smoothing.** Real noise varies frame to frame around its average, so
 * subtracting exactly the average leaves half the frames with residue. A modest over-subtraction
 * factor, combined with smoothing the gain across neighbouring bins, removes that residue
 * without gouging holes in the speech.
 */
public class NoiseReduction(
    /** How much of the profile to subtract. 1.0 is exact; above that is over-subtraction. */
    public val strength: Double = 1.6,
    /** Residual floor relative to the input bin, in dB. Never subtract past this. */
    public val floorDb: Double = -18.0,
    public val fftSize: Int = 1024,
) {
    init {
        require(fftSize >= 128 && fftSize and (fftSize - 1) == 0) { "FFT size must be a power of two" }
        require(strength >= 0.0)
    }

    /** The overlap. 75% with a Hann window sums to unity, so resynthesis is transparent. */
    private val hop = fftSize / 4

    private val fft = Fft(fftSize)
    private val window = Window.HANN.coefficients(fftSize)
    private val windowMeanSquare = window.sumOf { it * it } / fftSize

    /** A learned noise fingerprint. Magnitudes per bin. */
    public class Profile internal constructor(
        internal val magnitudes: DoubleArray,
        public val fftSize: Int,
        public val sampleRate: Int,
        public val framesAnalysed: Int,
        /** Mean of the analysis window squared, needed to undo the window's energy loss. */
        internal val windowMeanSquare: Double,
    ) {
        /**
         * Broadband level of the profile in dBFS — the measured noise floor shown to the user.
         *
         * Raw FFT magnitudes are not decibels of anything: they scale with the transform size
         * and are attenuated by the analysis window. Parseval's relation converts them back to
         * the RMS of the signal they came from, which is a number that means what it says.
         */
        public val levelDb: Double
            get() {
                if (magnitudes.isEmpty() || windowMeanSquare <= 0.0) {
                    return ai.sautiy.core.audio.Decibels.FLOOR_DB
                }
                val last = magnitudes.size - 1
                var energy = magnitudes[0] * magnitudes[0] + magnitudes[last] * magnitudes[last]
                for (b in 1 until last) energy += 2.0 * magnitudes[b] * magnitudes[b]
                val rms = sqrt(energy) / fftSize / sqrt(windowMeanSquare)
                return ai.sautiy.core.audio.Decibels.fromLinear(rms)
            }
    }

    /**
     * Learns a noise profile from a passage that contains only noise.
     *
     * The profile is the **median** across frames, not the mean. A mean is dragged upward by
     * any stray sound that crept into the passage — a chair, a page turning — and a profile
     * learned from a mean then subtracts that sound's spectrum from the entire recording.
     */
    public fun learn(noise: AudioBuffer): Profile {
        val mono = noise.toMono()
        val bins = fftSize / 2 + 1
        val frames = ArrayList<DoubleArray>()

        var position = 0
        while (position + fftSize <= mono.frameCount) {
            val real = DoubleArray(fftSize)
            val imaginary = DoubleArray(fftSize)
            for (i in 0 until fftSize) real[i] = mono.channels[0][position + i] * window[i]
            fft.forward(real, imaginary)

            val magnitudes = DoubleArray(bins)
            for (b in 0 until bins) magnitudes[b] = sqrt(real[b] * real[b] + imaginary[b] * imaginary[b])
            frames += magnitudes
            position += hop
        }

        val profile = DoubleArray(bins)
        if (frames.isEmpty()) return Profile(profile, fftSize, noise.sampleRate, 0, windowMeanSquare)

        val scratch = DoubleArray(frames.size)
        for (b in 0 until bins) {
            for (f in frames.indices) scratch[f] = frames[f][b]
            scratch.sort()
            profile[b] = scratch[scratch.size / 2]
        }
        return Profile(profile, fftSize, noise.sampleRate, frames.size, windowMeanSquare)
    }

    /**
     * Learns from the quietest part of the recording itself, so the user is not required to
     * record a separate noise sample — which, in practice, nobody does.
     */
    public fun learnFromQuietest(buffer: AudioBuffer, windowSeconds: Double = 0.5): Profile {
        val mono = buffer.toMono()
        val windowFrames = (windowSeconds * buffer.sampleRate).toInt().coerceAtMost(mono.frameCount)
        if (windowFrames < fftSize) return learn(mono)

        var quietestStart = 0
        var quietestEnergy = Double.MAX_VALUE
        val step = (windowFrames / 4).coerceAtLeast(1)

        var position = 0
        while (position + windowFrames <= mono.frameCount) {
            var energy = 0.0
            for (i in position until position + windowFrames) {
                energy += mono.channels[0][i].toDouble() * mono.channels[0][i]
            }
            if (energy < quietestEnergy) {
                quietestEnergy = energy
                quietestStart = position
            }
            position += step
        }
        return learn(mono.slice(quietestStart, quietestStart + windowFrames))
    }

    /** Applies the profile, returning a new buffer. The input is not modified. */
    public fun process(buffer: AudioBuffer, profile: Profile): AudioBuffer {
        require(profile.fftSize == fftSize) { "Profile was learned at a different FFT size" }
        val bins = fftSize / 2 + 1
        val floorGain = Math.pow(10.0, floorDb / 20.0)

        val out = AudioBuffer.silence(buffer.channelCount, buffer.frameCount, buffer.sampleRate)
        // Hann at 75% overlap sums to 1.5, so the resynthesis is scaled back by that.
        val overlapGain = 1.0 / 1.5

        for (c in 0 until buffer.channelCount) {
            val input = buffer.channels[c]
            val output = out.channels[c]

            var position = 0
            while (position < buffer.frameCount) {
                val real = DoubleArray(fftSize)
                val imaginary = DoubleArray(fftSize)
                val available = minOf(fftSize, buffer.frameCount - position)
                for (i in 0 until available) real[i] = input[position + i] * window[i]

                fft.forward(real, imaginary)

                // Gain per bin, computed before any of it is applied, so the smoothing below
                // reads unmodified neighbours.
                val gains = DoubleArray(bins)
                for (b in 0 until bins) {
                    val magnitude = sqrt(real[b] * real[b] + imaginary[b] * imaginary[b])
                    if (magnitude <= 0.0) {
                        gains[b] = floorGain
                        continue
                    }
                    val subtracted = magnitude - strength * profile.magnitudes[b]
                    gains[b] = max(subtracted / magnitude, floorGain)
                }

                // Three-bin smoothing: an isolated surviving bin is exactly what is heard as a
                // flickering tone, and averaging with its neighbours removes it.
                val smoothed = DoubleArray(bins)
                for (b in 0 until bins) {
                    val low = (b - 1).coerceAtLeast(0)
                    val high = (b + 1).coerceAtMost(bins - 1)
                    smoothed[b] = (gains[low] + gains[b] + gains[high]) / 3.0
                }

                for (b in 0 until bins) {
                    val gain = smoothed[b]
                    real[b] *= gain
                    imaginary[b] *= gain
                    // Keep the spectrum conjugate-symmetric so the inverse transform is real.
                    if (b in 1 until fftSize / 2) {
                        val mirror = fftSize - b
                        real[mirror] *= gain
                        imaginary[mirror] *= gain
                    }
                }

                fft.inverse(real, imaginary)

                for (i in 0 until available) {
                    output[position + i] += (real[i] * window[i] * overlapGain).toFloat()
                }
                position += hop
            }
        }
        return out
    }

    /** Learns from the quietest passage and applies in one call — the "Reduce noise" control. */
    public fun reduce(buffer: AudioBuffer): AudioBuffer = process(buffer, learnFromQuietest(buffer))
}
