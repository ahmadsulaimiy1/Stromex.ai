package ai.sautiy.core.edit

import kotlinx.serialization.Serializable

/**
 * Editorial Bible chapter 9.2 — the edit model.
 *
 * Four types and no others: a [Source] holds samples, a [Clip] is a window onto a source
 * placed in time, a [Layer] is an ordered lane of clips, and a [Timeline] is the project.
 *
 * **Nothing here contains audio.** That is the entire design. A timeline is a few hundred
 * bytes per clip describing how immutable, write-once source files should be assembled — so
 * an edit is a new description rather than a rewrite, undo is a step backwards through a list
 * rather than a repair, and chapter 9.1's first law holds mechanically instead of by
 * discipline.
 *
 * The invariants of chapter 9.2 are enforced in `init`. An illegal timeline is not something
 * to be validated later; it is something that cannot be constructed.
 */
@Serializable
public data class Source(
    val id: String,
    /** Path relative to the project directory. Never absolute — projects must survive a move. */
    val relativePath: String,
    val sampleRate: Int,
    val channelCount: Int,
    val frameCount: Long,
) {
    init {
        require(id.isNotBlank()) { "A source needs an id" }
        require(frameCount >= 0) { "A source cannot have negative length" }
        require(sampleRate > 0)
        require(channelCount in 1..2)
    }

    public val durationSeconds: Double get() = frameCount.toDouble() / sampleRate
}

/** The shape of a fade (chapter 9.4). */
@Serializable
public enum class FadeShape {
    /** Straight line. For the short fades that kill a click at an edit point. */
    LINEAR,

    /**
     * `sin(πt/2)`. For crossfades and joins between takes: two equal-power curves sum to
     * constant perceived loudness through the transition, where two linear curves dip in the
     * middle — the audible "hole" in a naive crossfade.
     */
    EQUAL_POWER,

    /** Smoothstep `t²(3−2t)`. For long fades in and out, where a linear ramp sounds mechanical. */
    SMOOTH,
    ;

    /** Fade-in gain at normalised position [t] in 0..1. */
    public fun gainIn(t: Double): Double {
        val x = t.coerceIn(0.0, 1.0)
        return when (this) {
            LINEAR -> x
            EQUAL_POWER -> kotlin.math.sin(x * Math.PI / 2.0)
            SMOOTH -> x * x * (3.0 - 2.0 * x)
        }
    }

    /** Fade-out gain at normalised position [t] in 0..1, where 0 is the start of the fade. */
    public fun gainOut(t: Double): Double = gainIn(1.0 - t)
}

/**
 * A window onto a source, placed on the timeline.
 *
 * @param sourceStartFrame where in the source this clip begins
 * @param lengthFrames how much of the source it uses
 * @param timelineStartFrame where on the timeline it sits
 */
@Serializable
public data class Clip(
    val id: String,
    val sourceId: String,
    val sourceStartFrame: Long,
    val lengthFrames: Long,
    val timelineStartFrame: Long,
    val gainDb: Double = 0.0,
    val fadeInFrames: Long = 0,
    val fadeOutFrames: Long = 0,
    val fadeShape: FadeShape = FadeShape.LINEAR,
) {
    init {
        // Chapter 9.2 invariant 4: a zero-length clip is deleted, not kept.
        require(lengthFrames > 0) { "A clip must have length; empty clips are removed, not stored" }
        require(sourceStartFrame >= 0) { "A clip cannot start before its source does" }
        require(timelineStartFrame >= 0) { "A clip cannot start before the timeline does" }
        // Chapter 9.2 invariant 3.
        require(fadeInFrames >= 0 && fadeOutFrames >= 0) { "Fades cannot be negative" }
        require(fadeInFrames + fadeOutFrames <= lengthFrames) {
            "Fades ($fadeInFrames + $fadeOutFrames) exceed the clip they are on ($lengthFrames)"
        }
    }

    public val timelineEndFrame: Long get() = timelineStartFrame + lengthFrames
    public val sourceEndFrame: Long get() = sourceStartFrame + lengthFrames

    public fun coversTimelineFrame(frame: Long): Boolean =
        frame >= timelineStartFrame && frame < timelineEndFrame

    public fun overlaps(startFrame: Long, endFrame: Long): Boolean =
        timelineStartFrame < endFrame && timelineEndFrame > startFrame

    /** Linear gain including any fade, at [offsetInClip] frames from the clip's start. */
    public fun gainAt(offsetInClip: Long): Double {
        val base = Math.pow(10.0, gainDb / 20.0)
        var gain = base
        if (fadeInFrames > 0 && offsetInClip < fadeInFrames) {
            gain *= fadeShape.gainIn(offsetInClip.toDouble() / fadeInFrames)
        }
        val fromEnd = lengthFrames - offsetInClip
        if (fadeOutFrames > 0 && fromEnd <= fadeOutFrames) {
            gain *= fadeShape.gainOut(1.0 - fromEnd.toDouble() / fadeOutFrames)
        }
        return gain
    }
}

/** An ordered lane of non-overlapping clips (chapter 9.2). */
@Serializable
public data class Layer(
    val id: String,
    val name: String,
    val clips: List<Clip> = emptyList(),
    val gainDb: Double = 0.0,
    val muted: Boolean = false,
    val soloed: Boolean = false,
    /** Index into the layer colour ramp. Colour is assigned, never chosen by the user. */
    val colourIndex: Int = 0,
) {
    init {
        require(name.isNotBlank()) { "A layer needs a name" }
        // Chapter 9.2 invariant 1: sorted and non-overlapping, enforced rather than assumed.
        for (i in 1 until clips.size) {
            require(clips[i].timelineStartFrame >= clips[i - 1].timelineEndFrame) {
                "Clips in '$name' overlap or are out of order: " +
                    "${clips[i - 1].id} ends at ${clips[i - 1].timelineEndFrame}, " +
                    "${clips[i].id} starts at ${clips[i].timelineStartFrame}"
            }
        }
    }

    public val lengthFrames: Long get() = clips.lastOrNull()?.timelineEndFrame ?: 0L

    public val isEmpty: Boolean get() = clips.isEmpty()

    public fun clipAt(frame: Long): Clip? = clips.firstOrNull { it.coversTimelineFrame(frame) }

    public fun clipsOverlapping(startFrame: Long, endFrame: Long): List<Clip> =
        clips.filter { it.overlaps(startFrame, endFrame) }

    /** Re-sorts and drops empties. Every operation funnels through this. */
    internal fun withClips(newClips: List<Clip>): Layer =
        copy(clips = newClips.filter { it.lengthFrames > 0 }.sortedBy { it.timelineStartFrame })
}

/** The project (chapter 9.2). */
@Serializable
public data class Timeline(
    val sampleRate: Int,
    val layers: List<Layer> = emptyList(),
    val sources: Map<String, Source> = emptyMap(),
) {
    init {
        require(sampleRate > 0)
        require(layers.map { it.id }.toSet().size == layers.size) { "Layer ids must be unique" }
        // Chapter 9.2 invariant 2: a clip's window always lies inside its source.
        for (layer in layers) {
            for (clip in layer.clips) {
                val source = sources[clip.sourceId]
                    ?: error("Clip ${clip.id} references unknown source ${clip.sourceId}")
                require(clip.sourceEndFrame <= source.frameCount) {
                    "Clip ${clip.id} reads to ${clip.sourceEndFrame} of a " +
                        "${source.frameCount}-frame source"
                }
            }
        }
    }

    /** Chapter 9.2 invariant 5: length is derived from content, never stored separately. */
    public val lengthFrames: Long get() = layers.maxOfOrNull { it.lengthFrames } ?: 0L

    public val durationSeconds: Double get() = lengthFrames.toDouble() / sampleRate

    public val isEmpty: Boolean get() = layers.all { it.isEmpty }

    public val hasSolo: Boolean get() = layers.any { it.soloed }

    /** True if this layer is heard in the mix, accounting for mute and the solo rule. */
    public fun isAudible(layer: Layer): Boolean = when {
        layer.muted -> false
        hasSolo -> layer.soloed
        else -> true
    }

    public fun layer(id: String): Layer? = layers.firstOrNull { it.id == id }

    internal fun withLayer(id: String, transform: (Layer) -> Layer): Timeline {
        val index = layers.indexOfFirst { it.id == id }
        require(index >= 0) { "No layer with id $id" }
        return copy(layers = layers.toMutableList().also { it[index] = transform(it[index]) })
    }

    public companion object {
        public fun empty(sampleRate: Int): Timeline = Timeline(sampleRate)
    }
}
