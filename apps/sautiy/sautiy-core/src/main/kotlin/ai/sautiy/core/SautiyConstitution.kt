package ai.sautiy.core

/**
 * Editorial Bible chapter 1, expressed as code.
 *
 * The constitution is not prose that happens to live next to a codebase — the budgets below
 * are referenced by the engine (buffer sizing, flush cadence, recovery windows) and asserted
 * by tests, so that a regression against a principle breaks the build rather than quietly
 * degrading the product.
 */
public object SautiyConstitution {

    /** Application name, exactly as it is permitted to appear. */
    public const val PRODUCT_NAME: String = "SAUTIY™"

    /** Author of record. */
    public const val AUTHOR: String = "Imam Ahmad Sulaimiy"

    /** Author's title of record. */
    public const val AUTHOR_TITLE: String = "Senior Software Engineer, Product Architect & Founder"

    public const val ABOUT: String =
        "SAUTIY™ is engineered to deliver an elegant, dependable and professional mobile audio " +
            "production experience with intuitive workflows, premium design, and high-quality " +
            "recording, editing and publishing capabilities for creators, educators, reciters, " +
            "lecturers, broadcasters and podcasters."

    /**
     * The seven design principles in constitutional priority order (chapter 1.4). Where two
     * conflict, the earlier ordinal wins. Consulted by review tooling and the About screen.
     */
    public enum class Principle(public val ordinalRank: Int, public val statement: String) {
        IMMEDIATE(1, "Record begins within 300 ms. Playback begins within 100 ms. Nothing blocks."),
        OBVIOUS(2, "A first-time user starts recording in three seconds with no instruction."),
        REVERSIBLE(3, "Every edit undoes. Every deletion recovers."),
        CALM(4, "No badge, no nag, no interruption, no unearned celebration."),
        HONEST(5, "The meter shows the truth. Clipping is shown as clipping."),
        DEEP(6, "Real compression, real EQ, real limiting, real loudness targets."),
        BEAUTIFUL(7, "Spacing, type, alignment and motion of a standard that reads as luxury."),
    }
}

/**
 * The measurable success criteria of chapter 1.6. Every value is a hard ceiling, not a target:
 * exceeding one is a defect with a bug number, not a trade-off to be discussed.
 */
public object PerformanceBudget {

    /** Cold process start to an armed, interactive recording workspace. */
    public const val COLD_START_TO_ARMED_MS: Long = 700

    /** Tap on the record control to the first sample committed to the capture buffer. */
    public const val TAP_TO_FIRST_SAMPLE_MS: Long = 300

    /** Tap on play to audible output. */
    public const val TAP_TO_AUDIBLE_MS: Long = 100

    /** Maximum audio that may be lost if the process is killed without warning. */
    public const val MAX_SAMPLE_LOSS_ON_KILL_MS: Long = 2_000

    /**
     * How often the capture pipeline forces durable bytes to disk. Derived from — and kept
     * comfortably inside — [MAX_SAMPLE_LOSS_ON_KILL_MS].
     */
    public const val CAPTURE_FLUSH_INTERVAL_MS: Long = 1_000

    /** Frame budget for the live waveform at 60 fps. */
    public const val FRAME_BUDGET_MS: Double = 16.67

    /**
     * Target latency of the capture ring buffer. Small enough that monitoring feels live,
     * large enough to survive scheduler jitter on mid-range hardware.
     */
    public const val CAPTURE_BUFFER_MS: Int = 20

    /** Maximum taps to export a finished recording (chapter 1.6). */
    public const val MAX_TAPS_TO_EXPORT: Int = 3

    /** Maximum taps to begin recording from a cold launch. */
    public const val MAX_TAPS_TO_RECORD: Int = 1

    /** Minimum interactive target size, in density-independent pixels (chapter 17). */
    public const val MIN_TOUCH_TARGET_DP: Int = 48

    /**
     * Ceiling on decoded audio held in memory before the engine switches to a
     * memory-mapped/streaming strategy. 128 MiB of 32-bit float mono is roughly 12 minutes at
     * 44.1 kHz; beyond that SAUTIY streams from disk rather than growing the heap.
     */
    public const val IN_MEMORY_AUDIO_CEILING_BYTES: Long = 128L * 1024 * 1024
}
