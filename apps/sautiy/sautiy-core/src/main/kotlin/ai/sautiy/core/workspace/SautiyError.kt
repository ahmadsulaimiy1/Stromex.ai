package ai.sautiy.core.workspace

/**
 * Editorial Bible chapter 3.2.6 — error posture — made structurally impossible to violate.
 *
 * An error in SAUTIY is a state of the world, not a failure of the user. Every error carries
 * three parts in a fixed order: what is true, what that means, and what fixes it. Because the
 * type has no constructor without all three, an engineer cannot ship "Something went wrong."
 */
public data class SautiyError(
    /** What is true. Stated as fact, about the world, never about the user. */
    val fact: String,
    /** What that means for the task in hand. */
    val consequence: String,
    /** The single control that fixes it. */
    val remedy: Remedy,
    /** Where it is shown. Errors appear in place, next to the affected thing. */
    val presentation: Presentation = Presentation.IN_PLACE,
) {
    init {
        require(fact.isNotBlank()) { "An error must state what is true" }
        require(consequence.isNotBlank()) { "An error must state what it means" }
        require(!fact.contains("Sorry", ignoreCase = true)) {
            "Chapter 2.9: never apologise — it wastes a line and helps nobody"
        }
        require(!fact.contains("!")) { "Chapter 2.9: no exclamation marks" }
        require(!consequence.contains("!")) { "Chapter 2.9: no exclamation marks" }
        require(!fact.contains("you ", ignoreCase = true) || !fact.contains("failed", ignoreCase = true)) {
            "Chapter 3.2.6: an error never blames the user"
        }
    }

    /** The single action offered. One remedy, never a menu of them. */
    public data class Remedy(val label: String, val id: String) {
        init {
            require(label.trim().split(Regex("\\s+")).size <= CognitiveBudget.MAX_LABEL_WORDS) {
                "A remedy label is at most ${CognitiveBudget.MAX_LABEL_WORDS} words"
            }
        }
    }

    /**
     * Errors never appear as modal dialogs unless the user is about to lose data
     * (chapter 3.2.6).
     */
    public enum class Presentation { IN_PLACE, MODAL }

    public companion object {
        public val MicrophoneBusy: SautiyError = SautiyError(
            fact = "The microphone is in use by another app.",
            consequence = "Recording cannot start.",
            remedy = Remedy("Retry", "error.retryInput"),
        )

        public val MicrophoneDenied: SautiyError = SautiyError(
            fact = "SAUTIY does not have microphone access.",
            consequence = "Recording is unavailable until access is granted.",
            remedy = Remedy("Open settings", "error.openSettings"),
        )

        public val StorageFull: SautiyError = SautiyError(
            fact = "This device has no free storage.",
            consequence = "The recording has stopped and everything captured so far is saved.",
            remedy = Remedy("Free space", "error.manageStorage"),
            presentation = Presentation.MODAL,
        )

        public val RouteChanged: SautiyError = SautiyError(
            fact = "The audio input changed while recording.",
            consequence = "Recording paused at the moment the input was lost.",
            remedy = Remedy("Resume", "error.resume"),
        )

        public val ExportFailed: SautiyError = SautiyError(
            fact = "The chosen destination rejected the file.",
            consequence = "Nothing was written and the recording is unchanged.",
            remedy = Remedy("Choose destination", "error.chooseDestination"),
        )

        public val FileUnreadable: SautiyError = SautiyError(
            fact = "This recording's audio file is missing or unreadable.",
            consequence = "It cannot be played or exported.",
            remedy = Remedy("Recover", "error.recover"),
        )

        public val all: List<SautiyError> = listOf(
            MicrophoneBusy, MicrophoneDenied, StorageFull, RouteChanged, ExportFailed, FileUnreadable,
        )
    }
}

/**
 * Editorial Bible chapter 3.2.7 — the interruption law.
 *
 * SAUTIY interrupts the user in exactly four situations. This enum is closed; adding a fifth
 * member is a constitutional amendment, and `WorkspaceLawTest` will notice.
 *
 * There are no rating prompts, feature tours, tips, newsletters or badges.
 */
public enum class Interruption(public val justification: String) {
    STORAGE_EXHAUSTING(
        "Storage will run out within two minutes at the current bitrate.",
    ),
    INPUT_LOST(
        "The microphone was taken by another app, or the audio route changed mid-recording.",
    ),
    UNRECOVERABLE_DESTRUCTION(
        "A destructive action would discard audio that cannot be recovered from the trash.",
    ),
    CRASH_RECOVERY_AVAILABLE(
        "An unrecovered recording from a previous run exists. Offered once, on next launch.",
    ),
    ;

    public companion object {
        /** Chapter 3.2.7 permits exactly four. */
        public const val PERMITTED_COUNT: Int = 4
    }
}
