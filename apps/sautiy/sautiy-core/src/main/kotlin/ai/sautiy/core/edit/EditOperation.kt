package ai.sautiy.core.edit

/**
 * Editorial Bible chapter 9.3 — the operations.
 *
 * Every operation is a **pure function** from [Timeline] to [Timeline]. No operation touches
 * a sample, allocates a buffer, or performs I/O; each returns a new description. That is what
 * makes them free to apply speculatively (to preview an edit under the finger), free to store
 * in history, and impossible to get half-applied.
 *
 * Each carries a [label] because chapter 4.4.2's history panel lists steps by name and lets
 * the user tap any one of them to travel there.
 */
public sealed interface EditOperation {

    /** Shown in the history panel. Sentence case, at most three words (chapter 3.2.2). */
    public val label: String

    public fun applyTo(timeline: Timeline): Timeline

    public companion object {
        /**
         * Chapter 9.4's edit-point law. Every cut, split and join carries this fade at the
         * seam. A sample-accurate splice across a non-zero crossing is a step discontinuity,
         * and a step discontinuity is a click; five milliseconds is short enough to be
         * inaudible as a fade and long enough to remove the step entirely.
         */
        public const val SEAM_FADE_MS: Double = 5.0

        public fun seamFadeFrames(sampleRate: Int): Long =
            (SEAM_FADE_MS * sampleRate / 1000.0).toLong().coerceAtLeast(1)
    }
}

// --- Clip operations --------------------------------------------------------------------

/** Splits the clip under [atFrame] into two, sample-accurately (chapter 9.3). */
public data class Split(val layerId: String, val atFrame: Long) : EditOperation {
    override val label: String get() = "Split"

    override fun applyTo(timeline: Timeline): Timeline = timeline.withLayer(layerId) { layer ->
        val clip = layer.clipAt(atFrame) ?: return@withLayer layer
        // Splitting exactly at a clip boundary would produce a zero-length half, which
        // invariant 4 forbids and which is not what the user asked for anyway.
        if (atFrame <= clip.timelineStartFrame || atFrame >= clip.timelineEndFrame) return@withLayer layer

        val seam = EditOperation.seamFadeFrames(timeline.sampleRate)
        val leftLength = atFrame - clip.timelineStartFrame
        val rightLength = clip.timelineEndFrame - atFrame

        val left = clip.copy(
            id = "${clip.id}.a",
            lengthFrames = leftLength,
            fadeOutFrames = minOf(seam, leftLength - clip.fadeInFrames.coerceAtMost(leftLength - 1)),
        )
        val right = clip.copy(
            id = "${clip.id}.b",
            sourceStartFrame = clip.sourceStartFrame + leftLength,
            lengthFrames = rightLength,
            timelineStartFrame = atFrame,
            fadeInFrames = minOf(seam, rightLength - clip.fadeOutFrames.coerceAtMost(rightLength - 1)),
        )
        layer.withClips(layer.clips - clip + listOf(left, right))
    }
}

/**
 * Moves a clip's start or end without moving its audio — the handle-drag of chapter 9.6.
 *
 * @param newStartFrame new timeline position of the clip's start, or null to leave it
 * @param newEndFrame new timeline position of the clip's end, or null to leave it
 */
public data class Trim(
    val layerId: String,
    val clipId: String,
    val newStartFrame: Long? = null,
    val newEndFrame: Long? = null,
) : EditOperation {
    override val label: String get() = "Trim"

    override fun applyTo(timeline: Timeline): Timeline = timeline.withLayer(layerId) { layer ->
        val clip = layer.clips.firstOrNull { it.id == clipId } ?: return@withLayer layer
        val source = timeline.sources[clip.sourceId] ?: return@withLayer layer

        // Trimming the start slides the window into the source by the same amount, so the
        // audio under the remaining part does not move.
        val startShift = (newStartFrame ?: clip.timelineStartFrame) - clip.timelineStartFrame
        val newSourceStart = (clip.sourceStartFrame + startShift).coerceIn(0, source.frameCount - 1)
        val actualShift = newSourceStart - clip.sourceStartFrame

        val start = clip.timelineStartFrame + actualShift
        val end = (newEndFrame ?: clip.timelineEndFrame)
            .coerceAtMost(start + (source.frameCount - newSourceStart))
        val length = end - start
        if (length <= 0) return@withLayer layer.withClips(layer.clips - clip)

        val trimmed = clip.copy(
            sourceStartFrame = newSourceStart,
            timelineStartFrame = start,
            lengthFrames = length,
            fadeInFrames = clip.fadeInFrames.coerceAtMost(length),
            fadeOutFrames = clip.fadeOutFrames.coerceAtMost(length - clip.fadeInFrames.coerceAtMost(length)),
        )
        layer.withClips(layer.clips - clip + trimmed)
    }
}

/** Slides a clip along its layer (chapter 9.6, long-press to pick up). */
public data class MoveClip(
    val layerId: String,
    val clipId: String,
    val toFrame: Long,
) : EditOperation {
    override val label: String get() = "Move"

    override fun applyTo(timeline: Timeline): Timeline = timeline.withLayer(layerId) { layer ->
        val clip = layer.clips.firstOrNull { it.id == clipId } ?: return@withLayer layer
        val moved = clip.copy(timelineStartFrame = toFrame.coerceAtLeast(0))
        val others = layer.clips - clip
        // Landing on top of a neighbour would break invariant 1; the clip stops at the edge.
        val blocked = others.any { it.overlaps(moved.timelineStartFrame, moved.timelineEndFrame) }
        if (blocked) layer else layer.withClips(others + moved)
    }
}

/** Sets a clip's fades (chapter 9.4). */
public data class FadeClip(
    val layerId: String,
    val clipId: String,
    val fadeInFrames: Long,
    val fadeOutFrames: Long,
    val shape: FadeShape = FadeShape.SMOOTH,
) : EditOperation {
    override val label: String get() = "Fade"

    override fun applyTo(timeline: Timeline): Timeline = timeline.withLayer(layerId) { layer ->
        val clip = layer.clips.firstOrNull { it.id == clipId } ?: return@withLayer layer
        val inFrames = fadeInFrames.coerceIn(0, clip.lengthFrames)
        val outFrames = fadeOutFrames.coerceIn(0, clip.lengthFrames - inFrames)
        layer.withClips(
            layer.clips - clip + clip.copy(
                fadeInFrames = inFrames,
                fadeOutFrames = outFrames,
                fadeShape = shape,
            ),
        )
    }
}

// --- Range operations --------------------------------------------------------------------

/**
 * Removes a time range and closes the gap.
 *
 * Chapter 9.3's ripple law: this and [SilenceRange] are different intentions — cutting a
 * cough out of a sentence versus muting a passage — and SAUTIY never guesses which was meant.
 */
public data class DeleteRange(
    val startFrame: Long,
    val endFrame: Long,
    /** When null, every layer is cut so the layers stay in sync. */
    val layerId: String? = null,
) : EditOperation {
    override val label: String get() = "Cut"

    override fun applyTo(timeline: Timeline): Timeline {
        require(endFrame > startFrame) { "An empty range cannot be cut" }
        val span = endFrame - startFrame
        val seam = EditOperation.seamFadeFrames(timeline.sampleRate)

        val newLayers = timeline.layers.map { layer ->
            if (layerId != null && layer.id != layerId) return@map layer

            val kept = ArrayList<Clip>(layer.clips.size + 2)
            for (clip in layer.clips) {
                when {
                    // Entirely before the cut: untouched.
                    clip.timelineEndFrame <= startFrame -> kept += clip

                    // Entirely after: slides back by the span of the cut.
                    clip.timelineStartFrame >= endFrame ->
                        kept += clip.copy(timelineStartFrame = clip.timelineStartFrame - span)

                    // Entirely inside: gone.
                    clip.timelineStartFrame >= startFrame && clip.timelineEndFrame <= endFrame -> Unit

                    else -> {
                        // Straddles one or both edges: keep the surviving head and tail, each
                        // carrying a seam fade so the splice does not click.
                        val headLength = startFrame - clip.timelineStartFrame
                        if (headLength > 0) {
                            kept += clip.copy(
                                id = "${clip.id}.h",
                                lengthFrames = headLength,
                                fadeOutFrames = minOf(seam, headLength),
                            )
                        }
                        val tailLength = clip.timelineEndFrame - endFrame
                        if (tailLength > 0) {
                            val consumed = endFrame - clip.timelineStartFrame
                            kept += clip.copy(
                                id = "${clip.id}.t",
                                sourceStartFrame = clip.sourceStartFrame + consumed,
                                lengthFrames = tailLength,
                                timelineStartFrame = startFrame,
                                fadeInFrames = minOf(seam, tailLength),
                                fadeOutFrames = clip.fadeOutFrames.coerceAtMost(
                                    tailLength - minOf(seam, tailLength),
                                ),
                            )
                        }
                    }
                }
            }
            layer.withClips(kept)
        }
        return timeline.copy(layers = newLayers)
    }
}

/** Removes a time range and leaves the gap, so everything after it stays where it was. */
public data class SilenceRange(
    val startFrame: Long,
    val endFrame: Long,
    val layerId: String? = null,
) : EditOperation {
    override val label: String get() = "Silence"

    override fun applyTo(timeline: Timeline): Timeline {
        require(endFrame > startFrame) { "An empty range cannot be silenced" }
        val seam = EditOperation.seamFadeFrames(timeline.sampleRate)

        val newLayers = timeline.layers.map { layer ->
            if (layerId != null && layer.id != layerId) return@map layer

            val kept = ArrayList<Clip>(layer.clips.size + 2)
            for (clip in layer.clips) {
                if (!clip.overlaps(startFrame, endFrame)) {
                    kept += clip
                    continue
                }
                val headLength = startFrame - clip.timelineStartFrame
                if (headLength > 0) {
                    kept += clip.copy(
                        id = "${clip.id}.h",
                        lengthFrames = headLength,
                        fadeOutFrames = minOf(seam, headLength),
                    )
                }
                val tailLength = clip.timelineEndFrame - endFrame
                if (tailLength > 0) {
                    val consumed = endFrame - clip.timelineStartFrame
                    kept += clip.copy(
                        id = "${clip.id}.t",
                        sourceStartFrame = clip.sourceStartFrame + consumed,
                        lengthFrames = tailLength,
                        timelineStartFrame = endFrame,
                        fadeInFrames = minOf(seam, tailLength),
                        fadeOutFrames = clip.fadeOutFrames.coerceAtMost(
                            tailLength - minOf(seam, tailLength),
                        ),
                    )
                }
            }
            layer.withClips(kept)
        }
        return timeline.copy(layers = newLayers)
    }
}

/** Applies gain to whatever covers a range, splitting clips at the range edges as needed. */
public data class GainRange(
    val startFrame: Long,
    val endFrame: Long,
    val gainDb: Double,
    val layerId: String? = null,
) : EditOperation {
    override val label: String get() = "Gain"

    override fun applyTo(timeline: Timeline): Timeline {
        require(endFrame > startFrame) { "An empty range cannot be gained" }

        // Split at both edges first so the gain lands on exactly the selected span and not a
        // frame more. Splitting is itself an operation, so this stays pure.
        var result = timeline
        for (layer in timeline.layers) {
            if (layerId != null && layer.id != layerId) continue
            result = Split(layer.id, startFrame).applyTo(result)
            result = Split(layer.id, endFrame).applyTo(result)
        }

        val newLayers = result.layers.map { layer ->
            if (layerId != null && layer.id != layerId) return@map layer
            layer.withClips(
                layer.clips.map { clip ->
                    if (clip.timelineStartFrame >= startFrame && clip.timelineEndFrame <= endFrame) {
                        clip.copy(gainDb = clip.gainDb + gainDb)
                    } else {
                        clip
                    }
                },
            )
        }
        return result.copy(layers = newLayers)
    }
}

// --- Layer operations ---------------------------------------------------------------------

public data class AddLayer(val id: String, val name: String, val colourIndex: Int = 0) : EditOperation {
    override val label: String get() = "Add layer"
    override fun applyTo(timeline: Timeline): Timeline =
        timeline.copy(layers = timeline.layers + Layer(id = id, name = name, colourIndex = colourIndex))
}

public data class DeleteLayer(val layerId: String) : EditOperation {
    override val label: String get() = "Delete layer"
    override fun applyTo(timeline: Timeline): Timeline =
        timeline.copy(layers = timeline.layers.filterNot { it.id == layerId })
}

public data class RenameLayer(val layerId: String, val name: String) : EditOperation {
    override val label: String get() = "Rename"
    override fun applyTo(timeline: Timeline): Timeline = timeline.withLayer(layerId) { it.copy(name = name) }
}

public data class SetLayerGain(val layerId: String, val gainDb: Double) : EditOperation {
    override val label: String get() = "Layer gain"
    override fun applyTo(timeline: Timeline): Timeline = timeline.withLayer(layerId) { it.copy(gainDb = gainDb) }
}

public data class MuteLayer(val layerId: String, val muted: Boolean) : EditOperation {
    override val label: String get() = if (muted) "Mute" else "Unmute"
    override fun applyTo(timeline: Timeline): Timeline = timeline.withLayer(layerId) { it.copy(muted = muted) }
}

public data class SoloLayer(val layerId: String, val soloed: Boolean) : EditOperation {
    override val label: String get() = if (soloed) "Solo" else "Unsolo"
    override fun applyTo(timeline: Timeline): Timeline = timeline.withLayer(layerId) { it.copy(soloed = soloed) }
}

public data class DuplicateLayer(val layerId: String, val newId: String) : EditOperation {
    override val label: String get() = "Duplicate"

    override fun applyTo(timeline: Timeline): Timeline {
        val source = timeline.layer(layerId) ?: return timeline
        val copy = source.copy(
            id = newId,
            name = "${source.name} copy",
            clips = source.clips.map { it.copy(id = "$newId.${it.id}") },
            soloed = false,
        )
        val index = timeline.layers.indexOf(source)
        return timeline.copy(layers = timeline.layers.toMutableList().also { it.add(index + 1, copy) })
    }
}

/**
 * Flattens [fromLayerId] into [intoLayerId].
 *
 * Where the two overlap in time the merge is refused rather than silently losing audio: two
 * clips cannot occupy the same frames of one lane (invariant 1), and quietly dropping one of
 * them would be exactly the kind of invisible data loss chapter 1.3.5 forbids.
 */
public data class MergeLayers(val intoLayerId: String, val fromLayerId: String) : EditOperation {
    override val label: String get() = "Merge"

    override fun applyTo(timeline: Timeline): Timeline {
        val into = timeline.layer(intoLayerId) ?: return timeline
        val from = timeline.layer(fromLayerId) ?: return timeline

        for (a in into.clips) {
            for (b in from.clips) {
                if (a.overlaps(b.timelineStartFrame, b.timelineEndFrame)) return timeline
            }
        }
        val merged = into.withClips(into.clips + from.clips.map { it.copy(id = "${intoLayerId}.${it.id}") })
        return timeline
            .copy(layers = timeline.layers.filterNot { it.id == fromLayerId })
            .withLayer(intoLayerId) { merged }
    }
}

/** Places newly captured audio on a layer (chapter 7). */
public data class AppendRecording(
    val layerId: String,
    val source: Source,
    val atFrame: Long,
    val clipId: String,
) : EditOperation {
    override val label: String get() = "Record"

    override fun applyTo(timeline: Timeline): Timeline {
        val withSource = timeline.copy(sources = timeline.sources + (source.id to source))
        return withSource.withLayer(layerId) { layer ->
            layer.withClips(
                layer.clips + Clip(
                    id = clipId,
                    sourceId = source.id,
                    sourceStartFrame = 0,
                    lengthFrames = source.frameCount,
                    timelineStartFrame = atFrame,
                ),
            )
        }
    }
}

/** Applies several operations as one undoable step, under one label. */
public data class Composite(
    override val label: String,
    val operations: List<EditOperation>,
) : EditOperation {
    override fun applyTo(timeline: Timeline): Timeline =
        operations.fold(timeline) { acc, operation -> operation.applyTo(acc) }
}
