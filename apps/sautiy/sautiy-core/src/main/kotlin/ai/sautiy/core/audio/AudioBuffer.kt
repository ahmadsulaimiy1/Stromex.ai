package ai.sautiy.core.audio

import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

/**
 * A block of audio in SAUTIY's working representation: 32-bit float, **planar** (one
 * [FloatArray] per channel), nominally in −1.0..+1.0.
 *
 * Planar rather than interleaved because every DSP stage in chapter 10 operates per channel;
 * interleaving would force a stride multiply into the inner loop of every filter in the
 * product. The conversion to and from interleaved happens once, at the device boundary.
 *
 * Float rather than fixed point because intermediate stages routinely exceed full scale — a
 * boost before a limiter, the sum of two layers — and clamping at every stage instead of at
 * the output is exactly how a chain comes to sound crushed. Samples are permitted to leave
 * −1..+1 inside the chain and are brought back only at the point of encoding.
 */
public class AudioBuffer(
    public val channels: Array<FloatArray>,
    public val sampleRate: Int,
) {
    init {
        require(channels.isNotEmpty()) { "An audio buffer needs at least one channel" }
        require(channels.all { it.size == channels[0].size }) { "All channels must be the same length" }
        require(sampleRate > 0) { "Sample rate must be positive" }
    }

    public val channelCount: Int get() = channels.size
    public val frameCount: Int get() = channels[0].size
    public val format: AudioFormat get() = AudioFormat(sampleRate, channelCount)
    public val durationSeconds: Double get() = frameCount.toDouble() / sampleRate
    public val isEmpty: Boolean get() = frameCount == 0

    public operator fun get(channel: Int): FloatArray = channels[channel]

    /** A deep copy. Every edit in chapter 9 is non-destructive, which needs this to be cheap and correct. */
    public fun copy(): AudioBuffer = AudioBuffer(Array(channelCount) { channels[it].copyOf() }, sampleRate)

    /** Frames `[start, end)` as a new buffer. */
    public fun slice(startFrame: Int, endFrame: Int): AudioBuffer {
        require(startFrame in 0..frameCount) { "start $startFrame out of 0..$frameCount" }
        require(endFrame in startFrame..frameCount) { "end $endFrame out of $startFrame..$frameCount" }
        return AudioBuffer(Array(channelCount) { channels[it].copyOfRange(startFrame, endFrame) }, sampleRate)
    }

    /** Highest absolute sample across all channels — the true peak of the block, not an average. */
    public fun peak(): Float {
        var peak = 0f
        for (channel in channels) {
            for (sample in channel) {
                val magnitude = abs(sample)
                if (magnitude > peak) peak = magnitude
            }
        }
        return peak
    }

    /** Root-mean-square across all channels. */
    public fun rms(): Double {
        if (frameCount == 0) return 0.0
        var sum = 0.0
        for (channel in channels) {
            for (sample in channel) sum += sample.toDouble() * sample
        }
        return kotlin.math.sqrt(sum / (frameCount.toDouble() * channelCount))
    }

    /**
     * True if any sample reached or passed digital full scale. Reported to the user as
     * clipping, honestly, rather than hidden (chapter 1.4 principle 5).
     */
    public fun hasClipping(threshold: Float = CLIP_THRESHOLD): Boolean = peak() >= threshold

    /** Number of individual samples at or beyond full scale. */
    public fun clippedSampleCount(threshold: Float = CLIP_THRESHOLD): Int {
        var count = 0
        for (channel in channels) {
            for (sample in channel) if (abs(sample) >= threshold) count++
        }
        return count
    }

    /** Applies a linear gain in place. */
    public fun applyGain(gain: Float): AudioBuffer {
        if (gain == 1f) return this
        for (channel in channels) {
            for (i in channel.indices) channel[i] *= gain
        }
        return this
    }

    /** Hard-clamps to −1..+1. Called once, at the encoding boundary, and nowhere else. */
    public fun clampInPlace(): AudioBuffer {
        for (channel in channels) {
            for (i in channel.indices) channel[i] = channel[i].coerceIn(-1f, 1f)
        }
        return this
    }

    /**
     * Mixes [other] into this buffer at [atFrame], growing nothing — samples past the end are
     * discarded. Used for layer summing, where the mix length is fixed by the timeline.
     */
    public fun mixInPlace(other: AudioBuffer, atFrame: Int = 0, gain: Float = 1f): AudioBuffer {
        require(other.sampleRate == sampleRate) { "Cannot mix ${other.sampleRate} Hz into $sampleRate Hz" }
        val copyable = min(other.frameCount, frameCount - atFrame)
        if (copyable <= 0) return this
        for (c in 0 until channelCount) {
            // A mono layer feeds every channel; a stereo layer maps channel-for-channel.
            val source = other.channels[min(c, other.channelCount - 1)]
            val destination = channels[c]
            for (i in 0 until copyable) destination[atFrame + i] += source[i] * gain
        }
        return this
    }

    /** Downmix to mono by averaging. Used for analysis, never for the user's audio. */
    public fun toMono(): AudioBuffer {
        if (channelCount == 1) return this
        val mono = FloatArray(frameCount)
        for (i in 0 until frameCount) {
            var sum = 0f
            for (c in 0 until channelCount) sum += channels[c][i]
            mono[i] = sum / channelCount
        }
        return AudioBuffer(arrayOf(mono), sampleRate)
    }

    /** Duplicates mono to stereo, or passes stereo through. */
    public fun toStereo(): AudioBuffer {
        if (channelCount == 2) return this
        val source = channels[0]
        return AudioBuffer(arrayOf(source.copyOf(), source.copyOf()), sampleRate)
    }

    /** Interleaves into a single array, for handing to a platform audio device. */
    public fun interleave(): FloatArray {
        if (channelCount == 1) return channels[0].copyOf()
        val out = FloatArray(frameCount * channelCount)
        for (c in 0 until channelCount) {
            val channel = channels[c]
            var w = c
            for (i in 0 until frameCount) {
                out[w] = channel[i]
                w += channelCount
            }
        }
        return out
    }

    override fun toString(): String =
        "AudioBuffer(${channelCount}ch, $frameCount frames, ${sampleRate}Hz, ${"%.3f".format(durationSeconds)}s)"

    public companion object {
        /**
         * Full scale. A float sample at exactly 1.0 maps to the largest representable integer
         * and is, for every practical purpose, clipped — so SAUTIY counts it as such rather
         * than waiting for something impossible to exceed it.
         */
        public const val CLIP_THRESHOLD: Float = 0.99997f

        public fun silence(channelCount: Int, frameCount: Int, sampleRate: Int): AudioBuffer =
            AudioBuffer(Array(channelCount) { FloatArray(frameCount) }, sampleRate)

        public fun mono(samples: FloatArray, sampleRate: Int): AudioBuffer =
            AudioBuffer(arrayOf(samples), sampleRate)

        /** Splits an interleaved block into planar channels. */
        public fun fromInterleaved(interleaved: FloatArray, channelCount: Int, sampleRate: Int): AudioBuffer {
            require(channelCount > 0)
            require(interleaved.size % channelCount == 0) {
                "Interleaved length ${interleaved.size} is not a whole number of $channelCount-channel frames"
            }
            val frames = interleaved.size / channelCount
            val channels = Array(channelCount) { FloatArray(frames) }
            for (c in 0 until channelCount) {
                val channel = channels[c]
                var r = c
                for (i in 0 until frames) {
                    channel[i] = interleaved[r]
                    r += channelCount
                }
            }
            return AudioBuffer(channels, sampleRate)
        }

        /** Concatenates buffers of matching shape. */
        public fun concat(parts: List<AudioBuffer>): AudioBuffer {
            require(parts.isNotEmpty()) { "Nothing to concatenate" }
            val rate = parts[0].sampleRate
            val channelCount = parts[0].channelCount
            require(parts.all { it.sampleRate == rate && it.channelCount == channelCount }) {
                "All parts must share sample rate and channel count"
            }
            val total = parts.sumOf { it.frameCount }
            val channels = Array(channelCount) { FloatArray(total) }
            var offset = 0
            for (part in parts) {
                for (c in 0 until channelCount) {
                    part.channels[c].copyInto(channels[c], offset)
                }
                offset += part.frameCount
            }
            return AudioBuffer(channels, rate)
        }
    }
}

/** Decibel conversions, shared by every meter, gauge and readout in the product. */
public object Decibels {
    /**
     * The floor SAUTIY reports instead of −∞. −120 dBFS is below the noise floor of any
     * microphone ever fitted to a phone, so nothing real is hidden by it, and a finite number
     * is far easier to draw, animate and read aloud than negative infinity.
     */
    public const val FLOOR_DB: Double = -120.0

    public fun fromLinear(linear: Double): Double =
        if (linear <= 0.0) FLOOR_DB else max(FLOOR_DB, 20.0 * kotlin.math.log10(linear))

    public fun fromLinear(linear: Float): Double = fromLinear(linear.toDouble())

    public fun toLinear(db: Double): Double = Math.pow(10.0, db / 20.0)

    public fun toLinearFloat(db: Double): Float = toLinear(db).toFloat()

    /** Formats for display: one decimal place, explicit sign, and a real floor. */
    public fun format(db: Double): String = when {
        db <= FLOOR_DB -> "−∞ dB"
        db >= 0 -> "+%.1f dB".format(db)
        // U+2212 MINUS SIGN, not a hyphen: it aligns with the tabular figures of chapter 2.4.2.
        else -> "−%.1f dB".format(-db)
    }
}
