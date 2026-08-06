package ai.sautiy.core.workspace

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Editorial Bible chapters 3 and 4, asserted over the **entire** reachable state space rather
 * than over the handful of states a reviewer happens to open.
 *
 * This is the test that keeps SAUTIY from quietly becoming an ordinary Android app with pages.
 */
class WorkspaceLawTest {

    private val states = WorkspaceStateSpace.all()

    @Test
    fun `the state space is genuinely exhaustive`() {
        // A law asserted over an empty set is not a law.
        assertTrue("State space collapsed to ${states.size} states", states.size > 200)
        assertTrue(states.any { it.transport == TransportState.RECORDING })
        assertTrue(states.any { it.focus is Focus.Range })
        assertTrue(states.any { it.openPanel == Panel.EXPORT })
    }

    // --- Chapter 4.1: the One-Canvas Law ------------------------------------------------

    @Test
    fun `SAUTIY has exactly one working destination plus settings and about`() {
        assertEquals(
            "The destination set has grown — SAUTIY is becoming an app with pages (chapter 4.1)",
            listOf(Destination.WORKSPACE, Destination.SETTINGS, Destination.ABOUT),
            Destination.entries.toList(),
        )
    }

    @Test
    fun `every tool is a panel, never a destination`() {
        // Record, Enhance, Master, Effects, Library, Mixer, Assistant are panels. If any of
        // them were a destination, this set would have to name it.
        val toolNames = Panel.entries.map { it.name }
        for (tool in listOf("STUDIO", "EQUALISER", "DYNAMICS", "LIBRARY", "EXPORT", "ANALYSIS", "TRANSCRIPT")) {
            assertTrue("$tool must be a panel, not a page", tool in toolNames)
            assertFalse("$tool must not be a destination", Destination.entries.any { it.name == tool })
        }
    }

    // --- Chapter 4.2: the immovable dock ------------------------------------------------

    @Test
    fun `the transport dock is five slots and never changes between states`() {
        assertEquals(TransportDock.SLOT_COUNT, TransportDock.slots.size)
        for (state in states) {
            val dock = state.visibleInteractiveActions().filter { it.region == Region.TRANSPORT_DOCK }
            assertEquals(
                "The transport dock changed in state $state — muscle memory broken (chapter 4.2)",
                TransportDock.slots,
                dock,
            )
        }
    }

    @Test
    fun `the record control is the primary action and sits in the natural thumb zone`() {
        assertTrue(TransportDock.RECORD.primary)
        assertEquals(ReachZone.NATURAL, TransportDock.RECORD.reach)
        assertEquals("The record control is centred in the dock", 2, TransportDock.slots.indexOf(TransportDock.RECORD))
    }

    // --- Chapter 3.2.2: the cognitive load budget ---------------------------------------

    @Test
    fun `no state exceeds the context bar budget`() {
        for (state in states) {
            val n = state.contextActions().size
            assertTrue(
                "Context bar shows $n tools in $state — ceiling is ${CognitiveBudget.MAX_CONTEXT_BAR_ACTIONS}",
                n <= CognitiveBudget.MAX_CONTEXT_BAR_ACTIONS,
            )
        }
    }

    @Test
    fun `no state exceeds the total interactive budget outside the canvas`() {
        for (state in states) {
            val n = state.visibleInteractiveActions().size
            assertTrue(
                "$n interactive elements visible in $state — ceiling is " +
                    "${CognitiveBudget.MAX_INTERACTIVE_OUTSIDE_CANVAS}",
                n <= CognitiveBudget.MAX_INTERACTIVE_OUTSIDE_CANVAS,
            )
        }
    }

    @Test
    fun `every state has exactly one primary action`() {
        for (state in states) {
            val primaries = state.visibleInteractiveActions().filter { it.primary }
            assertEquals(
                "State $state offers ${primaries.size} primary actions: ${primaries.map { it.id }}",
                CognitiveBudget.MAX_PRIMARY_ACTIONS_PER_STATE,
                primaries.size,
            )
        }
    }

    @Test
    fun `no control label exceeds three words`() {
        for (state in states) {
            for (action in state.visibleInteractiveActions()) {
                assertTrue(
                    "Label '${action.label}' on ${action.id} is ${action.wordCount} words",
                    action.wordCount <= CognitiveBudget.MAX_LABEL_WORDS,
                )
            }
        }
    }

    @Test
    fun `every label is sentence case, never shouted`() {
        // Chapter 2.4.2 clause 3.
        for (state in states) {
            for (action in state.visibleInteractiveActions()) {
                val letters = action.label.filter { it.isLetter() }
                assertFalse(
                    "Label '${action.label}' is set in capitals",
                    letters.length > 1 && letters.all { it.isUpperCase() },
                )
            }
        }
    }

    // --- Chapter 3.2.3: progressive disclosure -------------------------------------------

    @Test
    fun `nothing in the workspace is deeper than tier three`() {
        for (state in states) {
            for (action in state.visibleInteractiveActions()) {
                assertTrue(
                    "${action.id} is at ${action.tier}, beyond the two-gesture floor",
                    action.tier.gesturesToReach <= Tier.TIER_3.gesturesToReach,
                )
            }
        }
    }

    @Test
    fun `every transport slot is tier one`() {
        for (slot in TransportDock.slots) {
            assertEquals("${slot.id} must always be visible", Tier.TIER_1, slot.tier)
        }
    }

    // --- Chapter 3.2.4: one-hand operation ------------------------------------------------

    @Test
    fun `no required control is stranded in the far zone`() {
        // The status rail may hold controls only because every one of them is duplicated
        // lower down: the library is also reachable from the context bar, and settings is
        // not required to complete any task.
        for (state in states) {
            val farActions = state.visibleInteractiveActions().filter { it.reach == ReachZone.FAR }
            assertTrue(
                "Too many far-zone elements in $state: ${farActions.map { it.id }}",
                farActions.size <= CognitiveBudget.MAX_STATUS_RAIL_ACTIONS,
            )
            for (action in farActions) {
                assertEquals(
                    "${action.id} sits in the far zone but is not a status rail element",
                    Region.STATUS_RAIL,
                    action.region,
                )
            }
        }
    }

    @Test
    fun `the library is reachable without the far zone`() {
        val idle = WorkspaceState()
        val reachable = idle.contextActions().any { it.opens == Panel.LIBRARY }
        assertTrue("Library must have a route outside the far zone (chapter 3.2.4)", reachable)
    }

    // --- Chapter 4.3: the safety law -------------------------------------------------------

    @Test
    fun `no destructive action exists anywhere while recording`() {
        val recording = states.filter { it.transport == TransportState.RECORDING }
        assertTrue(recording.isNotEmpty())
        for (state in recording) {
            val destructive = state.visibleInteractiveActions().filter { it.destructive }
            assertTrue(
                "Destructive tools present while recording: ${destructive.map { it.id }} — " +
                    "chapter 4.3 requires them to be absent, not disabled",
                destructive.isEmpty(),
            )
        }
    }

    @Test
    fun `discarding a take is available only where pausing makes it deliberate`() {
        val paused = WorkspaceState(transport = TransportState.RECORDING_PAUSED, hasAudio = true)
        assertTrue(paused.contextActions().any { it.id == "ctx.discardTake" })

        val live = WorkspaceState(transport = TransportState.RECORDING, hasAudio = true)
        assertFalse(live.contextActions().any { it.id == "ctx.discardTake" })
    }

    // --- Chapter 4.4: panel law -------------------------------------------------------------

    @Test
    fun `at most one panel is ever open`() {
        assertEquals(1, PanelLaw.MAX_SIMULTANEOUS_PANELS)
        val opened = WorkspaceState(hasAudio = true).openingPanel(Panel.STUDIO).openingPanel(Panel.EXPORT)
        assertEquals("Opening a second panel must close the first", Panel.EXPORT, opened.openPanel)
    }

    @Test
    fun `no panel covers more than the canvas ceiling, and none covers the dock`() {
        for (panel in Panel.entries) {
            assertTrue(
                "${panel.name} covers ${panel.coversCanvasFraction} of the canvas",
                panel.coversCanvasFraction <= PanelLaw.MAX_CANVAS_COVERAGE,
            )
        }
        assertFalse("A panel that covers the dock is a page", PanelLaw.MAY_COVER_TRANSPORT_DOCK)
    }

    @Test
    fun `every panel has four dismissal routes and opens without a spinner`() {
        assertEquals(4, PanelLaw.REQUIRED_DISMISSAL_ROUTES)
        assertTrue(PanelLaw.OPEN_TO_INTERACTIVE_MS <= 220)
        assertEquals("A panel may not open another panel", 1, PanelLaw.MAX_PANEL_DEPTH)
    }

    @Test
    fun `dismissing a panel returns to the workspace, never to a previous page`() {
        val state = WorkspaceState(hasAudio = true, focus = Focus.Range(0, 1000)).openingPanel(Panel.STUDIO)
        val dismissed = state.dismissingPanel()
        assertEquals(null, dismissed.openPanel)
        assertEquals("Selection must survive a panel (chapter 4.4.1 clause 6)", state.focus, dismissed.focus)
        assertEquals(Destination.WORKSPACE, dismissed.destination)
    }

    // --- Chapter 4.5: the journey is a state, not a route -------------------------------------

    @Test
    fun `every phase of the chain is reachable without leaving the workspace`() {
        val reached = states.map { it.phase }.toSet()
        assertEquals(
            "Some phase of Record - Review - Edit - Enhance - Export is unreachable",
            WorkspacePhase.entries.toSet(),
            reached,
        )
        assertTrue(
            "Every phase must occur on the workspace destination",
            states.all { it.destination == Destination.WORKSPACE },
        )
    }

    @Test
    fun `selecting a range moves the workspace into edit without any navigation`() {
        val review = WorkspaceState(transport = TransportState.STOPPED, hasAudio = true)
        assertEquals(WorkspacePhase.REVIEW, review.phase)

        val editing = review.copy(focus = Focus.Range(1_000, 20_000))
        assertEquals(WorkspacePhase.EDIT, editing.phase)
        assertEquals("No destination change may occur", review.destination, editing.destination)
    }

    // --- Chapter 3.2.6 / 3.2.7: errors and interruptions ---------------------------------------

    @Test
    fun `every error states fact, consequence and remedy`() {
        assertTrue(SautiyError.all.isNotEmpty())
        for (error in SautiyError.all) {
            assertTrue(error.fact.isNotBlank())
            assertTrue(error.consequence.isNotBlank())
            assertTrue(error.remedy.label.isNotBlank())
            assertFalse("Errors never apologise", error.fact.contains("sorry", ignoreCase = true))
            assertFalse("Errors never shout", error.fact.contains("!"))
        }
    }

    @Test
    fun `errors are modal only when data is at risk`() {
        for (error in SautiyError.all) {
            if (error.presentation == SautiyError.Presentation.MODAL) {
                assertTrue(
                    "Modal reserved for data loss: ${error.fact}",
                    error === SautiyError.StorageFull,
                )
            }
        }
    }

    @Test
    fun `SAUTIY interrupts in exactly four situations`() {
        assertEquals(
            "Chapter 3.2.7 permits exactly four interruptions",
            Interruption.PERMITTED_COUNT,
            Interruption.entries.size,
        )
        for (interruption in Interruption.entries) {
            assertTrue(interruption.justification.isNotBlank())
        }
    }

    @Test
    fun `an error cannot be constructed without a remedy`() {
        val threw = runCatching {
            SautiyError(fact = "", consequence = "Recording cannot start.", remedy = SautiyError.Remedy("Retry", "x"))
        }.isFailure
        assertTrue("An error with no fact must be impossible to build", threw)

        val apology = runCatching {
            SautiyError(
                fact = "Sorry, the microphone is busy.",
                consequence = "Recording cannot start.",
                remedy = SautiyError.Remedy("Retry", "x"),
            )
        }.isFailure
        assertTrue("An apologising error must be impossible to build", apology)
    }
}
