package ai.sautiy.core.edit

/**
 * Editorial Bible chapter 9.5 — history as a list of *states*, not of inverse operations.
 *
 * A timeline is metadata: a few hundred bytes per clip, next to megabytes of audio it
 * describes. So keeping a full state per step costs effectively nothing, and buys three things
 * an inverse-operation stack cannot give:
 *
 * 1. **Undo and redo are exact.** There is no inverse to get subtly wrong — no "unsplit" that
 *    forgets a fade, no "un-delete" that restores a clip at the wrong offset.
 * 2. **Time travel.** The history panel lists every step and the user taps any one to jump
 *    straight there. With inverses that means replaying a chain and hoping.
 * 3. **A new edit after undoing truncates cleanly**, leaving no orphaned inverses behind.
 *
 * The structure is immutable: every mutation returns a new [EditHistory], which is what lets
 * the workspace hold it in ordinary state without defensive copying.
 */
public class EditHistory private constructor(
    private val states: List<Timeline>,
    private val labels: List<String>,
    public val index: Int,
    public val droppedFromStart: Int,
) {
    init {
        require(states.isNotEmpty()) { "History always holds at least the initial state" }
        require(index in states.indices) { "History index $index is outside 0..${states.lastIndex}" }
        require(labels.size == states.size) { "Every state carries a label" }
    }

    public val current: Timeline get() = states[index]

    public val canUndo: Boolean get() = index > 0

    public val canRedo: Boolean get() = index < states.lastIndex

    /** Steps in the history panel, oldest first. The entry at [index] is the current one. */
    public val steps: List<String> get() = labels

    /** True once the cap has begun discarding the oldest steps, so the panel can say so. */
    public val isTruncated: Boolean get() = droppedFromStart > 0

    /**
     * Applies an operation and records the result.
     *
     * If the operation changes nothing — trimming a clip to the length it already had, splitting
     * at a boundary — no step is recorded. A history full of no-ops makes undo feel broken,
     * because the user presses it and nothing appears to happen.
     */
    public fun apply(operation: EditOperation): EditHistory {
        val next = operation.applyTo(current)
        if (next == current) return this

        // A new edit after undoing discards the redo future.
        val keptStates = states.subList(0, index + 1) + next
        val keptLabels = labels.subList(0, index + 1) + operation.label

        return if (keptStates.size > MAX_DEPTH) {
            val overflow = keptStates.size - MAX_DEPTH
            EditHistory(
                states = keptStates.subList(overflow, keptStates.size),
                labels = keptLabels.subList(overflow, keptLabels.size),
                index = MAX_DEPTH - 1,
                droppedFromStart = droppedFromStart + overflow,
            )
        } else {
            EditHistory(keptStates, keptLabels, keptStates.lastIndex, droppedFromStart)
        }
    }

    public fun undo(): EditHistory =
        if (canUndo) EditHistory(states, labels, index - 1, droppedFromStart) else this

    public fun redo(): EditHistory =
        if (canRedo) EditHistory(states, labels, index + 1, droppedFromStart) else this

    /** Jumps to any recorded step — the history panel's tap-to-travel (chapter 4.4.2). */
    public fun travelTo(step: Int): EditHistory =
        if (step in states.indices) EditHistory(states, labels, step, droppedFromStart) else this

    /**
     * Replaces the current state without recording a step. Used only for changes the user did
     * not make — a source file relocating on disk, for instance — which must never appear in
     * their history as something they did.
     */
    public fun replaceCurrent(timeline: Timeline): EditHistory =
        EditHistory(states.toMutableList().also { it[index] = timeline }, labels, index, droppedFromStart)

    public companion object {
        /**
         * Chapter 9.5. Deep enough that no real editing session reaches it; bounded so that a
         * runaway gesture loop cannot grow the heap without limit.
         */
        public const val MAX_DEPTH: Int = 200

        public fun of(initial: Timeline): EditHistory =
            EditHistory(listOf(initial), listOf("Open"), 0, 0)
    }
}
