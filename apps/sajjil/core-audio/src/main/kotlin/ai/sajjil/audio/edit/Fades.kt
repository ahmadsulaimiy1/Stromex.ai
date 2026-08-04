package ai.sajjil.audio.edit

import ai.sajjil.audio.AudioBuffer
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.min
import kotlin.math.sin

/** Shape of a fade. Curves differ audibly; the default is chosen per use, not globally. */
enum class FadeShape {
    /** Constant change in amplitude. Sounds like it slows down at the quiet end. */
    LINEAR,

    /**
     * Constant change in perceived loudness. The right default for fading music or ambience in
     * and out, because human hearing is logarithmic.
     */
    EQUAL_POWER,

    /** Slow start, fast finish. Good for fading *out* of speech without clipping the last word. */
    EXPONENTIAL,

    /** Smooth at both ends. The right choice for very short de-click fades at edit boundaries. */
    SMOOTH,
}

object Fades {

    /** Fades in over the first [frames] frames, in place. */
    fun fadeIn(buffer: AudioBuffer, frames: Int, shape: FadeShape = FadeShape.EQUAL_POWER) {
        val n = min(frames, buffer.frameCount)
        if (n <= 0) return
        for (channel in buffer.channels) {
            for (i in 0 until n) {
                channel[i] = (channel[i] * gain(i.toDouble() / n, shape)).toFloat()
            }
        }
    }

    /** Fades out over the last [frames] frames, in place. */
    fun fadeOut(buffer: AudioBuffer, frames: Int, shape: FadeShape = FadeShape.EQUAL_POWER) {
        val n = min(frames, buffer.frameCount)
        if (n <= 0) return
        val start = buffer.frameCount - n
        for (channel in buffer.channels) {
            for (i in 0 until n) {
                channel[start + i] = (channel[start + i] * gain(1.0 - i.toDouble() / n, shape)).toFloat()
            }
        }
    }

    /**
     * A very short symmetric fade around an edit point.
     *
     * Every cut, split and paste in the editor runs through this. Without it, joining two
     * unrelated waveforms produces a step discontinuity, which is heard as a click — the single
     * most common giveaway of amateur editing.
     */
    fun declickAt(buffer: AudioBuffer, frame: Int, halfWidthFrames: Int = 32) {
        val from = (frame - halfWidthFrames).coerceAtLeast(0)
        val until = (frame + halfWidthFrames).coerceAtMost(buffer.frameCount)
        val span = until - from
        if (span <= 1) return
        for (channel in buffer.channels) {
            for (i in from until until) {
                // Dip to zero at the join and back up, over a few milliseconds.
                val t = (i - from).toDouble() / span
                val depth = 1.0 - sin(PI * t)
                channel[i] = (channel[i] * depth).toFloat()
            }
        }
    }

    /** Crossfades [b] over the tail of [a], returning a new buffer. Used when joining takes. */
    fun crossfade(a: AudioBuffer, b: AudioBuffer, frames: Int): AudioBuffer {
        require(a.sampleRate == b.sampleRate && a.channelCount == b.channelCount) {
            "crossfade needs matching sample rate and channel count"
        }
        val n = min(frames, min(a.frameCount, b.frameCount))
        if (n <= 0) return AudioBuffer.concat(listOf(a, b))

        val total = a.frameCount + b.frameCount - n
        val channels = Array(a.channelCount) { FloatArray(total) }
        for (c in 0 until a.channelCount) {
            val out = channels[c]
            a.channels[c].copyInto(out, 0, 0, a.frameCount - n)
            val overlapStart = a.frameCount - n
            for (i in 0 until n) {
                val t = i.toDouble() / n
                val fadeOut = cos(t * PI / 2)
                val fadeIn = sin(t * PI / 2)
                out[overlapStart + i] =
                    (a.channels[c][overlapStart + i] * fadeOut + b.channels[c][i] * fadeIn).toFloat()
            }
            b.channels[c].copyInto(out, a.frameCount, n, b.frameCount)
        }
        return AudioBuffer(a.sampleRate, channels)
    }

    private fun gain(t: Double, shape: FadeShape): Double {
        val x = t.coerceIn(0.0, 1.0)
        return when (shape) {
            FadeShape.LINEAR -> x
            FadeShape.EQUAL_POWER -> sin(x * PI / 2)
            FadeShape.EXPONENTIAL -> x * x
            FadeShape.SMOOTH -> x * x * (3 - 2 * x)
        }
    }
}
