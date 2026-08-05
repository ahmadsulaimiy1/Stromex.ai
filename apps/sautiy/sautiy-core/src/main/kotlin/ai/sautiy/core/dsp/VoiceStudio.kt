package ai.sautiy.core.dsp

import ai.sautiy.core.analysis.Loudness
import ai.sautiy.core.audio.AudioBuffer
import kotlin.math.pow
import kotlinx.serialization.Serializable

/**
 * SAUTIY's Voice Studio: one integrated instrument, not a drawer of sliders.
 *
 * The signal chain is fixed, and the order is the whole point:
 *
 * ```
 * Input → Cleanup → Dynamics → Tone → Ambience → Loudness → Output
 * ```
 *
 * * **Cleanup** first, because every stage after it would otherwise spend its range on rumble
 *   and hiss. A compressor in particular turns the gaps between words *up*, so noise removed
 *   after compression has already been amplified.
 * * **Dynamics** before tone, so the equaliser shapes a signal whose level is already steady.
 *   Shaping first and compressing after makes the compressor chase the equaliser's own boosts.
 * * **Tone** — the eight refinement controls — on a clean, even voice.
 * * **Ambience** after tone, because you are putting a finished voice into a room. Equalising
 *   after the room instead would equalise the room, and the room is not what needs fixing.
 * * **Loudness** measured on the finished sound, which is the only sound anyone will hear.
 * * **Output** gain last, under the ceiling.
 *
 * De-essing sits at the end of Tone rather than in Cleanup: sibilance is usually made harsh by
 * the presence lift itself, so de-essing before the lift removes the wrong amount.
 */
public class VoiceStudio(
    public val settings: VoiceStudioSettings,
) {

    /** The finished audio and a measured account of what each stage actually did. */
    public data class Rendered(
        val audio: AudioBuffer,
        val report: Report,
    )

    public data class Report(
        val inputLufs: Double,
        val outputLufs: Double,
        val outputTruePeakDb: Double,
        val compressorReductionDb: Double = 0.0,
        val deEsserReductionDb: Double = 0.0,
        val limiterReductionDb: Double = 0.0,
        val normalisationGainDb: Double = 0.0,
        val normalisationLimitedByPeak: Boolean = false,
        val clipped: Boolean = false,
    )

    /**
     * Renders the complete chain onto a copy, leaving [input] untouched.
     *
     * This is what export writes and what "apply" commits. It runs the same stage objects as
     * [live], in the same order, plus the two stages that cannot exist in a real-time preview.
     */
    public fun render(input: AudioBuffer): Rendered {
        val audio = input.copy()
        val inputLufs = Loudness.integrated(input)

        // Noise reduction is spectral and needs a noise profile learned from the quietest part
        // of the *whole* recording. There is no honest streaming form of it, so it belongs here
        // and is declared as deferred in the live path rather than faked there.
        settings.cleanup.noiseReduction?.let { strength ->
            val reduced = NoiseReduction(strength = strength, floorDb = settings.cleanup.noiseFloorDb)
                .reduce(audio)
            for (c in 0 until audio.channelCount) reduced.channels[c].copyInto(audio.channels[c])
        }

        val realtime = live(audio.sampleRate, audio.channelCount)
        realtime.process(audio)

        var report = Report(
            inputLufs = inputLufs,
            outputLufs = Double.NEGATIVE_INFINITY,
            outputTruePeakDb = Double.NEGATIVE_INFINITY,
            compressorReductionDb = realtime.compressorReductionDb,
            deEsserReductionDb = realtime.deEsserReductionDb,
        )

        settings.loudness.target?.let { name ->
            val target = Loudness.Target.entries.firstOrNull { it.name == name }
            if (target != null) {
                val plan = Loudness.planNormalisation(audio, target)
                audio.applyGain(10.0.pow(plan.gainDb / 20.0).toFloat())
                report = report.copy(
                    normalisationGainDb = plan.gainDb,
                    normalisationLimitedByPeak = plan.limitedByTruePeak,
                )
            }
        }

        settings.loudness.limiterCeilingDb?.let { ceiling ->
            report = report.copy(limiterReductionDb = Limiter(ceilingDb = ceiling).process(audio))
        }

        return Rendered(
            audio,
            report.copy(
                outputLufs = Loudness.integrated(audio),
                outputTruePeakDb = Loudness.truePeakDb(audio),
                clipped = audio.hasClipping(),
            ),
        )
    }

    /**
     * A streaming instance of every stage that can run under a playback callback.
     *
     * Live preview is the reason this exists. Because [render] drives the same object, what the
     * user hears while auditioning is what the file will contain — for every setting except the
     * ones named in [deferredStages], which are listed so the panel can say so rather than imply
     * otherwise.
     */
    public fun live(sampleRate: Int, channelCount: Int): LiveVoiceStudio =
        LiveVoiceStudio(settings, sampleRate, channelCount)

    /** Stages [live] cannot run, named for the interface to display honestly. */
    public val deferredStages: List<String>
        get() = buildList {
            if (settings.cleanup.noiseReduction != null) add("Noise reduction")
            if (settings.loudness.target != null) add("Loudness normalisation")
            if (settings.loudness.limiterCeilingDb != null) add("Limiter")
        }
}

/**
 * The real-time half of the chain, with all filter state held across blocks.
 *
 * Every stage here is per-sample and causal. Nothing in it looks ahead, allocates per block or
 * rebuilds a filter — those are the three ways a preview turns into a click track.
 */
public class LiveVoiceStudio(
    public val settings: VoiceStudioSettings,
    public val sampleRate: Int,
    public val channelCount: Int,
) {
    private val highPass = settings.cleanup.highPassHz?.let { hz ->
        Array(channelCount) { Biquad.highPass(hz, sampleRate) }
    }

    private val humNotches = settings.cleanup.humHz?.let { fundamental ->
        // The fundamental plus two harmonics: mains hum on a phone is rarely a pure tone, and
        // notching only the fundamental leaves the buzz that made it noticeable.
        Array(channelCount) {
            (1..3).map { harmonic -> Biquad.notch(fundamental * harmonic, sampleRate, q = 30.0) }
        }
    }

    private val compressor = settings.dynamics.compressor
    private val follower = compressor?.let {
        EnvelopeFollower(it.attackMs, it.releaseMs, sampleRate, rms = true)
    }
    private val makeupLinear = compressor?.let {
        10.0.pow((it.makeupDb ?: it.toCompressor().automaticMakeupDb()) / 20.0)
    } ?: 1.0
    private val curve = compressor?.toCompressor()

    // A 12 kHz air shelf is meaningless on a 16 kHz voice memo, and a biquad designed at or
    // above Nyquist is not merely inaudible — it is unstable. Bands are moved down to stay
    // inside the band the recording actually has.
    private val toneBands = settings.refinement.bands().map { band ->
        val ceiling = sampleRate * 0.45
        if (band.frequency <= ceiling) band else band.copy(frequency = ceiling)
    }
    private val tone = if (toneBands.isEmpty()) null else {
        Array(channelCount) { toneBands.map { band -> band.build(sampleRate) }.toTypedArray() }
    }

    private val deEsser = settings.dynamics.deEsser?.let {
        StreamingDeEsser(
            frequencyHz = it.frequencyHz.coerceAtMost(sampleRate * 0.45),
            thresholdDb = it.thresholdDb,
            ratio = it.ratio,
            sampleRate = sampleRate,
            channelCount = channelCount,
        )
    }

    private val ambience = settings.effectiveAmbience.takeIf { !it.isBypassed }
        ?.build(sampleRate, channelCount)

    private val outputGain = 10.0.pow(settings.outputGainDb / 20.0).toFloat()

    /** Peak gain reduction the compressor has applied since the last [reset]. */
    public var compressorReductionDb: Double = 0.0
        private set

    /** Peak gain reduction the de-esser has applied since the last [reset]. */
    public val deEsserReductionDb: Double get() = deEsser?.maxReductionDb ?: 0.0

    /** Clears every filter and tail. Call on a seek, so the old audio does not ring into the new. */
    public fun reset() {
        highPass?.forEach { it.reset() }
        humNotches?.forEach { bank -> bank.forEach { it.reset() } }
        follower?.reset()
        tone?.forEach { bank -> bank.forEach { it.reset() } }
        deEsser?.reset()
        ambience?.reset()
        compressorReductionDb = 0.0
    }

    /** Processes one block in place and returns it. */
    public fun process(buffer: AudioBuffer): AudioBuffer {
        require(buffer.channelCount == channelCount) {
            "This chain was built for $channelCount channels, got ${buffer.channelCount}"
        }
        require(buffer.sampleRate == sampleRate) {
            "This chain was built for $sampleRate Hz, got ${buffer.sampleRate} Hz"
        }
        val frames = buffer.frameCount
        if (frames == 0) return buffer

        // --- Cleanup ------------------------------------------------------------------------
        for (c in 0 until channelCount) {
            val channel = buffer.channels[c]
            highPass?.get(c)?.let { filter ->
                for (i in 0 until frames) channel[i] = filter.processSample(channel[i].toDouble()).toFloat()
            }
            humNotches?.get(c)?.forEach { notch ->
                for (i in 0 until frames) channel[i] = notch.processSample(channel[i].toDouble()).toFloat()
            }
        }

        // --- Dynamics -----------------------------------------------------------------------
        if (curve != null && follower != null) {
            for (i in 0 until frames) {
                // Detection on the channel maximum, so a stereo image is not pulled sideways by
                // compressing each side against its own level.
                var detector = 0.0
                for (c in 0 until channelCount) {
                    val magnitude = kotlin.math.abs(buffer.channels[c][i].toDouble())
                    if (magnitude > detector) detector = magnitude
                }
                val envelope = follower.process(detector)
                val levelDb = if (envelope <= 0.0) -120.0 else 20.0 * kotlin.math.log10(envelope)
                val reduction = curve.gainReductionDb(levelDb)
                if (reduction < compressorReductionDb) compressorReductionDb = reduction

                val gain = (10.0.pow(reduction / 20.0) * makeupLinear).toFloat()
                for (c in 0 until channelCount) buffer.channels[c][i] *= gain
            }
        }

        // --- Tone ---------------------------------------------------------------------------
        tone?.let { banks ->
            for (c in 0 until channelCount) {
                val channel = buffer.channels[c]
                for (filter in banks[c]) {
                    for (i in 0 until frames) {
                        channel[i] = filter.processSample(channel[i].toDouble()).toFloat()
                    }
                }
            }
        }
        deEsser?.process(buffer)

        // --- Ambience -----------------------------------------------------------------------
        ambience?.process(buffer)

        // --- Output -------------------------------------------------------------------------
        if (outputGain != 1f) buffer.applyGain(outputGain)
        return buffer
    }
}

/**
 * A de-esser that keeps its state between blocks.
 *
 * Split with a Linkwitz-Riley crossover rather than by subtracting a high-pass from the signal.
 * That subtraction looks equivalent and is not: the filter's phase shift leaves most of the
 * sibilance in the "low" band, so the de-esser appears to work while reducing 7 kHz by under a
 * decibel. That bug shipped once here; the crossover is the fix, and this is its streaming form.
 */
public class StreamingDeEsser(
    public val frequencyHz: Double,
    public val thresholdDb: Double,
    public val ratio: Double,
    public val sampleRate: Int,
    public val channelCount: Int,
) {
    private val lowPass = Array(channelCount) {
        listOf(Biquad.lowPass(frequencyHz, sampleRate), Biquad.lowPass(frequencyHz, sampleRate))
    }
    private val highPass = Array(channelCount) {
        listOf(Biquad.highPass(frequencyHz, sampleRate), Biquad.highPass(frequencyHz, sampleRate))
    }
    private val follower = Array(channelCount) {
        EnvelopeFollower(attackMs = 1.0, releaseMs = 40.0, sampleRate = sampleRate, rms = false)
    }
    private val compressor = Compressor(
        thresholdDb = thresholdDb,
        ratio = ratio,
        attackMs = 1.0,
        releaseMs = 40.0,
        kneeDb = 3.0,
        makeupDb = 0.0,
    )

    public var maxReductionDb: Double = 0.0
        private set

    public fun reset() {
        lowPass.forEach { bank -> bank.forEach { it.reset() } }
        highPass.forEach { bank -> bank.forEach { it.reset() } }
        follower.forEach { it.reset() }
        maxReductionDb = 0.0
    }

    public fun process(buffer: AudioBuffer): AudioBuffer {
        for (c in 0 until channelCount) {
            val channel = buffer.channels[c]
            for (i in channel.indices) {
                val x = channel[i].toDouble()
                var low = x
                for (filter in lowPass[c]) low = filter.processSample(low)
                var high = x
                for (filter in highPass[c]) high = filter.processSample(high)

                val envelope = follower[c].process(high)
                val levelDb = if (envelope <= 0.0) -120.0 else 20.0 * kotlin.math.log10(envelope)
                val reduction = compressor.gainReductionDb(levelDb)
                if (reduction < maxReductionDb) maxReductionDb = reduction

                // Linkwitz-Riley sums flat, so an untouched band recombines to the original
                // signal exactly — the sibilant band is the only thing that moves.
                channel[i] = (low + high * 10.0.pow(reduction / 20.0)).toFloat()
            }
        }
        return buffer
    }
}

// --- Settings -------------------------------------------------------------------------------

/** Stage 1: what should not be in the recording at all. */
@Serializable
public data class CleanupStage(
    /** Rumble, handling noise and desk thumps. `null` leaves the bottom alone. */
    val highPassHz: Double? = 80.0,
    /** Spectral noise reduction strength. Offline only — see [VoiceStudio.deferredStages]. */
    val noiseReduction: Double? = null,
    val noiseFloorDb: Double = -18.0,
    /** Mains hum, 50 Hz or 60 Hz, notched with its first two harmonics. */
    val humHz: Double? = null,
) {
    init {
        require(highPassHz == null || highPassHz in 20.0..400.0) { "A voice high-pass belongs between 20 Hz and 400 Hz" }
        require(noiseReduction == null || noiseReduction in 0.0..4.0)
        require(humHz == null || humHz in 40.0..70.0) { "Mains hum is 50 Hz or 60 Hz" }
    }
}

/** Stage 2: making the level even. */
@Serializable
public data class DynamicsStage(
    val compressor: CompressorSettings? = null,
    val deEsser: DeEsserSettings? = null,
) {
    @Serializable
    public data class CompressorSettings(
        val thresholdDb: Double = -20.0,
        val ratio: Double = 3.0,
        val attackMs: Double = 10.0,
        val releaseMs: Double = 120.0,
        val kneeDb: Double = 6.0,
        val makeupDb: Double? = null,
    ) {
        init {
            require(ratio >= 1.0) { "A ratio below 1:1 is an expander" }
            require(attackMs > 0.0 && releaseMs > 0.0)
        }

        internal fun toCompressor(): Compressor = Compressor(
            thresholdDb = thresholdDb,
            ratio = ratio,
            attackMs = attackMs,
            releaseMs = releaseMs,
            kneeDb = kneeDb,
            makeupDb = makeupDb,
            detectRms = true,
        )
    }

    @Serializable
    public data class DeEsserSettings(
        val frequencyHz: Double = 6_000.0,
        val thresholdDb: Double = -28.0,
        val ratio: Double = 4.0,
    ) {
        init {
            require(frequencyHz in 2_000.0..12_000.0) { "Sibilance lives between 2 kHz and 12 kHz" }
            require(ratio >= 1.0)
        }
    }
}

/**
 * Stage 3: the eight voice refinement controls.
 *
 * Every one runs −1 to +1 with 0 neutral, so a control at rest is provably transparent and the
 * panel can show a centre detent that means something. They are named for what a listener hears,
 * not for a frequency, because "4 kHz, +3 dB, Q 0.8" is a description of a filter and "Presence"
 * is a description of a voice.
 *
 * [warmth] and [brightness] appear here *and* in [AmbienceSettings]. They are not duplicates:
 * these shape the voice, those shape the room it is in. A warm voice in a bright hall is a
 * perfectly ordinary thing to want, and one pair of controls could not express it.
 *
 * [depth] is the exception that proves the design: depth is distance, and distance is a room, so
 * it drives the ambience rather than the equaliser. Turning it up with no space selected does
 * nothing, and the panel says so instead of pretending.
 */
@Serializable
public data class VoiceRefinement(
    /** Intelligibility: lifts the consonant range and clears the mud underneath it. */
    val clarity: Double = 0.0,
    /** Fullness low down, softness up top. */
    val warmth: Double = 0.0,
    /** The lower-mid harmonics that make a voice sound like a person rather than a telephone. */
    val richness: Double = 0.0,
    /** How close the speaker feels. */
    val presence: Double = 0.0,
    /** Weight at the bottom of the voice. */
    val body: Double = 0.0,
    /** The open top octave. */
    val air: Double = 0.0,
    /** Overall tilt of the upper range. */
    val brightness: Double = 0.0,
    /** Distance. Drives the room, not the tone — see the class note. */
    val depth: Double = 0.0,
) {
    init {
        val controls = mapOf(
            "clarity" to clarity, "warmth" to warmth, "richness" to richness,
            "presence" to presence, "body" to body, "air" to air,
            "brightness" to brightness, "depth" to depth,
        )
        for ((name, value) in controls) {
            require(value in -1.0..1.0) { "$name runs from −1 to +1, was $value" }
        }
    }

    /** True when every control is centred, so nothing is done at all. */
    public val isNeutral: Boolean
        get() = clarity == 0.0 && warmth == 0.0 && richness == 0.0 && presence == 0.0 &&
            body == 0.0 && air == 0.0 && brightness == 0.0 && depth == 0.0

    /**
     * The filters these controls describe.
     *
     * A control at 0 contributes no band at all rather than a 0 dB band: a 0 dB biquad is
     * arithmetically transparent but still costs a multiply-add per sample per channel, and on
     * a phone eight of those on every voice is not free.
     */
    public fun bands(): List<EqBand> = buildList {
        if (clarity != 0.0) {
            add(EqBand(EqBand.Type.PEAKING, 2_400.0, clarity * 4.0, 0.9))
            // Clarity is as much about what is removed as what is added: the boxiness at 300 Hz
            // masks consonants, so lifting presence without clearing it just makes it louder.
            add(EqBand(EqBand.Type.PEAKING, 320.0, clarity * -2.5, 1.1))
        }
        if (warmth != 0.0) {
            add(EqBand(EqBand.Type.LOW_SHELF, 220.0, warmth * 4.0))
            add(EqBand(EqBand.Type.HIGH_SHELF, 8_000.0, warmth * -2.0))
        }
        if (richness != 0.0) add(EqBand(EqBand.Type.PEAKING, 420.0, richness * 3.0, 0.8))
        if (presence != 0.0) add(EqBand(EqBand.Type.PEAKING, 4_000.0, presence * 4.0, 0.8))
        if (body != 0.0) add(EqBand(EqBand.Type.LOW_SHELF, 120.0, body * 4.0))
        if (air != 0.0) add(EqBand(EqBand.Type.HIGH_SHELF, 12_000.0, air * 5.0))
        if (brightness != 0.0) add(EqBand(EqBand.Type.HIGH_SHELF, 7_000.0, brightness * 4.0))
    }
}

/** Stage 5: delivery level. Both parts are offline — they need the finished programme. */
@Serializable
public data class LoudnessStage(
    /** A [Loudness.Target] name, or `null` to leave the level as recorded. */
    val target: String? = null,
    val limiterCeilingDb: Double? = -1.0,
) {
    init {
        require(target == null || Loudness.Target.entries.any { it.name == target }) {
            "Unknown loudness target: $target"
        }
        require(limiterCeilingDb == null || limiterCeilingDb <= 0.0) { "A ceiling above 0 dBFS is not a ceiling" }
    }
}

/** The whole instrument, as one serialisable value. Holds no audio and changes nothing by itself. */
@Serializable
public data class VoiceStudioSettings(
    val cleanup: CleanupStage = CleanupStage(),
    val dynamics: DynamicsStage = DynamicsStage(),
    val refinement: VoiceRefinement = VoiceRefinement(),
    val ambience: AmbienceSettings = AmbienceSettings.NONE,
    /**
     * How much of the chosen room the user wants.
     *
     * Separate from the space itself, so someone who likes Lecture Hall but finds it too much can
     * say so without hunting for a smaller-sounding preset and losing the character they chose.
     */
    val ambienceMode: AmbienceMode = AmbienceMode.STUDIO,
    val loudness: LoudnessStage = LoudnessStage(),
    val outputGainDb: Double = 0.0,
) {
    /**
     * The ambience actually used, after [VoiceRefinement.depth] has had its say.
     *
     * Depth moves the listener back from the speaker, and moving back means more room, later
     * and larger. It cannot conjure a room that is not there, which is why a bypassed space
     * stays bypassed.
     */
    public val effectiveAmbience: AmbienceSettings
        get() {
            if (ambience.isBypassed) return ambience
            val depth = refinement.depth
            val withDepth = if (depth == 0.0) {
                ambience
            } else {
                ambience.copy(
                    wetDryMix = (ambience.wetDryMix * (1.0 + depth * 0.8)).coerceIn(0.0, 1.0),
                    preDelayMs = (ambience.preDelayMs * (1.0 + depth * 0.5)).coerceIn(0.0, 250.0),
                    roomSize = (ambience.roomSize + depth * 0.15).coerceIn(0.0, 1.0),
                )
            }
            return ambienceMode.applyTo(withDepth)
        }

    /** True when this would change nothing, so "Original" is an honest label. */
    public val isTransparent: Boolean
        get() = cleanup.highPassHz == null && cleanup.noiseReduction == null &&
            cleanup.humHz == null && dynamics.compressor == null && dynamics.deEsser == null &&
            refinement.isNeutral && ambience.isBypassed && loudness.target == null &&
            loudness.limiterCeilingDb == null && outputGainDb == 0.0

    public fun build(): VoiceStudio = VoiceStudio(this)
}

/**
 * The spaces.
 *
 * Each is named for a place rather than for a process, and each is a complete voice — cleanup,
 * dynamics, tone and room together — because a room chosen without the voice that belongs in it
 * is how a recording ends up sounding like a voice with reverb on it.
 *
 * **These numbers are starting points, not final tuning.** They are derived from the acoustics
 * of the places they are named for: a plastered room absorbs less treble than a carpeted one, a
 * larger space answers later and needs more diffusion to stop sounding grainy, and a longer tail
 * needs more speech priority to stay intelligible. That reasoning gets a preset close. Only
 * listening gets it right, and a listener has to do that part.
 */
public enum class VoiceSpacePreset(
    public val displayName: String,
    public val summary: String,
    public val settings: VoiceStudioSettings,
) {
    PURE_STUDIO(
        "Pure Studio",
        "No room at all. The voice exactly as the microphone heard it, cleaned.",
        VoiceStudioSettings(
            cleanup = CleanupStage(highPassHz = 80.0),
            dynamics = DynamicsStage(
                compressor = DynamicsStage.CompressorSettings(thresholdDb = -20.0, ratio = 3.0),
                deEsser = DynamicsStage.DeEsserSettings(thresholdDb = -26.0),
            ),
            refinement = VoiceRefinement(clarity = 0.25, presence = 0.20),
            ambience = AmbienceSettings.NONE,
        ),
    ),

    NATURAL_PRESENCE(
        "Natural Presence",
        "Almost nothing. Only enough space that the recording stops sounding dead.",
        VoiceStudioSettings(
            cleanup = CleanupStage(highPassHz = 75.0),
            dynamics = DynamicsStage(
                compressor = DynamicsStage.CompressorSettings(thresholdDb = -18.0, ratio = 2.0, kneeDb = 8.0),
            ),
            refinement = VoiceRefinement(clarity = 0.15),
            ambience = AmbienceSettings(
                roomSize = 0.2, decaySeconds = 0.38, preDelayMs = 8.0,
                earlyReflections = 0.78, lateReflections = 0.5, diffusion = 0.5,
                damping = 0.55, warmth = 0.52, brightness = 0.5,
                presence = 0.28, tailSmoothness = 0.6, speechPriority = 0.35,
                width = 1.0, wetDryMix = 0.05,
            ),
        ),
    ),

    VOCAL_BOOTH(
        "Vocal Booth",
        "A treated booth: close, controlled, with just enough air to breathe.",
        VoiceStudioSettings(
            cleanup = CleanupStage(highPassHz = 85.0),
            dynamics = DynamicsStage(
                compressor = DynamicsStage.CompressorSettings(thresholdDb = -20.0, ratio = 3.0),
                deEsser = DynamicsStage.DeEsserSettings(thresholdDb = -26.0),
            ),
            refinement = VoiceRefinement(clarity = 0.30, presence = 0.25),
            ambience = AmbienceSettings(
                roomSize = 0.1, decaySeconds = 0.3, preDelayMs = 6.0,
                earlyReflections = 0.85, lateReflections = 0.55, diffusion = 0.45,
                damping = 0.6, warmth = 0.55, brightness = 0.5,
                presence = 0.3, tailSmoothness = 0.55, speechPriority = 0.35,
                width = 1.0, wetDryMix = 0.07,
            ),
        ),
    ),

    WARM_STUDIO(
        "Warm Studio",
        "Wood, not glass. Fuller underneath and softer on top.",
        VoiceStudioSettings(
            cleanup = CleanupStage(highPassHz = 65.0),
            dynamics = DynamicsStage(
                compressor = DynamicsStage.CompressorSettings(thresholdDb = -20.0, ratio = 2.5),
            ),
            refinement = VoiceRefinement(warmth = 0.50, richness = 0.35, body = 0.30, air = -0.15),
            ambience = AmbienceSettings(
                roomSize = 0.3, decaySeconds = 0.7, preDelayMs = 14.0,
                earlyReflections = 0.65, lateReflections = 0.85, diffusion = 0.6,
                damping = 0.7, warmth = 0.72, brightness = 0.38,
                presence = 0.35, tailSmoothness = 0.7, speechPriority = 0.35,
                width = 1.0, wetDryMix = 0.12,
            ),
        ),
    ),

    BROADCAST(
        "Broadcast",
        "Tight, dense and even, delivered to the −23 LUFS broadcast standard.",
        VoiceStudioSettings(
            cleanup = CleanupStage(highPassHz = 90.0),
            dynamics = DynamicsStage(
                compressor = DynamicsStage.CompressorSettings(thresholdDb = -24.0, ratio = 4.0, attackMs = 5.0, releaseMs = 90.0),
                deEsser = DynamicsStage.DeEsserSettings(thresholdDb = -30.0, ratio = 5.0),
            ),
            refinement = VoiceRefinement(clarity = 0.40, presence = 0.30, body = 0.15),
            ambience = AmbienceSettings(
                roomSize = 0.18, decaySeconds = 0.42, preDelayMs = 9.0,
                earlyReflections = 0.75, lateReflections = 0.6, diffusion = 0.55,
                damping = 0.62, warmth = 0.52, brightness = 0.52,
                presence = 0.45, tailSmoothness = 0.6, speechPriority = 0.45,
                width = 1.0, wetDryMix = 0.06,
            ),
            loudness = LoudnessStage(target = "BROADCAST", limiterCeilingDb = -1.0),
        ),
    ),

    PODCAST(
        "Podcast",
        "Close and companionable, at the −16 LUFS podcast standard.",
        VoiceStudioSettings(
            cleanup = CleanupStage(highPassHz = 80.0),
            dynamics = DynamicsStage(
                compressor = DynamicsStage.CompressorSettings(thresholdDb = -22.0, ratio = 3.5),
                deEsser = DynamicsStage.DeEsserSettings(),
            ),
            refinement = VoiceRefinement(clarity = 0.30, warmth = 0.25, presence = 0.30, body = 0.20),
            ambience = AmbienceSettings(
                roomSize = 0.22, decaySeconds = 0.52, preDelayMs = 12.0,
                earlyReflections = 0.7, lateReflections = 0.75, diffusion = 0.58,
                damping = 0.6, warmth = 0.58, brightness = 0.5,
                presence = 0.4, tailSmoothness = 0.65, speechPriority = 0.4,
                width = 1.0, wetDryMix = 0.09,
            ),
            loudness = LoudnessStage(target = "PODCAST", limiterCeilingDb = -1.0),
        ),
    ),

    LECTURE_HALL(
        "Lecture Hall",
        "A teaching room: carrying, but every word still lands.",
        VoiceStudioSettings(
            cleanup = CleanupStage(highPassHz = 100.0),
            dynamics = DynamicsStage(
                compressor = DynamicsStage.CompressorSettings(thresholdDb = -26.0, ratio = 4.0, releaseMs = 200.0),
            ),
            refinement = VoiceRefinement(clarity = 0.45, presence = 0.35, depth = 0.20),
            ambience = AmbienceSettings(
                roomSize = 0.6, decaySeconds = 1.25, preDelayMs = 26.0,
                earlyReflections = 0.55, lateReflections = 1.0, diffusion = 0.7,
                damping = 0.52, warmth = 0.5, brightness = 0.5,
                presence = 0.55, tailSmoothness = 0.78, speechPriority = 0.5,
                width = 1.0, wetDryMix = 0.15,
            ),
            loudness = LoudnessStage(target = "SPOKEN_WORD", limiterCeilingDb = -1.5),
        ),
    ),

    SMALL_MOSQUE(
        "Small Mosque",
        "Plaster and carpet. A room that answers gently and lets every word through.",
        VoiceStudioSettings(
            cleanup = CleanupStage(highPassHz = 80.0),
            dynamics = DynamicsStage(
                compressor = DynamicsStage.CompressorSettings(thresholdDb = -19.0, ratio = 2.2, kneeDb = 8.0),
                deEsser = DynamicsStage.DeEsserSettings(thresholdDb = -25.0, ratio = 3.0),
            ),
            refinement = VoiceRefinement(clarity = 0.30, presence = 0.22, air = 0.22, depth = 0.25),
            ambience = AmbienceSettings(
                roomSize = 0.55, decaySeconds = 1.6, preDelayMs = 22.0,
                earlyReflections = 0.6, lateReflections = 1.0, diffusion = 0.72,
                damping = 0.45, warmth = 0.55, brightness = 0.55,
                presence = 0.5, tailSmoothness = 0.8, speechPriority = 0.5,
                width = 1.0, wetDryMix = 0.17,
            ),
        ),
    ),

    LARGE_MOSQUE(
        "Large Mosque",
        "Stone, height and distance. Long, open, and still intelligible.",
        VoiceStudioSettings(
            cleanup = CleanupStage(highPassHz = 75.0),
            dynamics = DynamicsStage(
                compressor = DynamicsStage.CompressorSettings(thresholdDb = -17.0, ratio = 2.0, kneeDb = 9.0),
                deEsser = DynamicsStage.DeEsserSettings(thresholdDb = -24.0, ratio = 3.0),
            ),
            refinement = VoiceRefinement(clarity = 0.28, presence = 0.20, air = 0.30, depth = 0.40),
            ambience = AmbienceSettings(
                roomSize = 0.85, decaySeconds = 2.8, preDelayMs = 38.0,
                earlyReflections = 0.45, lateReflections = 1.0, diffusion = 0.82,
                damping = 0.42, warmth = 0.52, brightness = 0.58,
                presence = 0.58, tailSmoothness = 0.85, speechPriority = 0.6,
                width = 1.0, wetDryMix = 0.22,
            ),
        ),
    ),

    GRAND_HALL(
        "Grand Hall",
        "Stone and height. A tail that answers three seconds later.",
        VoiceStudioSettings(
            cleanup = CleanupStage(highPassHz = 90.0),
            dynamics = DynamicsStage(
                compressor = DynamicsStage.CompressorSettings(thresholdDb = -22.0, ratio = 2.5),
            ),
            refinement = VoiceRefinement(clarity = 0.35, presence = 0.25, depth = 0.40),
            ambience = AmbienceSettings(
                roomSize = 0.92, decaySeconds = 3.2, preDelayMs = 44.0,
                earlyReflections = 0.38, lateReflections = 1.0, diffusion = 0.85,
                damping = 0.45, warmth = 0.5, brightness = 0.54,
                presence = 0.6, tailSmoothness = 0.88, speechPriority = 0.6,
                width = 1.0, wetDryMix = 0.24,
            ),
        ),
    ),

    AUDITORIUM(
        "Auditorium",
        "A full house. Reach and grandeur, without losing the consonants.",
        VoiceStudioSettings(
            cleanup = CleanupStage(highPassHz = 95.0),
            dynamics = DynamicsStage(
                compressor = DynamicsStage.CompressorSettings(thresholdDb = -24.0, ratio = 3.0),
            ),
            refinement = VoiceRefinement(clarity = 0.40, presence = 0.30, depth = 0.30),
            ambience = AmbienceSettings(
                roomSize = 0.8, decaySeconds = 2.0, preDelayMs = 34.0,
                earlyReflections = 0.48, lateReflections = 1.0, diffusion = 0.78,
                damping = 0.48, warmth = 0.5, brightness = 0.55,
                presence = 0.55, tailSmoothness = 0.82, speechPriority = 0.55,
                width = 1.0, wetDryMix = 0.19,
            ),
            loudness = LoudnessStage(target = "SPOKEN_WORD", limiterCeilingDb = -1.5),
        ),
    ),

    PRESTIGE_RECITATION(
        "Prestige Recitation",
        "Clarity, air and dignity. The dynamics of the voice kept intact.",
        VoiceStudioSettings(
            cleanup = CleanupStage(highPassHz = 70.0),
            dynamics = DynamicsStage(
                compressor = DynamicsStage.CompressorSettings(thresholdDb = -18.0, ratio = 2.0, kneeDb = 8.0),
                deEsser = DynamicsStage.DeEsserSettings(thresholdDb = -24.0, ratio = 3.0),
            ),
            refinement = VoiceRefinement(clarity = 0.30, presence = 0.20, air = 0.30, depth = 0.25),
            ambience = AmbienceSettings(
                roomSize = 0.7, decaySeconds = 1.8, preDelayMs = 30.0,
                earlyReflections = 0.52, lateReflections = 1.0, diffusion = 0.76,
                damping = 0.4, warmth = 0.48, brightness = 0.6,
                presence = 0.52, tailSmoothness = 0.84, speechPriority = 0.5,
                width = 1.0, wetDryMix = 0.18,
            ),
        ),
    ),

    MAJESTIC_RECITATION(
        "Majestic Recitation",
        "The great space. Long, wide and unhurried, for a voice that carries it.",
        VoiceStudioSettings(
            cleanup = CleanupStage(highPassHz = 70.0),
            dynamics = DynamicsStage(
                compressor = DynamicsStage.CompressorSettings(thresholdDb = -16.0, ratio = 1.8, kneeDb = 10.0),
                deEsser = DynamicsStage.DeEsserSettings(thresholdDb = -24.0, ratio = 3.0),
            ),
            refinement = VoiceRefinement(clarity = 0.25, presence = 0.20, air = 0.35, depth = 0.50),
            ambience = AmbienceSettings(
                roomSize = 1.0, decaySeconds = 3.6, preDelayMs = 55.0,
                earlyReflections = 0.4, lateReflections = 1.0, diffusion = 0.88,
                damping = 0.44, warmth = 0.5, brightness = 0.58,
                presence = 0.62, tailSmoothness = 0.9, speechPriority = 0.65,
                width = 1.0, wetDryMix = 0.26,
            ),
        ),
    ),

    ROYAL_PRESENCE(
        "Royal Presence",
        "Weight and ceremony. A large room heard from the front of it.",
        VoiceStudioSettings(
            cleanup = CleanupStage(highPassHz = 70.0),
            dynamics = DynamicsStage(
                compressor = DynamicsStage.CompressorSettings(thresholdDb = -19.0, ratio = 2.4, attackMs = 12.0),
                deEsser = DynamicsStage.DeEsserSettings(thresholdDb = -26.0),
            ),
            refinement = VoiceRefinement(warmth = 0.25, body = 0.35, presence = 0.28, air = 0.20, depth = 0.35),
            ambience = AmbienceSettings(
                roomSize = 0.75, decaySeconds = 2.2, preDelayMs = 40.0,
                earlyReflections = 0.55, lateReflections = 1.0, diffusion = 0.8,
                damping = 0.5, warmth = 0.6, brightness = 0.52,
                presence = 0.55, tailSmoothness = 0.85, speechPriority = 0.55,
                width = 1.0, wetDryMix = 0.2,
            ),
        ),
    ),

    CINEMATIC_VOICE(
        "Cinematic Voice",
        "Weight, distance and a dark tail. For narration that has to feel large.",
        VoiceStudioSettings(
            cleanup = CleanupStage(highPassHz = 55.0),
            dynamics = DynamicsStage(
                compressor = DynamicsStage.CompressorSettings(thresholdDb = -22.0, ratio = 3.5, attackMs = 15.0),
                deEsser = DynamicsStage.DeEsserSettings(thresholdDb = -28.0),
            ),
            refinement = VoiceRefinement(warmth = 0.30, richness = 0.25, body = 0.50, presence = 0.20, depth = 0.45),
            ambience = AmbienceSettings(
                roomSize = 0.88, decaySeconds = 2.5, preDelayMs = 42.0,
                earlyReflections = 0.32, lateReflections = 1.0, diffusion = 0.84,
                damping = 0.72, warmth = 0.74, brightness = 0.32,
                presence = 0.58, tailSmoothness = 0.86, speechPriority = 0.55,
                width = 1.0, wetDryMix = 0.21,
            ),
        ),
    ),

    ;

    /** Ready to render or to audition. */
    public fun studio(): VoiceStudio = VoiceStudio(settings)

    /** The same space at a different strength. */
    public fun inMode(mode: AmbienceMode): VoiceStudioSettings = settings.copy(ambienceMode = mode)

    public companion object {
        /**
         * Panel order: the near spaces first, then the far ones.
         *
         * Most recordings want less room than their maker first reaches for, so the list opens
         * where the right answer usually is.
         */
        public val cardOrder: List<VoiceSpacePreset> = listOf(
            PURE_STUDIO, NATURAL_PRESENCE, VOCAL_BOOTH, PODCAST, BROADCAST, WARM_STUDIO,
            LECTURE_HALL, SMALL_MOSQUE, PRESTIGE_RECITATION, AUDITORIUM, ROYAL_PRESENCE,
            CINEMATIC_VOICE, LARGE_MOSQUE, GRAND_HALL, MAJESTIC_RECITATION,
        )

        init {
            check(cardOrder.size == entries.size) { "Every space must appear in the panel exactly once" }
            check(cardOrder.toSet().size == entries.size) { "A space appears twice in the panel" }
        }
    }
}

/**
 * The two one-tap buttons.
 *
 * They exist because most people do not want to make twenty decisions about their voice; they
 * want it to sound right. Each returns ordinary settings that the panel can then open and edit,
 * so a one-tap result is a starting point rather than a black box.
 */
public object OneTap {

    /**
     * ✨ Enhance Voice — the safe improvement.
     *
     * Cleans, evens and clarifies; adds no room and changes no character. This is the one that
     * should never make anything worse, so it does nothing that cannot be undone by ear.
     */
    public fun enhanceVoice(): VoiceStudioSettings = VoiceStudioSettings(
        cleanup = CleanupStage(highPassHz = 80.0, noiseReduction = 1.3, noiseFloorDb = -20.0),
        dynamics = DynamicsStage(
            compressor = DynamicsStage.CompressorSettings(thresholdDb = -20.0, ratio = 2.5, kneeDb = 8.0),
            deEsser = DynamicsStage.DeEsserSettings(thresholdDb = -26.0, ratio = 3.0),
        ),
        refinement = VoiceRefinement(clarity = 0.3, presence = 0.25, warmth = 0.1),
        ambience = AmbienceSettings.NONE,
        loudness = LoudnessStage(target = "SPOKEN_WORD", limiterCeilingDb = -1.0),
    )

    /** 🎙 Studio Voice — the finished production: enhancement plus a treated room. */
    public fun studioVoice(): VoiceStudioSettings =
        VoiceSpacePreset.PODCAST.settings.let { base ->
            base.copy(
                cleanup = base.cleanup.copy(noiseReduction = 1.4, noiseFloorDb = -20.0),
                // Richer than Enhance Voice on purpose: this is the button for narration,
                // recitation and presentation, where a little more body and air is the point.
                refinement = base.refinement.copy(
                    warmth = 0.32,
                    richness = 0.30,
                    air = 0.28,
                    depth = 0.20,
                ),
                ambienceMode = AmbienceMode.STUDIO,
            )
        }
}
