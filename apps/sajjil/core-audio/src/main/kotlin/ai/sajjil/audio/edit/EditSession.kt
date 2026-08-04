package ai.sajjil.audio.edit

import ai.sajjil.audio.AudioBuffer

/**
 * A reversible edit.
 *
 * Every operation the editor offers reduces to one primitive — replace a frame range with some
 * other audio — and every such replacement can be inverted by remembering only the audio it
 * displaced. That keeps the undo history proportional to what was actually edited rather than to
 * the length of the recording, which matters when someone is trimming a two-hour lecture.
 */
data class ReplaceEdit(
    val label: String,
    val range: FrameRange,
    val replacement: AudioBuffer,
    /**
     * Whether the boundaries of this edit need a short de-click fade.
     *
     * True for anything that joins unrelated waveforms (cut, paste, delete). False for edits that
     * rewrite a region in place — a fade or a gain change is continuous with its neighbours
     * already, and dipping to zero at its edges would be an audible defect rather than a fix.
     */
    val declickJoins: Boolean = true,
)

private data class AppliedEdit(val label: String, val inverse: ReplaceEdit)

/**
 * The editor's state machine: current audio, selection, split markers, clipboard, undo/redo.
 *
 * Pure and platform-free, so the whole editing model is unit-testable without a device. The UI
 * layer observes [buffer] and [canUndo]/[canRedo] and does nothing else.
 */
class EditSession(
    initial: AudioBuffer,
    /**
     * Bounds how much displaced audio the history may hold. Beyond this the oldest steps are
     * dropped — an editor that runs the device out of memory is worse than one that forgets.
     */
    private val maximumUndoSteps: Int = 64,
) {
    var buffer: AudioBuffer = initial
        private set

    private val undoStack = ArrayDeque<AppliedEdit>()
    private val redoStack = ArrayDeque<AppliedEdit>()

    /** Current selection, or null when nothing is selected. */
    var selection: FrameRange? = null

    /** Frames at which the user has split the recording; drives the segment handles in the UI. */
    val splitPoints: MutableList<Int> = mutableListOf()

    var clipboard: AudioBuffer? = null
        private set

    val canUndo: Boolean get() = undoStack.isNotEmpty()
    val canRedo: Boolean get() = redoStack.isNotEmpty()

    val undoLabel: String? get() = undoStack.lastOrNull()?.label
    val redoLabel: String? get() = redoStack.lastOrNull()?.label

    val sampleRate: Int get() = buffer.sampleRate
    val frameCount: Int get() = buffer.frameCount

    // ---- primitive ----------------------------------------------------------------------

    /** Applies [edit] and pushes its inverse onto the undo stack. */
    fun apply(edit: ReplaceEdit) {
        val inverse = perform(edit)
        undoStack.addLast(AppliedEdit(edit.label, inverse))
        while (undoStack.size > maximumUndoSteps) undoStack.removeFirst()
        // Any new edit invalidates the redo branch — standard, and what users expect.
        redoStack.clear()
    }

    private fun perform(requested: ReplaceEdit): ReplaceEdit {
        require(requested.range.until <= buffer.frameCount) {
            "range ${requested.range.from}..${requested.range.until} exceeds ${buffer.frameCount} frames"
        }
        val edit = withDeclickedShoulders(requested)
        val range = edit.range
        // Captured before anything is modified, and covering the de-click shoulders too, so
        // undo restores the audio bit-for-bit rather than leaving faded edges behind.
        val displaced = buffer.slice(range.from, range.until)

        val parts = ArrayList<AudioBuffer>(3)
        if (range.from > 0) parts += buffer.slice(0, range.from)
        if (edit.replacement.frameCount > 0) parts += edit.replacement
        if (range.until < buffer.frameCount) parts += buffer.slice(range.until, buffer.frameCount)

        val next = if (parts.isEmpty()) {
            AudioBuffer.silence(buffer.sampleRate, buffer.channelCount, 0)
        } else {
            AudioBuffer.concat(parts)
        }

        val delta = edit.replacement.frameCount - range.length
        buffer = next
        shiftMarkers(range, delta)

        return ReplaceEdit(
            label = edit.label,
            range = FrameRange(range.from, range.from + edit.replacement.frameCount),
            replacement = displaced,
            // The inverse restores original audio; its own boundaries are the same joins, which
            // have already been softened. Softening them again would compound the fades.
            declickJoins = false,
        )
    }

    /**
     * Widens an edit to take in a few milliseconds on each side and folds the de-click fades into
     * its replacement.
     *
     * Doing it this way — rather than fading the buffer after the splice — is what keeps undo
     * exact: everything the edit touches lies inside the range whose original contents the
     * inverse holds.
     */
    private fun withDeclickedShoulders(edit: ReplaceEdit): ReplaceEdit {
        if (!edit.declickJoins) return edit
        val width = declickWidth()
        val from = (edit.range.from - width).coerceAtLeast(0)
        val until = (edit.range.until + width).coerceAtMost(buffer.frameCount)

        val leftShoulder = buffer.slice(from, edit.range.from)
        val rightShoulder = buffer.slice(edit.range.until, until)
        val parts = listOf(leftShoulder, edit.replacement, rightShoulder).filter { it.frameCount > 0 }
        if (parts.isEmpty()) return edit.copy(range = FrameRange(from, until))

        val composed = AudioBuffer.concat(parts)
        val firstJoin = leftShoulder.frameCount
        if (firstJoin in 1 until composed.frameCount) {
            Fades.declickAt(composed, firstJoin, width)
        }
        // When the replacement is empty the two shoulders meet at a single join, already handled.
        if (edit.replacement.frameCount > 0 && rightShoulder.frameCount > 0) {
            val secondJoin = firstJoin + edit.replacement.frameCount
            if (secondJoin in 1 until composed.frameCount) {
                Fades.declickAt(composed, secondJoin, width)
            }
        }
        return edit.copy(range = FrameRange(from, until), replacement = composed)
    }

    /** Roughly 3 ms — long enough to remove a step, short enough to be inaudible. */
    private fun declickWidth(): Int = (buffer.sampleRate / 1000.0 * 3).toInt().coerceAtLeast(8)

    fun undo(): Boolean {
        val step = undoStack.removeLastOrNull() ?: return false
        val inverse = perform(step.inverse)
        redoStack.addLast(AppliedEdit(step.label, inverse))
        return true
    }

    fun redo(): Boolean {
        val step = redoStack.removeLastOrNull() ?: return false
        val inverse = perform(step.inverse)
        undoStack.addLast(AppliedEdit(step.label, inverse))
        return true
    }

    // ---- operations ---------------------------------------------------------------------

    fun delete(range: FrameRange = requireSelection()) {
        // The selection is not cleared here on purpose: shiftMarkers drops it when it overlapped
        // the deleted audio and otherwise moves it to follow that audio's new position. Clearing
        // unconditionally would throw away a selection the edit never touched.
        apply(ReplaceEdit("Delete", range, emptyLike()))
    }

    fun copy(range: FrameRange = requireSelection()) {
        clipboard = buffer.slice(range.from, range.until)
    }

    fun cut(range: FrameRange = requireSelection()) {
        clipboard = buffer.slice(range.from, range.until)
        apply(ReplaceEdit("Cut", range, emptyLike()))
    }

    /** Pastes the clipboard at [frame]. Returns false when there is nothing to paste. */
    fun paste(frame: Int): Boolean {
        val clip = clipboard ?: return false
        val at = frame.coerceIn(0, buffer.frameCount)
        apply(ReplaceEdit("Paste", FrameRange(at, at), clip))
        return true
    }

    /** Keeps only [range], discarding everything outside it. */
    fun trimTo(range: FrameRange = requireSelection()) {
        val kept = buffer.slice(range.from, range.until)
        // Trimming produces no internal join — the cut edges become the file's own start and end.
        apply(ReplaceEdit("Trim", FrameRange(0, buffer.frameCount), kept, declickJoins = false))
        splitPoints.clear()
    }

    fun insertSilence(frame: Int, frames: Int) {
        require(frames >= 0) { "cannot insert a negative amount of silence" }
        val at = frame.coerceIn(0, buffer.frameCount)
        val silence = AudioBuffer.silence(buffer.sampleRate, buffer.channelCount, frames)
        apply(ReplaceEdit("Insert silence", FrameRange(at, at), silence))
    }

    /**
     * Marks a split point. Splitting does not alter audio — it only creates a handle the user can
     * grab. Treating it as a destructive operation is a common mistake that forces an undo just
     * to change your mind about where a boundary goes.
     */
    fun split(frame: Int) {
        val at = frame.coerceIn(0, buffer.frameCount)
        if (at > 0 && at < buffer.frameCount && splitPoints.none { it == at }) {
            splitPoints += at
            splitPoints.sort()
        }
    }

    fun clearSplits() = splitPoints.clear()

    /** The segments implied by the current split points, in order. */
    fun segments(): List<FrameRange> {
        val bounds = (listOf(0) + splitPoints.sorted() + listOf(buffer.frameCount)).distinct()
        return bounds.zipWithNext { a, b -> FrameRange(a, b) }.filter { it.length > 0 }
    }

    /**
     * Runs [transform] over [range] and records the result as one undoable step.
     *
     * This is how every effect — fade, gain, noise reduction, a whole enhancement chain — reaches
     * the timeline, so they all get undo for free and none of them need to know about history.
     */
    fun transform(
        label: String,
        range: FrameRange = FrameRange(0, buffer.frameCount),
        transform: (AudioBuffer) -> AudioBuffer,
    ) {
        val processed = transform(buffer.slice(range.from, range.until))
        require(processed.frameCount == range.length || range.length == buffer.frameCount) {
            "a region transform must preserve its length; \"$label\" returned " +
                "${processed.frameCount} frames for a ${range.length}-frame range"
        }
        apply(ReplaceEdit(label, range, processed, declickJoins = false))
    }

    fun fadeIn(range: FrameRange = requireSelection(), shape: FadeShape = FadeShape.EQUAL_POWER) {
        transform("Fade in", range) { slice ->
            slice.copy().also { Fades.fadeIn(it, it.frameCount, shape) }
        }
    }

    fun fadeOut(range: FrameRange = requireSelection(), shape: FadeShape = FadeShape.EQUAL_POWER) {
        transform("Fade out", range) { slice ->
            slice.copy().also { Fades.fadeOut(it, it.frameCount, shape) }
        }
    }

    fun applyGain(gainDb: Double, range: FrameRange = FrameRange(0, buffer.frameCount)) {
        transform("Gain", range) { slice ->
            slice.copy().also { it.applyGain(ai.sajjil.audio.dbToLinear(gainDb).toFloat()) }
        }
    }

    /** Replaces the whole recording, e.g. after appending a new take. One undoable step. */
    fun replaceAll(label: String, next: AudioBuffer) {
        apply(ReplaceEdit(label, FrameRange(0, buffer.frameCount), next, declickJoins = false))
    }

    fun append(label: String, extra: AudioBuffer) {
        apply(ReplaceEdit(label, FrameRange(buffer.frameCount, buffer.frameCount), extra))
    }

    // ---- internals ----------------------------------------------------------------------

    private fun requireSelection(): FrameRange =
        selection ?: throw IllegalStateException("this operation needs a selection")

    private fun emptyLike() = AudioBuffer.silence(buffer.sampleRate, buffer.channelCount, 0)

    /** Keeps split markers and the selection pointing at the same audio after an edit. */
    private fun shiftMarkers(range: FrameRange, delta: Int) {
        val iterator = splitPoints.listIterator()
        while (iterator.hasNext()) {
            val point = iterator.next()
            when {
                point <= range.from -> Unit
                point >= range.until -> iterator.set(point + delta)
                // A marker inside replaced audio no longer refers to anything; drop it.
                else -> iterator.remove()
            }
        }
        splitPoints.retainAll { it in 1 until buffer.frameCount }

        selection = selection?.let { current ->
            when {
                current.until <= range.from -> current
                current.from >= range.until -> FrameRange(current.from + delta, current.until + delta)
                else -> null
            }
        }
    }
}
