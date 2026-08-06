package ai.sautiy.core.dsp

import ai.sautiy.core.analysis.Loudness
import ai.sautiy.core.audio.AudioBuffer
import kotlin.math.abs
import kotlin.math.log10
import kotlin.math.sqrt
import kotlinx.serialization.Serializable

/**
 * Turning what a listener says into what the engine does.
 *
 * This exists because the tuning loop for a voice product is not a graph. Someone listens, and
 * says "too bright" or "too much room" — and the distance between that sentence and a parameter
 * change is where most audio products lose their tuning cycle. Either the listener has to learn
 * the parameters, or an engineer has to guess what they meant, and both are slow enough that the
 * tuning stops happening.
 *
 * So the vocabulary is fixed, small, and maps to a **defined** adjustment. A listener taps a
 * word; the preset moves; they listen again. No engineering knowledge is required at either end,
 * and the mapping is written down here rather than living in someone's head.
 *
 * Each note moves several parameters at once, because the words describe *perceptions* and
 * perceptions rarely have one cause. "Muddy" is low-mid build-up in the voice *and* low-frequency
 * energy in the room; moving only one of them leaves the listener saying "muddy" again.
 */
public enum class ListenerNote(
    public val displayName: String,
    public val summary: String,
) {
    TOO_BRIGHT("Too bright", "Sharp, thin, or tiring in the upper range."),
    TOO_DARK("Too dark", "Dull or closed in. Not enough life up top."),
    TOO_MUCH_AMBIENCE("Too much room", "The space is drawing attention to itself."),
    TOO_LITTLE_AMBIENCE("Too little room", "Flat and close. Nothing around the voice."),
    TOO_HARSH("Too harsh", "Aggressive or edgy, especially on consonants."),
    TOO_MUDDY("Too muddy", "Thick and unclear. Words run together."),
    EXCELLENT("Excellent", "Right as it is."),
    ;

    /**
     * Applies this note to a voice, one step at a time.
     *
     * Steps are deliberately small. A listener who says "too bright" means "less bright than
     * this", not "dark" — a large correction overshoots and produces a second round of notes in
     * the opposite direction, which is how tuning cycles turn into oscillation. Repeating a note
     * repeats the step, so a listener who means "much less bright" simply says it twice.
     */
    public fun applyTo(settings: VoiceStudioSettings): VoiceStudioSettings = when (this) {
        EXCELLENT -> settings

        // Brightness is carried by the voice's air and brightness controls *and* by the room's
        // top end. A recording called bright is usually all three.
        TOO_BRIGHT -> settings.withRefinement { it.nudge(air = -STEP, brightness = -STEP) }
            .withAmbience { it.copy(brightness = (it.brightness - STEP / 2).coerceIn(0.0, 1.0)) }

        TOO_DARK -> settings.withRefinement { it.nudge(air = STEP, brightness = STEP) }
            .withAmbience { it.copy(brightness = (it.brightness + STEP / 2).coerceIn(0.0, 1.0)) }

        // Less room, and less need to protect against it.
        TOO_MUCH_AMBIENCE -> settings.withAmbience {
            it.copy(wetDryMix = (it.wetDryMix * 0.72).coerceIn(0.0, 1.0))
        }

        TOO_LITTLE_AMBIENCE -> settings.withAmbience {
            // From a bypassed space this has to create one, or the note does nothing and the
            // listener is left tapping a control that appears broken.
            if (it.isBypassed) {
                AmbienceSettings(wetDryMix = 0.08, roomSize = 0.3, decaySeconds = 0.7, preDelayMs = 14.0)
            } else {
                it.copy(wetDryMix = (it.wetDryMix * 1.35).coerceIn(0.0, 1.0))
            }
        }

        // Harshness lives in the 2–5 kHz presence range and in sibilance. Pulling presence back
        // is not enough on its own if the de-esser is letting consonants through.
        TOO_HARSH -> settings
            .withRefinement { it.nudge(presence = -STEP, clarity = -STEP / 2) }
            .let { current ->
                val deEsser = current.dynamics.deEsser
                current.copy(
                    dynamics = current.dynamics.copy(
                        deEsser = deEsser?.copy(
                            thresholdDb = (deEsser.thresholdDb - 2.0).coerceAtLeast(-48.0),
                        ) ?: DynamicsStage.DeEsserSettings(thresholdDb = -28.0, ratio = 3.5),
                    ),
                )
            }

        // Mud is low-mid build-up in the voice and low energy in the room, so both move. The
        // room's own presence control comes up too: taking the room out of the consonant band is
        // what lets words separate again.
        TOO_MUDDY -> settings
            .withRefinement { it.nudge(warmth = -STEP, richness = -STEP, clarity = STEP) }
            .withAmbience {
                it.copy(
                    presence = (it.presence + STEP).coerceIn(0.0, 1.0),
                    speechPriority = (it.speechPriority + STEP).coerceIn(0.0, 1.0),
                )
            }
    }

    public companion object {
        /**
         * One step of correction.
         *
         * 0.18 of a control's full travel: clearly audible on a direct comparison, small enough
         * that a listener who tapped the wrong word can undo it by tapping the opposite one.
         */
        public const val STEP: Double = 0.18

        /** In the order a listener is most likely to reach for them. */
        public val order: List<ListenerNote> = listOf(
            EXCELLENT, TOO_BRIGHT, TOO_DARK, TOO_HARSH, TOO_MUDDY,
            TOO_MUCH_AMBIENCE, TOO_LITTLE_AMBIENCE,
        )
    }
}

private fun VoiceStudioSettings.withRefinement(
    change: (VoiceRefinement) -> VoiceRefinement,
): VoiceStudioSettings = copy(refinement = change(refinement))

private fun VoiceStudioSettings.withAmbience(
    change: (AmbienceSettings) -> AmbienceSettings,
): VoiceStudioSettings = copy(ambience = change(ambience))

/** Moves refinement controls by a delta, clamped, so a note can never produce an illegal value. */
private fun VoiceRefinement.nudge(
    clarity: Double = 0.0,
    warmth: Double = 0.0,
    richness: Double = 0.0,
    presence: Double = 0.0,
    body: Double = 0.0,
    air: Double = 0.0,
    brightness: Double = 0.0,
): VoiceRefinement = copy(
    clarity = (this.clarity + clarity).coerceIn(-1.0, 1.0),
    warmth = (this.warmth + warmth).coerceIn(-1.0, 1.0),
    richness = (this.richness + richness).coerceIn(-1.0, 1.0),
    presence = (this.presence + presence).coerceIn(-1.0, 1.0),
    body = (this.body + body).coerceIn(-1.0, 1.0),
    air = (this.air + air).coerceIn(-1.0, 1.0),
    brightness = (this.brightness + brightness).coerceIn(-1.0, 1.0),
)

/**
 * What several listeners said about one preset.
 *
 * A single listener's note is an opinion; the same note from four listeners is a defect. Keeping
 * them separate matters, because acting on one person's "too bright" is how a product ends up
 * tuned to one pair of ears — which is the failure mode this type exists to prevent.
 */
@Serializable
public data class ListeningPanel(
    /** How many listeners gave each note. */
    val notes: Map<String, Int> = emptyMap(),
) {
    public fun record(note: ListenerNote): ListeningPanel =
        copy(notes = notes + (note.name to (notes[note.name] ?: 0) + 1))

    public val listeners: Int get() = notes.values.sum()

    /** Notes at least this share of listeners agreed on. Below that it is one person's taste. */
    public fun consensus(threshold: Double = 0.5): List<ListenerNote> {
        if (listeners == 0) return emptyList()
        return ListenerNote.entries
            .filter { (notes[it.name] ?: 0).toDouble() / listeners >= threshold }
            .filter { it != ListenerNote.EXCELLENT }
    }

    /** True when most of the panel called it right as it is. */
    public fun isAccepted(threshold: Double = 0.5): Boolean =
        listeners > 0 && (notes[ListenerNote.EXCELLENT.name] ?: 0).toDouble() / listeners >= threshold

    /**
     * Applies everything the panel agreed on.
     *
     * Only consensus notes are applied, and each once, so a preset moves by the amount the panel
     * agreed rather than by the number of people who happened to be in the room.
     */
    public fun applyTo(settings: VoiceStudioSettings, threshold: Double = 0.5): VoiceStudioSettings =
        consensus(threshold).fold(settings) { current, note -> note.applyTo(current) }
}

/**
 * What a recording is actually like, in the few terms that decide how to treat it.
 *
 * Deliberately small. Every field here changes a decision in [VoiceAdvisor]; anything that would
 * not change a decision is not measured, because a number nobody acts on is a number that gets
 * trusted anyway.
 */
public data class VoiceAnalysis(
    val integratedLufs: Double,
    val truePeakDb: Double,
    val loudnessRangeLu: Double,
    val noiseFloorDb: Double,
    /** Energy below 250 Hz, relative to the whole, in dB. High is a thick or rumbling recording. */
    val lowTiltDb: Double,
    /** Energy from 2 to 6 kHz, relative to the whole, in dB. Low is a dull or distant recording. */
    val presenceTiltDb: Double,
    /** Energy above 6 kHz relative to the presence band. High is a sibilant or hissy recording. */
    val sibilanceTiltDb: Double,
) {
    /** Signal above the room. Below about 20 dB, noise reduction is doing real work. */
    public val signalToNoiseDb: Double get() = integratedLufs - noiseFloorDb

    public companion object {

        /** Measures a recording. Cheap enough to run on the whole take before enhancing it. */
        public fun of(buffer: AudioBuffer): VoiceAnalysis {
            val measurement = Loudness.measure(buffer)
            val profile = NoiseReduction().learnFromQuietest(buffer)

            val bands = bandEnergies(buffer)
            val total = bands.values.sum().coerceAtLeast(1e-20)
            fun tilt(band: String) = 10.0 * log10((bands.getValue(band) / total).coerceAtLeast(1e-12))

            return VoiceAnalysis(
                integratedLufs = measurement.integratedLufs,
                truePeakDb = measurement.truePeakDb,
                loudnessRangeLu = measurement.loudnessRangeLu,
                noiseFloorDb = profile.levelDb,
                lowTiltDb = tilt("low"),
                presenceTiltDb = tilt("presence"),
                sibilanceTiltDb = 10.0 * log10(
                    (bands.getValue("air") / bands.getValue("presence").coerceAtLeast(1e-20))
                        .coerceAtLeast(1e-12),
                ),
            )
        }

        /**
         * Band energies by direct filtering rather than by FFT.
         *
         * Four band-passes over the whole signal cost less than transforming it and are easier to
         * reason about: the bands are exactly the ones the decisions below refer to, with no
         * window, no bin edges and no leakage to explain away.
         */
        private fun bandEnergies(buffer: AudioBuffer): Map<String, Double> {
            val rate = buffer.sampleRate
            val mono = if (buffer.channelCount == 1) buffer else buffer.toMono()
            val samples = mono.channels[0]

            fun energyThrough(build: () -> List<Biquad>): Double {
                val chain = build()
                var energy = 0.0
                for (sample in samples) {
                    var value = sample.toDouble()
                    for (filter in chain) value = filter.processSample(value)
                    energy += value * value
                }
                return energy
            }

            // Two sections per edge, so each band's skirts are steep enough that "below 250 Hz"
            // means below 250 Hz rather than mostly below it.
            return mapOf(
                "low" to energyThrough {
                    listOf(Biquad.lowPass(250.0, rate), Biquad.lowPass(250.0, rate))
                },
                "mid" to energyThrough {
                    listOf(
                        Biquad.highPass(250.0, rate), Biquad.highPass(250.0, rate),
                        Biquad.lowPass(2_000.0, rate), Biquad.lowPass(2_000.0, rate),
                    )
                },
                "presence" to energyThrough {
                    listOf(
                        Biquad.highPass(2_000.0, rate), Biquad.highPass(2_000.0, rate),
                        Biquad.lowPass(minOf(6_000.0, rate * 0.45), rate),
                        Biquad.lowPass(minOf(6_000.0, rate * 0.45), rate),
                    )
                },
                "air" to energyThrough {
                    val edge = minOf(6_000.0, rate * 0.4)
                    listOf(Biquad.highPass(edge, rate), Biquad.highPass(edge, rate))
                },
            )
        }
    }
}

/**
 * Chooses the processing, so the user does not have to.
 *
 * "Enhance Voice" cannot be one fixed chain. A quiet, noisy phone recording of a lecture and a
 * close, clean recording of a narration need almost opposite treatment, and a single preset that
 * suits both suits neither. This looks at what the recording actually is and decides — which is
 * what the user was implicitly asking for when they pressed one button instead of opening a panel.
 *
 * Every rule below is stated as a threshold with a reason. None of them is a taste judgement, and
 * none of them requires the user to know what any of it means.
 */
public object VoiceAdvisor {

    /**
     * The balanced enhancement: cleaner, more even, clearer, and in no particular room.
     *
     * Nothing here is allowed to make a recording worse. Where the analysis is ambiguous the rule
     * is to do less, because a listener forgives an under-processed recording and does not forgive
     * one that has been mangled.
     */
    public fun enhance(analysis: VoiceAnalysis): VoiceStudioSettings {
        // Rumble and handling noise sit under the voice. A recording that is already thin does
        // not need as much taken out of it as one that is thick.
        val highPass = if (analysis.lowTiltDb > -6.0) 95.0 else 75.0

        // Noise reduction only where there is noise to reduce. Spectral subtraction always costs
        // something, so on a clean recording the honest amount is none.
        val noiseReduction = when {
            analysis.signalToNoiseDb < 14.0 -> 1.8
            analysis.signalToNoiseDb < 22.0 -> 1.3
            else -> null
        }

        // A wide loudness range is a recording that moves around and needs evening out; a narrow
        // one has already been compressed, by the room or by whatever recorded it, and squeezing
        // it again is what makes speech sound lifeless.
        val ratio = when {
            analysis.loudnessRangeLu > 12.0 -> 3.5
            analysis.loudnessRangeLu > 7.0 -> 2.6
            else -> 2.0
        }

        // Dull recordings get presence; already-forward ones do not, or they turn harsh.
        val presence = when {
            analysis.presenceTiltDb < -16.0 -> 0.45
            analysis.presenceTiltDb < -12.0 -> 0.28
            else -> 0.12
        }

        // Sibilant material gets a de-esser; material with no sibilance gets none rather than a
        // stage that can only remove something that is not there.
        val deEsser = when {
            analysis.sibilanceTiltDb > -8.0 -> DynamicsStage.DeEsserSettings(thresholdDb = -30.0, ratio = 4.5)
            analysis.sibilanceTiltDb > -14.0 -> DynamicsStage.DeEsserSettings(thresholdDb = -26.0, ratio = 3.0)
            else -> null
        }

        return VoiceStudioSettings(
            cleanup = CleanupStage(
                highPassHz = highPass,
                noiseReduction = noiseReduction,
                noiseFloorDb = -20.0,
            ),
            dynamics = DynamicsStage(
                compressor = DynamicsStage.CompressorSettings(
                    thresholdDb = -20.0,
                    ratio = ratio,
                    kneeDb = 8.0,
                ),
                deEsser = deEsser,
            ),
            refinement = VoiceRefinement(
                clarity = 0.28,
                presence = presence,
                // A thin recording is given body; a thick one is not given more.
                body = if (analysis.lowTiltDb < -12.0) 0.25 else 0.0,
                warmth = if (analysis.lowTiltDb < -12.0) 0.15 else 0.0,
            ),
            // Enhance Voice adds no room. Someone who wanted a room would have chosen one, and a
            // room applied without being asked for is the single change most likely to be wrong.
            ambience = AmbienceSettings.NONE,
            loudness = LoudnessStage(target = "SPOKEN_WORD", limiterCeilingDb = -1.0),
        )
    }

    /**
     * The richer chain, for narration, recitation and presentation.
     *
     * Everything [enhance] does, plus body, air and a treated room — the difference between "this
     * recording is fixed" and "this recording sounds produced".
     */
    public fun studio(analysis: VoiceAnalysis): VoiceStudioSettings {
        val base = enhance(analysis)
        return base.copy(
            refinement = base.refinement.copy(
                warmth = (base.refinement.warmth + 0.22).coerceIn(-1.0, 1.0),
                richness = 0.26,
                air = 0.24,
                depth = 0.18,
            ),
            ambience = VoiceSpacePreset.PODCAST.settings.ambience,
            character = VoiceCharacter(VoiceCharacter.REFINED),
            loudness = LoudnessStage(target = "PODCAST", limiterCeilingDb = -1.0),
        )
    }

    /**
     * Voice Match: suggests a chain that moves a recording *towards* a reference.
     *
     * This is a similarity aid and is documented as one everywhere it is offered. It compares
     * broad characteristics — level, tonal balance and how much the level moves — and closes part
     * of the gap. It cannot reproduce someone else's sound, and saying otherwise would be a
     * promise the physics does not support: the reference was made by a different voice in a
     * different room with a different microphone, and none of those three is recoverable from a
     * mix. What it can honestly do is stop a user having to guess which controls to reach for.
     */
    public fun matchTo(source: VoiceAnalysis, reference: VoiceAnalysis): VoiceStudioSettings {
        val base = enhance(source)

        // Each difference is halved. Matching a tonal balance exactly means inheriting the
        // reference's microphone and room as well as its intent, and overshooting a target that
        // was never reachable sounds worse than sitting sensibly short of it.
        fun close(differenceDb: Double, perDb: Double) =
            (differenceDb * 0.5 * perDb).coerceIn(-0.6, 0.6)

        val brighter = reference.presenceTiltDb - source.presenceTiltDb
        val airier = reference.sibilanceTiltDb - source.sibilanceTiltDb
        val fuller = reference.lowTiltDb - source.lowTiltDb

        return base.copy(
            refinement = base.refinement.copy(
                presence = (base.refinement.presence + close(brighter, 0.08)).coerceIn(-1.0, 1.0),
                air = (base.refinement.air + close(airier, 0.06)).coerceIn(-1.0, 1.0),
                body = (base.refinement.body + close(fuller, 0.08)).coerceIn(-1.0, 1.0),
            ),
            dynamics = base.dynamics.copy(
                compressor = base.dynamics.compressor?.copy(
                    // A reference that moves less than the source was compressed harder.
                    ratio = when {
                        reference.loudnessRangeLu < source.loudnessRangeLu - 4.0 -> 4.0
                        reference.loudnessRangeLu < source.loudnessRangeLu - 1.5 -> 3.0
                        else -> 2.2
                    },
                ),
            ),
            // Level is the one characteristic that *can* be matched exactly, so it is.
            loudness = LoudnessStage(
                target = Loudness.Target.entries
                    .minBy { abs(it.lufs - reference.integratedLufs) }
                    .name,
                limiterCeilingDb = -1.0,
            ),
        )
    }

    /**
     * What the match will and will not do, for the interface to show before it is applied.
     *
     * A feature called "match" invites a expectation it cannot meet. Saying so at the moment of
     * use is the difference between a useful aid and a broken promise.
     */
    public fun matchExplanation(source: VoiceAnalysis, reference: VoiceAnalysis): List<String> =
        buildList {
            val level = reference.integratedLufs - source.integratedLufs
            if (abs(level) > 1.0) {
                add("Level: ${if (level > 0) "raising" else "lowering"} by ${abs(level).toInt()} LU")
            }
            val brighter = reference.presenceTiltDb - source.presenceTiltDb
            if (abs(brighter) > 1.5) {
                add("Presence: ${if (brighter > 0) "more forward" else "further back"}")
            }
            val airier = reference.sibilanceTiltDb - source.sibilanceTiltDb
            if (abs(airier) > 1.5) add("Air: ${if (airier > 0) "more open" else "softer"}")
            val fuller = reference.lowTiltDb - source.lowTiltDb
            if (abs(fuller) > 1.5) add("Body: ${if (fuller > 0) "fuller" else "leaner"}")
            if (reference.loudnessRangeLu < source.loudnessRangeLu - 1.5) add("Dynamics: more even")
            add("The reference's voice, room and microphone cannot be copied — only approached.")
        }
}

/**
 * What the user is trying to achieve. The only names the interface shows.
 *
 * There is exactly one naming system on screen, and it names *results*. A person who sees both
 * "Prestige Recitation" and "Large Mosque" has to work out which of the two to choose, and the
 * honest answer — that one is the outcome and the other is how it is achieved — is not something
 * they should have to learn. So the acoustic spaces stay underneath as the implementation, and
 * appear only in engineering documentation and in Advanced Mode's "Based on" line.
 *
 * Ten. Not because ten is a round number, but because one preset that is unmistakably right is
 * worth more than a list nobody can tell apart, and a list this length can be auditioned end to
 * end in under a minute.
 */
public enum class VoiceOutcome(
    public val displayName: String,
    public val purpose: String,
    public val group: VoiceOutcomeGroup,
    /**
     * The acoustic profile underneath.
     *
     * Shown to the user only in Advanced Mode, as "Based on: …". It is transparency for someone
     * who wants it, not a second thing for everyone else to choose between.
     */
    public val basedOn: VoiceSpacePreset,
    public val character: Double = VoiceCharacter.REFINED,
) {
    CLEAR_SPEECH(
        "Clear Speech",
        "Every word plain. For notes, interviews, meetings and lectures.",
        VoiceOutcomeGroup.SPEECH,
        VoiceSpacePreset.PURE_STUDIO,
        VoiceCharacter.NATURAL,
    ),
    WARM_VOICE(
        "Warm Voice",
        "Softer and fuller. For a thin, harsh or tiring recording.",
        VoiceOutcomeGroup.SPEECH,
        VoiceSpacePreset.WARM_STUDIO,
    ),
    RICH_NARRATION(
        "Rich Narration",
        "Weight and polish. For audiobooks, voice-over and presentation.",
        VoiceOutcomeGroup.SPEECH,
        VoiceSpacePreset.ROYAL_PRESENCE,
        VoiceCharacter.RICH,
    ),

    STUDIO(
        "Studio",
        "Clean and close, as though recorded in a treated room.",
        VoiceOutcomeGroup.PROFESSIONAL,
        VoiceSpacePreset.VOCAL_BOOTH,
    ),
    BROADCAST(
        "Broadcast",
        "Tight and even, delivered to the broadcast standard.",
        VoiceOutcomeGroup.PROFESSIONAL,
        VoiceSpacePreset.BROADCAST,
    ),
    PODCAST(
        "Podcast",
        "Companionable and consistent, at the podcast standard.",
        VoiceOutcomeGroup.PROFESSIONAL,
        VoiceSpacePreset.PODCAST,
    ),
    LECTURE(
        "Lecture",
        "Carries across a room, and every word still lands.",
        VoiceOutcomeGroup.PROFESSIONAL,
        VoiceSpacePreset.LECTURE_HALL,
    ),

    PRESTIGE_RECITATION(
        "Prestige Recitation",
        "Clarity, air and dignity, with the dynamics of the voice intact.",
        VoiceOutcomeGroup.RECITATION,
        VoiceSpacePreset.PRESTIGE_RECITATION,
        VoiceCharacter.RICH,
    ),

    GRAND_SPACE(
        "Grand Space",
        "A large room you can hear. For recitation and performance.",
        VoiceOutcomeGroup.SPACE,
        VoiceSpacePreset.GRAND_HALL,
        VoiceCharacter.GRAND,
    ),
    IMMERSIVE(
        "Immersive",
        "The largest space, deliberately. For when the room is the point.",
        VoiceOutcomeGroup.SPACE,
        VoiceSpacePreset.MAJESTIC_RECITATION,
        VoiceCharacter.IMMERSIVE,
    ),
    ;

    public val settings: VoiceStudioSettings
        get() = basedOn.settings.copy(character = VoiceCharacter(character))

    public fun studio(): VoiceStudio = VoiceStudio(settings)

    /** The transparency line for Advanced Mode. Never shown otherwise. */
    public val advancedDetail: String get() = "Based on: ${basedOn.displayName}"

    public companion object {
        /** Panel order: grouped, everyday first. */
        public val cardOrder: List<VoiceOutcome> = entries.sortedBy { it.group.ordinal }

        init {
            check(entries.size == 10) { "Ten outcomes. One that is right beats a list nobody can tell apart." }
            check(entries.map { it.displayName }.toSet().size == entries.size) { "Two outcomes share a name" }
        }
    }
}

/**
 * The four things people are trying to do.
 *
 * Headings, not a second level of choice: a person scans to the group that describes their
 * situation and reads three names, rather than reading ten and deciding.
 */
public enum class VoiceOutcomeGroup(public val displayName: String) {
    SPEECH("Speech"),
    PROFESSIONAL("Professional"),
    RECITATION("Recitation"),
    SPACE("Space"),
}

/** Root-mean-square, for the analysis above. Kept here so the file is self-contained. */
internal fun rmsOf(samples: FloatArray): Double {
    var energy = 0.0
    for (sample in samples) energy += sample.toDouble() * sample
    return sqrt(energy / samples.size.coerceAtLeast(1))
}
