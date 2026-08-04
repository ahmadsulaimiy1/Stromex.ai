package ai.sautiy.core.dsp

import ai.sautiy.core.audio.AudioBuffer
import kotlin.math.pow
import kotlin.math.sqrt
import kotlinx.serialization.Serializable

/**
 * The space a voice is heard in.
 *
 * Three things separate this from the reverb most recorders ship.
 *
 * **It is specified in seconds, not in a dial position.** The comb feedback is derived from the
 * requested RT60 and each comb's own delay length, so every comb decays at the same rate and
 * "1.8 seconds" is a measurement rather than a label. A reverb whose decay changes when you
 * move the size control — as the naive Freeverb formulation does, because size *is* the
 * feedback there — cannot be described honestly to a user.
 *
 * **It has a pre-delay and early reflections.** They are what the ear actually uses to judge
 * distance and room dimension. A tail with no reflections in front of it sounds like an effect;
 * a tail with them sounds like a room, which is why a 0.15 mix here reads as "recorded in a
 * studio" where the same mix without them reads as "reverb was added".
 *
 * **It is streaming.** All state — pre-delay ring, reflection taps, combs, all-passes, damping
 * and the wet tone filters — lives in the instance and survives across calls, so processing a
 * file in 1 024-frame blocks gives bit-identical output to processing it in one. That is not a
 * refinement: a reverb that rebuilds its delay lines per block restarts the tail at every block
 * boundary, which is a click twenty-five times a second, and it is precisely why live preview
 * could not be built on the previous engine.
 */
public class Ambience(
    public val settings: AmbienceSettings,
    public val sampleRate: Int,
    public val channelCount: Int,
) {
    init {
        require(sampleRate > 0)
        require(channelCount in 1..2) { "SAUTIY processes mono and stereo" }
    }

    // Freeverb's comb tunings in frames at 44.1 kHz. Mutually prime, so their echo trains never
    // line up into a ringing pitch — the only property of these particular numbers that matters.
    private val combTunings = intArrayOf(1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617)
    private val allPassTunings = intArrayOf(556, 441, 341, 225)

    /**
     * Early-reflection taps in milliseconds at full room size, with their gains. Irregular and
     * mutually non-harmonic: an evenly spaced set of reflections is a comb filter, and a comb
     * filter on a voice is the metallic sound of a cheap reverb.
     */
    private val reflectionTapsMs = doubleArrayOf(8.3, 13.7, 19.1, 24.9, 31.3, 38.7, 44.1, 52.9)
    private val reflectionGains = doubleArrayOf(0.84, -0.72, 0.63, -0.55, 0.47, -0.40, 0.33, -0.27)

    private val sizeScale = 0.45 + settings.roomSize * 1.05
    private val rateScale = sampleRate / 44_100.0

    /** Feedback per comb, derived from RT60 so every comb decays at the same rate. */
    private fun feedbackFor(delayFrames: Int): Double {
        val delaySeconds = delayFrames.toDouble() / sampleRate
        // 60 dB of decay over decaySeconds: g^(t/d) = 10^(-3), so g = 10^(-3d/t).
        val g = 10.0.pow(-3.0 * delaySeconds / settings.decaySeconds)
        // Never at or above unity: a feedback loop that does not decay never stops.
        return g.coerceIn(0.0, 0.98)
    }

    private class Delay(size: Int) {
        private val buffer = FloatArray(size.coerceAtLeast(1))
        private var index = 0

        fun tick(input: Double): Double {
            val output = buffer[index].toDouble()
            buffer[index] = input.toFloat()
            if (++index >= buffer.size) index = 0
            return output
        }

        /**
         * The sample written [delayFrames] frames ago. `tick` has already advanced the index
         * past the slot it wrote, so the most recent sample is at `index − 1`, not at `index`;
         * a tap that forgets that is one frame early at every reflection.
         */
        fun tap(delayFrames: Int): Double {
            val position = ((index - 1 - delayFrames) % buffer.size + buffer.size) % buffer.size
            return buffer[position].toDouble()
        }

        fun clear() {
            buffer.fill(0f)
            index = 0
        }
    }

    private class Comb(size: Int, private val feedback: Double, private val damping: Double) {
        private val buffer = FloatArray(size.coerceAtLeast(1))
        private var index = 0
        private var store = 0.0

        fun process(input: Double): Double {
            val output = buffer[index].toDouble()
            // One-pole low-pass inside the loop. Its DC gain is 1, so the low-frequency decay
            // is exactly the requested RT60 while the highs die sooner — which is what a real
            // room does, and what "warmth" means here.
            store = output * (1.0 - damping) + store * damping
            buffer[index] = (input + store * feedback).toFloat()
            if (++index >= buffer.size) index = 0
            return output
        }

        fun clear() {
            buffer.fill(0f)
            index = 0
            store = 0.0
        }
    }

    private class AllPass(size: Int, private val feedback: Double) {
        private val buffer = FloatArray(size.coerceAtLeast(1))
        private var index = 0

        fun process(input: Double): Double {
            val buffered = buffer[index].toDouble()
            val output = -input + buffered
            buffer[index] = (input + buffered * feedback).toFloat()
            if (++index >= buffer.size) index = 0
            return output
        }

        fun clear() {
            buffer.fill(0f)
            index = 0
        }
    }

    // --- Per-channel state, built once and kept ---------------------------------------------

    private val preDelayFrames =
        (settings.preDelayMs * sampleRate / 1000.0).toInt().coerceAtLeast(1)

    private val preDelays = Array(channelCount) { Delay(preDelayFrames) }

    /** The reflection tap line must be long enough to hold the latest tap. */
    private val reflectionLine = Array(channelCount) { channel ->
        val longest = reflectionTapsMs.max() * sizeScale * (1.0 + channel * 0.13)
        Delay((longest * sampleRate / 1000.0).toInt() + 2)
    }

    private val reflectionOffsets = Array(channelCount) { channel ->
        IntArray(reflectionTapsMs.size) { tap ->
            // The second channel's reflections arrive at different times from the first. That
            // difference *is* the stereo image of the room; identical taps in both ears sound
            // like a room the width of a pencil.
            val spread = 1.0 + channel * 0.13 * settings.width
            val ms = reflectionTapsMs[tap] * sizeScale * spread
            (ms * sampleRate / 1000.0).toInt().coerceAtLeast(1)
        }
    }

    private val damping = settings.warmth.coerceIn(0.0, 1.0) * 0.55

    private val combs = Array(channelCount) { channel ->
        // 23 frames of stereo spread, as Freeverb uses, scaled by the width control.
        val spread = if (channel == 0) 0 else (23 * settings.width).toInt()
        Array(combTunings.size) { i ->
            val size = ((combTunings[i] + spread) * rateScale * sizeScale).toInt().coerceAtLeast(1)
            Comb(size, feedbackFor(size), damping)
        }
    }

    private val allPasses = Array(channelCount) { channel ->
        val spread = if (channel == 0) 0 else (23 * settings.width).toInt()
        Array(allPassTunings.size) { i ->
            val size = ((allPassTunings[i] + spread) * rateScale * sizeScale).toInt().coerceAtLeast(1)
            AllPass(size, 0.5)
        }
    }

    /** Tone on the wet path only, so brightening the room never brightens the voice. */
    private val wetTone = Array(channelCount) {
        Biquad.highShelf(6_000.0, sampleRate, (settings.brightness - 0.5) * 12.0)
    }

    /**
     * Input scaling for the comb bank.
     *
     * Eight decorrelated combs each with steady-state gain `1/(1−g)` sum in power, so the bank's
     * amplitude gain is roughly `sqrt(8)/(1−g)`. Dividing it out keeps a two-second hall and a
     * quarter-second booth at comparable wet levels — without this, decay time doubles as a
     * volume control and no preset can be compared with another by ear.
     */
    private val wetNormalise: Double = run {
        val meanFeedback = combTunings.map {
            feedbackFor(((it * rateScale * sizeScale).toInt().coerceAtLeast(1)))
        }.average()
        (1.0 - meanFeedback) / sqrt(combTunings.size.toDouble())
    }

    private val reflectionLevel = settings.earlyReflections
    private val effectiveWet = settings.amount * settings.wetDryMix
    private val effectiveDry = 1.0 - settings.amount * settings.wetDryMix

    /** Clears the tail. Call when playback jumps, so the old room does not follow the cursor. */
    public fun reset() {
        preDelays.forEach { it.clear() }
        reflectionLine.forEach { it.clear() }
        combs.forEach { bank -> bank.forEach { it.clear() } }
        allPasses.forEach { bank -> bank.forEach { it.clear() } }
        wetTone.forEach { it.reset() }
    }

    /**
     * Processes one block in place. State persists, so consecutive blocks join seamlessly.
     *
     * The buffer's channel count must match the one this instance was built for; a mismatch is
     * a programming error, not a condition to paper over.
     */
    public fun process(buffer: AudioBuffer): AudioBuffer {
        require(buffer.channelCount == channelCount) {
            "This Ambience was built for $channelCount channels, got ${buffer.channelCount}"
        }
        if (effectiveWet <= 0.0) return buffer

        val frames = buffer.frameCount
        val wet = Array(channelCount) { DoubleArray(frames) }

        for (c in 0 until channelCount) {
            val channel = buffer.channels[c]
            val preDelay = preDelays[c]
            val line = reflectionLine[c]
            val offsets = reflectionOffsets[c]
            val combBank = combs[c]
            val allPassBank = allPasses[c]
            val tone = wetTone[c]

            for (i in 0 until frames) {
                val input = channel[i].toDouble()

                // Pre-delay feeds the room only. The dry voice is never delayed, so no amount
                // of pre-delay can put the speaker out of time with the picture.
                val delayed = if (settings.preDelayMs > 0.0) preDelay.tick(input) else input

                line.tick(delayed)
                var early = 0.0
                if (reflectionLevel > 0.0) {
                    for (t in offsets.indices) early += line.tap(offsets[t]) * reflectionGains[t]
                    early *= reflectionLevel * 0.35
                }

                var tail = 0.0
                val fed = delayed * wetNormalise
                for (comb in combBank) tail += comb.process(fed)
                for (allPass in allPassBank) tail = allPass.process(tail)

                wet[c][i] = tone.processSample(early + tail)
            }
        }

        // Stereo width is applied to the wet signal after the fact, so one control spans the
        // whole range from a mono room to a fully decorrelated one without rebuilding anything.
        if (channelCount == 2) {
            val direct = 0.5 * (1.0 + settings.width)
            val crossed = 0.5 * (1.0 - settings.width)
            for (i in 0 until frames) {
                val l = wet[0][i]
                val r = wet[1][i]
                wet[0][i] = direct * l + crossed * r
                wet[1][i] = direct * r + crossed * l
            }
        }

        for (c in 0 until channelCount) {
            val channel = buffer.channels[c]
            for (i in 0 until frames) {
                channel[i] = (channel[i] * effectiveDry + wet[c][i] * effectiveWet).toFloat()
            }
        }
        return buffer
    }
}

/**
 * The ambience controls, as one serialisable value.
 *
 * Every field is a quantity a person can picture. `roomSize`, `width`, `earlyReflections`,
 * `warmth`, `brightness`, `amount` and `wetDryMix` are 0..1 because they describe proportions;
 * `decaySeconds` and `preDelayMs` are in real units because they describe time, and rounding
 * those into a 0..1 dial is how products end up unable to tell a user what their reverb is
 * doing.
 *
 * [amount] and [wetDryMix] are deliberately separate. `wetDryMix` is the preset's character —
 * how much room this *kind* of space has. `amount` is the one knob on the panel that makes the
 * whole effect stronger or weaker without changing that character. The wet level applied is
 * their product.
 */
@Serializable
public data class AmbienceSettings(
    /** Master strength of the whole ambience stage. 0 is a complete bypass. */
    val amount: Double = 1.0,
    /** Dimensions of the room: scales both the reflection times and the tail's delay lines. */
    val roomSize: Double = 0.5,
    /** 0 is a room in the middle of your head, 1 is a room you can turn your head inside. */
    val width: Double = 1.0,
    /** Level of the early reflections, which carry the sense of distance and dimension. */
    val earlyReflections: Double = 0.5,
    /** RT60: how long the tail takes to fall 60 dB. */
    val decaySeconds: Double = 1.0,
    /** Gap before the room answers. A larger gap reads as a larger room and keeps words clear. */
    val preDelayMs: Double = 20.0,
    /** How fast the high frequencies die inside the tail. Higher is a softer, darker room. */
    val warmth: Double = 0.5,
    /** Tone of the wet signal only. 0.5 is flat, below darkens, above opens the top. */
    val brightness: Double = 0.5,
    /** The preset's balance of room to voice. */
    val wetDryMix: Double = 0.15,
) {
    init {
        require(amount in 0.0..1.0) { "Amount is a proportion" }
        require(roomSize in 0.0..1.0) { "Room size is a proportion" }
        require(width in 0.0..1.0) { "Width is a proportion" }
        require(earlyReflections in 0.0..1.0) { "Early reflections is a proportion" }
        require(decaySeconds in 0.05..20.0) { "Decay must be between 0.05 s and 20 s" }
        require(preDelayMs in 0.0..250.0) { "Pre-delay must be between 0 ms and 250 ms" }
        require(warmth in 0.0..1.0) { "Warmth is a proportion" }
        require(brightness in 0.0..1.0) { "Brightness is a proportion" }
        require(wetDryMix in 0.0..1.0) { "Wet/dry mix is a proportion" }
    }

    /** True when this stage would change nothing, so a panel can say "no room" honestly. */
    public val isBypassed: Boolean get() = amount <= 0.0 || wetDryMix <= 0.0

    public fun build(sampleRate: Int, channelCount: Int): Ambience =
        Ambience(this, sampleRate, channelCount)

    public companion object {
        /** No room at all — the voice exactly as captured. */
        public val NONE: AmbienceSettings = AmbienceSettings(amount = 0.0, wetDryMix = 0.0)
    }
}
