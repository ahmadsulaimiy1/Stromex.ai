package ai.sajjil.audio.edit

import ai.sajjil.audio.AudioBuffer
import ai.sajjil.audio.dbToLinear
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.sqrt

/** A half-open frame range `[from, until)`. */
data class FrameRange(val from: Int, val until: Int) {
    val length: Int get() = until - from

    init {
        require(from >= 0 && until >= from) { "invalid range $from..$until" }
    }
}

data class SilenceSettings(
    /** Below this level counts as silence. */
    val thresholdDb: Double = -45.0,
    /** Stretches shorter than this are left alone — they are the natural rhythm of speech. */
    val minimumSilenceMs: Double = 700.0,
    /**
     * Silence is shortened to this rather than removed outright. Removing pauses entirely makes
     * speech sound frantic and unnatural; leaving a beat keeps it human.
     */
    val keepMs: Double = 250.0,
    /** Fade applied at each join, in ms, so shortening never introduces a click. */
    val edgeFadeMs: Double = 8.0,
)

/**
 * Finds and shortens silence.
 *
 * Detection runs on a 20 ms RMS envelope rather than raw samples: a single quiet sample inside a
 * word is not silence, and peak-based detection would constantly find it.
 */
class SilenceDetector(private val sampleRate: Int) {

    private val windowMs = 20.0

    /** Ranges considered silent under [settings]. */
    fun detect(buffer: AudioBuffer, settings: SilenceSettings = SilenceSettings()): List<FrameRange> {
        val windowSamples = max(1, (windowMs / 1000.0 * sampleRate).toInt())
        val threshold = dbToLinear(settings.thresholdDb)
        val minimumSilence = (settings.minimumSilenceMs / 1000.0 * sampleRate).toInt()

        val ranges = ArrayList<FrameRange>()
        var silenceStart = -1
        var offset = 0
        while (offset < buffer.frameCount) {
            val until = minOf(offset + windowSamples, buffer.frameCount)
            val quiet = rmsOf(buffer, offset, until) < threshold
            if (quiet) {
                if (silenceStart < 0) silenceStart = offset
            } else if (silenceStart >= 0) {
                if (offset - silenceStart >= minimumSilence) ranges += FrameRange(silenceStart, offset)
                silenceStart = -1
            }
            offset = until
        }
        if (silenceStart >= 0 && buffer.frameCount - silenceStart >= minimumSilence) {
            ranges += FrameRange(silenceStart, buffer.frameCount)
        }
        return ranges
    }

    /**
     * Returns a new buffer with long silences shortened to [SilenceSettings.keepMs].
     *
     * The original is not modified, so the editor can offer this as a preview the user can reject.
     */
    fun removeSilence(
        buffer: AudioBuffer,
        settings: SilenceSettings = SilenceSettings(),
    ): AudioBuffer {
        val ranges = detect(buffer, settings)
        if (ranges.isEmpty()) return buffer.copy()

        val keepSamples = (settings.keepMs / 1000.0 * sampleRate).toInt()
        val parts = ArrayList<AudioBuffer>()
        var cursor = 0
        for (range in ranges) {
            if (range.from > cursor) parts += buffer.slice(cursor, range.from)
            val keep = minOf(keepSamples, range.length)
            if (keep > 0) parts += buffer.slice(range.from, range.from + keep)
            cursor = range.until
        }
        if (cursor < buffer.frameCount) parts += buffer.slice(cursor, buffer.frameCount)
        if (parts.isEmpty()) return AudioBuffer.silence(buffer.sampleRate, buffer.channelCount, 0)

        val result = AudioBuffer.concat(parts)
        // Soften every join so the shortening cannot be heard as a click.
        val fadeFrames = (settings.edgeFadeMs / 1000.0 * sampleRate).toInt().coerceAtLeast(1)
        var joinAt = 0
        for (i in 0 until parts.size - 1) {
            joinAt += parts[i].frameCount
            Fades.declickAt(result, joinAt, fadeFrames)
        }
        return result
    }

    /** Trims leading and trailing silence only, which is what most recordings actually need. */
    fun trimEnds(buffer: AudioBuffer, thresholdDb: Double = -50.0, paddingMs: Double = 120.0): AudioBuffer {
        val threshold = dbToLinear(thresholdDb)
        val padding = (paddingMs / 1000.0 * sampleRate).toInt()

        var start = 0
        while (start < buffer.frameCount && loudestAt(buffer, start) < threshold) start++
        if (start >= buffer.frameCount) return AudioBuffer.silence(buffer.sampleRate, buffer.channelCount, 0)

        var end = buffer.frameCount - 1
        while (end > start && loudestAt(buffer, end) < threshold) end--

        val from = (start - padding).coerceAtLeast(0)
        val until = (end + 1 + padding).coerceAtMost(buffer.frameCount)
        return buffer.slice(from, until)
    }

    private fun loudestAt(buffer: AudioBuffer, frame: Int): Double {
        var peak = 0.0
        for (channel in buffer.channels) {
            val a = abs(channel[frame].toDouble())
            if (a > peak) peak = a
        }
        return peak
    }

    private fun rmsOf(buffer: AudioBuffer, from: Int, until: Int): Double {
        if (until <= from) return 0.0
        var sum = 0.0
        for (channel in buffer.channels) {
            for (i in from until until) {
                val v = channel[i].toDouble()
                sum += v * v
            }
        }
        return sqrt(sum / ((until - from) * buffer.channelCount))
    }
}
