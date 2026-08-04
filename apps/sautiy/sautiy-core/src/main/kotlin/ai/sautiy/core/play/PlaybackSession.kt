package ai.sautiy.core.play

import ai.sautiy.core.PerformanceBudget
import ai.sautiy.core.workspace.TransportState

/**
 * Editorial Bible chapter 8 — playback, with no Android in it.
 *
 * Chapter 1.3.4 is absolute: **listening outranks everything.** Playback must never wait for
 * waveform generation, loudness measurement, transcription or enhancement. This file is where
 * that priority is made structural rather than promised — the playback state carries no
 * reference to any analysis result, so there is nothing for it to wait on.
 */

/** A named point in a recording the user can return to. */
public data class Bookmark(
    val id: String,
    val frame: Long,
    val label: String = "",
    val colourIndex: Int = 0,
)

/**
 * Playback speed.
 *
 * Offered as named steps rather than a free slider because a slider invites fiddling and no
 * listener wants 1.37×. The steps are the ones people actually use, and 1.0 is always one tap
 * away.
 */
public enum class PlaybackSpeed(public val factor: Double, public val displayName: String) {
    HALF(0.5, "0.5×"),
    THREE_QUARTER(0.75, "0.75×"),
    NORMAL(1.0, "1×"),
    ONE_AND_QUARTER(1.25, "1.25×"),
    ONE_AND_HALF(1.5, "1.5×"),
    DOUBLE(2.0, "2×"),
    ;

    public companion object {
        public val Default: PlaybackSpeed = NORMAL

        public fun nearest(factor: Double): PlaybackSpeed =
            entries.minByOrNull { kotlin.math.abs(it.factor - factor) } ?: NORMAL
    }
}

/** A loop region, set by dragging on the waveform. */
public data class LoopRegion(val startFrame: Long, val endFrame: Long) {
    init {
        require(endFrame > startFrame) { "A loop must have length" }
    }

    public val lengthFrames: Long get() = endFrame - startFrame

    public fun contains(frame: Long): Boolean = frame in startFrame until endFrame
}

/** Everything the transport and the canvas need to draw playback. */
public data class PlaybackState(
    val transport: TransportState = TransportState.STOPPED,
    val positionFrames: Long = 0,
    val totalFrames: Long = 0,
    val sampleRate: Int = 48_000,
    val speed: PlaybackSpeed = PlaybackSpeed.Default,
    val loop: LoopRegion? = null,
    val bookmarks: List<Bookmark> = emptyList(),
    /**
     * True while the user is dragging the playhead. Scrubbing plays short grains at the finger's
     * position so the user hears where they are, which is the only way to find an edit point by
     * ear rather than by eye.
     */
    val scrubbing: Boolean = false,
    /**
     * When set, playback is comparing the processed and unprocessed versions of the same
     * moment. A/B is always available (chapter 10.6).
     */
    val comparingOriginal: Boolean = false,
) {
    public val positionMs: Long get() = positionFrames * 1_000L / sampleRate
    public val totalMs: Long get() = totalFrames * 1_000L / sampleRate
    public val isPlaying: Boolean get() = transport == TransportState.PLAYING

    public val progress: Double
        get() = if (totalFrames <= 0) 0.0 else (positionFrames.toDouble() / totalFrames).coerceIn(0.0, 1.0)

    /** The next bookmark after the playhead, for the skip control. */
    public fun nextBookmark(): Bookmark? = bookmarks.filter { it.frame > positionFrames }.minByOrNull { it.frame }

    /**
     * The bookmark "back" goes to.
     *
     * Ordinarily this is the start of the segment the playhead is in — the marker just passed.
     * But if the playhead is already within [GRACE_MS] of that marker, back goes to the one
     * *before* it instead.
     *
     * That grace window is not a refinement. Without it, pressing back while paused just after
     * a marker returns to that same marker, leaves the playhead there, and every subsequent
     * press returns it again: the control locks and the user cannot walk backwards through
     * their own markers at all.
     */
    public fun previousBookmark(): Bookmark? {
        val graceFrames = GRACE_MS * sampleRate / 1_000
        val current = bookmarks.filter { it.frame < positionFrames }.maxByOrNull { it.frame } ?: return null
        if (positionFrames - current.frame > graceFrames) return current
        return bookmarks.filter { it.frame < current.frame }.maxByOrNull { it.frame } ?: current
    }

    /** Where the playhead goes next, honouring any loop. */
    public fun advanced(byFrames: Long): PlaybackState {
        val raw = positionFrames + byFrames
        val next = when {
            loop != null && raw >= loop.endFrame -> loop.startFrame + (raw - loop.endFrame) % loop.lengthFrames
            raw >= totalFrames -> totalFrames
            else -> raw
        }
        val ended = loop == null && next >= totalFrames && totalFrames > 0
        return copy(
            positionFrames = next.coerceIn(0, totalFrames),
            transport = if (ended) TransportState.STOPPED else transport,
        )
    }

    public fun seekTo(frame: Long): PlaybackState = copy(positionFrames = frame.coerceIn(0, totalFrames))

    public companion object {
        /** How long after a marker "back" still means "return to this one". */
        public const val GRACE_MS: Long = 2_000
    }
}

/**
 * The legal transitions of the playback state machine (chapter 8).
 */
public object PlaybackMachine {

    public enum class Command { PLAY, PAUSE, STOP, SEEK, SCRUB_START, SCRUB_END }

    public fun next(current: TransportState, command: Command): TransportState? = when (command) {
        // Playing from a paused recording is legal and is what makes review-in-place work:
        // the user pauses the take, listens back, and resumes without leaving the workspace.
        Command.PLAY -> when (current) {
            TransportState.STOPPED, TransportState.PLAYBACK_PAUSED, TransportState.IDLE,
            TransportState.ARMED, TransportState.RECORDING_PAUSED,
            -> TransportState.PLAYING

            else -> null
        }

        Command.PAUSE -> when (current) {
            TransportState.PLAYING -> TransportState.PLAYBACK_PAUSED
            else -> null
        }

        Command.STOP -> when (current) {
            TransportState.PLAYING, TransportState.PLAYBACK_PAUSED -> TransportState.STOPPED
            else -> null
        }

        // Seeking never changes whether audio is running. A transport that stops on seek makes
        // scrubbing through a recording impossible.
        Command.SEEK -> current

        Command.SCRUB_START -> when (current) {
            TransportState.PLAYING, TransportState.PLAYBACK_PAUSED, TransportState.STOPPED -> current
            else -> null
        }

        Command.SCRUB_END -> when (current) {
            TransportState.PLAYING, TransportState.PLAYBACK_PAUSED, TransportState.STOPPED -> current
            else -> null
        }
    }

    public fun isLegal(current: TransportState, command: Command): Boolean = next(current, command) != null
}

/**
 * The latency policy of chapter 8.
 *
 * Playback must be audible within 100 ms of the tap (chapter 1.6). That budget is spent, not
 * assumed: the device buffer is sized small enough that the first block reaches the speaker
 * quickly, and the first block is rendered from the timeline directly rather than waiting for
 * any file to be decoded in full.
 */
public object PlaybackPolicy {

    /**
     * The output buffer. 40 ms is small enough to keep the tap-to-audible budget and large
     * enough to survive a scheduler hiccup on a mid-range device without a dropout.
     */
    public const val OUTPUT_BUFFER_MS: Int = 40

    /**
     * How much audio is rendered ahead of the playhead. Two buffers of headroom means a
     * momentary stall in rendering does not become an audible gap.
     */
    public const val RENDER_AHEAD_BUFFERS: Int = 2

    /** Grain length while scrubbing. Long enough to have pitch, short enough to track a finger. */
    public const val SCRUB_GRAIN_MS: Int = 60

    public fun outputBufferFrames(sampleRate: Int): Int =
        (OUTPUT_BUFFER_MS * sampleRate / 1_000).coerceAtLeast(256)

    public fun scrubGrainFrames(sampleRate: Int): Int = SCRUB_GRAIN_MS * sampleRate / 1_000

    init {
        check(OUTPUT_BUFFER_MS.toLong() < PerformanceBudget.TAP_TO_AUDIBLE_MS) {
            "The output buffer alone would exceed the tap-to-audible budget"
        }
    }
}
