package ai.sautiy.core.dsp

import ai.sautiy.core.analysis.Loudness
import ai.sautiy.core.audio.AudioBuffer
import kotlinx.serialization.Serializable

/**
 * Editorial Bible chapter 10 — the studio chain.
 *
 * A chain is a **recipe, not a rendering**. It is a small serialisable value describing what
 * should happen to the audio; it holds no samples and modifies nothing until [StudioChain.apply]
 * is called on a copy. That is what makes "revert to original" always available (chapter 3.2.8)
 * and what lets the user audition a preset against another without a round trip through disk.
 *
 * The order of the stages is fixed and is not a matter of taste:
 *
 * 1. **High-pass** — remove rumble first, so nothing downstream wastes headroom on energy
 *    nobody will hear.
 * 2. **Noise reduction** — before compression, because a compressor turns up the gaps between
 *    words and would otherwise amplify exactly the noise being removed.
 * 3. **Equalisation** — shape the tone while the dynamics are still natural.
 * 4. **De-essing** — after EQ, since a presence lift is usually what made the sibilance sharp.
 * 5. **Compression** — even out the level of the tone that now exists.
 * 6. **Space** — put the finished voice in a room, not the room in the voice.
 * 7. **Loudness normalisation** — measure the result and set the delivery level.
 * 8. **Limiting** — last, so nothing after it can push a peak back over the ceiling.
 */
@Serializable
public data class StudioChain(
    val highPassHz: Double? = null,
    val noiseReduction: NoiseReductionSettings? = null,
    val equaliser: List<EqBandSettings> = emptyList(),
    val deEsser: DeEsserSettings? = null,
    val compressor: CompressorSettings? = null,
    val space: SpaceSettings? = null,
    val loudnessTargetName: String? = null,
    val limiterCeilingDb: Double? = null,
    val outputGainDb: Double = 0.0,
) {
    @Serializable
    public data class NoiseReductionSettings(val strength: Double = 1.6, val floorDb: Double = -18.0)

    @Serializable
    public data class EqBandSettings(
        val type: String,
        val frequency: Double,
        val gainDb: Double = 0.0,
        val q: Double = 1.0,
    ) {
        internal fun toBand(): EqBand = EqBand(EqBand.Type.valueOf(type), frequency, gainDb, q)
    }

    @Serializable
    public data class DeEsserSettings(
        val frequencyHz: Double = 6_000.0,
        val thresholdDb: Double = -28.0,
        val ratio: Double = 4.0,
    )

    @Serializable
    public data class CompressorSettings(
        val thresholdDb: Double = -18.0,
        val ratio: Double = 3.0,
        val attackMs: Double = 10.0,
        val releaseMs: Double = 120.0,
        val kneeDb: Double = 6.0,
        val makeupDb: Double? = null,
    )

    @Serializable
    public data class SpaceSettings(
        val size: Double = 0.4,
        val damping: Double = 0.6,
        val mix: Double = 0.12,
        val echoDelayMs: Double? = null,
        val echoFeedback: Double = 0.3,
        val echoMix: Double = 0.2,
    )

    /** True when this chain would change nothing, so the UI can show "Original" honestly. */
    public val isTransparent: Boolean
        get() = highPassHz == null && noiseReduction == null && equaliser.isEmpty() &&
            deEsser == null && compressor == null && space == null &&
            loudnessTargetName == null && limiterCeilingDb == null && outputGainDb == 0.0

    /** What the chain did, for the analysis panel — never estimated, always measured. */
    public data class Report(
        val compressorReductionDb: Double = 0.0,
        val deEsserReductionDb: Double = 0.0,
        val limiterReductionDb: Double = 0.0,
        val normalisationGainDb: Double = 0.0,
        val normalisationLimitedByPeak: Boolean = false,
        val inputLufs: Double = Double.NEGATIVE_INFINITY,
        val outputLufs: Double = Double.NEGATIVE_INFINITY,
        val outputTruePeakDb: Double = Double.NEGATIVE_INFINITY,
    )

    /**
     * Applies the chain to a **copy**, leaving [input] untouched (chapter 9.1).
     *
     * @return the processed audio and a measured report of what each stage actually did
     */
    public fun apply(input: AudioBuffer): Pair<AudioBuffer, Report> {
        var audio = input.copy()
        var report = Report(inputLufs = Loudness.integrated(input))

        highPassHz?.let { frequency ->
            for (channel in audio.channels) {
                Biquad.highPass(frequency, audio.sampleRate).process(channel)
            }
        }

        noiseReduction?.let { settings ->
            val reducer = NoiseReduction(strength = settings.strength, floorDb = settings.floorDb)
            audio = reducer.reduce(audio)
        }

        if (equaliser.isNotEmpty()) {
            Equaliser(equaliser.map { it.toBand() }, audio.sampleRate).process(audio)
        }

        deEsser?.let { settings ->
            val reduction = DeEsser(
                frequencyHz = settings.frequencyHz,
                thresholdDb = settings.thresholdDb,
                ratio = settings.ratio,
            ).process(audio)
            report = report.copy(deEsserReductionDb = reduction)
        }

        compressor?.let { settings ->
            val reduction = Compressor(
                thresholdDb = settings.thresholdDb,
                ratio = settings.ratio,
                attackMs = settings.attackMs,
                releaseMs = settings.releaseMs,
                kneeDb = settings.kneeDb,
                makeupDb = settings.makeupDb,
            ).process(audio)
            report = report.copy(compressorReductionDb = reduction)
        }

        space?.let { settings ->
            if (settings.echoDelayMs != null) {
                Echo(
                    delayMs = settings.echoDelayMs,
                    feedback = settings.echoFeedback,
                    mix = settings.echoMix,
                ).process(audio)
            }
            if (settings.mix > 0.0) {
                Reverb(size = settings.size, damping = settings.damping, mix = settings.mix).process(audio)
            }
        }

        loudnessTargetName?.let { name ->
            val target = Loudness.Target.entries.firstOrNull { it.name == name }
            if (target != null) {
                val plan = Loudness.planNormalisation(audio, target)
                audio.applyGain(Math.pow(10.0, plan.gainDb / 20.0).toFloat())
                report = report.copy(
                    normalisationGainDb = plan.gainDb,
                    normalisationLimitedByPeak = plan.limitedByTruePeak,
                )
            }
        }

        if (outputGainDb != 0.0) {
            audio.applyGain(Math.pow(10.0, outputGainDb / 20.0).toFloat())
        }

        limiterCeilingDb?.let { ceiling ->
            val reduction = Limiter(ceilingDb = ceiling).process(audio)
            report = report.copy(limiterReductionDb = reduction)
        }

        return audio to report.copy(
            outputLufs = Loudness.integrated(audio),
            outputTruePeakDb = Loudness.truePeakDb(audio),
        )
    }
}

/**
 * The preset cards of chapter 10.
 *
 * Nine presets, each named for a *situation* rather than for a process. A user knows whether
 * they recorded a lecture; they do not know whether they want 3:1 at −18 dB with a 6 dB knee.
 * Every preset expands to reveal exactly those numbers, because chapter 1.4 principle 6 says a
 * professional must never be limited and principle 5 says nothing may be hidden.
 */
public enum class StudioPreset(
    public val displayName: String,
    public val summary: String,
    public val chain: StudioChain,
) {
    NATURAL(
        "Natural",
        "Gentle cleaning only. Nothing you can hear working.",
        StudioChain(
            highPassHz = 70.0,
            limiterCeilingDb = -1.0,
        ),
    ),

    STUDIO(
        "Studio",
        "A clean, close, controlled voice.",
        StudioChain(
            highPassHz = 80.0,
            noiseReduction = StudioChain.NoiseReductionSettings(strength = 1.4),
            equaliser = listOf(
                StudioChain.EqBandSettings("PEAKING", 250.0, -2.0, 1.0),
                StudioChain.EqBandSettings("PEAKING", 3_000.0, 2.0, 0.9),
                StudioChain.EqBandSettings("HIGH_SHELF", 9_000.0, 1.5),
            ),
            deEsser = StudioChain.DeEsserSettings(thresholdDb = -26.0),
            compressor = StudioChain.CompressorSettings(thresholdDb = -20.0, ratio = 3.0),
            limiterCeilingDb = -1.0,
        ),
    ),

    BROADCAST(
        "Broadcast",
        "Dense and even, to the −23 LUFS delivery standard.",
        StudioChain(
            highPassHz = 90.0,
            noiseReduction = StudioChain.NoiseReductionSettings(strength = 1.6),
            equaliser = listOf(
                StudioChain.EqBandSettings("PEAKING", 200.0, -3.0, 1.2),
                StudioChain.EqBandSettings("PEAKING", 2_500.0, 2.5, 1.0),
            ),
            deEsser = StudioChain.DeEsserSettings(thresholdDb = -30.0, ratio = 5.0),
            compressor = StudioChain.CompressorSettings(thresholdDb = -24.0, ratio = 4.0, attackMs = 5.0, releaseMs = 90.0),
            loudnessTargetName = "BROADCAST",
            limiterCeilingDb = -1.0,
        ),
    ),

    PODCAST(
        "Podcast",
        "Warm and consistent, at the −16 LUFS podcast standard.",
        StudioChain(
            highPassHz = 80.0,
            noiseReduction = StudioChain.NoiseReductionSettings(strength = 1.5),
            equaliser = listOf(
                StudioChain.EqBandSettings("LOW_SHELF", 160.0, 1.5),
                StudioChain.EqBandSettings("PEAKING", 400.0, -2.0, 1.1),
                StudioChain.EqBandSettings("PEAKING", 4_000.0, 2.0, 0.8),
            ),
            deEsser = StudioChain.DeEsserSettings(),
            compressor = StudioChain.CompressorSettings(thresholdDb = -22.0, ratio = 3.5),
            loudnessTargetName = "PODCAST",
            limiterCeilingDb = -1.0,
        ),
    ),

    LECTURE(
        "Lecture",
        "For a room, a lapel microphone and ninety minutes.",
        StudioChain(
            highPassHz = 110.0,
            noiseReduction = StudioChain.NoiseReductionSettings(strength = 1.9, floorDb = -16.0),
            equaliser = listOf(
                StudioChain.EqBandSettings("PEAKING", 300.0, -3.5, 1.0),
                StudioChain.EqBandSettings("PEAKING", 2_800.0, 3.0, 0.9),
            ),
            compressor = StudioChain.CompressorSettings(thresholdDb = -26.0, ratio = 4.0, releaseMs = 200.0),
            loudnessTargetName = "SPOKEN_WORD",
            limiterCeilingDb = -1.5,
        ),
    ),

    RECITATION(
        "Recitation",
        "Clarity and air, with the dynamics of the voice kept intact.",
        StudioChain(
            highPassHz = 70.0,
            noiseReduction = StudioChain.NoiseReductionSettings(strength = 1.3, floorDb = -20.0),
            equaliser = listOf(
                StudioChain.EqBandSettings("PEAKING", 220.0, -1.5, 1.0),
                StudioChain.EqBandSettings("PEAKING", 3_500.0, 1.5, 0.8),
                StudioChain.EqBandSettings("HIGH_SHELF", 10_000.0, 1.0),
            ),
            deEsser = StudioChain.DeEsserSettings(thresholdDb = -24.0, ratio = 3.0),
            // Deliberately light: recitation lives on its dynamics, and flattening them is the
            // one thing a reciter will never forgive.
            compressor = StudioChain.CompressorSettings(thresholdDb = -18.0, ratio = 2.0, kneeDb = 8.0),
            space = StudioChain.SpaceSettings(size = 0.35, damping = 0.7, mix = 0.08),
            limiterCeilingDb = -1.0,
        ),
    ),

    WARM(
        "Warm",
        "Fuller and softer. For a thin or distant recording.",
        StudioChain(
            highPassHz = 60.0,
            equaliser = listOf(
                StudioChain.EqBandSettings("LOW_SHELF", 200.0, 3.0),
                StudioChain.EqBandSettings("PEAKING", 5_000.0, -2.0, 0.9),
                StudioChain.EqBandSettings("HIGH_SHELF", 11_000.0, -2.0),
            ),
            compressor = StudioChain.CompressorSettings(thresholdDb = -20.0, ratio = 2.5),
            limiterCeilingDb = -1.0,
        ),
    ),

    DEEP(
        "Deep",
        "Weight and authority, without losing words.",
        StudioChain(
            highPassHz = 50.0,
            equaliser = listOf(
                StudioChain.EqBandSettings("LOW_SHELF", 140.0, 4.0),
                StudioChain.EqBandSettings("PEAKING", 500.0, -2.5, 1.2),
                StudioChain.EqBandSettings("PEAKING", 3_000.0, 1.5, 0.9),
            ),
            deEsser = StudioChain.DeEsserSettings(thresholdDb = -28.0),
            compressor = StudioChain.CompressorSettings(thresholdDb = -22.0, ratio = 3.5, attackMs = 15.0),
            limiterCeilingDb = -1.0,
        ),
    ),

    BRIGHT(
        "Bright",
        "Forward and articulate. For a dull room.",
        StudioChain(
            highPassHz = 90.0,
            equaliser = listOf(
                StudioChain.EqBandSettings("PEAKING", 300.0, -2.5, 1.0),
                StudioChain.EqBandSettings("PEAKING", 4_500.0, 3.0, 0.8),
                StudioChain.EqBandSettings("HIGH_SHELF", 9_000.0, 3.0),
            ),
            // Brightening lifts sibilance by construction, so the de-esser is not optional here.
            deEsser = StudioChain.DeEsserSettings(thresholdDb = -30.0, ratio = 5.0),
            compressor = StudioChain.CompressorSettings(thresholdDb = -20.0, ratio = 3.0),
            limiterCeilingDb = -1.0,
        ),
    ),
    ;

    public companion object {
        /** The card order in the Studio panel. Natural first, because most recordings need least. */
        public val cardOrder: List<StudioPreset> = listOf(
            NATURAL, STUDIO, PODCAST, LECTURE, RECITATION, BROADCAST, WARM, DEEP, BRIGHT,
        )
    }
}
