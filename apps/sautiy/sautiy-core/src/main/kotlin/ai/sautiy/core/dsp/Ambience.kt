package ai.sautiy.core.dsp

import ai.sautiy.core.audio.AudioBuffer
import kotlin.math.abs
import kotlin.math.pow
import kotlin.math.sin
import kotlin.math.sqrt
import kotlinx.serialization.Serializable

/**
 * The space a voice is heard in.
 *
 * ## What makes a mobile reverb sound artificial, and what is done about it here
 *
 * **Static comb delays ring.** A fixed-length feedback comb has resonant peaks every `rate/length`
 * Hz, and eight of them sum into a metallic, pitched tail — the sound that makes people say a
 * recording has "reverb on it" rather than "was recorded in a room". Real rooms do not do this,
 * because air moves and surfaces are not perfectly parallel. Every comb here is **modulated**: its
 * read position wanders by a fraction of a millisecond on a slow, mutually detuned LFO, which
 * smears those peaks into a continuous response. This is the single largest difference between a
 * tail that sounds like a room and one that sounds like an effect.
 *
 * **Thin echo density sounds grainy.** A handful of reflections per second is heard as separate
 * events. [AmbienceSettings.diffusion] drives a chain of nested all-pass sections that multiply
 * each reflection into many, so the tail arrives as texture rather than as ticks.
 *
 * **Low frequencies turn a room to mud.** Voice energy below about 200 Hz carries no
 * intelligibility but plenty of power, and feeding it into a long tail is what makes a large
 * space unusable for speech. The reverb send is high-passed; the dry voice keeps its weight.
 *
 * **Room masks consonants.** The more space, the less speech survives it. When
 * [AmbienceSettings.speechPriority] is up, the wet path is ducked by the dry signal's own
 * envelope — the room recedes while a word is being spoken and blooms in the gaps between them,
 * which is what a mixing engineer does by hand and what keeps a cathedral intelligible.
 *
 * ## Two properties that are not negotiable
 *
 * **Decay is specified in seconds.** Comb feedback is derived from the requested RT60 and each
 * comb's own length, so every comb decays at the same rate and the number the panel prints is a
 * measurement. A reverb whose decay changes when you move the size control cannot be described
 * honestly to a user.
 *
 * **It is streaming.** All state lives in the instance and survives across calls, so processing a
 * file in 1 024-frame blocks is bit-identical to processing it in one. An engine that rebuilds
 * its delay lines per block restarts the tail at every boundary — a click twenty-five times a
 * second — which is why live preview could not be built on the previous one.
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

    /**
     * All-pass tunings, short to long. The first four are Freeverb's; the rest extend the chain
     * for the higher diffusion settings, and are chosen mutually prime to the combs for the same
     * reason the combs are prime to each other.
     */
    private val allPassTunings = intArrayOf(556, 441, 341, 225, 180, 137, 99, 73)

    /**
     * Early-reflection taps in milliseconds at full room size, with their gains. Irregular and
     * mutually non-harmonic: an evenly spaced set of reflections *is* a comb filter, and a comb
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
         * The sample written [delayFrames] frames ago. `tick` has already advanced the index past
         * the slot it wrote, so the most recent sample is at `index − 1`, not at `index`; a tap
         * that forgets that is one frame early at every reflection.
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

    /**
     * A damped feedback comb whose delay length wanders.
     *
     * The modulation is what stops the tail ringing. Depth is a fraction of a millisecond and the
     * rate is under a hertz, so it is inaudible as pitch movement on speech while being more than
     * enough to smear the comb's resonant peaks. Each comb gets its own rate and starting phase;
     * modulating them in lock-step would simply move the ringing rather than remove it.
     */
    private class ModulatedComb(
        private val baseDelay: Int,
        private val feedback: Double,
        private val damping: Double,
        private val depth: Double,
        rateHz: Double,
        sampleRate: Int,
        private var phase: Double,
    ) {
        // Headroom for the modulation on both sides, plus one for the interpolation partner.
        private val buffer = FloatArray(baseDelay + depth.toInt() + 3)
        private var writeIndex = 0
        private var store = 0.0
        private val step = 2.0 * Math.PI * rateHz / sampleRate

        fun process(input: Double): Double {
            val offset = baseDelay + depth * sin(phase)
            phase += step
            if (phase > 2.0 * Math.PI) phase -= 2.0 * Math.PI

            // Fractional read, linearly interpolated. Without interpolation the modulation
            // becomes a series of one-sample jumps, which is a click train rather than movement.
            val readPosition = writeIndex - offset
            val whole = kotlin.math.floor(readPosition).toInt()
            val fraction = readPosition - whole
            val a = buffer[((whole % buffer.size) + buffer.size) % buffer.size].toDouble()
            val b = buffer[(((whole + 1) % buffer.size) + buffer.size) % buffer.size].toDouble()
            val output = a + (b - a) * fraction

            // One-pole low-pass inside the loop. Its DC gain is 1, so the low-frequency decay is
            // exactly the requested RT60 while the highs die sooner — which is what a real room
            // does, and what damping means here.
            store = output * (1.0 - damping) + store * damping
            buffer[writeIndex] = (input + store * feedback).toFloat()
            if (++writeIndex >= buffer.size) writeIndex = 0
            return output
        }

        fun clear() {
            buffer.fill(0f)
            writeIndex = 0
            store = 0.0
        }
    }

    /**
     * A true unity-gain Schroeder all-pass.
     *
     * Freeverb's simplified form — `out = −in + buf; buf = in + buf·g` — is the one usually
     * copied, and it is not all-pass: its gain rises with the feedback coefficient. Raising both
     * the coefficient and the number of sections to increase diffusion therefore made the whole
     * tail louder, which is a diffusion control that doubles as a volume control. This is the
     * textbook structure, whose magnitude response really is flat, so diffusion changes the
     * *texture* of the tail and nothing else.
     */
    private class AllPass(size: Int, private val feedback: Double) {
        private val buffer = FloatArray(size.coerceAtLeast(1))
        private var index = 0

        fun process(input: Double): Double {
            val delayed = buffer[index].toDouble()
            val v = input + feedback * delayed
            val output = delayed - feedback * v
            buffer[index] = v.toFloat()
            if (++index >= buffer.size) index = 0
            return output
        }

        fun clear() {
            buffer.fill(0f)
            index = 0
        }
    }

    /** Peak envelope of the dry voice, for the ducking that keeps speech above the room. */
    private class Envelope(attackMs: Double, releaseMs: Double, sampleRate: Int) {
        private val attack = kotlin.math.exp(-1.0 / (attackMs / 1000.0 * sampleRate))
        private val release = kotlin.math.exp(-1.0 / (releaseMs / 1000.0 * sampleRate))
        private var value = 0.0

        fun process(sample: Double): Double {
            val magnitude = abs(sample)
            val coefficient = if (magnitude > value) attack else release
            value = coefficient * value + (1.0 - coefficient) * magnitude
            return value
        }

        fun clear() {
            value = 0.0
        }
    }

    // --- Per-channel state, built once and kept ---------------------------------------------

    private val preDelayFrames =
        (settings.preDelayMs * sampleRate / 1000.0).toInt().coerceAtLeast(1)

    private val preDelays = Array(channelCount) { Delay(preDelayFrames) }

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

    private val dampingAmount = settings.damping.coerceIn(0.0, 1.0) * 0.55

    /**
     * Modulation depth in frames, and rate in hertz.
     *
     * Tail smoothness buys both: more wander and slightly faster movement. At zero the combs are
     * static and the tail rings; at one the movement is around half a millisecond, which is
     * inaudible on speech and enough to break the resonances up completely.
     */
    private val modulationDepth = settings.tailSmoothness * 24.0 * rateScale
    private val modulationRate = 0.19 + settings.tailSmoothness * 0.42

    private val combs = Array(channelCount) { channel ->
        // 23 frames of stereo spread, as Freeverb uses, scaled by the width control.
        val spread = if (channel == 0) 0 else (23 * settings.width).toInt()
        Array(combTunings.size) { i ->
            val size = ((combTunings[i] + spread) * rateScale * sizeScale).toInt().coerceAtLeast(1)
            ModulatedComb(
                baseDelay = size,
                feedback = feedbackFor(size),
                damping = dampingAmount,
                depth = modulationDepth,
                // Mutually detuned, and different between the ears. Locked rates would move the
                // ringing rather than remove it.
                rateHz = modulationRate * (0.83 + 0.11 * i) * (if (channel == 0) 1.0 else 1.07),
                sampleRate = sampleRate,
                phase = i * 0.7854 + channel * 1.31,
            )
        }
    }

    /**
     * How many all-pass sections are in circuit, and how strongly they diffuse.
     *
     * Four is Freeverb's chain and is enough for a small room. A large hall at low diffusion is
     * audibly grainy, so the count and the coefficient both rise with the control.
     */
    private val allPassCount = (4 + (settings.diffusion * 4.0)).toInt().coerceIn(4, allPassTunings.size)
    private val allPassFeedback = 0.42 + settings.diffusion * 0.28

    private val allPasses = Array(channelCount) { channel ->
        val spread = if (channel == 0) 0 else (23 * settings.width).toInt()
        Array(allPassCount) { i ->
            val size = ((allPassTunings[i] + spread) * rateScale * sizeScale).toInt().coerceAtLeast(1)
            AllPass(size, allPassFeedback)
        }
    }

    /**
     * The reverb send is high-passed.
     *
     * Voice energy below about 200 Hz carries no intelligibility and a great deal of power, and
     * putting it into a long tail is exactly what turns a large space to mud. The dry voice keeps
     * its weight; only the room loses the bottom.
     */
    private val sendHighPass = Array(channelCount) {
        Biquad.highPass(AmbienceSettings.SEND_HIGH_PASS_HZ, sampleRate)
    }

    /** Tone on the wet path only, so brightening the room never brightens the voice. */
    private val wetBrightness = Array(channelCount) {
        Biquad.highShelf(6_000.0, sampleRate, (settings.brightness - 0.5) * 12.0)
    }

    /** Warmth is the wet signal's low-mid tilt — the room's material, not its absorption. */
    private val wetWarmth = Array(channelCount) {
        Biquad.lowShelf(320.0, sampleRate, (settings.warmth - 0.5) * 7.0)
    }

    /**
     * A dip in the room around the consonant band.
     *
     * Presence here does not brighten anything: it takes the *room* out of the way of the
     * consonants, so a large space can be loud without swallowing the words. Turning it up cuts
     * the wet path where speech carries its intelligibility, which is the opposite of what an
     * exciter does and far more useful on a voice.
     */
    private val wetPresenceDip = Array(channelCount) {
        Biquad.peaking(2_600.0, sampleRate, -settings.presence * 6.0, 1.1)
    }

    private val duckEnvelope = Array(channelCount) { Envelope(attackMs = 6.0, releaseMs = 320.0, sampleRate) }

    /**
     * Mean magnitude of the loop's one-pole damping filter across the band.
     *
     * `y[n] = (1 − d)·x[n] + d·y[n−1]`, evaluated at sixty-four points. At `d = 0` this is 1 and
     * the normalisation reduces to the textbook form.
     */
    private val dampingMeanMagnitude: Double = run {
        val d = dampingAmount
        if (d <= 0.0) return@run 1.0
        val points = 64
        var sum = 0.0
        for (i in 0 until points) {
            val w = Math.PI * (i + 0.5) / points
            val re = 1.0 - d * kotlin.math.cos(w)
            val im = d * kotlin.math.sin(w)
            sum += (1.0 - d) / sqrt(re * re + im * im)
        }
        sum / points
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
        // The damping filter sits inside the loop, so the feedback the bank actually achieves is
        // the configured one multiplied by that filter's magnitude — which is 1 only at DC and
        // falls with frequency. Ignoring it, as the textbook formula does, understates the loop
        // gain badly on a damped room: a soft hall came out around 17 dB below a dry one, so
        // every large preset's mix had to be dialled up to compensate and no two presets could be
        // compared. Averaging the filter's magnitude across the band costs sixty-four operations
        // once and makes the normalisation true for any damping setting.
        val effective = meanFeedback * dampingMeanMagnitude
        (1.0 - effective) / sqrt(combTunings.size.toDouble())
    }

    private val reflectionLevel = settings.earlyReflections
    private val lateLevel = settings.lateReflections
    private val effectiveWet = settings.amount * settings.wetDryMix
    private val effectiveDry = 1.0 - settings.amount * settings.wetDryMix

    /** Clears the tail. Call when playback jumps, so the old room does not follow the cursor. */
    public fun reset() {
        preDelays.forEach { it.clear() }
        reflectionLine.forEach { it.clear() }
        combs.forEach { bank -> bank.forEach { it.clear() } }
        allPasses.forEach { bank -> bank.forEach { it.clear() } }
        sendHighPass.forEach { it.reset() }
        wetBrightness.forEach { it.reset() }
        wetWarmth.forEach { it.reset() }
        wetPresenceDip.forEach { it.reset() }
        duckEnvelope.forEach { it.clear() }
    }

    /**
     * Processes one block in place. State persists, so consecutive blocks join seamlessly.
     *
     * The buffer's channel count must match the one this instance was built for; a mismatch is a
     * programming error, not a condition to paper over.
     */
    public fun process(buffer: AudioBuffer): AudioBuffer {
        require(buffer.channelCount == channelCount) {
            "This Ambience was built for $channelCount channels, got ${buffer.channelCount}"
        }
        if (effectiveWet <= 0.0) return buffer

        val frames = buffer.frameCount
        val wet = Array(channelCount) { DoubleArray(frames) }
        val duck = DoubleArray(frames) { 1.0 }

        for (c in 0 until channelCount) {
            val channel = buffer.channels[c]
            val preDelay = preDelays[c]
            val line = reflectionLine[c]
            val offsets = reflectionOffsets[c]
            val combBank = combs[c]
            val allPassBank = allPasses[c]
            val highPass = sendHighPass[c]
            val brightness = wetBrightness[c]
            val warmth = wetWarmth[c]
            val presenceDip = wetPresenceDip[c]
            val envelope = duckEnvelope[c]

            for (i in 0 until frames) {
                val input = channel[i].toDouble()

                // Speech priority: the room recedes while a word is being spoken and blooms in
                // the gaps. Measured on the dry voice before the pre-delay, so the duck is in
                // time with the words rather than with the room's answer to them.
                if (settings.speechPriority > 0.0) {
                    val level = envelope.process(input)
                    val reduction = 1.0 - settings.speechPriority * (level * 3.0).coerceAtMost(0.75)
                    if (c == 0 || reduction < duck[i]) duck[i] = reduction
                }

                // Pre-delay feeds the room only. The dry voice is never delayed, so no amount of
                // pre-delay can put the speaker out of time with the picture.
                val delayed = if (settings.preDelayMs > 0.0) preDelay.tick(input) else input

                // The send loses the bottom; the dry voice keeps it.
                val send = highPass.processSample(delayed)

                line.tick(send)
                var early = 0.0
                if (reflectionLevel > 0.0) {
                    for (t in offsets.indices) early += line.tap(offsets[t]) * reflectionGains[t]
                    early *= reflectionLevel * 0.35
                }

                var tail = 0.0
                if (lateLevel > 0.0) {
                    val fed = send * wetNormalise
                    for (comb in combBank) tail += comb.process(fed)
                    for (allPass in allPassBank) tail = allPass.process(tail)
                    tail *= lateLevel
                }

                var value = early + tail
                value = warmth.processSample(value)
                value = brightness.processSample(value)
                if (settings.presence > 0.0) value = presenceDip.processSample(value)
                wet[c][i] = value
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
                channel[i] = (channel[i] * effectiveDry + wet[c][i] * effectiveWet * duck[i]).toFloat()
            }
        }
        return buffer
    }
}

/**
 * The ambience controls, as one serialisable value.
 *
 * Every field is a quantity a person can picture. The proportions run 0..1; `decaySeconds` and
 * `preDelayMs` are in real units because they describe time, and rounding those into a 0..1 dial
 * is how products end up unable to tell a user what their reverb is doing.
 *
 * [amount] and [wetDryMix] are deliberately separate. `wetDryMix` is the preset's character — how
 * much room this *kind* of space has. `amount` is the one knob on the panel that makes the whole
 * effect stronger or weaker without changing that character. The wet level applied is their
 * product.
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
    /** Level of the late tail — the room's sustain, as distinct from its shape. */
    val lateReflections: Double = 1.0,
    /** RT60: how long the tail takes to fall 60 dB. */
    val decaySeconds: Double = 1.0,
    /** Gap before the room answers. A larger gap reads as a larger room and keeps words clear. */
    val preDelayMs: Double = 20.0,
    /**
     * Echo density. Low is a bare, grainy room where reflections are heard as separate events;
     * high is a soft, continuous texture. Large spaces need more of it than small ones.
     */
    val diffusion: Double = 0.6,
    /** How fast the high frequencies are absorbed inside the tail. Soft rooms absorb more. */
    val damping: Double = 0.5,
    /** Tone of the wet path low down. Below 0.5 is stone and glass, above is wood and cloth. */
    val warmth: Double = 0.5,
    /** Tone of the wet path up top. 0.5 is flat, below darkens, above opens. */
    val brightness: Double = 0.5,
    /**
     * How far the room stays out of the way of the consonants.
     *
     * This cuts the *wet* path in the speech band rather than boosting anything, so a large space
     * can be loud without swallowing words.
     */
    val presence: Double = 0.35,
    /**
     * How much the tail is kept moving.
     *
     * Static delay lines ring at fixed frequencies and that ringing is the metallic sound of a
     * cheap reverb. At 0 the combs are still; at 1 they wander by around half a millisecond,
     * which is inaudible on speech and enough to break the resonances up entirely.
     */
    val tailSmoothness: Double = 0.7,
    /**
     * How hard the room ducks out of the way of the voice.
     *
     * At 0 the room is constant. Turned up, it recedes while a word is being spoken and blooms in
     * the gaps — which is what keeps a cathedral intelligible and is done by hand on every
     * professional vocal.
     */
    val speechPriority: Double = 0.4,
    /** The preset's balance of room to voice. */
    val wetDryMix: Double = 0.15,
) {
    init {
        val proportions = mapOf(
            "amount" to amount, "roomSize" to roomSize, "width" to width,
            "earlyReflections" to earlyReflections, "lateReflections" to lateReflections,
            "diffusion" to diffusion, "damping" to damping, "warmth" to warmth,
            "brightness" to brightness, "presence" to presence,
            "tailSmoothness" to tailSmoothness, "speechPriority" to speechPriority,
            "wetDryMix" to wetDryMix,
        )
        for ((name, value) in proportions) {
            require(value in 0.0..1.0) { "$name is a proportion, was $value" }
        }
        require(decaySeconds in 0.05..20.0) { "Decay must be between 0.05 s and 20 s" }
        require(preDelayMs in 0.0..250.0) { "Pre-delay must be between 0 ms and 250 ms" }
    }

    /** True when this stage would change nothing, so a panel can say "no room" honestly. */
    public val isBypassed: Boolean get() = amount <= 0.0 || wetDryMix <= 0.0

    public fun build(sampleRate: Int, channelCount: Int): Ambience =
        Ambience(this, sampleRate, channelCount)

    public companion object {
        /**
         * Where the reverb send is high-passed.
         *
         * Below this, voice energy carries no intelligibility and a great deal of power. Sending
         * it into a long tail is precisely what makes a large room unusable for speech.
         */
        public const val SEND_HIGH_PASS_HZ: Double = 190.0

        /** No room at all — the voice exactly as captured. */
        public val NONE: AmbienceSettings = AmbienceSettings(amount = 0.0, wetDryMix = 0.0)
    }
}

/**
 * How much room the user wants, independent of which room.
 *
 * The same space at three strengths, rather than three sets of presets. A person who likes
 * Lecture Hall but finds it too much should be able to say so in one control without having to
 * find a different, smaller-sounding preset and lose the character they chose.
 */
public enum class AmbienceMode(
    public val displayName: String,
    public val summary: String,
    internal val mixScale: Double,
    internal val speechPriorityFloor: Double,
) {
    /** Subtle. The recording stops sounding dead and nothing else changes. */
    NATURAL("Natural", "Just enough room that the recording stops sounding dead.", 0.55, 0.5),

    /** The default: polished and controlled, for podcasts and narration. */
    STUDIO("Studio", "Polished and controlled. For narration and podcasts.", 1.0, 0.35),

    /** Deliberately large, for someone who wants to hear the space. */
    IMMERSIVE("Immersive", "A room you can hear. For recitation and performance.", 1.6, 0.25),
    ;

    /**
     * Applies the mode to a space.
     *
     * Immersive raises the mix, and because more room means less speech, it also raises the floor
     * under [AmbienceSettings.speechPriority] — the protection scales with the thing it protects
     * against, so turning the room up cannot quietly cost intelligibility.
     */
    public fun applyTo(settings: AmbienceSettings): AmbienceSettings {
        if (settings.isBypassed) return settings
        return settings.copy(
            wetDryMix = (settings.wetDryMix * mixScale).coerceIn(0.0, 1.0),
            speechPriority = maxOf(settings.speechPriority, speechPriorityFloor).coerceIn(0.0, 1.0),
        )
    }
}
