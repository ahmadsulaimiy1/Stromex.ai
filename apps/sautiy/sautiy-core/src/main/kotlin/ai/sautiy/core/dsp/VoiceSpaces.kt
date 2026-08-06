package ai.sautiy.core.dsp

/**
 * The second layer: an acoustic environment, chosen deliberately.
 *
 * Layer one is what you want to achieve — Clear Speech, Rich Narration. Most people never leave
 * it, and they should not have to. This layer is for someone who has decided they want a
 * particular *place*, which for a reciter or a lecturer is often the whole point.
 *
 * These are **not presets.** A preset is a complete voice; an environment is only the room. It
 * replaces the room underneath the chosen outcome and leaves the outcome's cleanup, dynamics and
 * tone exactly as they were — so "Rich Narration in a Large Hall" is still Rich Narration, and
 * changing the room does not quietly change the voice.
 */
public enum class AcousticSpace(
    public val displayName: String,
    public val summary: String,
    internal val profile: AmbienceSettings,
) {
    VOCAL_BOOTH(
        "Vocal Booth",
        "A treated booth. Close and controlled, with just enough air to breathe.",
        AmbienceSettings(
            roomSize = 0.10, decaySeconds = 0.30, preDelayMs = 6.0,
            earlyReflections = 0.85, lateReflections = 0.55, diffusion = 0.45,
            damping = 0.60, warmth = 0.55, brightness = 0.50,
            presence = 0.30, tailSmoothness = 0.55, speechPriority = 0.35,
            wetDryMix = 0.07,
        ),
    ),
    BROADCAST_BOOTH(
        "Broadcast Booth",
        "Dead and tight, the way a news studio is built. Nothing between you and the microphone.",
        AmbienceSettings(
            roomSize = 0.14, decaySeconds = 0.36, preDelayMs = 8.0,
            earlyReflections = 0.78, lateReflections = 0.45, diffusion = 0.50,
            damping = 0.66, warmth = 0.52, brightness = 0.52,
            presence = 0.42, tailSmoothness = 0.58, speechPriority = 0.45,
            wetDryMix = 0.05,
        ),
    ),
    SMALL_HALL(
        "Small Hall",
        "A room with wooden surfaces and a modest ceiling. Warm, and never in the way.",
        AmbienceSettings(
            roomSize = 0.45, decaySeconds = 0.95, preDelayMs = 18.0,
            earlyReflections = 0.62, lateReflections = 0.90, diffusion = 0.64,
            damping = 0.55, warmth = 0.62, brightness = 0.46,
            presence = 0.45, tailSmoothness = 0.74, speechPriority = 0.45,
            wetDryMix = 0.13,
        ),
    ),
    LARGE_HALL(
        "Large Hall",
        "Stone and height. A long answer that arrives a beat after you stop.",
        AmbienceSettings(
            roomSize = 0.90, decaySeconds = 2.90, preDelayMs = 42.0,
            earlyReflections = 0.40, lateReflections = 1.0, diffusion = 0.84,
            damping = 0.45, warmth = 0.50, brightness = 0.54,
            presence = 0.58, tailSmoothness = 0.88, speechPriority = 0.58,
            wetDryMix = 0.22,
        ),
    ),
    AUDITORIUM(
        "Auditorium",
        "A full house. Reach and grandeur, with the consonants still landing.",
        AmbienceSettings(
            roomSize = 0.80, decaySeconds = 1.95, preDelayMs = 34.0,
            earlyReflections = 0.48, lateReflections = 1.0, diffusion = 0.78,
            damping = 0.48, warmth = 0.50, brightness = 0.55,
            presence = 0.55, tailSmoothness = 0.82, speechPriority = 0.55,
            wetDryMix = 0.18,
        ),
    ),
    SMALL_MOSQUE(
        "Small Mosque",
        "Plaster and carpet. A room that answers gently and lets every word through.",
        AmbienceSettings(
            roomSize = 0.55, decaySeconds = 1.55, preDelayMs = 22.0,
            earlyReflections = 0.60, lateReflections = 1.0, diffusion = 0.72,
            damping = 0.46, warmth = 0.56, brightness = 0.55,
            presence = 0.50, tailSmoothness = 0.80, speechPriority = 0.50,
            wetDryMix = 0.16,
        ),
    ),
    LARGE_MOSQUE(
        "Large Mosque",
        "Stone, height and distance. Long and open, and still intelligible.",
        AmbienceSettings(
            roomSize = 0.86, decaySeconds = 2.70, preDelayMs = 38.0,
            earlyReflections = 0.44, lateReflections = 1.0, diffusion = 0.82,
            damping = 0.42, warmth = 0.53, brightness = 0.58,
            presence = 0.58, tailSmoothness = 0.86, speechPriority = 0.58,
            wetDryMix = 0.21,
        ),
    ),
    GRAND_MOSQUE(
        "Grand Mosque",
        "The largest of them. Marble, air and a tail that takes its time.",
        AmbienceSettings(
            roomSize = 1.0, decaySeconds = 3.60, preDelayMs = 52.0,
            earlyReflections = 0.38, lateReflections = 1.0, diffusion = 0.88,
            damping = 0.44, warmth = 0.52, brightness = 0.57,
            presence = 0.62, tailSmoothness = 0.90, speechPriority = 0.64,
            wetDryMix = 0.25,
        ),
    ),
    ;

    /**
     * Puts the chosen outcome in this room.
     *
     * Only the room changes. The outcome's cleanup, dynamics and tone are untouched, because a
     * person who moves to a larger hall has not asked for a different voice.
     */
    public fun applyTo(settings: VoiceStudioSettings): VoiceStudioSettings =
        settings.copy(ambience = profile)

    public companion object {
        /** Nearest first, so the list opens where most recordings belong. */
        public val order: List<AcousticSpace> = entries.toList()
    }
}

/**
 * The Recitation Studio.
 *
 * Recitation is the case this application is most often used for and the one where a generic
 * reverb is least acceptable: the voice carries meaning that must stay intelligible, the dynamics
 * are part of the delivery and must not be flattened, and the sense of space is not decoration —
 * it is much of why the recording is worth keeping.
 *
 * ## About the names
 *
 * "Makkah Inspired" and "Madinah Inspired" are **creative ambience profiles inspired by the
 * general acoustic character of very large stone spaces.** They are not measurements of any
 * building, they do not reproduce any specific place, and SAUTIY has no affiliation with any
 * mosque or institution. The word "inspired" is in the name for that reason and
 * [DISCLOSURE] is shown wherever these profiles are offered. Claiming otherwise would be a
 * promise no impulse-response-free reverb can keep, and one that would matter to the people who
 * care most about these recordings.
 */
public enum class RecitationProfile(
    public val displayName: String,
    public val summary: String,
    internal val profile: AmbienceSettings,
    /** Where the intensity control starts for this profile. */
    public val defaultIntensity: Double,
) {
    NATURAL(
        "Natural",
        "Almost nothing. Only enough space that the recording stops sounding dead.",
        AmbienceSettings(
            roomSize = 0.22, decaySeconds = 0.45, preDelayMs = 10.0,
            earlyReflections = 0.76, lateReflections = 0.55, diffusion = 0.52,
            damping = 0.52, warmth = 0.54, brightness = 0.52,
            presence = 0.30, tailSmoothness = 0.62, speechPriority = 0.35,
            wetDryMix = 0.06,
        ),
        VoiceCharacter.NATURAL,
    ),
    MAKKAH_INSPIRED(
        "Makkah Inspired",
        "Vast, open and bright. Marble and air, with the voice still forward.",
        AmbienceSettings(
            roomSize = 1.0, decaySeconds = 3.90, preDelayMs = 58.0,
            earlyReflections = 0.36, lateReflections = 1.0, diffusion = 0.90,
            damping = 0.40, warmth = 0.48, brightness = 0.62,
            presence = 0.64, tailSmoothness = 0.92, speechPriority = 0.66,
            wetDryMix = 0.24,
        ),
        VoiceCharacter.GRAND,
    ),
    MADINAH_INSPIRED(
        "Madinah Inspired",
        "Large but softer. Warmer surfaces, a rounder tail, and an unhurried decay.",
        AmbienceSettings(
            roomSize = 0.94, decaySeconds = 3.20, preDelayMs = 48.0,
            earlyReflections = 0.42, lateReflections = 1.0, diffusion = 0.86,
            damping = 0.54, warmth = 0.64, brightness = 0.48,
            presence = 0.58, tailSmoothness = 0.90, speechPriority = 0.62,
            wetDryMix = 0.22,
        ),
        VoiceCharacter.GRAND,
    ),
    GRAND_MOSQUE(
        "Grand Mosque",
        "Stone, height and a long answer. The largest ordinary room there is.",
        AcousticSpace.GRAND_MOSQUE.profile,
        VoiceCharacter.GRAND,
    ),
    PRESTIGE(
        "Prestige",
        "Clarity, air and dignity, with the dynamics of the voice kept intact.",
        AmbienceSettings(
            roomSize = 0.70, decaySeconds = 1.80, preDelayMs = 30.0,
            earlyReflections = 0.52, lateReflections = 1.0, diffusion = 0.76,
            damping = 0.40, warmth = 0.48, brightness = 0.60,
            presence = 0.52, tailSmoothness = 0.84, speechPriority = 0.50,
            wetDryMix = 0.17,
        ),
        VoiceCharacter.RICH,
    ),
    MAJESTIC(
        "Majestic",
        "Long, wide and unhurried, for a voice that can carry it.",
        // Deliberately not the same room as Grand Mosque. That one is a building's acoustics;
        // this is a produced sound — tighter and more controlled than the raw space, and wider.
        AmbienceSettings(
            roomSize = 0.97, decaySeconds = 3.25, preDelayMs = 50.0,
            earlyReflections = 0.40, lateReflections = 1.0, diffusion = 0.88,
            damping = 0.44, warmth = 0.50, brightness = 0.58,
            presence = 0.62, tailSmoothness = 0.90, speechPriority = 0.65,
            wetDryMix = 0.25,
        ),
        VoiceCharacter.GRAND,
    ),
    IMMERSIVE(
        "Immersive",
        "The room as the subject. Deliberately expansive.",
        AmbienceSettings(
            roomSize = 1.0, decaySeconds = 4.40, preDelayMs = 62.0,
            earlyReflections = 0.34, lateReflections = 1.0, diffusion = 0.92,
            damping = 0.42, warmth = 0.52, brightness = 0.56,
            presence = 0.66, tailSmoothness = 0.94, speechPriority = 0.70,
            wetDryMix = 0.28,
        ),
        VoiceCharacter.IMMERSIVE,
    ),
    ;

    /**
     * The recitation voice in this space.
     *
     * Built on Prestige Recitation's treatment rather than on a generic chain: light compression
     * that leaves the delivery's dynamics alone, a gentle de-esser, and clarity without a presence
     * lift that would turn recitation harsh.
     */
    public val settings: VoiceStudioSettings
        get() = VoiceSpacePreset.PRESTIGE_RECITATION.settings.copy(
            ambience = profile,
            character = VoiceCharacter(defaultIntensity),
        )

    public fun studio(): VoiceStudio = VoiceStudio(settings)

    public companion object {
        /**
         * Shown wherever these profiles are offered.
         *
         * Not a legal footnote to be tucked away: the people who care most about these recordings
         * are exactly the people who would be misled by a name that implied more than it can do.
         */
        public const val DISCLOSURE: String =
            "Creative ambience profiles inspired by the character of large stone spaces. " +
                "They do not reproduce any specific building, and SAUTIY is not affiliated with " +
                "any mosque or institution."

        public val order: List<RecitationProfile> = entries.toList()
    }
}

/**
 * One tap: look at the recording, choose a starting point, and say why.
 *
 * A beginner does not know which outcome fits what they just recorded, and asking them is asking
 * them to make a judgement they do not yet have the vocabulary for. This makes it and shows its
 * reasoning, so the recommendation is a starting point they can disagree with rather than a
 * decision made on their behalf.
 */
public object AutoStudio {

    /** What was chosen, how much of it, and the reason in one sentence. */
    public data class Recommendation(
        val outcome: VoiceOutcome,
        val intensity: Double,
        val reason: String,
    ) {
        public val settings: VoiceStudioSettings
            get() = outcome.settings.copy(character = VoiceCharacter(intensity))
    }

    /**
     * Chooses from what the recording actually is.
     *
     * The rules are ordered by how confidently they can be read from the audio. A very noisy or
     * very quiet recording is unmistakable and gets the safe answer; a clean, wide-dynamic one is
     * probably deliberate and gets the richer one. Where nothing stands out the answer is the
     * middle, because a recommendation nobody can fault is worth more than a bold one that is
     * sometimes wrong.
     */
    public fun recommend(analysis: VoiceAnalysis): Recommendation = when {
        analysis.signalToNoiseDb < 14.0 -> Recommendation(
            VoiceOutcome.CLEAR_SPEECH,
            VoiceCharacter.NATURAL,
            "There is noticeable background noise, so this keeps the words plain and adds no room.",
        )

        analysis.presenceTiltDb < -17.0 -> Recommendation(
            VoiceOutcome.CLEAR_SPEECH,
            VoiceCharacter.REFINED,
            "The recording sounds distant, so this brings the voice forward before anything else.",
        )

        analysis.sibilanceTiltDb > -8.0 -> Recommendation(
            VoiceOutcome.WARM_VOICE,
            VoiceCharacter.REFINED,
            "The top end is sharp, so this softens it and fills in underneath.",
        )

        analysis.lowTiltDb < -13.0 -> Recommendation(
            VoiceOutcome.WARM_VOICE,
            VoiceCharacter.RICH,
            "The voice is thin, so this adds body and a little room around it.",
        )

        analysis.loudnessRangeLu > 11.0 -> Recommendation(
            VoiceOutcome.RICH_NARRATION,
            VoiceCharacter.RICH,
            "The delivery moves a lot, which suits narration — evened out, with weight and polish.",
        )

        else -> Recommendation(
            VoiceOutcome.PODCAST,
            VoiceCharacter.REFINED,
            "A clean, steady recording. This keeps it natural and brings it to a consistent level.",
        )
    }
}
