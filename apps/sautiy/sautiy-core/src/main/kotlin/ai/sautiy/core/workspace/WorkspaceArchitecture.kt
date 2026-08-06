package ai.sautiy.core.workspace

/**
 * Editorial Bible chapter 4 — the One-Canvas Law — as code.
 *
 * SAUTIY is not an application with screens. It is one intelligent studio. Everything a user
 * can reach is either a region of the single canvas or a panel that arrives *over* it without
 * removing it. This file is the machine-readable form of that law, and
 * `WorkspaceLawTest` fails the build if the product ever drifts from it.
 *
 * The whole navigation model of the product is the pure function
 * [WorkspaceState.contextActions] — state in, tools out. There is no router, no back stack of
 * destinations, and no place for a screen to hide.
 */

/** The fixed regions of the canvas (chapter 4.2). Their positions never change. */
public enum class Region(public val reach: ReachZone) {
    /** Truth about the session. Values change; controls barely exist here. */
    STATUS_RAIL(ReachZone.FAR),

    /** The audio itself — waveform, timeline, meters, spectrogram. */
    CANVAS(ReachZone.STRETCH),

    /** Which material exists. */
    LAYER_STRIP(ReachZone.STRETCH),

    /** The adaptive cluster: tools for whatever is selected right now. */
    CONTEXT_BAR(ReachZone.STRETCH),

    /** Immovable. Five slots, same five functions, for the life of the product. */
    TRANSPORT_DOCK(ReachZone.NATURAL),

    /** A panel over the canvas. Never a page. */
    PANEL(ReachZone.NATURAL),
}

/**
 * Thumb reachability, measured from the bottom edge of the display (chapter 3.2.4).
 *
 * A control required to complete a task may never live in [FAR] unless an equivalent control
 * also exists lower down.
 */
public enum class ReachZone(public val fromBottomFraction: ClosedFloatingPointRange<Double>) {
    NATURAL(0.00..0.35),
    STRETCH(0.35..0.65),
    FAR(0.65..1.00),
}

/** Progressive-disclosure tier (chapter 3.2.3). Nothing may exist beyond [TIER_3]. */
public enum class Tier(public val gesturesToReach: Int) {
    /** Always visible. Zero gestures. */
    TIER_1(0),

    /** One deliberate tap or drag. */
    TIER_2(1),

    /** Inside an opened panel. Two gestures. The floor of the product. */
    TIER_3(2),
}

/**
 * The twelve panels (chapter 4.4.2). Twelve panels, one canvas, zero pages.
 *
 * @param coversCanvasFraction how much of the canvas height this panel occupies. Capped by
 *   [PanelLaw.MAX_CANVAS_COVERAGE] so the waveform — the context — stays visible.
 */
public enum class Panel(public val coversCanvasFraction: Double) {
    STUDIO(0.55),
    EQUALISER(0.62),
    DYNAMICS(0.62),
    SPACE(0.50),
    ANALYSIS(0.60),
    LAYERS(0.45),
    MARKERS(0.45),
    HISTORY(0.50),
    TRANSCRIPT(0.60),
    LIBRARY(0.62),
    PROJECT(0.55),
    EXPORT(0.55),
}

/** Chapter 4.4.1, as constants the UI layer reads rather than re-deciding. */
public object PanelLaw {
    /** At most one panel is open at a time. There is no stacking, so there is no "where am I". */
    public const val MAX_SIMULTANEOUS_PANELS: Int = 1

    /** A panel never covers more than this much of the canvas height. */
    public const val MAX_CANVAS_COVERAGE: Double = 0.62

    /** A panel never covers the transport dock. This is what makes it a panel and not a page. */
    public const val MAY_COVER_TRANSPORT_DOCK: Boolean = false

    /** Close affordance, downward drag, tap on the canvas above, system back. */
    public const val REQUIRED_DISMISSAL_ROUTES: Int = 4

    /** Open-to-interactive ceiling, in milliseconds. No spinner is permitted inside this. */
    public const val OPEN_TO_INTERACTIVE_MS: Int = 220

    /** A panel may not open another panel. */
    public const val MAX_PANEL_DEPTH: Int = 1
}

/**
 * The only full destinations in SAUTIY, ever (chapter 4.1.2).
 *
 * `WORKSPACE` is the application. `SETTINGS` and `ABOUT` are genuinely outside the work — the
 * user is not making audio while reading a licence — and returning from them restores the
 * workspace exactly as it was.
 *
 * If this set ever grows, the product has become an ordinary Android app with pages, and
 * `WorkspaceLawTest` will say so.
 */
public enum class Destination {
    WORKSPACE,
    SETTINGS,
    ABOUT,
}

/** What the user is doing with time and the microphone. */
public enum class TransportState {
    /** Nothing captured yet in this session. */
    IDLE,

    /** Input is live and metered, but nothing is being written. */
    ARMED,

    RECORDING,
    RECORDING_PAUSED,
    PLAYING,
    PLAYBACK_PAUSED,

    /** Audio exists and time is stopped. */
    STOPPED,
    ;

    public val isCapturing: Boolean get() = this == RECORDING || this == RECORDING_PAUSED
    public val isMoving: Boolean get() = this == RECORDING || this == PLAYING
}

/** The phase of the Record → Review → Edit → Enhance → Export chain (chapter 4.5). */
public enum class WorkspacePhase { RECORD, REVIEW, EDIT, ENHANCE, EXPORT }

/** What the user has selected. This — not a menu — is what drives the context bar. */
public sealed interface Focus {
    /** Nothing selected. The canvas as a whole has focus. */
    public data object None : Focus

    /** A time range on the waveform, in frames. */
    public data class Range(val startFrame: Long, val endFrame: Long) : Focus {
        init {
            require(endFrame > startFrame) { "A range selection must be non-empty" }
        }

        public val lengthFrames: Long get() = endFrame - startFrame
    }

    public data class Layer(val layerId: String) : Focus

    public data class Marker(val markerId: String) : Focus
}

/**
 * A single tool the user can press.
 *
 * Every field is a law from chapter 3 or 4 attached to the thing it governs, so the rules are
 * checkable by walking the action set rather than by reading the UI code.
 */
public data class WorkspaceAction(
    val id: String,
    /** Sentence case, at most three words (chapter 3.2.2). */
    val label: String,
    val region: Region,
    val tier: Tier,
    /**
     * True if pressing this can destroy audio the user has not yet secured. Destructive
     * actions are *absent* — not disabled — while recording (chapter 4.3, safety law).
     */
    val destructive: Boolean = false,
    /** True for the single primary action of a state (chapter 3.2.2: exactly one). */
    val primary: Boolean = false,
    /** The panel this opens, if any. */
    val opens: Panel? = null,
) {
    val reach: ReachZone get() = region.reach
    val wordCount: Int get() = label.trim().split(Regex("\\s+")).size
}

/**
 * The immovable transport dock (chapter 4.2). Exactly five slots, in this order, for the life
 * of the product. A user who has learned that the red circle sits under their thumb is never
 * made wrong.
 */
public object TransportDock {
    public val MONITOR: WorkspaceAction =
        WorkspaceAction("transport.monitor", "Monitor", Region.TRANSPORT_DOCK, Tier.TIER_1)
    public val REWIND: WorkspaceAction =
        WorkspaceAction("transport.rewind", "Rewind", Region.TRANSPORT_DOCK, Tier.TIER_1)
    public val RECORD: WorkspaceAction =
        WorkspaceAction("transport.record", "Record", Region.TRANSPORT_DOCK, Tier.TIER_1, primary = true)
    public val PLAY: WorkspaceAction =
        WorkspaceAction("transport.play", "Play", Region.TRANSPORT_DOCK, Tier.TIER_1)
    public val COMMIT: WorkspaceAction =
        WorkspaceAction("transport.commit", "Export", Region.TRANSPORT_DOCK, Tier.TIER_1, opens = Panel.EXPORT)

    /** Positional order. This list is frozen; reordering it is a breaking change to muscle memory. */
    public val slots: List<WorkspaceAction> = listOf(MONITOR, REWIND, RECORD, PLAY, COMMIT)

    public const val SLOT_COUNT: Int = 5
}

/** Chapter 3.2.2 budgets, as constants the tests read. */
public object CognitiveBudget {
    public const val MAX_CONTEXT_BAR_ACTIONS: Int = 6
    public const val MAX_STATUS_RAIL_ACTIONS: Int = 2
    public const val MAX_INTERACTIVE_OUTSIDE_CANVAS: Int = 13
    public const val MAX_PRIMARY_ACTIONS_PER_STATE: Int = 1
    public const val MAX_LABEL_WORDS: Int = 3
}

/**
 * The complete state of the studio. Everything the user can see is derived from this; nothing
 * is navigated to.
 */
public data class WorkspaceState(
    val transport: TransportState = TransportState.IDLE,
    val focus: Focus = Focus.None,
    val hasAudio: Boolean = false,
    val layerCount: Int = 0,
    val markerCount: Int = 0,
    val openPanel: Panel? = null,
    val canUndo: Boolean = false,
    val canRedo: Boolean = false,
    val destination: Destination = Destination.WORKSPACE,
) {

    /**
     * The phase of the journey (chapter 4.5). Derived, never routed to — which is precisely
     * why the user can move backwards through the chain without losing anything.
     */
    public val phase: WorkspacePhase
        get() = when {
            openPanel == Panel.EXPORT -> WorkspacePhase.EXPORT
            openPanel in setOf(Panel.STUDIO, Panel.EQUALISER, Panel.DYNAMICS, Panel.SPACE) -> WorkspacePhase.ENHANCE
            transport.isCapturing || transport == TransportState.ARMED -> WorkspacePhase.RECORD
            focus is Focus.Range || focus is Focus.Layer -> WorkspacePhase.EDIT
            hasAudio -> WorkspacePhase.REVIEW
            else -> WorkspacePhase.RECORD
        }

    /**
     * The adaptive context bar (chapter 4.3) — the entire navigation model of SAUTIY, as one
     * pure function. State in, tools out.
     *
     * While recording, destructive tools are not disabled; they are absent. A control that
     * cannot be pressed is still a control the eye must process.
     */
    public fun contextActions(): List<WorkspaceAction> {
        val actions = when {
            transport == TransportState.RECORDING || transport == TransportState.ARMED -> listOf(
                action("ctx.marker", "Marker", Tier.TIER_1),
                action("ctx.layer", "Layer", Tier.TIER_2),
                action("ctx.monitorLevel", "Input", Tier.TIER_2),
                action("ctx.noise", "Noise", Tier.TIER_2, opens = Panel.ANALYSIS),
            )

            transport == TransportState.RECORDING_PAUSED -> listOf(
                action("ctx.marker", "Marker", Tier.TIER_1),
                action("ctx.discardTake", "Discard take", Tier.TIER_2, destructive = true),
            )

            transport == TransportState.PLAYING || transport == TransportState.PLAYBACK_PAUSED -> listOf(
                action("ctx.speed", "Speed", Tier.TIER_2),
                action("ctx.loop", "Loop", Tier.TIER_2),
                action("ctx.marker", "Marker", Tier.TIER_1),
                action("ctx.compare", "Compare", Tier.TIER_2),
            )

            focus is Focus.Range -> listOf(
                action("ctx.cut", "Cut", Tier.TIER_2, destructive = true),
                action("ctx.split", "Split", Tier.TIER_2),
                action("ctx.fade", "Fade", Tier.TIER_2),
                action("ctx.silence", "Silence", Tier.TIER_2, destructive = true),
                action("ctx.gain", "Gain", Tier.TIER_2),
                action("ctx.deselect", "Deselect", Tier.TIER_1),
            )

            focus is Focus.Layer -> listOf(
                action("ctx.rename", "Rename", Tier.TIER_2),
                action("ctx.mute", "Mute", Tier.TIER_2),
                action("ctx.solo", "Solo", Tier.TIER_2),
                action("ctx.layerGain", "Gain", Tier.TIER_2),
                action("ctx.duplicate", "Duplicate", Tier.TIER_2),
                action("ctx.deleteLayer", "Delete layer", Tier.TIER_2, destructive = true),
            )

            focus is Focus.Marker -> listOf(
                action("ctx.renameMarker", "Rename", Tier.TIER_2),
                action("ctx.jump", "Jump", Tier.TIER_1),
                action("ctx.deleteMarker", "Delete", Tier.TIER_2, destructive = true),
            )

            hasAudio -> listOf(
                action("ctx.undo", "Undo", Tier.TIER_1),
                action("ctx.redo", "Redo", Tier.TIER_1),
                action("ctx.enhance", "Enhance", Tier.TIER_2, opens = Panel.STUDIO),
                action("ctx.trim", "Trim", Tier.TIER_2),
                action("ctx.analysis", "Quality", Tier.TIER_2, opens = Panel.ANALYSIS),
            )

            else -> listOf(
                action("ctx.input", "Input", Tier.TIER_2),
                action("ctx.quality", "Quality", Tier.TIER_2),
                action("ctx.library", "Library", Tier.TIER_2, opens = Panel.LIBRARY),
                action("ctx.projects", "Projects", Tier.TIER_2, opens = Panel.PROJECT),
            )
        }

        // Chapter 4.3, safety law: while capturing, a destructive tool is absent, not disabled.
        // RECORDING_PAUSED is the deliberate exception — discarding a take is the whole point
        // of pausing — and it is the only place a destructive action survives this filter.
        return if (transport == TransportState.RECORDING) {
            actions.filterNot { it.destructive }
        } else {
            actions
        }
    }

    /** Interactive elements in the status rail (chapter 4.2: values, not controls). */
    public fun statusRailActions(): List<WorkspaceAction> = listOf(
        WorkspaceAction("rail.project", "Project", Region.STATUS_RAIL, Tier.TIER_2, opens = Panel.LIBRARY),
        WorkspaceAction("rail.settings", "Settings", Region.STATUS_RAIL, Tier.TIER_2),
    )

    /**
     * Every interactive element visible in this state, outside the canvas and layer strip.
     * This is what chapter 3.2.2's total budget is measured against.
     */
    public fun visibleInteractiveActions(): List<WorkspaceAction> =
        TransportDock.slots + contextActions() + statusRailActions()

    private fun action(
        id: String,
        label: String,
        tier: Tier,
        destructive: Boolean = false,
        opens: Panel? = null,
    ) = WorkspaceAction(
        id = id,
        label = label,
        region = Region.CONTEXT_BAR,
        tier = tier,
        destructive = destructive,
        opens = opens,
    )

    /** Opening a panel closes any other (chapter 4.4.1 clause 1). */
    public fun openingPanel(panel: Panel): WorkspaceState = copy(openPanel = panel)

    /** All four dismissal routes land here. */
    public fun dismissingPanel(): WorkspaceState = copy(openPanel = null)
}

/**
 * Every state the workspace can legally be in, enumerated so the laws of chapters 3 and 4 can
 * be asserted over *all* of them rather than over the handful a reviewer happened to open.
 */
public object WorkspaceStateSpace {
    public fun all(): List<WorkspaceState> {
        val focuses = listOf(
            Focus.None,
            Focus.Range(0, 44_100),
            Focus.Layer("layer-1"),
            Focus.Marker("marker-1"),
        )
        val panels: List<Panel?> = listOf(null) + Panel.entries

        return buildList {
            for (transport in TransportState.entries) {
                for (focus in focuses) {
                    for (hasAudio in listOf(false, true)) {
                        for (panel in panels) {
                            // A selection cannot exist before any audio does.
                            if (!hasAudio && focus !is Focus.None) continue
                            add(
                                WorkspaceState(
                                    transport = transport,
                                    focus = focus,
                                    hasAudio = hasAudio,
                                    layerCount = if (hasAudio) 1 else 0,
                                    openPanel = panel,
                                    canUndo = hasAudio,
                                ),
                            )
                        }
                    }
                }
            }
        }
    }
}
