package ai.sajjil.audio.waveform

import ai.sajjil.audio.AudioBuffer
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sqrt

/**
 * Per-bucket minimum, maximum and RMS for waveform drawing.
 *
 * Minimum and maximum give the familiar filled envelope; RMS drawn inside it is what makes a
 * waveform readable at a glance, because it tracks perceived loudness rather than stray peaks.
 */
class WaveformPeaks(
    val minima: FloatArray,
    val maxima: FloatArray,
    val rms: FloatArray,
    /** How many source frames each bucket covers. */
    val framesPerBucket: Int,
    val sampleRate: Int,
) {
    val bucketCount: Int get() = minima.size

    fun bucketForFrame(frame: Int): Int =
        (frame / framesPerBucket).coerceIn(0, max(0, bucketCount - 1))

    companion object {
        /** Extracts [targetBuckets] buckets spanning the whole buffer. */
        fun extract(buffer: AudioBuffer, targetBuckets: Int): WaveformPeaks =
            extractRange(buffer, 0, buffer.frameCount, targetBuckets)

        /**
         * Extracts buckets for `[from, until)` only.
         *
         * The editor calls this on every zoom and scroll, so it never walks more of the recording
         * than is actually on screen — that is what keeps a two-hour file scrolling at 60 fps.
         */
        fun extractRange(
            buffer: AudioBuffer,
            from: Int,
            until: Int,
            targetBuckets: Int,
        ): WaveformPeaks {
            require(targetBuckets > 0) { "targetBuckets must be positive" }
            val start = from.coerceIn(0, buffer.frameCount)
            val end = until.coerceIn(start, buffer.frameCount)
            val span = end - start

            if (span == 0) {
                return WaveformPeaks(FloatArray(0), FloatArray(0), FloatArray(0), 1, buffer.sampleRate)
            }

            val framesPerBucket = max(1, span / targetBuckets)
            val bucketCount = (span + framesPerBucket - 1) / framesPerBucket

            val minima = FloatArray(bucketCount)
            val maxima = FloatArray(bucketCount)
            val rms = FloatArray(bucketCount)

            for (b in 0 until bucketCount) {
                val bucketStart = start + b * framesPerBucket
                val bucketEnd = min(bucketStart + framesPerBucket, end)
                var lo = Float.MAX_VALUE
                var hi = -Float.MAX_VALUE
                var sumSquares = 0.0
                var count = 0
                for (channel in buffer.channels) {
                    for (i in bucketStart until bucketEnd) {
                        val v = channel[i]
                        if (v < lo) lo = v
                        if (v > hi) hi = v
                        sumSquares += v.toDouble() * v
                        count++
                    }
                }
                if (count == 0) {
                    minima[b] = 0f
                    maxima[b] = 0f
                    rms[b] = 0f
                } else {
                    minima[b] = lo
                    maxima[b] = hi
                    rms[b] = sqrt(sumSquares / count).toFloat()
                }
            }
            return WaveformPeaks(minima, maxima, rms, framesPerBucket, buffer.sampleRate)
        }
    }
}

/**
 * A fixed-size ring of recent levels for the live recording meter.
 *
 * Recording pushes one value per audio block from the capture thread; the UI reads a snapshot on
 * the main thread. Nothing here allocates after construction, which is what keeps the record
 * screen from stuttering while it draws.
 */
class LiveWaveform(val capacity: Int = 240) {
    private val values = FloatArray(capacity)
    private var writeIndex = 0
    private var filled = 0

    @Synchronized
    fun push(level: Float) {
        values[writeIndex] = level.coerceIn(0f, 1f)
        writeIndex = (writeIndex + 1) % capacity
        if (filled < capacity) filled++
    }

    /**
     * Oldest-to-newest snapshot, safe to hand to the UI.
     *
     * Values are right-aligned and the leading gap is zero-filled, so a recording that has just
     * started draws as a meter growing in from the right rather than a full-width bar.
     */
    @Synchronized
    fun snapshot(into: FloatArray = FloatArray(capacity)): FloatArray {
        into.fill(0f)
        val oldest = writeIndex - filled
        for (i in 0 until filled) {
            val index = ((oldest + i) % capacity + capacity) % capacity
            into[capacity - filled + i] = values[index]
        }
        return into
    }

    @Synchronized
    fun clear() {
        values.fill(0f)
        writeIndex = 0
        filled = 0
    }
}
