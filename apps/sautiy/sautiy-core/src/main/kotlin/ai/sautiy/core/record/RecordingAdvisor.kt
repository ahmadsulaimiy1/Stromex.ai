package ai.sautiy.core.record

import ai.sautiy.core.dsp.VoiceCharacter

/**
 * What to say to someone holding a phone, before they have recorded anything.
 *
 * Almost every bad recording is bad for one of four reasons, and all four are fixable in the two
 * seconds before the take: too far away, too close, too loud, or a room that is too noisy. None of
 * them is fixable afterwards. Noise reduction is repair; moving 15 cm is prevention, and prevention
 * sounds better than any processing ever will.
 *
 * So this reads the live input and says one thing. **One**, and only when there is something worth
 * saying. A panel that always shows advice is wallpaper within a day; advice that appears when
 * something is actually wrong gets read. And it never blocks, never confirms, never asks: the
 * record button stays exactly as available as it was.
 *
 * The thresholds are chosen so a normal, decent recording produces [Guidance.NONE] — silence. If
 * this fires on good material it is a bug, not a feature.
 */
public object RecordingAdvisor {

    /** How much attention a piece of advice deserves. Decides colour, not wording. */
    public enum class Weight {
        /** Nothing wrong. */
        NONE,

        /** Worth improving, and the recording would still be usable as it is. */
        SUGGESTION,

        /** Will damage the recording. Still not a block — it is the user's take. */
        WARNING,
    }

    /**
     * One sentence of guidance, or nothing.
     *
     * [action] is what to physically do, in words that need no equipment: "move a little closer",
     * not "increase input gain by 6 dB". [because] is why, so the user learns rather than obeys.
     */
    public data class Guidance(
        val weight: Weight,
        val action: String? = null,
        val because: String? = null,
        /**
         * The Voice Space intensity this room deserves afterwards.
         *
         * A noisy room is not a room to add more room to — the noise gets a tail. A quiet room can
         * take as much as the user likes. Null means the analysis has nothing useful to say yet.
         */
        val suggestedIntensity: Double? = null,
    ) {
        public val isSilent: Boolean get() = weight == Weight.NONE

        public companion object {
            public val NONE: Guidance = Guidance(Weight.NONE)
        }
    }

    /** Clipping is not a matter of degree. Once it has happened the take has holes in it. */
    public const val CLIPPING_PEAK_DB: Double = -0.5

    /** Above this the speaker is close enough that plosives and proximity boom start. */
    public const val TOO_CLOSE_PEAK_DB: Double = -3.0

    /** Below this there is not enough signal to work with, whatever is done later. */
    public const val TOO_QUIET_RMS_DB: Double = -38.0

    /** The comfortable middle: loud enough to be clean, quiet enough to survive a raised voice. */
    public const val IDEAL_RMS_DB: Double = -20.0

    /** Above this the room is audible between words and will be audible in the tail. */
    public const val NOISY_ROOM_DB: Double = -46.0

    /** Below about this much signal above the room, cleanup stops being optional. */
    public const val POOR_SNR_DB: Double = 18.0

    /**
     * Reads the live input and returns at most one thing to say.
     *
     * Ordered by how much damage each problem does, and it stops at the first one. Two pieces of
     * advice at once is a form of not advising: the user reads the first, acts on it, and the
     * second was about a symptom of the first anyway.
     *
     * @param peakDb the loudest sample seen recently, in dBFS
     * @param rmsDb the running level, in dBFS
     * @param noiseFloorDb the level between words, in dBFS
     * @param clippedAlready whether full scale has already been reached in this session
     */
    public fun assess(
        peakDb: Double,
        rmsDb: Double,
        noiseFloorDb: Double,
        clippedAlready: Boolean = false,
    ): Guidance {
        // Nothing arriving at all. Not advice — the meters already say this, and repeating it in
        // words is how a screen fills up with text that means nothing.
        if (rmsDb <= -70.0) return Guidance.NONE

        val snr = rmsDb - noiseFloorDb
        val intensity = suggestedIntensity(noiseFloorDb, snr)

        if (clippedAlready || peakDb >= CLIPPING_PEAK_DB) {
            return Guidance(
                weight = Weight.WARNING,
                action = "Move back slightly, or speak a little softer",
                because = "The loudest words are reaching the top of the scale, and what goes " +
                    "over the top is gone — no processing can put it back.",
                suggestedIntensity = intensity,
            )
        }

        if (rmsDb <= TOO_QUIET_RMS_DB) {
            return Guidance(
                weight = Weight.WARNING,
                action = "Move closer — about a hand's width from the microphone",
                because = "At this level the room is a large part of what is being recorded, and " +
                    "raising the voice afterwards raises the room with it.",
                suggestedIntensity = intensity,
            )
        }

        if (noiseFloorDb >= NOISY_ROOM_DB || snr <= POOR_SNR_DB) {
            return Guidance(
                weight = Weight.SUGGESTION,
                action = "Try a quieter spot, or turn off the fan",
                because = "There is a steady background here. It can be reduced afterwards, but " +
                    "never as well as not recording it.",
                suggestedIntensity = intensity,
            )
        }

        if (peakDb >= TOO_CLOSE_PEAK_DB) {
            return Guidance(
                weight = Weight.SUGGESTION,
                action = "A little further back, and slightly off to one side",
                because = "This close, p and b sounds hit the microphone directly and the voice " +
                    "picks up a boom that is hard to remove cleanly.",
                suggestedIntensity = intensity,
            )
        }

        // A good signal. The only thing left worth saying is what the room will take afterwards,
        // and even that is offered rather than announced.
        return Guidance(weight = Weight.NONE, suggestedIntensity = intensity)
    }

    /**
     * How much Voice Space this room can carry.
     *
     * Room level and noise are the same decision seen twice: ambience is a delay line fed by
     * whatever is in the microphone, so adding a large space to a noisy recording gives the noise
     * a tail. A clean recording is the only one that can take a big space without sounding like a
     * big noisy space.
     */
    public fun suggestedIntensity(noiseFloorDb: Double, snrDb: Double): Double = when {
        noiseFloorDb >= -40.0 || snrDb <= 12.0 -> VoiceCharacter.NATURAL
        noiseFloorDb >= NOISY_ROOM_DB || snrDb <= POOR_SNR_DB -> VoiceCharacter.REFINED
        noiseFloorDb >= -58.0 -> VoiceCharacter.RICH
        else -> VoiceCharacter.GRAND
    }

    /**
     * Where the level sits in the comfortable band, as 0 to 1, for a gauge rather than a number.
     *
     * 0.5 is [IDEAL_RMS_DB]. A person aiming at the middle of an arc does not need to be told what
     * −20 dBFS means, and −20 dBFS is not what they were trying to achieve anyway.
     */
    public fun levelPosition(rmsDb: Double): Double {
        val low = TOO_QUIET_RMS_DB
        val high = TOO_CLOSE_PEAK_DB
        val mid = IDEAL_RMS_DB
        return when {
            rmsDb <= low -> 0.0
            rmsDb >= high -> 1.0
            rmsDb <= mid -> 0.5 * (rmsDb - low) / (mid - low)
            else -> 0.5 + 0.5 * (rmsDb - mid) / (high - mid)
        }
    }
}
