package ai.sautiy.core.dsp

import ai.sautiy.core.audio.AudioBuffer

/**
 * A Schroeder–Moorer reverberator: eight parallel damped comb filters into four series
 * all-pass filters, per channel.
 *
 * This topology is chosen because it is *controllable*. A convolution reverb would sound
 * better and would need an impulse response per space, megabytes each, chosen by a user who
 * has no way to audition them on a phone speaker. This gives one honest room with two
 * understandable controls — how big, and how bright — and runs in a few operations per sample.
 *
 * Chapter 10 offers it as **Space**: a lecture recorded in a dead room can be given back some
 * air, and a recitation can be placed in a room without pretending to be in a cathedral.
 */
public class Reverb(
    /** 0..1. Small is a booth, large is a hall. */
    public val size: Double = 0.5,
    /** 0..1. How quickly the high frequencies die away. Higher damping is a softer room. */
    public val damping: Double = 0.5,
    /** 0..1 wet/dry mix. */
    public val mix: Double = 0.25,
    /** 0..1 stereo width of the reverb tail. Ignored for mono material. */
    public val width: Double = 1.0,
) {
    init {
        require(size in 0.0..1.0)
        require(damping in 0.0..1.0)
        require(mix in 0.0..1.0)
    }

    // Freeverb's tunings, in frames at 44.1 kHz. Mutually prime so their echo trains do not
    // line up into a ringing pitch — the single most important property of the numbers.
    private val combTunings = intArrayOf(1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617)
    private val allPassTunings = intArrayOf(556, 441, 341, 225)
    private val stereoSpread = 23

    private class Comb(size: Int, private val feedback: Double, private val damping: Double) {
        private val buffer = FloatArray(size)
        private var index = 0
        private var store = 0.0

        fun process(input: Double): Double {
            val output = buffer[index].toDouble()
            store = output * (1.0 - damping) + store * damping
            buffer[index] = (input + store * feedback).toFloat()
            if (++index >= buffer.size) index = 0
            return output
        }
    }

    private class AllPass(size: Int, private val feedback: Double) {
        private val buffer = FloatArray(size)
        private var index = 0

        fun process(input: Double): Double {
            val buffered = buffer[index].toDouble()
            val output = -input + buffered
            buffer[index] = (input + buffered * feedback).toFloat()
            if (++index >= buffer.size) index = 0
            return output
        }
    }

    /** Applies reverb in place. */
    public fun process(buffer: AudioBuffer): AudioBuffer {
        val rateScale = buffer.sampleRate / 44_100.0
        val roomSize = 0.70 + size * 0.28
        val dampingAmount = damping * 0.4
        val wet = mix
        val dry = 1.0 - mix

        for (c in 0 until buffer.channelCount) {
            val spread = if (c == 0) 0 else (stereoSpread * width).toInt()
            val combs = combTunings.map {
                Comb(((it + spread) * rateScale).toInt().coerceAtLeast(1), roomSize, dampingAmount)
            }
            val allPasses = allPassTunings.map {
                AllPass(((it + spread) * rateScale).toInt().coerceAtLeast(1), 0.5)
            }

            val channel = buffer.channels[c]
            for (i in channel.indices) {
                val input = channel[i].toDouble()
                // Scaled down before the combs: eight parallel feedback loops sum to a great
                // deal of gain, and letting that reach full scale before the mix is what makes
                // naive reverbs distort on anything loud.
                val fed = input * 0.015

                var accumulated = 0.0
                for (comb in combs) accumulated += comb.process(fed)
                for (allPass in allPasses) accumulated = allPass.process(accumulated)

                channel[i] = (input * dry + accumulated * wet).toFloat()
            }
        }
        return buffer
    }

    /** Approximate RT60 in seconds, so the panel can print a number rather than a vague dial. */
    public val decaySeconds: Double
        get() {
            val roomSize = 0.70 + size * 0.28
            val averageDelay = combTunings.average() / 44_100.0
            // Time for the feedback loop to fall 60 dB.
            return averageDelay * (-60.0 / (20.0 * kotlin.math.log10(roomSize)))
        }
}

/**
 * A simple delay line with feedback — "Echo" in the panel.
 *
 * Distinct from [Reverb] because they are different intentions: echo is a repetition the
 * listener can count, reverb is a space they cannot. Presenting them as one control with a
 * slider between them, as some products do, makes both harder to use.
 */
public class Echo(
    public val delayMs: Double = 250.0,
    public val feedback: Double = 0.35,
    public val mix: Double = 0.25,
    /** Rolls off the repeats, so an echo decays the way a real one does. */
    public val dampingHz: Double = 6_000.0,
) {
    init {
        require(delayMs > 0.0)
        require(feedback in 0.0..0.95) { "Feedback at or above 1.0 never decays" }
        require(mix in 0.0..1.0)
    }

    public fun process(buffer: AudioBuffer): AudioBuffer {
        val delayFrames = (delayMs * buffer.sampleRate / 1000.0).toInt().coerceAtLeast(1)
        for (channel in buffer.channels) {
            val line = FloatArray(delayFrames)
            var index = 0
            val damper = Biquad.lowPass(dampingHz, buffer.sampleRate)

            for (i in channel.indices) {
                val delayed = line[index].toDouble()
                val damped = damper.processSample(delayed)
                line[index] = (channel[i] + damped * feedback).toFloat()
                channel[i] = (channel[i] * (1.0 - mix) + delayed * mix).toFloat()
                if (++index >= delayFrames) index = 0
            }
        }
        return buffer
    }
}
