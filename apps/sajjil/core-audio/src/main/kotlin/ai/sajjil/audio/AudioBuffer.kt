package ai.sajjil.audio

import kotlin.math.abs
import kotlin.math.max
import kotlin.math.sqrt

/**
 * Non-interleaved 32-bit float PCM, one array per channel, samples normalised to [-1, 1].
 *
 * Non-interleaved is the right default here because almost every process in this engine is
 * per-channel (filters, gates, gain), and the few that are not (stereo width, M/S) are cheaper to
 * express against separate channel arrays than against a strided interleaved one.
 */
class AudioBuffer(
    val sampleRate: Int,
    val channels: Array<FloatArray>,
) {
    init {
        require(sampleRate > 0) { "sampleRate must be positive, was $sampleRate" }
        require(channels.isNotEmpty()) { "an AudioBuffer needs at least one channel" }
        val n = channels[0].size
        require(channels.all { it.size == n }) { "all channels must have the same length" }
    }

    val channelCount: Int get() = channels.size

    /** Frames, i.e. samples per channel. */
    val frameCount: Int get() = channels[0].size

    val durationSeconds: Double get() = frameCount.toDouble() / sampleRate

    operator fun get(channel: Int): FloatArray = channels[channel]

    fun isMono(): Boolean = channelCount == 1

    fun copy(): AudioBuffer = AudioBuffer(sampleRate, Array(channelCount) { channels[it].copyOf() })

    /** A new buffer holding frames `[from, until)`. */
    fun slice(from: Int, until: Int): AudioBuffer {
        require(from in 0..frameCount) { "from=$from out of range 0..$frameCount" }
        require(until in from..frameCount) { "until=$until out of range $from..$frameCount" }
        return AudioBuffer(sampleRate, Array(channelCount) { channels[it].copyOfRange(from, until) })
    }

    /** Peak absolute sample across all channels, in linear amplitude. */
    fun peak(): Float {
        var peak = 0f
        for (channel in channels) {
            for (sample in channel) {
                val a = abs(sample)
                if (a > peak) peak = a
            }
        }
        return peak
    }

    /** Root-mean-square across all channels, in linear amplitude. */
    fun rms(): Double {
        if (frameCount == 0) return 0.0
        var sum = 0.0
        for (channel in channels) {
            for (sample in channel) sum += sample.toDouble() * sample
        }
        return sqrt(sum / (frameCount.toDouble() * channelCount))
    }

    fun applyGain(linear: Float) {
        for (channel in channels) {
            for (i in channel.indices) channel[i] *= linear
        }
    }

    /** Downmix to a single channel, averaging. Returns `this` when already mono. */
    fun toMono(): AudioBuffer {
        if (isMono()) return this
        val out = FloatArray(frameCount)
        for (channel in channels) {
            for (i in out.indices) out[i] += channel[i]
        }
        val scale = 1f / channelCount
        for (i in out.indices) out[i] *= scale
        return AudioBuffer(sampleRate, arrayOf(out))
    }

    /** Duplicate mono to [target] channels. Returns `this` when the count already matches. */
    fun toChannelCount(target: Int): AudioBuffer {
        require(target > 0) { "target channel count must be positive" }
        if (target == channelCount) return this
        val mono = toMono()[0]
        return AudioBuffer(sampleRate, Array(target) { mono.copyOf() })
    }

    companion object {
        fun silence(sampleRate: Int, channelCount: Int, frames: Int): AudioBuffer =
            AudioBuffer(sampleRate, Array(channelCount) { FloatArray(frames) })

        /** Concatenate buffers that share a sample rate and channel count. */
        fun concat(parts: List<AudioBuffer>): AudioBuffer {
            require(parts.isNotEmpty()) { "cannot concatenate an empty list" }
            val sampleRate = parts[0].sampleRate
            val channelCount = parts[0].channelCount
            require(parts.all { it.sampleRate == sampleRate && it.channelCount == channelCount }) {
                "all parts must share a sample rate and channel count"
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
            return AudioBuffer(sampleRate, channels)
        }
    }
}

/** Linear amplitude to decibels. Floors at [floorDb] so silence does not produce -Infinity. */
fun linearToDb(linear: Double, floorDb: Double = -120.0): Double {
    if (linear <= 0.0) return floorDb
    return max(floorDb, 20.0 * kotlin.math.log10(linear))
}

/** Decibels to linear amplitude. */
fun dbToLinear(db: Double): Double = Math.pow(10.0, db / 20.0)

internal fun Float.clampToUnit(): Float = when {
    this > 1f -> 1f
    this < -1f -> -1f
    else -> this
}
