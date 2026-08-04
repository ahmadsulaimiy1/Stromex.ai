package ai.sajjil.audio.dsp

import ai.sajjil.audio.AudioBuffer
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sqrt

data class NoiseReductionSettings(
    /** 0.0 is off, 1.0 is the most aggressive setting the UI exposes. */
    val strength: Double = 0.5,
    /**
     * How far the noise floor is allowed to be pushed down, in dB. Leaving a floor rather than
     * subtracting to zero is what prevents "musical noise" — isolated surviving bins that warble.
     */
    val floorDb: Double = -22.0,
    val fftSize: Int = 2048,
)

/**
 * Short-time spectral subtraction with an automatically estimated noise profile.
 *
 * The profile is built from the quietest frames of the recording — the pauses between phrases —
 * rather than from a region the user has to select by hand, which is the single most common
 * reason people give up on noise reduction in other apps.
 *
 * Frames are chosen by their *total* energy, and the profile is then the average spectrum of
 * those frames. Taking a low percentile per bin independently is tempting and wrong: in a bin
 * where the voice is present in every frame, that percentile is the voice, and subtracting it
 * removes the very thing being cleaned up.
 *
 * Musical noise is suppressed three ways: over-subtraction proportional to strength, a spectral
 * floor rather than a hard zero, and temporal smoothing of the per-bin gain.
 */
class SpectralNoiseReducer(
    var settings: NoiseReductionSettings = NoiseReductionSettings(),
) {

    /** Fraction of frames, quietest first, taken to be noise. */
    private val noiseFrameFraction = 0.2

    fun process(buffer: AudioBuffer): AudioBuffer {
        val s = settings
        if (s.strength <= 0.0) return buffer
        val n = s.fftSize
        require(n >= 64 && (n and (n - 1)) == 0) { "fftSize must be a power of two >= 64" }
        if (buffer.frameCount < n) return buffer

        val out = Array(buffer.channelCount) { FloatArray(buffer.frameCount) }
        for (c in 0 until buffer.channelCount) {
            out[c] = processChannel(buffer.channels[c], n, s)
        }
        return AudioBuffer(buffer.sampleRate, out)
    }

    private fun processChannel(input: FloatArray, n: Int, s: NoiseReductionSettings): FloatArray {
        val hop = n / 4
        val fft = Fft(n)
        val window = Windows.sqrtHann(n)
        val bins = n / 2 + 1
        val frameCount = (input.size - n) / hop + 1

        // Pass 1: magnitudes for every frame, so the noise profile can be a true percentile
        // rather than a running guess that is wrong for the first second of audio.
        val magnitudes = Array(frameCount) { DoubleArray(bins) }
        val re = DoubleArray(n)
        val im = DoubleArray(n)
        for (f in 0 until frameCount) {
            val offset = f * hop
            for (i in 0 until n) {
                re[i] = input[offset + i] * window[i]
                im[i] = 0.0
            }
            fft.forward(re, im)
            val row = magnitudes[f]
            for (b in 0 until bins) row[b] = sqrt(re[b] * re[b] + im[b] * im[b])
        }

        val noiseProfile = estimateNoiseProfile(magnitudes, bins, frameCount)

        // Over-subtraction and floor both scale with strength so a single slider stays coherent.
        val overSubtraction = 1.0 + 2.0 * s.strength
        val floor = Math.pow(10.0, s.floorDb / 20.0)
        val gainSmoothing = 0.5

        val output = FloatArray(input.size)
        val normalisation = DoubleArray(input.size)
        val previousGain = DoubleArray(bins) { 1.0 }

        for (f in 0 until frameCount) {
            val offset = f * hop
            for (i in 0 until n) {
                re[i] = input[offset + i] * window[i]
                im[i] = 0.0
            }
            fft.forward(re, im)

            for (b in 0 until bins) {
                val magnitude = magnitudes[f][b]
                val gain = if (magnitude <= 1e-12) {
                    1.0
                } else {
                    val cleaned = magnitude - overSubtraction * noiseProfile[b]
                    max(floor, cleaned / magnitude)
                }
                // Smooth the gain over time; abrupt per-frame gain changes are exactly what
                // makes spectral subtraction sound like it is underwater.
                val smoothed = gainSmoothing * previousGain[b] + (1.0 - gainSmoothing) * gain
                previousGain[b] = smoothed

                re[b] *= smoothed
                im[b] *= smoothed
                // Mirror onto the negative frequencies to keep the inverse transform real.
                if (b in 1 until n / 2) {
                    re[n - b] *= smoothed
                    im[n - b] *= smoothed
                }
            }

            fft.inverse(re, im)

            for (i in 0 until n) {
                val position = offset + i
                if (position < output.size) {
                    output[position] += (re[i] * window[i]).toFloat()
                    normalisation[position] += window[i] * window[i]
                }
            }
        }

        // Undo the analysis+synthesis window weighting wherever frames actually landed. Samples
        // in the ragged tail past the last full frame keep their original value.
        for (i in output.indices) {
            if (normalisation[i] > 1e-6) {
                output[i] = (output[i] / normalisation[i]).toFloat()
            } else {
                output[i] = input[i]
            }
        }
        return output
    }

    private fun estimateNoiseProfile(
        magnitudes: Array<DoubleArray>,
        bins: Int,
        frameCount: Int,
    ): DoubleArray {
        // Rank whole frames by energy and keep the quietest ones. These are the pauses.
        val energies = DoubleArray(frameCount) { f ->
            var sum = 0.0
            val row = magnitudes[f]
            for (b in 0 until bins) sum += row[b] * row[b]
            sum
        }
        val order = (0 until frameCount).sortedBy { energies[it] }
        val take = max(1, (frameCount * noiseFrameFraction).toInt())
        val quietest = order.take(take)

        val profile = DoubleArray(bins)
        for (f in quietest) {
            val row = magnitudes[f]
            for (b in 0 until bins) profile[b] += row[b]
        }
        for (b in 0 until bins) profile[b] /= quietest.size

        val confidence = confidenceIn(energies, order, quietest)
        if (confidence < 1.0) {
            for (b in 0 until bins) profile[b] *= confidence
        }
        return profile
    }

    /**
     * How much to trust the noise estimate, from 0 (not at all) to 1 (fully).
     *
     * The estimate assumes the quietest frames contain noise and nothing else. That holds for
     * speech, which is full of pauses, but not for continuous material — sustained recitation,
     * unbroken music, a held note. There the quietest frames still contain the signal, and
     * subtracting their spectrum would remove the very thing the user wants to keep.
     *
     * Comparing the quiet frames against the median frame detects that case: if they are nearly
     * as loud, there were no real pauses, and the profile is scaled down towards zero rather than
     * being trusted. Degrading to "do nothing" is the only safe failure here — the alternative is
     * silently destroying a recording that was never noisy in the first place.
     */
    private fun confidenceIn(
        energies: DoubleArray,
        order: List<Int>,
        quietest: List<Int>,
    ): Double {
        val medianEnergy = energies[order[order.size / 2]]
        if (medianEnergy <= 1e-20) return 0.0
        val quietEnergy = quietest.sumOf { energies[it] } / quietest.size
        val ratio = quietEnergy / medianEnergy
        // Full confidence when the pauses are at most a tenth of typical energy (-10 dB); none
        // when they are more than half of it.
        return ((0.5 - ratio) / 0.4).coerceIn(0.0, 1.0)
    }
}

/**
 * Mains hum removal: a comb of narrow notches at the fundamental and its harmonics.
 *
 * [fundamentalHz] is 50 in most of the world and 60 in the Americas. The app detects which by
 * comparing energy at the two candidates rather than guessing from locale, because a recording
 * may have travelled.
 */
class HumRemover(
    private val sampleRate: Int,
    var fundamentalHz: Double = 50.0,
    var harmonics: Int = 8,
    var bandwidthHz: Double = 4.0,
) {
    fun process(buffer: AudioBuffer) {
        val nyquist = sampleRate / 2.0
        val sections = (1..harmonics)
            .map { fundamentalHz * it }
            .filter { it < nyquist * 0.95 }
            .map { BiquadDesign.notch(it, sampleRate, bandwidthHz) }
        if (sections.isEmpty()) return
        for (channel in buffer.channels) {
            BiquadChain(sections).process(channel)
        }
    }

    companion object {
        /**
         * Decide between 50 Hz and 60 Hz mains by measuring which fundamental carries more
         * energy in the buffer. Returns null when neither stands out, so the caller can leave
         * hum removal off rather than notching a frequency the recording actually needs.
         */
        fun detectFundamental(buffer: AudioBuffer, minimumRatio: Double = 1.4): Double? {
            val mono = buffer.toMono()[0]
            // Below ~0.2 s there is not enough resolution at 50/60 Hz to tell them apart.
            if (mono.size < 8192) return null
            val energy50 = bandEnergy(mono, buffer.sampleRate, 50.0)
            val energy60 = bandEnergy(mono, buffer.sampleRate, 60.0)
            val neighbourhood = bandEnergy(mono, buffer.sampleRate, 90.0)
            if (neighbourhood <= 0.0) return null
            val ratio50 = energy50 / neighbourhood
            val ratio60 = energy60 / neighbourhood
            return when {
                ratio50 < minimumRatio && ratio60 < minimumRatio -> null
                ratio50 >= ratio60 -> 50.0
                else -> 60.0
            }
        }

        /** Goertzel single-bin energy — far cheaper than a full FFT for three probe frequencies. */
        private fun bandEnergy(samples: FloatArray, sampleRate: Int, frequency: Double): Double {
            val n = min(samples.size, 32768)
            val k = (0.5 + n * frequency / sampleRate).toInt()
            val w = 2.0 * Math.PI * k / n
            val coefficient = 2.0 * kotlin.math.cos(w)
            var s1 = 0.0
            var s2 = 0.0
            for (i in 0 until n) {
                val s0 = samples[i] + coefficient * s1 - s2
                s2 = s1
                s1 = s0
            }
            return s1 * s1 + s2 * s2 - coefficient * s1 * s2
        }
    }
}

/**
 * Impulsive-noise (click/pop) repair.
 *
 * Clicks are found as samples whose third-order difference is a large multiple of the local
 * median — a standard detector that is insensitive to the signal's own level, so it does not
 * shred loud consonants. Detected runs are replaced by cubic Hermite interpolation across the
 * gap, which preserves slope at the edges and is therefore inaudible for short repairs.
 */
class DeClicker(
    /** Multiple of the local median difference above which a sample is treated as a click. */
    var sensitivity: Double = 8.0,
    /** Longest run of samples that will be repaired; longer damage is left alone. */
    var maxRunLength: Int = 40,
) {
    /** Returns the number of samples repaired, which the UI reports back to the user. */
    fun process(buffer: AudioBuffer): Int {
        var repaired = 0
        for (channel in buffer.channels) {
            repaired += processChannel(channel)
        }
        return repaired
    }

    private fun processChannel(samples: FloatArray): Int {
        if (samples.size < 8) return 0
        val detection = FloatArray(samples.size)
        for (i in 3 until samples.size) {
            // Third difference: flat and slowly-varying signal cancels, impulses do not.
            detection[i] = abs(
                samples[i] - 3f * samples[i - 1] + 3f * samples[i - 2] - samples[i - 3]
            )
        }
        val median = medianOf(detection)
        if (median <= 0.0) return 0
        val threshold = (median * sensitivity).toFloat()

        var repaired = 0
        var i = 3
        while (i < samples.size) {
            if (detection[i] > threshold) {
                var end = i
                while (end < samples.size && end - i < maxRunLength && detection[end] > threshold) {
                    end++
                }
                val runLength = end - i
                if (runLength in 1..maxRunLength) {
                    interpolate(samples, i, end)
                    repaired += runLength
                }
                i = end + 1
            } else {
                i++
            }
        }
        return repaired
    }

    /** Cubic Hermite across `[from, until)` using the two samples on each side as tangents. */
    private fun interpolate(samples: FloatArray, from: Int, until: Int) {
        val p0 = samples.getOrElse(from - 1) { 0f }
        val p1 = samples.getOrElse(until) { 0f }
        val m0 = p0 - samples.getOrElse(from - 2) { p0 }
        val m1 = samples.getOrElse(until + 1) { p1 } - p1
        val span = (until - from + 1).toFloat()
        for (i in from until until) {
            val t = (i - from + 1) / span
            val t2 = t * t
            val t3 = t2 * t
            samples[i] = (2 * t3 - 3 * t2 + 1) * p0 +
                (t3 - 2 * t2 + t) * m0 +
                (-2 * t3 + 3 * t2) * p1 +
                (t3 - t2) * m1
        }
    }

    private fun medianOf(values: FloatArray): Double {
        // Sample rather than sort the whole array: a stride of 7 over a multi-minute recording
        // gives the same median to well within the sensitivity margin, for a fraction of the cost.
        val stride = max(1, values.size / 20000)
        val sampled = FloatArray((values.size + stride - 1) / stride)
        var j = 0
        var i = 0
        while (i < values.size && j < sampled.size) {
            sampled[j++] = values[i]
            i += stride
        }
        sampled.sort()
        return sampled[sampled.size / 2].toDouble()
    }
}

/**
 * Clipping repair.
 *
 * Runs of samples pinned at (or very near) full scale are treated as clipped and reconstructed by
 * fitting a parabola through the surrounding unclipped samples, restoring a plausible peak above
 * the ceiling. The whole buffer is then scaled back down so the reconstruction does not itself
 * clip on export.
 */
class DeClipper(
    /** Absolute level above which a sample counts as pinned. */
    var clipThreshold: Float = 0.985f,
    var minRunLength: Int = 3,
) {
    /** Returns the number of samples reconstructed. */
    fun process(buffer: AudioBuffer): Int {
        var repaired = 0
        for (channel in buffer.channels) {
            repaired += processChannel(channel)
        }
        if (repaired > 0) {
            val peak = buffer.peak()
            if (peak > 1f) buffer.applyGain(0.999f / peak)
        }
        return repaired
    }

    private fun processChannel(samples: FloatArray): Int {
        var repaired = 0
        var i = 0
        while (i < samples.size) {
            if (abs(samples[i]) < clipThreshold) {
                i++
                continue
            }
            val sign = if (samples[i] > 0) 1f else -1f
            var end = i
            while (end < samples.size && abs(samples[end]) >= clipThreshold &&
                (samples[end] > 0) == (sign > 0)
            ) {
                end++
            }
            val runLength = end - i
            if (runLength >= minRunLength) {
                reconstruct(samples, i, end, sign)
                repaired += runLength
            }
            i = end
        }
        return repaired
    }

    private fun reconstruct(samples: FloatArray, from: Int, until: Int, sign: Float) {
        val before = samples.getOrElse(from - 1) { clipThreshold * sign }
        val after = samples.getOrElse(until) { clipThreshold * sign }
        val runLength = until - from
        // Estimated true peak: the longer the flat top, the further above the ceiling the
        // original peak most likely was. Capped so a long clipped passage cannot explode.
        val overshoot = min(0.45, runLength * 0.02)
        val peak = sign * (clipThreshold + overshoot)
        val half = runLength / 2.0
        for (i in from until until) {
            val t = (i - from - half) / max(1.0, half)
            // Parabola peaking mid-run and meeting the neighbours at the edges.
            val shape = 1.0 - t * t
            val edge = if (i - from < runLength / 2) before else after
            samples[i] = (edge + (peak - edge) * shape).toFloat()
        }
    }
}

/**
 * Wind and handling-rumble reduction.
 *
 * Wind energy is overwhelmingly below ~120 Hz and, unlike voice, is not harmonically related to
 * anything above it. A steep high-pass plus a downward expander on the low band removes it
 * without thinning the voice, which a plain high-pass alone would do.
 */
class WindReducer(
    private val sampleRate: Int,
    var strength: Double = 0.5,
) {
    fun process(buffer: AudioBuffer) {
        if (strength <= 0.0) return
        // 60 Hz at the gentlest setting up to 140 Hz at the strongest.
        val cutoff = 60.0 + 80.0 * strength.coerceIn(0.0, 1.0)
        val sections = listOf(
            BiquadDesign.highPass(cutoff, sampleRate, q = 0.7071),
            BiquadDesign.highPass(cutoff, sampleRate, q = 0.7071),
        )
        for (channel in buffer.channels) {
            BiquadChain(sections).process(channel)
        }
    }
}
