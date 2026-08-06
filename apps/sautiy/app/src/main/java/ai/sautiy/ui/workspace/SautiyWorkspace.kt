package ai.sautiy.ui.workspace

import ai.sautiy.core.design.Motion
import ai.sautiy.core.workspace.Panel
import ai.sautiy.core.workspace.PanelLaw
import ai.sautiy.core.workspace.TransportState
import ai.sautiy.core.workspace.WorkspaceAction
import ai.sautiy.core.record.RecordingAdvisor
import ai.sautiy.ui.components.ConditionDot
import ai.sautiy.ui.components.LevelMeter
import ai.sautiy.ui.components.StorageIndicator
import ai.sautiy.ui.icons.SautiyIcons
import ai.sautiy.ui.theme.SautiyMotion
import ai.sautiy.ui.theme.SautiyShapes
import ai.sautiy.ui.theme.SautiySpace
import ai.sautiy.ui.theme.SautiyTheme
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.Crossfade
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.sizeIn
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp

/**
 * **The application.**
 *
 * Editorial Bible chapter 4: SAUTIY is not an app with screens, it is one intelligent studio.
 * This composable is the whole of it. There is no navigation host here, no back stack of
 * destinations and no place for a screen to hide — because there are no screens.
 *
 * The four regions of chapter 4.2 are laid out in fixed positions so the hands learn them once:
 *
 * ```
 *   STATUS RAIL      truth about the session — values, barely any controls
 *   CANVAS           the audio itself
 *   LAYER STRIP      which material exists
 *   CONTEXT BAR      the adaptive cluster: tools for what is selected right now
 *   TRANSPORT DOCK   immovable, five slots, for the life of the product
 * ```
 *
 * A panel arrives *over* the canvas and never removes it, never covers the dock, and never
 * exceeds 62% of the canvas height — which is precisely what makes it a panel and not a page.
 */
@Composable
fun SautiyWorkspace(
    state: WorkspaceUiState,
    actions: WorkspaceActions,
    modifier: Modifier = Modifier,
) {
    val colours = SautiyTheme.colours

    BoxWithConstraints(
        modifier = modifier
            .fillMaxSize()
            .background(colours.canvas),
    ) {
        val totalHeight = maxHeight

        Column(modifier = Modifier.fillMaxSize()) {
            StatusRail(state = state, onProject = actions.onOpenLibrary, onSettings = actions.onOpenSettings)

            Box(modifier = Modifier.weight(1f).fillMaxWidth()) {
                if (state.hasAudio || state.transport.isCapturing) {
                    WaveformCanvas(
                        columns = state.waveform,
                        playheadFrame = state.playheadFrame,
                        totalFrames = state.totalFrames,
                        selection = state.selection,
                        markers = state.markerFrames,
                        isRecording = state.transport == TransportState.RECORDING,
                        onSeek = actions.onSeek,
                        onSelectionChanged = actions.onSelectionChanged,
                        onZoom = actions.onZoom,
                    )
                } else {
                    EmptyCanvas()
                }

                // The timer sits over the canvas, where the eye already is, rather than in the
                // rail where it would compete with the project name.
                Text(
                    text = formatTimecode(
                        if (state.transport.isCapturing) state.recordedFrames else state.playheadFrame,
                        state.sampleRate,
                    ),
                    style = SautiyTheme.type.timerHero,
                    color = if (state.transport == TransportState.RECORDING) colours.ember else colours.textPrimary,
                    modifier = Modifier
                        .align(Alignment.TopCenter)
                        .padding(top = SautiySpace.xxl),
                )

                if (state.transport.isCapturing || state.monitoring) {
                    LiveStudio(
                        state = state,
                        modifier = Modifier
                            .align(Alignment.BottomCenter)
                            .padding(horizontal = SautiySpace.pageInset, vertical = SautiySpace.l),
                    )
                }
            }

            // Live Studio: while the microphone is open, everything that is not about the sound
            // arriving goes away. The layer strip, the context tools and their labels are all
            // things to decide about, and a person who is speaking cannot decide about anything.
            // What is left is the waveform, the level, and the four conditions that would ruin
            // the take. Recording should feel calm, and calm is mostly subtraction.
            if (!state.transport.isCapturing) {
                LayerStrip(
                    layers = state.layers,
                    selectedLayerId = state.selectedLayerId,
                    onSelect = actions.onSelectLayer,
                    onAddLayer = actions.onAddLayer,
                    // A layer cannot be added mid-take: it would start a second capture stream the
                    // hardware has no way to provide.
                    canAddLayer = true,
                )

                ContextBar(actions = state.contextActions, onAction = actions.onContextAction)
            }

            TransportDock(
                transport = state.transport,
                monitoring = state.monitoring,
                canExport = state.hasAudio && !state.transport.isCapturing,
                onMonitor = actions.onToggleMonitor,
                onRewind = actions.onRewind,
                onRecord = actions.onRecordOrStop,
                onPlay = actions.onPlayOrPause,
                onCommit = actions.onCommit,
            )
        }

        // --- The panel layer -----------------------------------------------------------------
        //
        // Chapter 4.4.1: at most one panel, never over the dock, never past the coverage
        // ceiling, dismissed four ways. The scrim is one of those four.
        AnimatedVisibility(
            visible = state.openPanel != null,
            enter = fadeIn(SautiyMotion.fast()),
            exit = fadeOut(SautiyMotion.exit()),
        ) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(colours.canvas.copy(alpha = 0.45f))
                    .clickable(
                        onClickLabel = "Close panel",
                        role = Role.Button,
                        onClick = actions.onDismissPanel,
                    ),
            )
        }

        AnimatedVisibility(
            visible = state.openPanel != null,
            enter = slideInVertically(SautiyMotion.emphasised()) { it } + fadeIn(SautiyMotion.fast()),
            exit = slideOutVertically(SautiyMotion.exit()) { it } + fadeOut(SautiyMotion.exit()),
            modifier = Modifier.align(Alignment.BottomCenter),
        ) {
            val panel = state.openPanel
            if (panel != null) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        // The coverage ceiling is read from the law, not chosen here, so a panel
                        // cannot quietly grow past it.
                        .height(totalHeight * panel.coversCanvasFraction.toFloat().coerceAtMost(PanelLaw.MAX_CANVAS_COVERAGE.toFloat()))
                        // The dock stays clear beneath it. This is what makes it a panel.
                        .padding(bottom = DOCK_HEIGHT)
                        .clip(SautiyShapes.sheet)
                        .background(colours.surfaceOverlay),
                ) {
                    PanelHost(
                        panel = panel,
                        state = state,
                        actions = actions,
                    )
                }
            }
        }
    }
}

/**
 * The status rail (chapter 4.2). Truth about the session, and almost nothing to press.
 *
 * Both of its interactive elements are duplicated lower down — the library is also on the
 * context bar, and settings is not required to complete any task — so chapter 3.2.4's rule
 * against stranding a required control in the far zone holds.
 */
@Composable
private fun StatusRail(
    state: WorkspaceUiState,
    onProject: () -> Unit,
    onSettings: () -> Unit,
) {
    val colours = SautiyTheme.colours

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = SautiySpace.pageInset, vertical = SautiySpace.m),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(
            modifier = Modifier
                .weight(1f)
                .sizeIn(minHeight = SautiySpace.minTouchTarget)
                .clickable(onClickLabel = "Project and library", role = Role.Button, onClick = onProject),
            verticalArrangement = Arrangement.Center,
        ) {
            Text(
                text = state.projectName,
                style = SautiyTheme.type.titleMedium,
                color = colours.textPrimary,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(SautiySpace.s),
            ) {
                Text(
                    text = state.qualityName,
                    style = SautiyTheme.type.labelSmall,
                    color = colours.textTertiary,
                )
                StorageIndicator(
                    secondsRemaining = state.secondsRemaining,
                    critical = state.storageCritical,
                )
                if (state.hasClipped) {
                    // Clipping is shown as clipping (chapter 1.4 principle 5) and carries a word
                    // as well as a colour, so it survives colour blindness.
                    Text(
                        text = "Clipped",
                        style = SautiyTheme.type.labelSmall,
                        color = colours.critical,
                    )
                }
            }
        }

        if (state.transport == TransportState.RECORDING) {
            RecordingIndicator()
            Spacer(modifier = Modifier.width(SautiySpace.m))
        }

        Box(
            modifier = Modifier
                .size(SautiySpace.minTouchTarget)
                .clickable(onClickLabel = "Settings", role = Role.Button, onClick = onSettings),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                imageVector = SautiyIcons.Settings,
                contentDescription = null,
                tint = colours.textSecondary,
                modifier = Modifier.size(22.dp),
            )
        }
    }
}

/**
 * Live Studio — the five things worth knowing while the microphone is open, and nothing else.
 *
 * Level, clipping, background noise and quality. Every one of them is a reason a take gets thrown
 * away, and every one of them is fixable in the moment. Nothing else is here, because everything
 * else is a decision, and a person mid-sentence cannot make one.
 *
 * The guidance line is the only prose, it appears only when something is actually wrong, and it
 * says what to *do* — "move a little closer" — rather than what is wrong. It never blocks the
 * transport and never asks for a response.
 */
@Composable
private fun LiveStudio(state: WorkspaceUiState, modifier: Modifier = Modifier) {
    val colours = SautiyTheme.colours
    val guidance = state.guidance
    val quiet = state.noiseFloorDb < RecordingAdvisor.NOISY_ROOM_DB

    Column(
        modifier = modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        if (!guidance.isSilent && guidance.action != null) {
            // One sentence, in the weight the problem deserves. A warning is ember because it will
            // damage the recording; a suggestion is not, because the take is still usable.
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(SautiyShapes.medium)
                    .background(
                        if (guidance.weight == RecordingAdvisor.Weight.WARNING) {
                            colours.critical.copy(alpha = 0.16f)
                        } else {
                            colours.surfaceRaised
                        },
                    )
                    .padding(SautiySpace.m),
            ) {
                Text(
                    text = guidance.action,
                    style = SautiyTheme.type.titleMedium,
                    color = if (guidance.weight == RecordingAdvisor.Weight.WARNING) {
                        colours.critical
                    } else {
                        colours.textPrimary
                    },
                )
                guidance.because?.let {
                    Text(
                        text = it,
                        style = SautiyTheme.type.bodyMedium,
                        color = colours.textTertiary,
                    )
                }
            }
            Spacer(modifier = Modifier.height(SautiySpace.m))
        }

        LevelMeter(peakDb = state.peakDb, rmsDb = state.rmsDb)

        Spacer(modifier = Modifier.height(SautiySpace.m))

        // Four conditions, each a word and a dot. Read in peripheral vision by somebody who is
        // speaking, which is why none of them is a number.
        Row(horizontalArrangement = Arrangement.spacedBy(SautiySpace.l)) {
            ConditionDot(
                label = if (state.hasClipped) "Clipped" else "Headroom",
                good = !state.hasClipped,
                warning = state.hasClipped,
            )
            ConditionDot(
                label = if (quiet) "Quiet room" else "Background",
                good = quiet,
                warning = !quiet && state.noiseFloorDb > -36.0,
            )
            ConditionDot(
                label = when {
                    state.qualityScore >= 80 -> "Good"
                    state.qualityScore >= 55 -> "Usable"
                    else -> "Poor"
                },
                good = state.qualityScore >= 80,
                warning = state.qualityScore < 55,
            )
        }
    }
}

/** Ember, and only ever ember (chapter 2.3.4 clause 1). */
@Composable
private fun RecordingIndicator() {
    Box(
        modifier = Modifier
            .size(10.dp)
            .background(SautiyTheme.colours.ember, RoundedCornerShape(percent = 50)),
    )
}

/**
 * The layer strip (chapter 4.2), matching the reference layout: an add control, then one row
 * per layer with its name and its material.
 */
@Composable
private fun LayerStrip(
    layers: List<LayerRow>,
    selectedLayerId: String?,
    canAddLayer: Boolean,
    onSelect: (String) -> Unit,
    onAddLayer: () -> Unit,
) {
    val colours = SautiyTheme.colours

    Column(modifier = Modifier.fillMaxWidth()) {
        if (canAddLayer) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .sizeIn(minHeight = SautiySpace.minTouchTarget)
                    .clickable(onClickLabel = "Add layer", role = Role.Button, onClick = onAddLayer)
                    .padding(horizontal = SautiySpace.pageInset),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(SautiySpace.m),
            ) {
                Icon(
                    imageVector = SautiyIcons.Add,
                    contentDescription = null,
                    tint = colours.textPrimary,
                    modifier = Modifier.size(22.dp),
                )
                Text(
                    text = "Add layer",
                    style = SautiyTheme.type.bodyMedium,
                    color = colours.textPrimary,
                )
            }
        }

        for (layer in layers) {
            val selected = layer.id == selectedLayerId
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp)
                    .padding(horizontal = SautiySpace.s, vertical = SautiySpace.xxs)
                    .clip(SautiyShapes.small)
                    .background(if (selected) colours.signalSelection else colours.surface)
                    .clickable(onClickLabel = layer.name, role = Role.Button) { onSelect(layer.id) }
                    .padding(horizontal = SautiySpace.m),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(SautiySpace.m),
            ) {
                Icon(
                    imageVector = SautiyIcons.Waveform,
                    contentDescription = null,
                    tint = if (layer.muted) colours.textDisabled else colours.signal,
                    modifier = Modifier.size(20.dp),
                )
                Text(
                    text = layer.name,
                    style = SautiyTheme.type.bodyMedium,
                    color = if (layer.muted) colours.textDisabled else colours.signal,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.weight(1f),
                )
                if (layer.muted) {
                    Text(
                        text = "Muted",
                        style = SautiyTheme.type.labelSmall,
                        color = colours.textTertiary,
                    )
                }
            }
        }
    }
}

/**
 * The adaptive context bar (chapter 4.3) — the entire navigation model of SAUTIY.
 *
 * Its contents come straight from `WorkspaceState.contextActions()`, a pure function in
 * `sautiy-core` that is asserted over every reachable state: never more than six tools, never a
 * destructive one while recording, never a label over three words. This composable only draws
 * what that function returned.
 *
 * It cross-fades and never changes height, so the region below it — the dock — cannot move.
 */
@Composable
private fun ContextBar(
    actions: List<WorkspaceAction>,
    onAction: (WorkspaceAction) -> Unit,
) {
    val colours = SautiyTheme.colours
    val scroll = rememberScrollState()

    Crossfade(
        targetState = actions,
        animationSpec = SautiyMotion.fast(),
        label = "contextBar",
    ) { current ->
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .height(CONTEXT_BAR_HEIGHT)
                .horizontalScroll(scroll)
                .padding(horizontal = SautiySpace.pageInset),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(SautiySpace.xxl),
        ) {
            for (action in current) {
                ContextTool(
                    label = action.label,
                    icon = iconFor(action.id),
                    tint = if (action.destructive) colours.critical else colours.textPrimary,
                    onClick = { onAction(action) },
                )
            }
        }
    }
}

@Composable
private fun ContextTool(
    label: String,
    icon: ImageVector,
    tint: Color,
    onClick: () -> Unit,
) {
    Column(
        modifier = Modifier
            .sizeIn(minWidth = SautiySpace.minTouchTarget, minHeight = SautiySpace.minTouchTarget)
            .clickable(onClickLabel = label, role = Role.Button, onClick = onClick),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = tint,
            modifier = Modifier.size(24.dp),
        )
        // Chapter 2.5 icon law 2: anything not universally understood carries a persistent
        // label. Trim, split and normalise are not universally understood.
        Text(
            text = label,
            style = SautiyTheme.type.labelSmall,
            color = SautiyTheme.colours.textTertiary,
            maxLines = 1,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(top = SautiySpace.xxs),
        )
    }
}

/** Maps a core action id to its glyph. The core never knows about icons. */
private fun iconFor(id: String): ImageVector = when (id) {
    "ctx.marker" -> SautiyIcons.Marker
    "ctx.layer" -> SautiyIcons.Layers
    "ctx.input" -> SautiyIcons.Monitor
    "ctx.monitorLevel" -> SautiyIcons.Monitor
    "ctx.noise", "ctx.analysis", "ctx.quality" -> SautiyIcons.Analysis
    "ctx.discardTake", "ctx.deleteLayer", "ctx.deleteMarker" -> SautiyIcons.Close
    "ctx.speed" -> SautiyIcons.Speed
    "ctx.loop" -> SautiyIcons.Loop
    "ctx.compare" -> SautiyIcons.Compare
    "ctx.cut" -> SautiyIcons.Cut
    "ctx.split" -> SautiyIcons.Split
    "ctx.fade" -> SautiyIcons.Fade
    "ctx.silence" -> SautiyIcons.Stop
    "ctx.gain", "ctx.layerGain" -> SautiyIcons.Equaliser
    "ctx.deselect" -> SautiyIcons.Close
    "ctx.rename", "ctx.renameMarker" -> SautiyIcons.Marker
    "ctx.mute" -> SautiyIcons.Monitor
    "ctx.solo" -> SautiyIcons.Waveform
    "ctx.duplicate" -> SautiyIcons.Layers
    "ctx.jump" -> SautiyIcons.Commit
    "ctx.undo" -> SautiyIcons.Undo
    "ctx.redo" -> SautiyIcons.Redo
    "ctx.enhance" -> SautiyIcons.Enhance
    "ctx.trim" -> SautiyIcons.Trim
    "ctx.library" -> SautiyIcons.Library
    "ctx.projects" -> SautiyIcons.Library
    else -> SautiyIcons.Waveform
}

/**
 * The empty state (chapter 18).
 *
 * It states what this is for and offers the one action, and it does not apologise for being
 * empty. The record control is already under the thumb, so the copy points at it rather than
 * repeating it as a second button the user would have to choose between.
 */
@Composable
private fun EmptyCanvas() {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = SautiySpace.h4),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Icon(
            imageVector = SautiyIcons.Waveform,
            contentDescription = null,
            tint = SautiyTheme.colours.textDisabled,
            modifier = Modifier.size(48.dp),
        )
        Spacer(modifier = Modifier.height(SautiySpace.xxl))
        Text(
            text = "Ready",
            style = SautiyTheme.type.displaySmall,
            color = SautiyTheme.colours.textPrimary,
        )
        Spacer(modifier = Modifier.height(SautiySpace.s))
        Text(
            text = "Press record to begin. Everything is saved from the first moment.",
            style = SautiyTheme.type.bodyMedium,
            color = SautiyTheme.colours.textTertiary,
            textAlign = TextAlign.Center,
        )
    }
}

internal val DOCK_HEIGHT = 108.dp
internal val CONTEXT_BAR_HEIGHT = 76.dp
