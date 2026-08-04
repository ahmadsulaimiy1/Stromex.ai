package ai.sajjil.app.ui.studio

import ai.sajjil.app.Services
import ai.sajjil.app.audio.ExportFormat
import ai.sajjil.app.ui.Format
import ai.sajjil.app.ui.components.EmptyState
import ai.sajjil.app.ui.components.CircularIconButton
import ai.sajjil.app.ui.components.LoudnessGauge
import ai.sajjil.app.ui.components.QualityRing
import ai.sajjil.app.ui.components.TransportBar
import ai.sajjil.app.ui.components.WaveformView
import ai.sajjil.app.ui.export.ExportSheet
import ai.sajjil.app.ui.theme.Radius
import ai.sajjil.app.ui.theme.Space
import ai.sajjil.app.ui.theme.sajjilColors
import ai.sajjil.audio.chain.AmbienceProfiles
import ai.sajjil.audio.chain.StudioPresets
import ai.sajjil.audio.chain.VoiceStyles
import ai.sajjil.audio.dsp.ReverbSettings
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.ContentCut
import androidx.compose.material.icons.filled.ExpandLess
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material.icons.filled.GraphicEq
import androidx.compose.material.icons.filled.IosShare
import androidx.compose.material.icons.filled.Redo
import androidx.compose.material.icons.filled.Save
import androidx.compose.material.icons.filled.SurroundSound
import androidx.compose.material.icons.filled.Tune
import androidx.compose.material.icons.filled.Undo
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.delay

/**
 * The Studio.
 *
 * One large waveform, one obvious primary action, and everything professional folded behind a
 * panel that stays shut until it is asked for. A beginner sees a waveform, a preset row and
 * "Studio Enhance"; a professional opens the panel and reaches the same engine's parameters.
 */
@Composable
fun StudioScreen(
    services: Services,
    recordingId: Long?,
    onOpenLibrary: () -> Unit,
    onStartRecording: () -> Unit,
) {
    val viewModel: StudioViewModel = viewModel(factory = StudioViewModel.Factory(services))
    val state by viewModel.state.collectAsStateWithLifecycle()
    val playback by services.playback.state.collectAsStateWithLifecycle()

    var panelTab by remember { mutableStateOf(StudioPanelTab.ENHANCE) }
    var panelOpen by remember { mutableStateOf(false) }
    var showExport by remember { mutableStateOf(false) }

    LaunchedEffect(recordingId) {
        recordingId?.let(viewModel::open)
    }

    // Keep the playhead in step with playback without asking the player on every frame.
    LaunchedEffect(playback.isPlaying) {
        while (playback.isPlaying) {
            services.playback.refreshPosition()
            viewModel.setPlayheadFromMillis(playback.positionMs)
            delay(60)
        }
    }

    if (recordingId == null && state.recording == null && !state.isLoading) {
        EmptyState(
            icon = Icons.Filled.Tune,
            title = "Nothing open in Studio",
            body = "Open a recording from your Library, or record something new, and it will appear " +
                "here ready to edit and enhance.",
            actionLabel = "Open Library",
            onAction = onOpenLibrary,
        )
        return
    }

    if (state.isLoading) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            CircularProgressIndicator(color = MaterialTheme.colorScheme.primary)
        }
        return
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = Space.pageHorizontal),
    ) {
        Spacer(Modifier.height(Space.md))

        StudioHeader(
            title = state.recording?.title.orEmpty(),
            subtitle = buildString {
                append(Format.duration(state.recording?.durationMs ?: 0))
                state.recording?.let { append(" · ${Format.relativeDate(it.createdAt)}") }
            },
            quality = state.quality,
        )

        Spacer(Modifier.height(Space.md))

        WaveformView(
            peaks = state.peaks,
            totalFrames = state.totalFrames,
            playheadFrame = state.playheadFrame,
            selection = state.selection,
            splitPoints = state.splitPoints,
            zoom = state.zoom,
            scrollFraction = state.scrollFraction,
            height = 200.dp,
            onSeek = viewModel::seekToFrame,
            onSelectionChange = viewModel::setSelection,
            onSplit = viewModel::split,
            onLongPress = { viewModel.setSelection(null) },
            onZoomChange = viewModel::setZoom,
            onScrollChange = viewModel::setScroll,
        )

        Spacer(Modifier.height(Space.sm))

        EditToolbar(
            canUndo = state.canUndo,
            canRedo = state.canRedo,
            hasSelection = state.selection != null,
            hasUnsavedEdits = state.hasUnsavedEdits,
            onUndo = viewModel::undo,
            onRedo = viewModel::redo,
            onTrim = viewModel::trimToSelection,
            onCut = viewModel::cutSelection,
            onSave = viewModel::saveEdits,
        )

        Spacer(Modifier.height(Space.md))

        TransportBar(
            isPlaying = playback.isPlaying,
            onPlayPause = {
                if (playback.recordingId == state.recording?.id) {
                    services.playback.togglePlayPause()
                } else {
                    viewModel.playFromPlayhead()
                }
            },
            onSkipBack = services.playback::skipBack,
            onSkipForward = services.playback::skipForward,
        )

        Spacer(Modifier.height(Space.md))

        // The one-touch action. Deliberately the largest and only filled button on the screen.
        Button(
            onClick = viewModel::enhance,
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            shape = RoundedCornerShape(Radius.medium),
        ) {
            Icon(Icons.Filled.AutoAwesome, contentDescription = null)
            Spacer(Modifier.width(Space.sm))
            Text("Studio Enhance", style = MaterialTheme.typography.labelLarge)
        }

        Spacer(Modifier.height(Space.md))

        StudioPanel(
            open = panelOpen,
            tab = panelTab,
            state = state,
            onOpenChange = { panelOpen = it },
            onTabChange = { panelTab = it; panelOpen = true },
            onSelectPreset = viewModel::selectPreset,
            onSelectVoiceStyle = viewModel::selectVoiceStyle,
            onSelectAmbience = viewModel::selectAmbience,
            onAdjustAmbience = viewModel::adjustAmbience,
            onExport = { showExport = true },
        )

        Spacer(Modifier.height(Space.md))

        TaskStrip(task = state.task, onDismiss = viewModel::clearTask)

        Spacer(Modifier.height(Space.xxl))
    }

    if (showExport) {
        ExportSheet(
            services = services,
            onDismiss = { showExport = false },
            onExport = { format, quality ->
                viewModel.export(format, quality)
                showExport = false
            },
            lastExport = state.lastExport,
        )
    }
}

@Composable
private fun StudioHeader(
    title: String,
    subtitle: String,
    quality: ai.sajjil.audio.analysis.QualityReport?,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f)) {
            Text(
                text = title.ifEmpty { "Untitled recording" },
                style = MaterialTheme.typography.headlineMedium,
                color = MaterialTheme.colorScheme.onSurface,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
            Spacer(Modifier.height(Space.xs))
            Text(
                text = subtitle,
                style = MaterialTheme.typography.bodySmall,
                color = sajjilColors.onSurfaceMuted,
            )
        }
        Spacer(Modifier.width(Space.md))
        QualityRing(score = quality?.score, grade = quality?.grade, size = 76.dp)
    }

    // The single most useful finding, in plain language. The rest live in the panel.
    quality?.findings?.firstOrNull()?.let { finding ->
        Spacer(Modifier.height(Space.sm))
        Text(
            text = finding.message,
            style = MaterialTheme.typography.bodySmall,
            color = when (finding.severity) {
                ai.sajjil.audio.analysis.QualityFinding.Severity.PROBLEM -> sajjilColors.problem
                ai.sajjil.audio.analysis.QualityFinding.Severity.WARNING -> sajjilColors.caution
                ai.sajjil.audio.analysis.QualityFinding.Severity.INFO -> sajjilColors.onSurfaceMuted
            },
        )
    }
}

@Composable
private fun EditToolbar(
    canUndo: Boolean,
    canRedo: Boolean,
    hasSelection: Boolean,
    hasUnsavedEdits: Boolean,
    onUndo: () -> Unit,
    onRedo: () -> Unit,
    onTrim: () -> Unit,
    onCut: () -> Unit,
    onSave: () -> Unit,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceEvenly,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        CircularIconButton(
            icon = Icons.Filled.Undo,
            description = "Undo",
            onClick = onUndo,
            enabled = canUndo,
            tint = sajjilColors.onSurfaceMuted,
        )
        CircularIconButton(
            icon = Icons.Filled.Redo,
            description = "Redo",
            onClick = onRedo,
            enabled = canRedo,
            tint = sajjilColors.onSurfaceMuted,
        )
        CircularIconButton(
            icon = Icons.Filled.ContentCut,
            description = "Cut the selection",
            onClick = onCut,
            enabled = hasSelection,
            tint = sajjilColors.onSurfaceMuted,
        )
        CircularIconButton(
            icon = Icons.Filled.GraphicEq,
            description = "Keep only the selection",
            onClick = onTrim,
            enabled = hasSelection,
            tint = sajjilColors.onSurfaceMuted,
        )
        CircularIconButton(
            icon = Icons.Filled.Save,
            description = "Save edits",
            onClick = onSave,
            enabled = hasUnsavedEdits,
            tint = if (hasUnsavedEdits) MaterialTheme.colorScheme.primary else sajjilColors.onSurfaceMuted,
        )
    }
}

enum class StudioPanelTab(val label: String) {
    ENHANCE("Enhance"),
    ECHO("Echo"),
    VOICE("Voice"),
    EXPORT("Export"),
}

/**
 * The floating Studio panel.
 *
 * Collapsed it is four words. Expanded it shows the controls for whichever one was tapped, and
 * nothing from the other three. That is what keeps depth available without ever putting it in the
 * way — the beginner never opens it, and the professional opens it once and it stays open.
 */
@Composable
private fun StudioPanel(
    open: Boolean,
    tab: StudioPanelTab,
    state: StudioUiState,
    onOpenChange: (Boolean) -> Unit,
    onTabChange: (StudioPanelTab) -> Unit,
    onSelectPreset: (ai.sajjil.audio.chain.StudioPreset?) -> Unit,
    onSelectVoiceStyle: (ai.sajjil.audio.chain.VoiceStyle) -> Unit,
    onSelectAmbience: (ai.sajjil.audio.chain.AmbienceProfile) -> Unit,
    onAdjustAmbience: (ReverbSettings) -> Unit,
    onExport: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(sajjilColors.surfaceElevated, RoundedCornerShape(Radius.large))
            .border(
                1.dp,
                MaterialTheme.colorScheme.outline.copy(alpha = 0.5f),
                RoundedCornerShape(Radius.large),
            )
            .padding(Space.md),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            for (entry in StudioPanelTab.entries) {
                val selected = open && entry == tab
                Text(
                    text = entry.label,
                    style = MaterialTheme.typography.labelLarge,
                    color = if (selected) {
                        MaterialTheme.colorScheme.primary
                    } else {
                        sajjilColors.onSurfaceMuted
                    },
                    modifier = Modifier
                        .clickable {
                            if (entry == StudioPanelTab.EXPORT) onExport() else onTabChange(entry)
                        }
                        .padding(horizontal = Space.sm, vertical = Space.sm),
                )
            }
            Spacer(Modifier.weight(1f))
            CircularIconButton(
                icon = if (open) Icons.Filled.ExpandLess else Icons.Filled.ExpandMore,
                description = if (open) "Close the studio panel" else "Open the studio panel",
                onClick = { onOpenChange(!open) },
                tint = sajjilColors.onSurfaceMuted,
            )
        }

        AnimatedVisibility(visible = open) {
            Column {
                Spacer(Modifier.height(Space.sm))
                when (tab) {
                    StudioPanelTab.ENHANCE -> PresetRow(
                        selectedId = state.selectedPreset?.id,
                        onSelect = onSelectPreset,
                    )
                    StudioPanelTab.VOICE -> VoiceStyleRow(
                        selectedId = state.selectedVoiceStyle.id,
                        onSelect = onSelectVoiceStyle,
                    )
                    StudioPanelTab.ECHO -> EchoStudio(
                        state = state,
                        onSelectAmbience = onSelectAmbience,
                        onAdjust = onAdjustAmbience,
                    )
                    StudioPanelTab.EXPORT -> Unit
                }
            }
        }
    }
}

@Composable
private fun PresetRow(
    selectedId: String?,
    onSelect: (ai.sajjil.audio.chain.StudioPreset?) -> Unit,
) {
    LazyRow(horizontalArrangement = Arrangement.spacedBy(Space.sm)) {
        items(StudioPresets.ALL) { preset ->
            ChoiceCard(
                title = preset.name,
                summary = preset.summary,
                selected = preset.id == selectedId,
                onClick = { onSelect(if (preset.id == selectedId) null else preset) },
            )
        }
    }
}

@Composable
private fun VoiceStyleRow(
    selectedId: String,
    onSelect: (ai.sajjil.audio.chain.VoiceStyle) -> Unit,
) {
    LazyRow(horizontalArrangement = Arrangement.spacedBy(Space.sm)) {
        items(VoiceStyles.ALL) { style ->
            ChoiceCard(
                title = style.name,
                summary = style.summary,
                selected = style.id == selectedId,
                onClick = { onSelect(style) },
            )
        }
    }
}

/**
 * The Echo Studio.
 *
 * A profile chosen from cards, then six sliders that mean something to a listener rather than to
 * a DSP engineer: Amount, Room Size, Warmth, Decay, Width, Early Reflections.
 */
@Composable
private fun EchoStudio(
    state: StudioUiState,
    onSelectAmbience: (ai.sajjil.audio.chain.AmbienceProfile) -> Unit,
    onAdjust: (ReverbSettings) -> Unit,
) {
    val current = state.ambienceOverride ?: state.selectedAmbience.reverb

    Column {
        LazyRow(horizontalArrangement = Arrangement.spacedBy(Space.sm)) {
            items(AmbienceProfiles.ALL) { profile ->
                ChoiceCard(
                    title = profile.name,
                    summary = profile.summary,
                    selected = profile.id == state.selectedAmbience.id && state.ambienceOverride == null,
                    onClick = { onSelectAmbience(profile) },
                )
            }
        }

        Spacer(Modifier.height(Space.md))

        LabelledSlider("Amount", current.amount) { onAdjust(current.copy(amount = it)) }
        LabelledSlider("Room size", current.size) { onAdjust(current.copy(size = it)) }
        LabelledSlider("Warmth", current.warmth) { onAdjust(current.copy(warmth = it)) }
        LabelledSlider(
            label = "Decay",
            value = (current.decaySeconds / 6.0).coerceIn(0.0, 1.0),
            valueLabel = String.format(java.util.Locale.US, "%.1f s", current.decaySeconds),
        ) { onAdjust(current.copy(decaySeconds = it * 6.0)) }
        LabelledSlider("Width", current.width) { onAdjust(current.copy(width = it)) }
        LabelledSlider("Early reflections", current.earlyReflections) {
            onAdjust(current.copy(earlyReflections = it))
        }
    }
}

@Composable
private fun LabelledSlider(
    label: String,
    value: Double,
    valueLabel: String? = null,
    onChange: (Double) -> Unit,
) {
    Column(Modifier.padding(vertical = Space.xs)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Text(
                text = label,
                style = MaterialTheme.typography.labelMedium,
                color = sajjilColors.onSurfaceMuted,
            )
            Text(
                text = valueLabel ?: Format.percent(value),
                style = MaterialTheme.typography.labelMedium,
                color = sajjilColors.onSurfaceFaint,
            )
        }
        Slider(
            value = value.toFloat(),
            onValueChange = { onChange(it.toDouble()) },
            valueRange = 0f..1f,
        )
    }
}

@Composable
private fun ChoiceCard(
    title: String,
    summary: String,
    selected: Boolean,
    onClick: () -> Unit,
) {
    val borderColor = if (selected) {
        MaterialTheme.colorScheme.primary
    } else {
        MaterialTheme.colorScheme.outline.copy(alpha = 0.6f)
    }
    Column(
        modifier = Modifier
            .width(180.dp)
            .background(
                if (selected) MaterialTheme.colorScheme.primary.copy(alpha = 0.10f) else Color.Transparent,
                RoundedCornerShape(Radius.medium),
            )
            .border(if (selected) 2.dp else 1.dp, borderColor, RoundedCornerShape(Radius.medium))
            .clickable(onClick = onClick)
            .padding(Space.md),
    ) {
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,
            color = if (selected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface,
        )
        Spacer(Modifier.height(Space.xs))
        Text(
            text = summary,
            style = MaterialTheme.typography.bodySmall,
            color = sajjilColors.onSurfaceMuted,
            maxLines = 3,
            overflow = TextOverflow.Ellipsis,
        )
    }
}

/** Progress, success and failure in one place, so a screen never has three ways to say something. */
@Composable
private fun TaskStrip(task: StudioTask, onDismiss: () -> Unit) {
    when (task) {
        StudioTask.Idle -> Unit
        is StudioTask.Working -> Column(Modifier.fillMaxWidth()) {
            Text(
                text = task.label,
                style = MaterialTheme.typography.labelMedium,
                color = sajjilColors.onSurfaceMuted,
            )
            Spacer(Modifier.height(Space.xs))
            LinearProgressIndicator(
                progress = { task.progress.toFloat().coerceIn(0f, 1f) },
                modifier = Modifier.fillMaxWidth(),
            )
        }
        is StudioTask.Finished -> Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(sajjilColors.good.copy(alpha = 0.12f), RoundedCornerShape(Radius.small))
                .padding(Space.md),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = task.message,
                style = MaterialTheme.typography.bodySmall,
                color = sajjilColors.good,
                modifier = Modifier.weight(1f),
            )
            TextButton(onClick = onDismiss) { Text("Dismiss") }
        }
        is StudioTask.Failed -> Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(sajjilColors.problem.copy(alpha = 0.12f), RoundedCornerShape(Radius.small))
                .padding(Space.md),
        ) {
            Text(
                text = task.title,
                style = MaterialTheme.typography.titleMedium,
                color = sajjilColors.problem,
            )
            Spacer(Modifier.height(Space.xs))
            Text(
                text = task.body,
                style = MaterialTheme.typography.bodySmall,
                color = sajjilColors.onSurfaceMuted,
            )
            Spacer(Modifier.height(Space.sm))
            TextButton(onClick = onDismiss) { Text("Dismiss") }
        }
    }
}
