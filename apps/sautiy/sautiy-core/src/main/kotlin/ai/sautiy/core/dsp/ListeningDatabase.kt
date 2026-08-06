package ai.sautiy.core.dsp

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

/**
 * What listeners have said about each preset, kept, so the presets get better.
 *
 * Not machine learning and not a cloud service. It is a tally: every time someone taps "too
 * bright" while auditioning Rich Narration, that lands here against Rich Narration. Once enough
 * people have said the same thing, the preset moves — by the amount they agreed on, once, in the
 * direction the word means.
 *
 * The reason this is worth building rather than shipping fixed numbers is that no amount of
 * acoustic reasoning can tell you whether Grand Space is a little too bright for the average
 * person's headphones. Only the average person can, and they will tell you for free if tapping a
 * word takes one second. Presets tuned this way are tuned by the people who use them.
 *
 * **Deliberate limits, so this cannot quietly go wrong:**
 * * Consensus, never a single voice. One person's headphones are not evidence — [MIN_LISTENERS]
 *   independent notes before a preset moves at all.
 * * Each agreed note applied **once**, however many people said it. Ten people saying "too bright"
 *   means the preset is too bright, not ten times too bright.
 * * Correction total capped at [MAX_ROUNDS] steps per preset, so a preset can be improved and
 *   cannot be walked off a cliff by a run of extreme listeners.
 * * The result stays inside [SignatureSound]. Listeners may retune the house style; they may not
 *   demolish it.
 * * "Excellent" is counted too. A preset most people are happy with must be able to prove it, or
 *   the only thing recorded is complaints.
 */
@Serializable
public data class ListeningDatabase(
    /** Preset name → note name → how many listeners said it. */
    val tallies: Map<String, Map<String, Int>> = emptyMap(),
) {

    /** One listener, one word, about one preset. */
    public fun record(preset: String, note: ListenerNote): ListeningDatabase {
        val forPreset = tallies[preset].orEmpty()
        val next = forPreset + (note.name to (forPreset[note.name] ?: 0) + 1)
        return copy(tallies = tallies + (preset to next))
    }

    /** How many notes have been left about a preset — the sample size behind any claim about it. */
    public fun listeners(preset: String): Int = tallies[preset].orEmpty().values.sum()

    /** How many of them said it was right as it was. */
    public fun approvals(preset: String): Int =
        tallies[preset].orEmpty()[ListenerNote.EXCELLENT.name] ?: 0

    /**
     * The share who were happy, as 0 to 1, or null when too few have listened to say.
     *
     * Null rather than 0.0 for an unheard preset: "nobody liked it" and "nobody has heard it" are
     * completely different facts and a gauge that shows them the same way is lying.
     */
    public fun approval(preset: String): Double? {
        val total = listeners(preset)
        if (total < MIN_LISTENERS) return null
        return approvals(preset).toDouble() / total
    }

    /**
     * The notes a majority of listeners agreed on, excluding "excellent".
     *
     * Majority of the *critical* notes rather than of all notes: a preset can be liked by most
     * people and still be slightly too bright for the rest, and that is worth fixing. Excellent is
     * counted for [approval] and excluded here because "leave it alone" is not a correction.
     */
    public fun consensus(preset: String, threshold: Double = 0.5): List<ListenerNote> {
        val forPreset = tallies[preset].orEmpty()
        val critical = forPreset.filterKeys { it != ListenerNote.EXCELLENT.name }
        val total = critical.values.sum()
        if (total < MIN_LISTENERS) return emptyList()
        return ListenerNote.order
            .filter { it != ListenerNote.EXCELLENT }
            .filter { (critical[it.name] ?: 0).toDouble() / total >= threshold }
    }

    /**
     * A preset as the listeners would have it.
     *
     * Applies each agreed note once, caps the total correction, and puts the result back inside
     * the house style. Returns the settings unchanged when nobody has said anything, so a fresh
     * install behaves exactly as designed and this can never be the cause of a preset sounding
     * different from its documentation without evidence.
     */
    public fun tuned(preset: String, settings: VoiceStudioSettings): VoiceStudioSettings {
        val notes = consensus(preset).take(MAX_ROUNDS)
        if (notes.isEmpty()) return settings
        val moved = notes.fold(settings) { current, note -> note.applyTo(current) }
        return SignatureSound.applyTo(moved)
    }

    /** A sentence for the panel, or null when there is nothing honest to say yet. */
    public fun evidence(preset: String): String? {
        val total = listeners(preset)
        if (total < MIN_LISTENERS) return null
        val share = approval(preset) ?: return null
        val notes = consensus(preset)
        val listenerWord = if (total == 1) "listener" else "listeners"
        return if (notes.isEmpty()) {
            "${(share * 100).toInt()}% of $total $listenerWord were happy with this."
        } else {
            "$total $listenerWord; most said " +
                notes.joinToString(" and ") { it.displayName.lowercase() } + ", and it has moved."
        }
    }

    public companion object {
        /**
         * Before this many notes, a preset does not move.
         *
         * Three, not one. One note is a person's taste, their headphones and possibly a mistap.
         * Three people saying the same word about the same preset is the smallest thing that is
         * not one person.
         */
        public const val MIN_LISTENERS: Int = 3

        /**
         * The most a preset may be corrected in total.
         *
         * Two steps of 0.18 is a clearly audible change and well short of a different preset. A
         * preset that genuinely needs more than this was designed wrongly, and the fix for that is
         * a person looking at it — not an unbounded feedback loop.
         */
        public const val MAX_ROUNDS: Int = 2

        private val format = Json { ignoreUnknownKeys = true; encodeDefaults = true }

        public fun encode(database: ListeningDatabase): String =
            format.encodeToString(serializer(), database)

        /** A corrupt tally file loses opinions, not recordings, so it fails to an empty database. */
        public fun decode(text: String): ListeningDatabase =
            runCatching { format.decodeFromString(serializer(), text) }
                .getOrElse { ListeningDatabase() }
    }
}
