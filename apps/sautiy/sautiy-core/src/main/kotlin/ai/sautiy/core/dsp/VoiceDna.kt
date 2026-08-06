package ai.sautiy.core.dsp

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

/**
 * A sound a person has decided is theirs, saved whole.
 *
 * The problem this solves is not storage. It is that a reciter who spent twenty minutes getting
 * their Qur'an voice right, and who records twice a week, currently has to get it right again
 * every time — and will not. They will settle for the nearest preset, and the twenty minutes of
 * judgement they made about *their own voice* is thrown away every session. That is the difference
 * between a tool someone uses and a tool someone commits to.
 *
 * So a Voice DNA is the *complete* instrument: cleanup, dynamics, tone, room, intensity, loudness,
 * output gain. Not a reference to a preset with adjustments on top — the whole value, because a
 * preset that gets re-tuned in a later version would silently change a sound the user had already
 * decided was finished. A saved sound is a promise that it will not move.
 *
 * The names are the user's, and the suggested ones are named for occasions rather than for
 * settings: "My Qur'an Voice", not "Prestige + 60%".
 */
@Serializable
public data class VoiceDna(
    val id: String,
    val name: String,
    val settings: VoiceStudioSettings,
    val createdAtEpochMs: Long,
    /**
     * What it started from, kept for the user's benefit rather than the engine's.
     *
     * Six months later "My Lecture Voice" says nothing about what it is. "Started from Lecture"
     * is the sentence that makes a saved sound comprehensible again, and it costs one string.
     */
    val basedOn: String? = null,
    /** Times it has been recalled. What sorts the list, so a favourite rises without being marked. */
    val timesUsed: Int = 0,
) {
    init {
        require(name.isNotBlank()) { "A saved sound needs a name" }
        require(id.isNotBlank()) { "A saved sound needs an id" }
    }

    /**
     * One line describing the sound, in the terms the panel uses everywhere else.
     *
     * Assembled rather than stored, so it can never disagree with the settings it describes.
     */
    public val summary: String
        get() = buildList {
            basedOn?.let { add(it) }
            val room = settings.effectiveAmbience
            if (room.isBypassed) add("no room") else add("Voice Space ${settings.character.percent}%")
            if (settings.cleanup.noiseReduction != null) add("noise reduction")
            if (settings.dynamics.compressor != null) add("levelled")
        }.joinToString(" · ")

    /** Recalling it counts, so the list can order itself by what the user actually reaches for. */
    public fun recalled(): VoiceDna = copy(timesUsed = timesUsed + 1)

    public companion object {

        /**
         * The four occasions, offered as names before the user has typed anything.
         *
         * Offered rather than created: an app that ships four empty saved sounds has four rows
         * that do nothing until configured, which is exactly what chapter 1's no-empty-shell
         * clause forbids. These are name suggestions for a save that is actually happening.
         */
        public val suggestedNames: List<String> = listOf(
            "My Qur'an Voice",
            "My Lecture Voice",
            "My Podcast Voice",
            "My Broadcast Voice",
        )

        /**
         * A saved sound from what is currently set up.
         *
         * The settings pass through [SignatureSound.applyTo] on the way in. A person can hand-edit
         * a voice outside the house style, and that is theirs to do — but a *saved* sound is one
         * they will reuse for years, and the one place worth insisting the house rules hold is the
         * sound someone is about to make permanent.
         */
        public fun of(
            id: String,
            name: String,
            settings: VoiceStudioSettings,
            createdAtEpochMs: Long,
            basedOn: String? = null,
        ): VoiceDna = VoiceDna(
            id = id,
            name = name.trim(),
            settings = SignatureSound.applyTo(settings),
            createdAtEpochMs = createdAtEpochMs,
            basedOn = basedOn,
        )

        /**
         * A name that is not already taken, by adding a number rather than refusing.
         *
         * Refusing a duplicate name makes the user solve a problem the app created. Two lecture
         * series are a real thing to have.
         */
        public fun uniqueName(desired: String, existing: List<VoiceDna>): String {
            val taken = existing.map { it.name.lowercase() }.toSet()
            val base = desired.trim().ifBlank { "My Voice" }
            if (base.lowercase() !in taken) return base
            var n = 2
            while ("${base.lowercase()} $n" in taken) n++
            return "$base $n"
        }
    }
}

/**
 * The saved sounds, as one serialisable value.
 *
 * A list rather than a map so the order is the user's. Most-used first is computed rather than
 * stored, so recalling a sound does not rewrite the whole file's ordering.
 */
@Serializable
public data class VoiceDnaLibrary(
    val entries: List<VoiceDna> = emptyList(),
) {
    /** What the panel shows: what they reach for most, then what they made most recently. */
    public val ordered: List<VoiceDna>
        get() = entries.sortedWith(
            compareByDescending<VoiceDna> { it.timesUsed }.thenByDescending { it.createdAtEpochMs },
        )

    public fun find(id: String): VoiceDna? = entries.firstOrNull { it.id == id }

    /** Adds or replaces by id, so saving over an existing sound is the same operation. */
    public fun save(dna: VoiceDna): VoiceDnaLibrary =
        copy(entries = entries.filterNot { it.id == dna.id } + dna)

    public fun delete(id: String): VoiceDnaLibrary = copy(entries = entries.filterNot { it.id == id })

    public fun rename(id: String, name: String): VoiceDnaLibrary {
        val trimmed = name.trim()
        if (trimmed.isBlank()) return this
        return copy(entries = entries.map { if (it.id == id) it.copy(name = trimmed) else it })
    }

    /** Marks a recall. Returns the library and the sound, so the caller needs one call. */
    public fun recall(id: String): Pair<VoiceDnaLibrary, VoiceDna>? {
        val found = find(id) ?: return null
        val used = found.recalled()
        return save(used) to used
    }

    public companion object {
        private val format = Json {
            /**
             * Tolerant on the way in, exact on the way out.
             *
             * A saved sound written by an older version must still load after a field is added,
             * or an update silently deletes work the user did months ago. Encoding defaults keeps
             * the file readable and diffable.
             */
            ignoreUnknownKeys = true
            encodeDefaults = true
        }

        public fun encode(library: VoiceDnaLibrary): String =
            format.encodeToString(serializer(), library)

        /**
         * Reads a library, or returns an empty one.
         *
         * A corrupt file must not take the app down on launch. It loses the saved sounds — which
         * is bad and is why the store writes atomically — but a recorder that cannot open because
         * of a preset file is worse than one with no presets.
         */
        public fun decode(text: String): VoiceDnaLibrary =
            runCatching { format.decodeFromString(serializer(), text) }.getOrElse { VoiceDnaLibrary() }
    }
}
