package ai.sautiy.core.record

import ai.sautiy.core.PerformanceBudget
import ai.sautiy.core.audio.CaptureQuality
import ai.sautiy.core.workspace.Interruption
import ai.sautiy.core.workspace.SautiyError
import ai.sautiy.core.workspace.TransportState

/**
 * Editorial Bible chapter 7 — the capture state machine, with no Android in it.
 *
 * Everything that decides *what should happen* during a recording lives here: which
 * transitions are legal, when to flush, when storage has become a problem, what a take is, and
 * what to offer after a crash. The Android layer owns only the parts that genuinely need a
 * device — opening `AudioRecord`, running the capture thread, holding a wake lock.
 *
 * The split exists so that the rules of chapter 7 can be tested exhaustively on a plain JVM,
 * rather than being verified by recording on a phone and hoping.
 */

/** A single continuous stretch of capture. Pausing and resuming stays within one take. */
public data class Take(
    val id: String,
    val fileName: String,
    val quality: CaptureQuality,
    val frameCount: Long = 0,
    val startedAtEpochMs: Long = 0,
    val markers: List<Marker> = emptyList(),
) {
    public val durationSeconds: Double get() = frameCount.toDouble() / quality.format.sampleRate

    public val durationMs: Long get() = frameCount * 1_000L / quality.format.sampleRate
}

/** A point the user marked while recording, so they can find it later without listening back. */
public data class Marker(
    val id: String,
    val frame: Long,
    val label: String = "",
)

/**
 * What the user can see about a recording in progress.
 *
 * Every field is a fact the status rail or the canvas displays. Nothing is derived twice, so
 * the timer and the waveform cannot disagree about how long the recording is.
 */
public data class RecordingState(
    val transport: TransportState = TransportState.IDLE,
    val quality: CaptureQuality = CaptureQuality.STUDIO,
    val take: Take? = null,
    val elapsedFrames: Long = 0,
    val peakLinear: Float = 0f,
    val rmsLinear: Double = 0.0,
    val clippedSampleCount: Int = 0,
    /**
     * Free storage, or null when it has not been measured yet.
     *
     * Null rather than [Long.MAX_VALUE], which is what this used to default to. That default was not
     * harmless stand-in text: `Long.MAX_VALUE` divided by the studio byte rate is 26,687,997,791
     * hours, and the workspace rendered it literally as **"26687997791 h left"** on the first screen
     * anybody sees. Three million years of headroom, asserted before a single byte had been counted.
     *
     * Caught in a screenshot diagnostic, and it is the same defect as the hard-coded −62 dB noise
     * floor: a number the app had not measured, stated as though it had. The Trust Principle does not
     * distinguish between exaggerating quality and exaggerating capacity. An unmeasured quantity has
     * to be absent, so that whatever renders it has no choice but to say nothing.
     */
    val freeBytes: Long? = null,
    val error: SautiyError? = null,
    val pendingInterruption: Interruption? = null,
) {
    public val elapsedMs: Long get() = elapsedFrames * 1_000L / quality.format.sampleRate

    public val isCapturing: Boolean get() = transport.isCapturing

    /**
     * Seconds of recording the remaining storage can hold, at the quality actually in use — or null
     * while [freeBytes] is unmeasured, so nothing downstream can print a figure nobody counted.
     */
    public val secondsRemaining: Long? get() = freeBytes?.let { quality.secondsAvailable(it) }

    /**
     * Chapter 3.2.7 permits an interruption when storage will run out within two minutes.
     * Anything earlier is nagging; anything later is too late to act on.
     *
     * False while storage is unmeasured. Not knowing is not the same as being fine, but interrupting
     * a recording on the strength of a number we never took would be worse than staying quiet.
     */
    public val storageIsCritical: Boolean
        get() = secondsRemaining?.let { it <= STORAGE_WARNING_SECONDS } ?: false

    /** True once the input has clipped. Shown, never hidden (chapter 1.4 principle 5). */
    public val hasClipped: Boolean get() = clippedSampleCount > 0

    /**
     * A single honest quality score, 0..100, for the gauge on the canvas.
     *
     * Deliberately built from things that are *measured* — headroom, clipping, level — and not
     * from anything speculative. A score a user cannot explain is a score they cannot act on,
     * so each deduction below corresponds to a sentence the analysis panel can print.
     */
    public fun qualityScore(noiseFloorDb: Double): Int {
        var score = 100

        // Clipping is the only unrecoverable capture fault, and is penalised as such.
        if (clippedSampleCount > 0) score -= 40

        val peakDb = ai.sautiy.core.audio.Decibels.fromLinear(peakLinear.toDouble())
        when {
            peakDb > -1.0 -> score -= 20 // no headroom left
            // A peak at −34 dBFS needs 33 dB of gain to reach a delivery level, and that gain
            // lifts the room with it. This is a serious fault, not a minor one.
            peakDb < -30.0 -> score -= 35
            peakDb < -18.0 -> score -= 10
        }

        val signalToNoise = peakDb - noiseFloorDb
        when {
            signalToNoise < 20 -> score -= 30
            signalToNoise < 35 -> score -= 15
            signalToNoise < 50 -> score -= 5
        }
        return score.coerceIn(0, 100)
    }

    public companion object {
        public const val STORAGE_WARNING_SECONDS: Long = 120
    }
}

/**
 * The legal transitions of the capture state machine (chapter 7).
 *
 * Written as an explicit table rather than as scattered `if` statements so that the illegal
 * transitions are as visible as the legal ones — "stop while idle" and "resume while playing"
 * are exactly the paths that produce a zero-length file or a stuck UI in a recorder that grew
 * its transitions organically.
 */
public object RecordingMachine {

    public enum class Command { ARM, START, PAUSE, RESUME, STOP, DISCARD, FAIL }

    /** Returns the state after [command], or null if the command is not legal here. */
    public fun next(current: TransportState, command: Command): TransportState? = when (command) {
        Command.ARM -> when (current) {
            TransportState.IDLE, TransportState.STOPPED -> TransportState.ARMED
            else -> null
        }

        Command.START -> when (current) {
            // Recording can begin from idle without arming first: chapter 3.2.1 requires one
            // tap from cold launch, and requiring an arm step would make it two.
            TransportState.IDLE, TransportState.ARMED, TransportState.STOPPED,
            TransportState.PLAYBACK_PAUSED,
            -> TransportState.RECORDING

            else -> null
        }

        Command.PAUSE -> when (current) {
            TransportState.RECORDING -> TransportState.RECORDING_PAUSED
            else -> null
        }

        Command.RESUME -> when (current) {
            TransportState.RECORDING_PAUSED -> TransportState.RECORDING
            else -> null
        }

        Command.STOP -> when (current) {
            TransportState.RECORDING, TransportState.RECORDING_PAUSED -> TransportState.STOPPED
            else -> null
        }

        Command.DISCARD -> when (current) {
            TransportState.RECORDING_PAUSED -> TransportState.IDLE
            else -> null
        }

        // Losing the microphone mid-recording pauses rather than stops, so the take survives
        // and the user can resume when the other app lets go (chapter 3.2.7).
        Command.FAIL -> when (current) {
            TransportState.RECORDING -> TransportState.RECORDING_PAUSED
            else -> null
        }
    }

    public fun isLegal(current: TransportState, command: Command): Boolean = next(current, command) != null
}

/**
 * The durability policy of chapter 1.3.5.
 *
 * Capture writes continuously and forces bytes to disk on a fixed cadence, so a process kill
 * costs at most one flush interval. This object is where that promise is made arithmetic
 * rather than aspirational.
 */
public object CapturePolicy {

    /** Frames between forced flushes at [sampleRate]. */
    public fun flushIntervalFrames(sampleRate: Int): Long =
        PerformanceBudget.CAPTURE_FLUSH_INTERVAL_MS * sampleRate / 1_000

    /** Worst-case audio lost if the process dies immediately before a flush. */
    public fun worstCaseLossMs(): Long = PerformanceBudget.CAPTURE_FLUSH_INTERVAL_MS

    /** The device read buffer, sized from the constitutional capture latency. */
    public fun captureBufferFrames(sampleRate: Int): Int =
        (PerformanceBudget.CAPTURE_BUFFER_MS * sampleRate / 1_000).coerceAtLeast(256)

    init {
        check(worstCaseLossMs() <= PerformanceBudget.MAX_SAMPLE_LOSS_ON_KILL_MS) {
            "The flush cadence violates the constitutional sample-loss ceiling"
        }
    }
}

/**
 * Crash recovery (chapter 1.3.5 and 3.2.7).
 *
 * A take is "unrecovered" when a capture file exists on disk that no project claims. Because
 * the capture format is WAV written incrementally, that file is already playable — recovery is
 * a matter of noticing it and offering it, not of repairing anything.
 */
public object CrashRecovery {

    public data class Candidate(
        val fileName: String,
        val frameCount: Long,
        val sampleRate: Int,
        val lastModifiedEpochMs: Long,
    ) {
        public val durationSeconds: Double get() = frameCount.toDouble() / sampleRate
    }

    /**
     * Filters the candidates worth offering.
     *
     * Sub-second fragments are discarded rather than offered: a recording the user made by
     * brushing the control and immediately killing the app is noise, and offering to recover it
     * on next launch spends one of the four permitted interruptions on nothing.
     */
    public const val MINIMUM_RECOVERABLE_SECONDS: Double = 1.0

    public fun worthOffering(candidates: List<Candidate>): List<Candidate> =
        candidates
            .filter { it.durationSeconds >= MINIMUM_RECOVERABLE_SECONDS }
            .sortedByDescending { it.lastModifiedEpochMs }

    /** Chapter 3.2.7: offered once, on next launch, and never again. */
    public fun interruptionFor(candidates: List<Candidate>): Interruption? =
        if (worthOffering(candidates).isEmpty()) null else Interruption.CRASH_RECOVERY_AVAILABLE
}
