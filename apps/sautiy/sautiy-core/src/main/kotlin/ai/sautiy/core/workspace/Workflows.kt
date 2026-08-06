package ai.sautiy.core.workspace

/**
 * The six things people actually do, written down as tap counts — Phase Ω, directive 2.
 *
 * Friction is invisible from inside a codebase. Every step feels justified to the person who added
 * it, and nobody ever adds a seventh tap on purpose. The only way to see it is to write the taps
 * down and read the total, which is what this file is for.
 *
 * Each workflow lists its steps in order, each step names the single thing the user does, and the
 * budget is the number of taps beyond which the workflow has stopped being direct. A test asserts
 * every workflow is inside its budget, so a step added later has to be argued for against a number
 * rather than slipped in.
 *
 * **This is a specification, not a measurement.** It states what the interface is built to do; it
 * does not prove a thumb can do it. That needs a person with a phone, and it is recorded as unproven
 * rather than claimed.
 */
public object Workflows {

    /** One thing the user does, and why it cannot be removed. */
    public data class Step(
        val tap: String,
        /** Why this step exists. A step whose justification is weak is the one to delete next. */
        val because: String,
    )

    public data class Workflow(
        val name: String,
        val steps: List<Step>,
        /** The most taps this may ever take. Exceeding it fails the build. */
        val budget: Int,
        /** What the user was trying to achieve, in their words. */
        val goal: String,
    ) {
        public val taps: Int get() = steps.size
        public val isWithinBudget: Boolean get() = taps <= budget
        public val slack: Int get() = budget - taps
    }

    /**
     * Record. **One tap.**
     *
     * This is the number that matters most and the one most apps get wrong: a recorder that asks
     * anything at all before recording has already lost the thought the user was trying to capture.
     * No permission prompt in the path (asked on first launch, not at the moment of pressing), no
     * quality dialogue, no name, no confirmation. Press, and it is recording.
     */
    public val record: Workflow = Workflow(
        name = "Record",
        goal = "Capture this, now, before I lose it",
        budget = 1,
        steps = listOf(
            Step("Record", "Nothing may come between the thought and the microphone."),
        ),
    )

    /** Play. One tap, and it starts from where the playhead already is. */
    public val play: Workflow = Workflow(
        name = "Play",
        goal = "Hear what I just recorded",
        budget = 1,
        steps = listOf(
            Step("Play", "The playhead is already somewhere; play means play from there."),
        ),
    )

    /**
     * Improve a recording. **Zero taps.**
     *
     * The one workflow that got shorter by disappearing. Cleanup runs when a take ends, so the user
     * does nothing at all to get the better result — and the Original / Enhanced pair on the canvas
     * is how they know it happened and how they undo it.
     *
     * Kept in this list precisely *because* it is zero, so that anybody who later adds a tap to it
     * has to argue against a number rather than against a habit.
     */
    public val improve: Workflow = Workflow(
        name = "Improve",
        goal = "Have this sound better than my phone recorded it",
        budget = 0,
        steps = emptyList(),
    )

    /**
     * Refine it deliberately. **Two taps.**
     *
     * Studio, then an outcome. Distinct in purpose from [improve] rather than a faster version of
     * it: Auto Improve produces a result, and this is where somebody who wants a different result
     * goes to choose one.
     *
     * A one-tap version of this was tried and removed. "Enhance Voice" ran the same chain that now
     * runs automatically, so pressing it changed nothing audible — a control that appears broken.
     * "Studio Voice" was that chain plus a Podcast room, which is what the Podcast card does, under
     * a name that says what it is for.
     */
    public val refine: Workflow = Workflow(
        name = "Refine",
        goal = "Make this sound the way I want rather than the way it came out",
        budget = 2,
        steps = listOf(
            Step(
                "Studio",
                "The one place the sound is decided, and the only place it changes on purpose.",
            ),
            Step(
                "Podcast",
                "An outcome named for the job it does, applied to what is playing and to what will be exported.",
            ),
        ),
    )

    /**
     * Save my own sound. **Three taps.**
     *
     * Studio, Save this as my own sound, then a suggested name. The name is a tap rather than typing
     * because naming is where people abandon a save — asked to invent one they close the sheet, and
     * the sound is lost. Typing a custom name is available and is not on this path.
     */
    public val saveSound: Workflow = Workflow(
        name = "Save my sound",
        goal = "Keep this exact sound so I never rebuild it",
        budget = 3,
        steps = listOf(
            Step("Studio", "Where the sound already is."),
            Step(
                "Save this as my own sound",
                "Saving is offered rather than automatic: a sound worth keeping is a judgement, and the app guessing which takes are worth keeping would fill the list with rubbish.",
            ),
            Step("My Qur'an Voice", "A suggested name is one tap; inventing one is where saves die."),
        ),
    )

    /**
     * Recall a saved sound. **Two taps.**
     *
     * The whole point of Voice DNA. Studio, then the row. The row *is* the button — rename and
     * delete sit beneath it rather than behind it, because putting them behind the same tap would
     * have thrown away the gesture the feature exists for.
     */
    public val recallSound: Workflow = Workflow(
        name = "Recall my sound",
        goal = "Put my voice back exactly as I left it",
        budget = 2,
        steps = listOf(
            Step("Studio", "Where the sounds live."),
            Step("My Qur'an Voice", "The row is the button. One tap, complete sound."),
        ),
    )

    /**
     * Export. **Three taps.**
     *
     * Export, the format, then Export — and the last-used format is already selected, so the common
     * case is two. The destination picker is the system's and is not counted, because those taps are
     * Android's and removing them would mean writing somewhere the user then has to go and find.
     */
    public val export: Workflow = Workflow(
        name = "Export",
        goal = "Get a file I can publish",
        budget = 3,
        steps = listOf(
            Step(
                "Export",
                "The panel is where the format lives, and the format is the one decision an export genuinely needs from the user.",
            ),
            Step("MP3", "Already selected if it was used last, so this tap is usually free."),
            Step("Export", "Opens the system destination picker."),
        ),
    )

    /**
     * Share. **Two taps.**
     *
     * Export, then Share. It does not require exporting first: if a file has already been written
     * this session it is reused, and if not, one is written on the way to the share sheet. Making
     * the user export *then* share would have been the same file twice and a step they could not
     * see the reason for.
     */
    public val share: Workflow = Workflow(
        name = "Share",
        goal = "Send this to someone",
        budget = 2,
        steps = listOf(
            Step(
                "Export",
                "Share lives beside Export because they are the same act with different destinations, and separating them would mean two places to look for one thing.",
            ),
            Step("Share", "Writes the file if needed, then opens the share sheet."),
        ),
    )

    /** Every workflow, for the test and for anyone auditing the friction. */
    public val all: List<Workflow> = listOf(
        record, play, improve, refine, saveSound, recallSound, export, share,
    )

    /** Total taps across every common workflow. One number to watch over releases. */
    public val totalTaps: Int get() = all.sumOf { it.taps }
}
