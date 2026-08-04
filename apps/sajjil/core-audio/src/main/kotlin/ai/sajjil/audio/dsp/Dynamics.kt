package ai.sajjil.audio.dsp

import ai.sajjil.audio.AudioBuffer
import ai.sajjil.audio.dbToLinear
import ai.sajjil.audio.linearToDb
import kotlin.math.abs
import kotlin.math.exp
import kotlin.math.max

/**
 * One-pole envelope follower with separate attack and release time constants.
 *
 * Time constants use the standard `exp(-1 / (tau * fs))` form, so "10 ms attack" means the
 * envelope covers 63% of a step in 10 ms — the same convention hardware compressors use.
 */
class EnvelopeFollower(
    sampleRate: Int,
    attackMs: Double,
    releaseMs: Double,
) {
    private var attackCoefficient = coefficientFor(attackMs, sampleRate)
    private var releaseCoefficient = coefficientFor(releaseMs, sampleRate)
    private var envelope = 0.0

    fun reset() {
        envelope = 0.0
    }

    fun setTimes(attackMs: Double, releaseMs: Double, sampleRate: Int) {
        attackCoefficient = coefficientFor(attackMs, sampleRate)
        releaseCoefficient = coefficientFor(releaseMs, sampleRate)
    }

    fun process(input: Double): Double {
        val target = abs(input)
        val coefficient = if (target > envelope) attackCoefficient else releaseCoefficient
        envelope = target + coefficient * (envelope - target)
        return envelope
    }

    val current: Double get() = envelope

    private companion object {
        fun coefficientFor(timeMs: Double, sampleRate: Int): Double {
            if (timeMs <= 0.0) return 0.0
            return exp(-1.0 / (timeMs / 1000.0 * sampleRate))
        }
    }
}

data class CompressorSettings(
    /** Level above which gain reduction starts, in dBFS. */
    val thresholdDb: Double = -18.0,
    /** N:1. 1.0 is a bypass. */
    val ratio: Double = 3.0,
    val attackMs: Double = 10.0,
    val releaseMs: Double = 120.0,
    /** Width of the soft knee in dB, centred on the threshold. 0 gives a hard knee. */
    val kneeDb: Double = 6.0,
    val makeupGainDb: Double = 0.0,
) {
    companion object {
        val BYPASS = CompressorSettings(ratio = 1.0)
    }
}

/**
 * Feed-forward compressor with a soft knee, operating on the signal's peak envelope.
 *
 * Channels are linked: gain reduction is computed from the loudest channel and applied to all of
 * them, so a stereo image does not wander when one side is louder.
 */
class Compressor(
    private val sampleRate: Int,
    var settings: CompressorSettings = CompressorSettings(),
) {
    private val follower = EnvelopeFollower(sampleRate, settings.attackMs, settings.releaseMs)
    private var lastGainReductionDb = 0.0

    /** Most recent gain reduction, as a positive number of dB. Drives the UI meter. */
    val gainReductionDb: Double get() = lastGainReductionDb

    fun reset() {
        follower.reset()
        lastGainReductionDb = 0.0
    }

    fun process(buffer: AudioBuffer) {
        val s = settings
        if (s.ratio <= 1.0 && s.makeupGainDb == 0.0) return
        follower.setTimes(s.attackMs, s.releaseMs, sampleRate)
        val makeup = dbToLinear(s.makeupGainDb)
        val channels = buffer.channels
        for (i in 0 until buffer.frameCount) {
            var loudest = 0.0
            for (channel in channels) {
                val a = abs(channel[i].toDouble())
                if (a > loudest) loudest = a
            }
            val envelope = follower.process(loudest)
            val gain = gainFor(envelope, s) * makeup
            for (channel in channels) {
                channel[i] = (channel[i] * gain).toFloat()
            }
        }
    }

    private fun gainFor(envelope: Double, s: CompressorSettings): Double {
        val levelDb = linearToDb(envelope)
        val overshoot = levelDb - s.thresholdDb
        val half = s.kneeDb / 2.0
        val reductionDb = when {
            // Below the knee: untouched.
            overshoot <= -half -> 0.0
            // Inside the knee: quadratic interpolation into the ratio, which is what makes a
            // soft knee sound gradual instead of switching on.
            overshoot < half && s.kneeDb > 0.0 -> {
                val x = overshoot + half
                (1.0 / s.ratio - 1.0) * x * x / (2.0 * s.kneeDb)
            }
            // Above the knee: the full ratio applies.
            else -> (1.0 / s.ratio - 1.0) * overshoot
        }
        lastGainReductionDb = -reductionDb
        return dbToLinear(reductionDb)
    }
}

data class LimiterSettings(
    /** Nothing is allowed above this, in dBFS. */
    val ceilingDb: Double = -1.0,
    val lookaheadMs: Double = 5.0,
    val releaseMs: Double = 60.0,
)

/**
 * Look-ahead brick-wall limiter.
 *
 * The delay line holds the signal back by the look-ahead time while the gain computer sees the
 * peak early, so the gain is already down by the time the transient arrives — that is what makes
 * it transparent rather than a clipper. Gain rides down instantly and recovers over [
 * LimiterSettings.releaseMs].
 */
class Limiter(
    private val sampleRate: Int,
    var settings: LimiterSettings = LimiterSettings(),
) {
    private var delayLine: Array<FloatArray> = emptyArray()
    private var delaySamples = 0
    private var writeIndex = 0
    private var currentGain = 1.0

    fun reset() {
        delayLine.forEach { it.fill(0f) }
        writeIndex = 0
        currentGain = 1.0
    }

    fun process(buffer: AudioBuffer) {
        val s = settings
        val ceiling = dbToLinear(s.ceilingDb)
        val lookahead = max(1, (s.lookaheadMs / 1000.0 * sampleRate).toInt())
        ensureDelayLine(buffer.channelCount, lookahead)

        val releaseCoefficient = exp(-1.0 / (max(1.0, s.releaseMs) / 1000.0 * sampleRate))
        val channels = buffer.channels

        for (i in 0 until buffer.frameCount) {
            // Peak of the incoming (not yet delayed) frame — this is the "look ahead".
            var incomingPeak = 0.0
            for (c in channels.indices) {
                val a = abs(channels[c][i].toDouble())
                if (a > incomingPeak) incomingPeak = a
            }

            val requiredGain = if (incomingPeak > ceiling) ceiling / incomingPeak else 1.0
            // Attack is instantaneous by construction; only recovery is smoothed.
            currentGain = if (requiredGain < currentGain) {
                requiredGain
            } else {
                requiredGain + releaseCoefficient * (currentGain - requiredGain)
            }

            for (c in channels.indices) {
                val delayed = delayLine[c][writeIndex]
                delayLine[c][writeIndex] = channels[c][i]
                // Hard safety clamp: floating point drift must never let a sample past the
                // ceiling, because the integer conversion on export would wrap it.
                val limited = delayed * currentGain
                channels[c][i] = limited.coerceIn(-ceiling, ceiling).toFloat()
            }
            writeIndex = (writeIndex + 1) % delaySamples
        }
    }

    private fun ensureDelayLine(channelCount: Int, lookahead: Int) {
        if (delayLine.size != channelCount || delaySamples != lookahead) {
            delaySamples = lookahead
            delayLine = Array(channelCount) { FloatArray(lookahead) }
            writeIndex = 0
            currentGain = 1.0
        }
    }

    /** Samples of latency this limiter introduces; callers align other paths against it. */
    val latencySamples: Int get() = delaySamples
}

data class GateSettings(
    /** Signal below this opens gain reduction, in dBFS. */
    val thresholdDb: Double = -45.0,
    /** How far down the gate pulls, in dB. Gentler than a hard mute and far less obvious. */
    val rangeDb: Double = -18.0,
    val attackMs: Double = 2.0,
    val holdMs: Double = 60.0,
    val releaseMs: Double = 180.0,
    /** Gate re-closes only [hysteresisDb] below the open threshold, preventing chatter. */
    val hysteresisDb: Double = 4.0,
)

/**
 * Downward expander / noise gate with hold and hysteresis.
 *
 * Hold is what stops the gate chattering on the natural decay of a word ending, and hysteresis
 * stops it flickering when the signal hovers at the threshold. Both matter far more for speech
 * than the raw threshold does.
 */
class NoiseGate(
    private val sampleRate: Int,
    var settings: GateSettings = GateSettings(),
) {
    private val follower = EnvelopeFollower(sampleRate, 1.0, 20.0)
    private var gain = 1.0
    private var holdCounter = 0
    private var open = false

    fun reset() {
        follower.reset()
        gain = 1.0
        holdCounter = 0
        open = false
    }

    fun process(buffer: AudioBuffer) {
        val s = settings
        val openThreshold = dbToLinear(s.thresholdDb)
        val closeThreshold = dbToLinear(s.thresholdDb - s.hysteresisDb)
        val floor = dbToLinear(s.rangeDb)
        val holdSamples = (s.holdMs / 1000.0 * sampleRate).toInt()
        val attackCoefficient = exp(-1.0 / (max(0.1, s.attackMs) / 1000.0 * sampleRate))
        val releaseCoefficient = exp(-1.0 / (max(1.0, s.releaseMs) / 1000.0 * sampleRate))
        val channels = buffer.channels

        for (i in 0 until buffer.frameCount) {
            var loudest = 0.0
            for (channel in channels) {
                val a = abs(channel[i].toDouble())
                if (a > loudest) loudest = a
            }
            val envelope = follower.process(loudest)

            if (open) {
                if (envelope < closeThreshold) {
                    if (holdCounter > 0) holdCounter-- else open = false
                } else {
                    holdCounter = holdSamples
                }
            } else if (envelope > openThreshold) {
                open = true
                holdCounter = holdSamples
            }

            val target = if (open) 1.0 else floor
            val coefficient = if (target > gain) attackCoefficient else releaseCoefficient
            gain = target + coefficient * (gain - target)

            for (channel in channels) {
                channel[i] = (channel[i] * gain).toFloat()
            }
        }
    }
}

data class DeEsserSettings(
    /** Centre of the sibilance band. 6–8 kHz suits most voices. */
    val frequencyHz: Double = 6500.0,
    val thresholdDb: Double = -28.0,
    /** Maximum reduction applied to the sibilant band, in dB. */
    val rangeDb: Double = 8.0,
)

/**
 * Split-band de-esser.
 *
 * The sibilant band is isolated with a band-pass, its level drives a fast detector, and the
 * reduction is applied to that band alone before it is summed back with the rest of the signal.
 * Broadband ducking (the naive approach) audibly pumps the whole voice on every "s".
 */
class DeEsser(
    private val sampleRate: Int,
    var settings: DeEsserSettings = DeEsserSettings(),
) {
    private var detectors: Array<Biquad> = emptyArray()
    private var bandSplitters: Array<Biquad> = emptyArray()
    private var followers: Array<EnvelopeFollower> = emptyArray()

    fun reset() {
        detectors.forEach { it.reset() }
        bandSplitters.forEach { it.reset() }
        followers.forEach { it.reset() }
    }

    fun process(buffer: AudioBuffer) {
        val s = settings
        ensureState(buffer.channelCount)
        val bandCoefficients = BiquadDesign.bandPass(s.frequencyHz, sampleRate, q = 2.0)
        val threshold = dbToLinear(s.thresholdDb)
        val maxReduction = dbToLinear(-s.rangeDb)

        for (c in buffer.channels.indices) {
            detectors[c].coefficients = bandCoefficients
            bandSplitters[c].coefficients = bandCoefficients
            val channel = buffer.channels[c]
            val detector = detectors[c]
            val splitter = bandSplitters[c]
            val follower = followers[c]
            for (i in channel.indices) {
                val x = channel[i].toDouble()
                val band = splitter.processSample(x)
                val envelope = follower.process(detector.processSample(x))
                if (envelope > threshold) {
                    val excess = envelope / threshold
                    // Reduction grows with overshoot but never exceeds the configured range.
                    val gain = max(maxReduction, 1.0 / excess)
                    // Subtract the attenuated portion of the band only.
                    channel[i] = (x - band * (1.0 - gain)).toFloat()
                }
            }
        }
    }

    private fun ensureState(channelCount: Int) {
        if (detectors.size == channelCount) return
        detectors = Array(channelCount) { Biquad() }
        bandSplitters = Array(channelCount) { Biquad() }
        followers = Array(channelCount) { EnvelopeFollower(sampleRate, 1.0, 35.0) }
    }
}

/**
 * Stereo width control via mid/side.
 *
 * [width] of 1.0 is untouched, 0.0 collapses to mono, above 1.0 widens. Capped at 2.0 because
 * beyond that the mono sum starts cancelling badly, which is worse on a phone speaker than any
 * width benefit is worth.
 */
object StereoWidener {
    fun process(buffer: AudioBuffer, width: Double) {
        if (buffer.channelCount < 2) return
        val w = width.coerceIn(0.0, 2.0)
        if (abs(w - 1.0) < 1e-9) return
        val left = buffer.channels[0]
        val right = buffer.channels[1]
        for (i in left.indices) {
            val mid = (left[i] + right[i]) * 0.5
            val side = (left[i] - right[i]) * 0.5 * w
            left[i] = (mid + side).toFloat()
            right[i] = (mid - side).toFloat()
        }
    }
}
