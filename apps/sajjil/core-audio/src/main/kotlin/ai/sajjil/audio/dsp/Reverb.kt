package ai.sajjil.audio.dsp

import ai.sajjil.audio.AudioBuffer
import kotlin.math.max
import kotlin.math.pow

data class ReverbSettings(
    /** Wet/dry mix, 0.0 dry to 1.0 fully wet. The UI calls this "Amount". */
    val amount: Double = 0.2,
    /** Room scale, 0.0 small to 1.0 large. The UI calls this "Size". */
    val size: Double = 0.5,
    /** RT60 in seconds. The UI calls this "Decay". */
    val decaySeconds: Double = 1.4,
    /**
     * High-frequency damping, 0.0 bright to 1.0 dark. The UI calls this "Warmth" because that is
     * what it does perceptually — real rooms absorb treble faster than bass.
     */
    val warmth: Double = 0.4,
    /** Delay before the tail begins, in ms. Longer reads as a larger space. */
    val preDelayMs: Double = 20.0,
) {
    companion object {
        val DRY = ReverbSettings(amount = 0.0)
    }
}

/**
 * Feedback delay network reverb: four delay lines cross-coupled through a Householder matrix,
 * each with a one-pole low-pass in the feedback path for frequency-dependent decay.
 *
 * An FDN was chosen over a Schroeder comb/allpass bank because it reaches a dense, smooth tail
 * with far fewer delay lines, which matters on a phone. The four delay lengths are mutually prime
 * so their echo patterns do not line up and produce a metallic ring.
 */
class Reverb(
    private val sampleRate: Int,
    settings: ReverbSettings = ReverbSettings(),
) {
    // Mutually prime lengths, in samples at 44.1 kHz; scaled by size and sample rate at build.
    private val baseDelays = intArrayOf(1153, 1601, 2153, 2833)

    private lateinit var lines: Array<FloatArray>
    private lateinit var writeIndices: IntArray
    private lateinit var damping: DoubleArray
    private lateinit var dampingState: DoubleArray
    private var feedbackGain = 0.0
    // The reverb is fed a mono sum, so a single pre-delay line covers every channel.
    private var preDelayLine = FloatArray(0)
    private var preDelayIndex = 0

    var settings: ReverbSettings = settings
        set(value) {
            field = value
            rebuild()
        }

    init {
        rebuild()
    }

    private fun rebuild() {
        val s = settings
        val rateScale = sampleRate / 44100.0
        // Size scales the delay lengths between roughly a booth and a hall.
        val sizeScale = 0.35 + 1.65 * s.size.coerceIn(0.0, 1.0)
        lines = Array(baseDelays.size) { i ->
            FloatArray(max(16, (baseDelays[i] * rateScale * sizeScale).toInt()))
        }
        writeIndices = IntArray(baseDelays.size)
        dampingState = DoubleArray(baseDelays.size)

        // A one-pole coefficient per line: more warmth means more treble absorbed per pass.
        val dampingCoefficient = (0.05 + 0.75 * s.warmth.coerceIn(0.0, 1.0))
        damping = DoubleArray(baseDelays.size) { dampingCoefficient }

        // Feedback gain that yields the requested RT60 for the mean delay length:
        //   g = 10 ^ (-3 * meanDelaySeconds / RT60)
        val meanDelaySeconds = lines.map { it.size }.average() / sampleRate
        val rt60 = max(0.05, s.decaySeconds)
        feedbackGain = 10.0.pow(-3.0 * meanDelaySeconds / rt60).coerceIn(0.0, 0.98)
    }

    fun reset() {
        lines.forEach { it.fill(0f) }
        writeIndices.fill(0)
        dampingState.fill(0.0)
        preDelayLine.fill(0f)
        preDelayIndex = 0
    }

    fun process(buffer: AudioBuffer) {
        val s = settings
        if (s.amount <= 0.0) return
        val wet = s.amount.coerceIn(0.0, 1.0)
        // Equal-power crossfade: a linear mix dips in perceived level at the midpoint.
        val wetGain = kotlin.math.sin(wet * Math.PI / 2)
        val dryGain = kotlin.math.cos(wet * Math.PI / 2)

        val preDelaySamples = max(1, (s.preDelayMs / 1000.0 * sampleRate).toInt())
        ensurePreDelay(preDelaySamples)

        val lineCount = lines.size
        val outputs = DoubleArray(lineCount)

        for (i in 0 until buffer.frameCount) {
            // Reverb is fed a mono sum; the tail is decorrelated back out across the channels.
            var input = 0.0
            for (channel in buffer.channels) input += channel[i]
            input /= buffer.channelCount

            val delayedInput = preDelayLine[preDelayIndex].toDouble()
            preDelayLine[preDelayIndex] = input.toFloat()
            preDelayIndex = (preDelayIndex + 1) % preDelaySamples

            for (l in 0 until lineCount) {
                outputs[l] = lines[l][writeIndices[l]].toDouble()
            }

            // Householder feedback matrix: y = x - (2/N) * sum(x). Unitary, so it redistributes
            // energy between lines without adding or losing any — the tail stays stable.
            var sum = 0.0
            for (l in 0 until lineCount) sum += outputs[l]
            val scale = 2.0 / lineCount

            var tail = 0.0
            for (l in 0 until lineCount) {
                val mixed = outputs[l] - scale * sum
                // One-pole low-pass in the feedback path.
                dampingState[l] = mixed * (1.0 - damping[l]) + dampingState[l] * damping[l]
                val written = delayedInput + dampingState[l] * feedbackGain
                lines[l][writeIndices[l]] = written.toFloat()
                writeIndices[l] = (writeIndices[l] + 1) % lines[l].size
                tail += outputs[l]
            }
            tail /= lineCount

            for (c in buffer.channels.indices) {
                // Alternate the sign of the tail per channel for a wider, less centred image.
                val sign = if (c % 2 == 0) 1.0 else -1.0
                val dry = buffer.channels[c][i]
                buffer.channels[c][i] = (dry * dryGain + tail * sign * wetGain).toFloat()
            }
        }
    }

    private fun ensurePreDelay(samples: Int) {
        if (preDelayLine.size != samples) {
            preDelayLine = FloatArray(samples)
            preDelayIndex = 0
        }
    }
}
