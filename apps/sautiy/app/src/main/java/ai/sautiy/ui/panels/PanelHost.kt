package ai.sautiy.ui.workspace

import ai.sautiy.core.analysis.Loudness
import ai.sautiy.core.codec.ExportFormat
import ai.sautiy.core.dsp.StudioPreset
import ai.sautiy.core.play.PlaybackSpeed
import ai.sautiy.core.workspace.Panel
import ai.sautiy.ui.components.QualityGauge
import ai.sautiy.ui.icons.SautiyIcons
import ai.sautiy.ui.theme.SautiyShapes
import ai.sautiy.ui.theme.SautiySpace
import ai.sautiy.ui.theme.SautiyTheme
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.sizeIn
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp

/**
 * Routes an open [Panel] to its content — Editorial Bible chapter 4.4.
 *
 * Every panel shares one scaffold, so the header, the drag affordance, the dismissal routes and
 * the insets are identical across all twelve and cannot drift apart. The panel bodies below are
 * therefore only ever *content*, never chrome.
 */
@Composable
fun PanelHost(
    panel: Panel,
    state: WorkspaceUiState,
    actions: WorkspaceActions,
) {
    PanelScaffold(title = panelTitle(panel), onDismiss = actions.onDismissPanel) {
        when (panel) {
            Panel.STUDIO -> StudioPanel(state, actions)
            Panel.EXPORT -> ExportPanel(state, actions)
            Panel.ANALYSIS -> AnalysisPanel(state)
            Panel.LIBRARY -> LibraryPanel(state, actions)
            Panel.HISTORY -> HistoryPanel(state, actions)
            Panel.LAYERS -> LayersPanel(state, actions)
            Panel.MARKERS -> MarkersPanel(state, actions)
            Panel.EQUALISER -> EqualiserPanel(state)
            Panel.DYNAMICS -> DynamicsPanel(state)
            Panel.SPACE -> SpacePanel(state)
            Panel.TRANSCRIPT -> TranscriptPanel()
            Panel.PROJECT -> ProjectPanel(state)
        }
    }
}

private fun panelTitle(panel: Panel): String = when (panel) {
    Panel.STUDIO -> "Studio"
    Panel.EQUALISER -> "Equaliser"
    Panel.DYNAMICS -> "Dynamics"
    Panel.SPACE -> "Space"
    Panel.ANALYSIS -> "Analysis"
    Panel.LAYERS -> "Layers"
    Panel.MARKERS -> "Markers"
    Panel.HISTORY -> "History"
    Panel.TRANSCRIPT -> "Transcript"
    Panel.LIBRARY -> "Library"
    Panel.PROJECT -> "Project"
    Panel.EXPORT -> "Export"
}

/**
 * The shared panel chrome.
 *
 * The drag handle is not decoration: it is one of the four dismissal routes chapter 4.4.1
 * requires, and it is the one a thumb finds without looking.
 */
@Composable
private fun PanelScaffold(
    title: String,
    onDismiss: () -> Unit,
    content: @Composable () -> Unit,
) {
    val colours = SautiyTheme.colours

    Column(modifier = Modifier.fillMaxWidth()) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = SautiySpace.m, bottom = SautiySpace.xs),
            contentAlignment = Alignment.Center,
        ) {
            Box(
                modifier = Modifier
                    .width(36.dp)
                    .height(4.dp)
                    .background(colours.border, RoundedCornerShape(percent = 50)),
            )
        }

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = SautiySpace.pageInset, vertical = SautiySpace.s),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = title,
                style = SautiyTheme.type.titleLarge,
                color = colours.textPrimary,
                modifier = Modifier.weight(1f),
            )
            Box(
                modifier = Modifier
                    .size(SautiySpace.minTouchTarget)
                    .clickable(onClickLabel = "Close panel", role = Role.Button, onClick = onDismiss),
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    imageVector = SautiyIcons.Close,
                    contentDescription = null,
                    tint = colours.textSecondary,
                    modifier = Modifier.size(20.dp),
                )
            }
        }

        Box(modifier = Modifier.padding(horizontal = SautiySpace.pageInset)) { content() }
    }
}

/**
 * The Studio panel — chapter 10.3's preset cards.
 *
 * Named for situations rather than processes, because a user knows whether they recorded a
 * lecture and does not know whether they want 3:1 at −18 dBFS with a 6 dB knee. Each card
 * expands to those numbers on touch, and never before.
 */
@Composable
private fun StudioPanel(state: WorkspaceUiState, actions: WorkspaceActions) {
    val colours = SautiyTheme.colours

    LazyColumn(verticalArrangement = Arrangement.spacedBy(SautiySpace.s)) {
        items(StudioPreset.cardOrder) { preset ->
            val applied = state.appliedPreset == preset
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(SautiyShapes.medium)
                    .background(if (applied) colours.signalSelection else colours.surfaceRaised)
                    .border(
                        width = if (applied) 1.5.dp else 0.dp,
                        color = if (applied) colours.signal else colours.surfaceRaised,
                        shape = SautiyShapes.medium,
                    )
                    .clickable(onClickLabel = preset.displayName, role = Role.Button) {
                        actions.onApplyPreset(preset)
                    }
                    .padding(SautiySpace.l),
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = preset.displayName,
                        style = SautiyTheme.type.titleMedium,
                        color = colours.textPrimary,
                        modifier = Modifier.weight(1f),
                    )
                    if (applied) {
                        Text(
                            text = "Applied",
                            style = SautiyTheme.type.labelSmall,
                            color = colours.signal,
                        )
                    }
                }
                Spacer(modifier = Modifier.height(SautiySpace.xxs))
                Text(
                    text = preset.summary,
                    style = SautiyTheme.type.bodyMedium,
                    color = colours.textTertiary,
                )

                // Tier 3 (chapter 3.2.3): the real numbers, revealed only once this card is the
                // applied one. A professional is never limited; a beginner never has to look.
                if (applied) {
                    Spacer(modifier = Modifier.height(SautiySpace.m))
                    val chain = preset.chain
                    chain.compressor?.let {
                        ParameterRow("Compression", "${it.ratio}:1 at ${it.thresholdDb.toInt()} dB")
                    }
                    chain.highPassHz?.let { ParameterRow("High-pass", "${it.toInt()} Hz") }
                    chain.deEsser?.let { ParameterRow("De-esser", "${(it.frequencyHz / 1000).toInt()} kHz") }
                    chain.loudnessTargetName?.let {
                        val target = Loudness.Target.valueOf(it)
                        ParameterRow("Loudness", "${target.lufs} LUFS")
                    }
                    chain.limiterCeilingDb?.let { ParameterRow("Ceiling", "$it dBTP") }

                    Spacer(modifier = Modifier.height(SautiySpace.s))
                    Text(
                        text = "Revert to original",
                        style = SautiyTheme.type.labelLarge,
                        color = colours.signal,
                        modifier = Modifier
                            .sizeIn(minHeight = SautiySpace.minTouchTarget)
                            .clickable(
                                onClickLabel = "Revert to original",
                                role = Role.Button,
                                onClick = actions.onRevertPreset,
                            ),
                    )
                }
            }
        }
    }
}

@Composable
private fun ParameterRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = SautiySpace.xxs),
    ) {
        Text(
            text = label,
            style = SautiyTheme.type.bodyMedium,
            color = SautiyTheme.colours.textTertiary,
            modifier = Modifier.weight(1f),
        )
        Text(text = value, style = SautiyTheme.type.numeric, color = SautiyTheme.colours.textSecondary)
    }
}

/**
 * The Export panel — chapter 1.6's three-tap guarantee.
 *
 * Commit, choose the format, export. The last-used format is pre-selected, so the common case
 * is two taps.
 */
@Composable
private fun ExportPanel(state: WorkspaceUiState, actions: WorkspaceActions) {
    val colours = SautiyTheme.colours

    Column {
        for (format in ExportFormat.panelOrder) {
            val chosen = state.exportFormat == format
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = SautiySpace.xxs)
                    .clip(SautiyShapes.medium)
                    .background(if (chosen) colours.signalSelection else colours.surfaceRaised)
                    .clickable(onClickLabel = format.displayName, role = Role.Button) {
                        actions.onChooseExportFormat(format)
                    }
                    .padding(SautiySpace.l),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = format.displayName,
                        style = SautiyTheme.type.titleMedium,
                        color = colours.textPrimary,
                    )
                    Text(
                        text = format.summary,
                        style = SautiyTheme.type.bodyMedium,
                        color = colours.textTertiary,
                    )
                }
                if (format.lossless) {
                    Text(text = "Exact", style = SautiyTheme.type.labelSmall, color = colours.safe)
                }
            }
        }

        Spacer(modifier = Modifier.height(SautiySpace.l))

        val progress = state.exportProgress
        if (progress != null) {
            LinearProgressIndicator(
                progress = { progress.toFloat() },
                modifier = Modifier.fillMaxWidth(),
                color = colours.signal,
                trackColor = colours.surfaceRaised,
            )
        } else {
            Row(horizontalArrangement = Arrangement.spacedBy(SautiySpace.m)) {
                PrimaryAction(label = "Export", onClick = actions.onExport, modifier = Modifier.weight(1f))
                PrimaryAction(
                    label = "Share",
                    onClick = actions.onShare,
                    modifier = Modifier.weight(1f),
                    filled = false,
                )
            }
        }
    }
}

@Composable
private fun PrimaryAction(
    label: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    filled: Boolean = true,
) {
    val colours = SautiyTheme.colours
    Box(
        modifier = modifier
            .sizeIn(minHeight = SautiySpace.minTouchTarget)
            .height(52.dp)
            .clip(SautiyShapes.pill)
            .background(if (filled) colours.commit else colours.surfaceRaised)
            .clickable(onClickLabel = label, role = Role.Button, onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        Text(
            text = label,
            style = SautiyTheme.type.labelLarge,
            color = if (filled) colours.onCommit else colours.textPrimary,
        )
    }
}

/** The Analysis panel — every number measured, none estimated (chapter 10.4). */
@Composable
private fun AnalysisPanel(state: WorkspaceUiState) {
    Column {
        QualityGauge(score = state.qualityScore, reason = state.qualityReason)
        Spacer(modifier = Modifier.height(SautiySpace.l))
        ParameterRow("Peak", ai.sautiy.core.audio.Decibels.format(state.peakDb))
        ParameterRow("Noise floor", ai.sautiy.core.audio.Decibels.format(state.noiseFloorDb))
        ParameterRow("Signal to noise", "${(state.peakDb - state.noiseFloorDb).toInt()} dB")
        ParameterRow("Clipping", if (state.hasClipped) "Yes" else "None")
        ParameterRow("Duration", formatDuration(state.totalFrames, state.sampleRate))
    }
}

/** The Library panel. A panel, not a page (chapter 4.1). */
@Composable
private fun LibraryPanel(state: WorkspaceUiState, actions: WorkspaceActions) {
    val colours = SautiyTheme.colours

    if (state.library.isEmpty()) {
        EmptyPanelState(
            title = "No recordings yet",
            body = "Recordings appear here as soon as you make them.",
        )
        return
    }

    LazyColumn(verticalArrangement = Arrangement.spacedBy(SautiySpace.xs)) {
        items(state.library) { row ->
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .sizeIn(minHeight = SautiySpace.minTouchTarget)
                    .clip(SautiyShapes.small)
                    .clickable(onClickLabel = row.title, role = Role.Button) { actions.onOpenRecording(row.id) }
                    .padding(vertical = SautiySpace.m),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(SautiySpace.m),
            ) {
                Icon(
                    imageVector = SautiyIcons.Waveform,
                    contentDescription = null,
                    tint = colours.signal,
                    modifier = Modifier.size(20.dp),
                )
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = row.title,
                        style = SautiyTheme.type.bodyLarge,
                        color = colours.textPrimary,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Text(
                        text = formatDuration(row.durationFrames, row.sampleRate),
                        style = SautiyTheme.type.timerInline,
                        color = colours.textTertiary,
                    )
                }
                if (row.favourite) {
                    Text(text = "Favourite", style = SautiyTheme.type.labelSmall, color = colours.caution)
                }
            }
        }
    }
}

/** The History panel — chapter 9.5's time travel. Tap any step to go there. */
@Composable
private fun HistoryPanel(state: WorkspaceUiState, actions: WorkspaceActions) {
    val colours = SautiyTheme.colours

    LazyColumn(verticalArrangement = Arrangement.spacedBy(SautiySpace.xxs)) {
        items(state.historySteps.size) { index ->
            val current = index == state.historyIndex
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .sizeIn(minHeight = SautiySpace.minTouchTarget)
                    .clip(SautiyShapes.small)
                    .background(if (current) colours.signalSelection else colours.surface)
                    .clickable(onClickLabel = state.historySteps[index], role = Role.Button) {
                        actions.onTravelHistory(index)
                    }
                    .padding(horizontal = SautiySpace.m, vertical = SautiySpace.m),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = state.historySteps[index],
                    style = SautiyTheme.type.bodyMedium,
                    color = if (index <= state.historyIndex) colours.textPrimary else colours.textDisabled,
                    modifier = Modifier.weight(1f),
                )
                if (current) {
                    Text(text = "Now", style = SautiyTheme.type.labelSmall, color = colours.signal)
                }
            }
        }
    }
}

@Composable
private fun LayersPanel(state: WorkspaceUiState, actions: WorkspaceActions) {
    val colours = SautiyTheme.colours
    LazyColumn(verticalArrangement = Arrangement.spacedBy(SautiySpace.xs)) {
        items(state.layers) { layer ->
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .sizeIn(minHeight = SautiySpace.minTouchTarget)
                    .clickable(onClickLabel = layer.name, role = Role.Button) { actions.onSelectLayer(layer.id) }
                    .padding(vertical = SautiySpace.m),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = layer.name,
                    style = SautiyTheme.type.bodyLarge,
                    color = if (layer.muted) colours.textDisabled else colours.textPrimary,
                    modifier = Modifier.weight(1f),
                )
                if (layer.soloed) Text("Solo", style = SautiyTheme.type.labelSmall, color = colours.signal)
                if (layer.muted) Text("Muted", style = SautiyTheme.type.labelSmall, color = colours.textTertiary)
            }
        }
    }
}

@Composable
private fun MarkersPanel(state: WorkspaceUiState, actions: WorkspaceActions) {
    if (state.markerFrames.isEmpty()) {
        EmptyPanelState(
            title = "No markers",
            body = "Drop a marker while recording to find a moment again later.",
        )
        return
    }
    LazyColumn(verticalArrangement = Arrangement.spacedBy(SautiySpace.xxs)) {
        items(state.markerFrames) { frame ->
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .sizeIn(minHeight = SautiySpace.minTouchTarget)
                    .clickable(onClickLabel = "Jump", role = Role.Button) { actions.onSeek(frame) }
                    .padding(vertical = SautiySpace.m),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = formatTimecode(frame, state.sampleRate),
                    style = SautiyTheme.type.timerInline,
                    color = SautiyTheme.colours.textPrimary,
                )
            }
        }
    }
}

/**
 * The Equaliser, Dynamics and Space panels show the parameters of the applied chain.
 *
 * They read from the chain rather than holding their own state, so the curve on screen is
 * always the filter in the audio — chapter 10.5's rule that the drawn response is computed from
 * the coefficients rather than maintained alongside them.
 */
@Composable
private fun EqualiserPanel(state: WorkspaceUiState) {
    val chain = state.appliedPreset?.chain
    if (chain == null || chain.equaliser.isEmpty()) {
        EmptyPanelState("No equalisation", "This preset shapes nothing. Choose another to see its bands.")
        return
    }
    Column {
        for (band in chain.equaliser) {
            ParameterRow(
                label = "${band.frequency.toInt()} Hz",
                value = "${if (band.gainDb >= 0) "+" else ""}${band.gainDb} dB  Q ${band.q}",
            )
        }
    }
}

@Composable
private fun DynamicsPanel(state: WorkspaceUiState) {
    val chain = state.appliedPreset?.chain
    val compressor = chain?.compressor
    if (compressor == null) {
        EmptyPanelState("No compression", "This preset leaves the dynamics alone.")
        return
    }
    Column {
        ParameterRow("Threshold", "${compressor.thresholdDb} dB")
        ParameterRow("Ratio", "${compressor.ratio}:1")
        ParameterRow("Attack", "${compressor.attackMs} ms")
        ParameterRow("Release", "${compressor.releaseMs} ms")
        ParameterRow("Knee", "${compressor.kneeDb} dB")
        chain.limiterCeilingDb?.let { ParameterRow("Limiter ceiling", "$it dBTP") }
    }
}

@Composable
private fun SpacePanel(state: WorkspaceUiState) {
    val space = state.appliedPreset?.chain?.space
    if (space == null) {
        EmptyPanelState("No space", "This preset adds no room. The recording is left as it was made.")
        return
    }
    Column {
        ParameterRow("Size", "${(space.size * 100).toInt()}%")
        ParameterRow("Damping", "${(space.damping * 100).toInt()}%")
        ParameterRow("Mix", "${(space.mix * 100).toInt()}%")
        space.echoDelayMs?.let { ParameterRow("Echo", "${it.toInt()} ms") }
    }
}

@Composable
private fun TranscriptPanel() {
    EmptyPanelState(
        title = "No transcript",
        body = "Transcription runs on this device when a recording is finished. Nothing is uploaded.",
    )
}

@Composable
private fun ProjectPanel(state: WorkspaceUiState) {
    Column {
        ParameterRow("Project", state.projectName)
        ParameterRow("Quality", state.quality.displayName)
        ParameterRow("Sample rate", "${state.sampleRate} Hz")
        ParameterRow("Layers", "${state.layers.size}")
        ParameterRow("Duration", formatDuration(state.totalFrames, state.sampleRate))
    }
}

/**
 * The empty state pattern of chapter 18: say what this is for, in the product's own voice, and
 * never apologise for the absence of content.
 */
@Composable
private fun EmptyPanelState(title: String, body: String) {
    Column(
        modifier = Modifier.fillMaxWidth().padding(vertical = SautiySpace.h4),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(text = title, style = SautiyTheme.type.titleMedium, color = SautiyTheme.colours.textPrimary)
        Spacer(modifier = Modifier.height(SautiySpace.xs))
        Text(
            text = body,
            style = SautiyTheme.type.bodyMedium,
            color = SautiyTheme.colours.textTertiary,
            textAlign = androidx.compose.ui.text.style.TextAlign.Center,
        )
    }
}
