package ai.sautiy.core.dsp

/**
 * How much work a recording actually needs — and permission to do almost none.
 *
 * The failure mode of every "enhance" button ever shipped is that it does the same amount of work
 * to everything. Hand it a clean, close, well-levelled recording and it compresses, brightens and
 * de-esses it anyway, and the result is worse than the input. The user is then in the worst
 * position an app can put them in: the feature made it worse, and they cannot tell which part.
 *
 * So restraint is computed, not assumed. Four measured deficits, each scaled by how far the
 * recording is from adequate rather than from perfect:
 *
 * * **Noise** — signal above the room. The one deficit that genuinely cannot be ignored.
 * * **Level** — how far off a sensible delivery level it is.
 * * **Balance** — how far the presence band is from where speech is intelligible.
 * * **Movement** — how much the level wanders, which is what compression is for.
 *
 * The total is the strength. Below [TRANSPARENT_BELOW] the honest answer is *do almost nothing*,
 * and [VoiceAdvisor.enhance] takes that answer: a gentle high-pass to remove rumble nobody wants,
 * a delivery level, and no tone shaping, no compression and no de-essing at all.
 *
 * This is the whole point: **on a good recording, Enhance Voice should be nearly inaudible.** A
 * test asserts it, by measuring that a clean, close, balanced signal comes out within a decibel of
 * how it went in across every band.
 */
public data class Restraint(
    /** 0 = leave it alone; 1 = everything is wrong and everything should move. */
    val strength: Double,
    /** The biggest single deficit, for the panel to name. Null when there is nothing to name. */
    val principal: String?,
    /** What the user is told, in one sentence. */
    val summary: String,
) {
    init {
        require(strength in 0.0..1.0) { "Strength runs 0 to 1, was $strength" }
    }

    /** True when the honest treatment is almost none. */
    public val isTransparent: Boolean get() = strength < TRANSPARENT_BELOW

    /** The strength as a percentage, for a gauge. */
    public val percent: Int get() = kotlin.math.round(strength * 100).toInt()

    public companion object {
        /**
         * Below this total deficit, do almost nothing.
         *
         * 0.18 of the full range. Chosen so a recording made at a sensible distance in a quiet
         * room falls under it, and a recording with any one real problem does not.
         */
        public const val TRANSPARENT_BELOW: Double = 0.18

        /**
         * Reads the four deficits and decides how hard to work.
         *
         * Each deficit is normalised against the point at which it stops being a problem, not
         * against the worst case: a recording 3 dB from ideal is not 3/60ths of a problem, it is
         * no problem at all, and treating it as a small one is how a chain ends up always doing a
         * little of everything.
         */
        public fun of(analysis: VoiceAnalysis): Restraint {
            val deficits = linkedMapOf(
                // Below 24 dB the room is audible between words; below 12 it is a co-star.
                "background noise" to ramp(analysis.signalToNoiseDb, adequate = 24.0, bad = 12.0),

                // −23 LUFS is spoken-word delivery. Being quiet is not a fault in itself, so this
                // only counts distance from a workable range, and only downwards — a loud
                // recording is handled by the ceiling, not by enhancement.
                "level" to ramp(analysis.integratedLufs, adequate = -26.0, bad = -40.0),

                // Presence carries consonants. Around −14 dB relative is intelligible speech.
                "clarity" to ramp(analysis.presenceTiltDb, adequate = -14.0, bad = -22.0),

                // A range beyond about 9 LU means the quiet passages will be lost on a phone
                // speaker; below that, evening it out costs more life than it gains consistency.
                "uneven delivery" to ramp(-analysis.loudnessRangeLu, adequate = -9.0, bad = -16.0),
            )

            // The mean rather than the sum: four small imperfections are not one large problem,
            // and a recording should not be heavily processed for being slightly imperfect in
            // several ways at once. The largest deficit still pulls the mean up on its own.
            val strength = (deficits.values.sum() / deficits.size).coerceIn(0.0, 1.0)
            val principal = deficits.maxByOrNull { it.value }
                ?.takeIf { it.value > 0.25 }
                ?.key

            val summary = when {
                strength < TRANSPARENT_BELOW ->
                    "This recording is already clean. Almost nothing has been changed."
                principal != null ->
                    "Working mainly on $principal."
                else ->
                    "A light, even treatment across the whole recording."
            }

            return Restraint(strength, principal, summary)
        }

        /**
         * 0 at or above [adequate], 1 at or below [bad], linear between.
         *
         * Deliberately one-sided. A deficit measures being *short* of adequate; being comfortably
         * past it earns no processing at all rather than a negative amount of it.
         */
        private fun ramp(value: Double, adequate: Double, bad: Double): Double = when {
            value >= adequate -> 0.0
            value <= bad -> 1.0
            else -> (adequate - value) / (adequate - bad)
        }
    }
}
