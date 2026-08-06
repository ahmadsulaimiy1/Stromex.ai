package ai.sautiy.core.analysis

import ai.sautiy.core.audio.AudioBuffer
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sqrt

/**
 * The waveform the user actually sees.
 *
 * A phone cannot draw ten million samples at 60 fps, and it does not need to: at any zoom
 * level a pixel column represents many frames, and what the eye needs from that column is its
 * **extremes** and its **energy**. So SAUTIY reduces audio to per-bucket (min, max, rms)
 * triples once, and every subsequent draw is a cheap read out of the right pyramid level.
 *
 * Min *and* max are both kept rather than a single magnitude, because a waveform drawn from
 * magnitude alone is symmetric and lies about asymmetric material — which speech, with its
 * plosives and its DC-offset microphones, very much is.
 */
public class PeakLevel(
    public val framesPerBucket: Int,
    public val minima: FloatArray,
    public val maxima: FloatArray,
    public val rms: FloatArray,
) {
    public val bucketCount: Int get() = minima.size

    init {
        require(framesPerBucket > 0)
        require(maxima.size == minima.size && rms.size == minima.size) {
            "Peak arrays must be the same length"
        }
    }

    /** Decimates by [factor] to produce the next, coarser level. O(n), and exact. */
    public fun decimate(factor: Int): PeakLevel {
        require(factor > 1)
        val outCount = (bucketCount + factor - 1) / factor
        val outMin = FloatArray(outCount)
        val outMax = FloatArray(outCount)
        val outRms = FloatArray(outCount)

        for (i in 0 until outCount) {
            val start = i * factor
            val end = min(start + factor, bucketCount)
            var lo = Float.MAX_VALUE
            var hi = -Float.MAX_VALUE
            var energy = 0.0
            for (j in start until end) {
                if (minima[j] < lo) lo = minima[j]
                if (maxima[j] > hi) hi = maxima[j]
                energy += rms[j].toDouble() * rms[j]
            }
            val span = (end - start).coerceAtLeast(1)
            outMin[i] = if (lo == Float.MAX_VALUE) 0f else lo
            outMax[i] = if (hi == -Float.MAX_VALUE) 0f else hi
            outRms[i] = sqrt(energy / span).toFloat()
        }
        return PeakLevel(framesPerBucket * factor, outMin, outMax, outRms)
    }
}

/**
 * A mip-map of peak levels, so that any zoom from "the whole two-hour lecture" to "forty
 * milliseconds around this click" is served by a level whose bucket size is within a factor of
 * four of what the screen needs.
 */
public class WaveformPyramid(
    public val levels: List<PeakLevel>,
    public val sampleRate: Int,
    public val totalFrames: Long,
) {
    init {
        require(levels.isNotEmpty()) { "A pyramid needs a base level" }
    }

    public val base: PeakLevel get() = levels.first()

    /** The coarsest level still fine enough to fill [pixelWidth] columns over [frameSpan]. */
    public fun levelFor(frameSpan: Long, pixelWidth: Int): PeakLevel {
        if (pixelWidth <= 0 || frameSpan <= 0) return levels.last()
        val wanted = frameSpan.toDouble() / pixelWidth
        // The finest level that is still no finer than what we need, so we never read more
        // buckets than there are pixels.
        return levels.lastOrNull { it.framesPerBucket <= wanted } ?: base
    }

    /**
     * Produces exactly [pixelWidth] columns covering frames `[startFrame, endFrame)`, ready to
     * be drawn without further arithmetic in the draw loop.
     *
     * Ranges beyond the end of the audio yield silent columns rather than throwing, because
     * during recording the view legitimately runs ahead of the material.
     */
    public fun columns(startFrame: Long, endFrame: Long, pixelWidth: Int): WaveformColumns {
        require(pixelWidth > 0)
        val span = (endFrame - startFrame).coerceAtLeast(1)
        val level = levelFor(span, pixelWidth)

        val minima = FloatArray(pixelWidth)
        val maxima = FloatArray(pixelWidth)
        val rms = FloatArray(pixelWidth)

        for (x in 0 until pixelWidth) {
            val from = startFrame + span * x / pixelWidth
            val to = startFrame + span * (x + 1) / pixelWidth
            val firstBucket = (from / level.framesPerBucket).toInt()
            val lastBucket = ((to - 1) / level.framesPerBucket).toInt()

            var lo = 0f
            var hi = 0f
            var energy = 0.0
            var counted = 0
            for (b in max(0, firstBucket)..min(lastBucket, level.bucketCount - 1)) {
                if (counted == 0) {
                    lo = level.minima[b]
                    hi = level.maxima[b]
                } else {
                    if (level.minima[b] < lo) lo = level.minima[b]
                    if (level.maxima[b] > hi) hi = level.maxima[b]
                }
                energy += level.rms[b].toDouble() * level.rms[b]
                counted++
            }
            minima[x] = lo
            maxima[x] = hi
            rms[x] = if (counted == 0) 0f else sqrt(energy / counted).toFloat()
        }
        return WaveformColumns(minima, maxima, rms, startFrame, endFrame)
    }
}

/** One screenful of waveform, one entry per pixel column. */
public data class WaveformColumns(
    val minima: FloatArray,
    val maxima: FloatArray,
    val rms: FloatArray,
    val startFrame: Long,
    val endFrame: Long,
) {
    val width: Int get() = minima.size

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is WaveformColumns) return false
        return startFrame == other.startFrame &&
            endFrame == other.endFrame &&
            minima.contentEquals(other.minima) &&
            maxima.contentEquals(other.maxima) &&
            rms.contentEquals(other.rms)
    }

    override fun hashCode(): Int {
        var result = minima.contentHashCode()
        result = 31 * result + maxima.contentHashCode()
        result = 31 * result + rms.contentHashCode()
        result = 31 * result + startFrame.hashCode()
        result = 31 * result + endFrame.hashCode()
        return result
    }
}

/**
 * Builds peaks **incrementally**.
 *
 * This is why the live waveform can draw itself while recording and why opening a two-hour
 * file does not block: audio is fed in as it arrives, complete buckets are emitted
 * immediately, and the partial bucket at the tail is carried forward. Nothing waits for the
 * whole file to exist (chapter 1.3.4).
 */
public class PeakBuilder(
    public val framesPerBucket: Int = DEFAULT_BASE_BUCKET,
) {
    private val minima = ArrayList<Float>(1024)
    private val maxima = ArrayList<Float>(1024)
    private val rms = ArrayList<Float>(1024)

    private var partialMin = Float.MAX_VALUE
    private var partialMax = -Float.MAX_VALUE
    private var partialEnergy = 0.0
    private var partialFrames = 0

    public var framesConsumed: Long = 0
        private set

    /** Feeds a block. Returns the number of *newly completed* buckets. */
    public fun append(buffer: AudioBuffer): Int {
        val before = minima.size
        val channelCount = buffer.channelCount
        val frames = buffer.frameCount

        for (i in 0 until frames) {
            // Peaks are taken across channels: a transient on either side is a transient the
            // user must be able to see.
            var lo = Float.MAX_VALUE
            var hi = -Float.MAX_VALUE
            var energy = 0.0
            for (c in 0 until channelCount) {
                val sample = buffer.channels[c][i]
                if (sample < lo) lo = sample
                if (sample > hi) hi = sample
                energy += sample.toDouble() * sample
            }
            energy /= channelCount

            if (lo < partialMin) partialMin = lo
            if (hi > partialMax) partialMax = hi
            partialEnergy += energy
            partialFrames++

            if (partialFrames == framesPerBucket) {
                closeBucket()
            }
        }
        framesConsumed += frames
        return minima.size - before
    }

    private fun closeBucket() {
        val span = partialFrames.coerceAtLeast(1)
        minima.add(if (partialMin == Float.MAX_VALUE) 0f else partialMin)
        maxima.add(if (partialMax == -Float.MAX_VALUE) 0f else partialMax)
        rms.add(sqrt(partialEnergy / span).toFloat())
        partialMin = Float.MAX_VALUE
        partialMax = -Float.MAX_VALUE
        partialEnergy = 0.0
        partialFrames = 0
    }

    /**
     * Snapshots the current state, including the in-progress bucket, without disturbing the
     * builder. The live waveform reads this every frame while recording continues.
     */
    public fun snapshot(): PeakLevel {
        val extra = if (partialFrames > 0) 1 else 0
        val count = minima.size + extra
        val outMin = FloatArray(count)
        val outMax = FloatArray(count)
        val outRms = FloatArray(count)
        for (i in minima.indices) {
            outMin[i] = minima[i]
            outMax[i] = maxima[i]
            outRms[i] = rms[i]
        }
        if (extra == 1) {
            val last = count - 1
            outMin[last] = if (partialMin == Float.MAX_VALUE) 0f else partialMin
            outMax[last] = if (partialMax == -Float.MAX_VALUE) 0f else partialMax
            outRms[last] = sqrt(partialEnergy / partialFrames).toFloat()
        }
        return PeakLevel(framesPerBucket, outMin, outMax, outRms)
    }

    /** Closes any partial bucket and returns the finished base level. */
    public fun finish(): PeakLevel {
        if (partialFrames > 0) closeBucket()
        return PeakLevel(framesPerBucket, minima.toFloatArray(), maxima.toFloatArray(), rms.toFloatArray())
    }

    public companion object {
        /**
         * 256 frames per base bucket — about 5.3 ms at 48 kHz. Fine enough that a click is
         * visible at maximum zoom, coarse enough that an hour of audio reduces to roughly
         * 675 000 buckets, or 8 MB of peaks: comfortably held in memory and quick to build.
         */
        public const val DEFAULT_BASE_BUCKET: Int = 256
    }
}

/** Peak generation entry points. */
public object Waveform {

    /** Pyramid ratios: each level is four times coarser than the one below it. */
    public const val PYRAMID_FACTOR: Int = 4

    /** How many levels to build. Five levels span 256 to 65 536 frames per bucket. */
    public const val PYRAMID_LEVELS: Int = 5

    /** Builds a full pyramid from a complete buffer. */
    public fun pyramid(
        buffer: AudioBuffer,
        baseBucket: Int = PeakBuilder.DEFAULT_BASE_BUCKET,
    ): WaveformPyramid {
        val builder = PeakBuilder(baseBucket)
        builder.append(buffer)
        return pyramid(builder.finish(), buffer.sampleRate, buffer.frameCount.toLong())
    }

    /** Builds the coarser levels above an existing base level. */
    public fun pyramid(base: PeakLevel, sampleRate: Int, totalFrames: Long): WaveformPyramid {
        val levels = ArrayList<PeakLevel>(PYRAMID_LEVELS)
        levels.add(base)
        var current = base
        repeat(PYRAMID_LEVELS - 1) {
            if (current.bucketCount <= 1) return@repeat
            current = current.decimate(PYRAMID_FACTOR)
            levels.add(current)
        }
        return WaveformPyramid(levels, sampleRate, totalFrames)
    }

    /**
     * The instantaneous level for the recording meter, as dBFS peak and dBFS RMS.
     *
     * Peak is what protects against clipping; RMS is what correlates with loudness. A meter
     * that shows only one of them is lying by omission, so SAUTIY shows both (chapter 1.4
     * principle 5).
     */
    public fun instantLevel(buffer: AudioBuffer): InstantLevel {
        var peak = 0f
        var energy = 0.0
        var count = 0
        for (channel in buffer.channels) {
            for (sample in channel) {
                val magnitude = abs(sample)
                if (magnitude > peak) peak = magnitude
                energy += sample.toDouble() * sample
                count++
            }
        }
        val rmsLinear = if (count == 0) 0.0 else sqrt(energy / count)
        return InstantLevel(peakLinear = peak, rmsLinear = rmsLinear)
    }
}

/** One meter reading. */
public data class InstantLevel(val peakLinear: Float, val rmsLinear: Double) {
    public val peakDb: Double get() = ai.sautiy.core.audio.Decibels.fromLinear(peakLinear)
    public val rmsDb: Double get() = ai.sautiy.core.audio.Decibels.fromLinear(rmsLinear)
    public val isClipping: Boolean get() = peakLinear >= AudioBuffer.CLIP_THRESHOLD
}
