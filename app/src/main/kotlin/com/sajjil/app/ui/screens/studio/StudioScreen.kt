package com.sajjil.app.ui.screens.studio

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Switch
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.app.export.ExportFormat
import com.sajjil.app.ui.components.GlassCard
import com.sajjil.app.ui.components.LoudnessHistoryView
import com.sajjil.app.ui.components.SpectrogramView
import com.sajjil.app.ui.screens.enhance.EnhanceUiState
import com.sajjil.app.ui.screens.enhance.EnhanceViewModel
import com.sajjil.app.ui.screens.master.MasterUiState
import com.sajjil.app.ui.screens.master.MasterViewModel
import com.sajjil.core.dsp.NoiseReductionStrength
import com.sajjil.core.modes.VoiceProfile

/**
 * One Studio, not two disconnected screens: Enhance and Master used to force picking a
 * recording twice from two separate "Select a recording" lists that had no idea about each
 * other. Selecting a recording here drives both view models at once, and Enhance/Master
 * become tabs of a single workspace instead of separate bottom-nav destinations.
 *
 * The underlying processing (noise reduction, mastering chain, restoration, export) is
 * untouched -- this is a UI consolidation, not a DSP change.
 */
@Composable
fun StudioScreen(
    enhanceViewModel: EnhanceViewModel,
    masterViewModel: MasterViewModel,
    modifier: Modifier = Modifier,
) {
    val enhanceState by enhanceViewModel.uiState.collectAsStateWithLifecycle()
    val masterState by masterViewModel.uiState.collectAsStateWithLifecycle()
    var tab by remember { mutableStateOf(0) }

    Column(modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text("SAJJIL Studio", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.SemiBold)
        Text("Enhance and master a recording without leaving the workspace.", style = MaterialTheme.typography.bodyMedium)

        Text("Select a recording", style = MaterialTheme.typography.titleMedium)
        LazyColumn(Modifier.fillMaxWidth().height(150.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            items(enhanceState.recordings, key = { it.id }) { recording ->
                StudioRecordingRow(recording, isSelected = recording.id == enhanceState.selected?.id) {
                    enhanceViewModel.select(recording)
                    masterViewModel.select(recording)
                }
            }
        }

        if (enhanceState.selected != null) {
            TabRow(selectedTabIndex = tab) {
                Tab(selected = tab == 0, onClick = { tab = 0 }, text = { Text("Enhance") })
                Tab(selected = tab == 1, onClick = { tab = 1 }, text = { Text("Master") })
            }

            Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                if (tab == 0) EnhanceBody(enhanceViewModel, enhanceState) else MasterBody(masterViewModel, masterState)
            }
        } else {
            Text("Choose a recording above to begin.", style = MaterialTheme.typography.bodyMedium)
        }
    }
}

@Composable
private fun EnhanceBody(viewModel: EnhanceViewModel, state: EnhanceUiState) {
    Text("Noise Reduction Strength", style = MaterialTheme.typography.titleMedium)
    LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        items(NoiseReductionStrength.entries) { strength ->
            FilterChip(
                selected = strength == state.strength,
                onClick = { viewModel.setStrength(strength) },
                label = { Text(strength.name.lowercase().replaceFirstChar(Char::uppercase)) },
            )
        }
    }

    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        OutlinedButton(onClick = { viewModel.playOriginal() }) { Text("Preview Original") }
        if (state.enhancedFile != null) {
            OutlinedButton(onClick = { viewModel.playEnhanced() }) { Text("Preview Enhanced") }
        }
    }

    Button(onClick = { viewModel.enhance() }, enabled = !state.isProcessing) {
        if (state.isProcessing) {
            CircularProgressIndicator(modifier = Modifier.height(18.dp), strokeWidth = 2.dp)
        } else {
            Text("Apply Enhancement")
        }
    }

    if (state.enhancedFile != null) {
        OutlinedButton(onClick = { viewModel.saveToLibrary() }, enabled = !state.savedToLibrary) {
            Text(if (state.savedToLibrary) "Saved to Library" else "Save to Library")
        }
    }
}

@Composable
private fun MasterBody(viewModel: MasterViewModel, state: MasterUiState) {
    StudioToggleRow(
        label = "Adaptive Mastering — detect content and build the chain automatically",
        checked = state.useAdaptiveMastering,
        onCheckedChange = viewModel::setUseAdaptiveMastering,
    )
    state.adaptiveClassification?.let { classification ->
        Text(
            "Detected: ${classification.type.name.lowercase().replaceFirstChar(Char::uppercase)} " +
                "(${(classification.confidence * 100).toInt()}% confidence) — a heuristic estimate, not a verdict.",
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.primary,
        )
    }

    if (!state.useAdaptiveMastering) {
        Text("Voice Profile", style = MaterialTheme.typography.titleMedium)
        LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            items(VoiceProfile.entries) { profile ->
                FilterChip(
                    selected = profile == state.profile,
                    onClick = { viewModel.selectProfile(profile) },
                    label = { Text(profile.displayName) },
                )
            }
        }
    }

    Text("Audio Restoration Laboratory", style = MaterialTheme.typography.titleMedium)
    StudioToggleRow(
        label = "Repair damage (declip, denoise, rescue level)",
        checked = state.repairDamage,
        onCheckedChange = viewModel::setRepairDamage,
    )
    StudioToggleRow(
        label = "AI Echo Removal (dereverberate)",
        checked = state.removeEcho,
        onCheckedChange = viewModel::setRemoveEcho,
    )

    Text("Reference Match (optional)", style = MaterialTheme.typography.titleMedium)
    LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        item {
            FilterChip(
                selected = state.referenceRecording == null,
                onClick = { viewModel.selectReferenceRecording(null) },
                label = { Text("None") },
            )
        }
        items(state.recordings.filter { it.id != state.selected?.id }, key = { it.id }) { recording ->
            FilterChip(
                selected = recording.id == state.referenceRecording?.id,
                onClick = { viewModel.selectReferenceRecording(recording) },
                label = { Text(recording.title) },
            )
        }
    }

    Text("Export Format", style = MaterialTheme.typography.titleMedium)
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        ExportFormat.entries.forEach { format ->
            FilterChip(
                selected = format == state.exportFormat,
                onClick = { viewModel.selectExportFormat(format) },
                label = { Text(format.displayName) },
            )
        }
    }

    Button(onClick = { viewModel.master() }, enabled = !state.isProcessing) {
        if (state.isProcessing) {
            CircularProgressIndicator(modifier = Modifier.height(18.dp), strokeWidth = 2.dp)
        } else {
            Text("Master & Export")
        }
    }

    state.report?.let { report ->
        GlassCard {
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("Executive Dashboard", style = MaterialTheme.typography.titleMedium)
                StudioScoreRow("Studio Readiness", report.studioReadinessScore)
                StudioScoreRow("Broadcast Readiness", report.broadcastReadinessScore)
                StudioScoreRow("Archive Readiness", report.archiveReadinessScore)
                StudioScoreRow("Clarity", report.clarityScore)
                StudioScoreRow("Noise", report.noiseScore)
                StudioScoreRow("Loudness", report.loudnessScore)
                report.echoScore?.let { StudioScoreRow("Echo", it) }
            }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton(onClick = { viewModel.playMastered() }) { Text("Preview Mastered") }
            OutlinedButton(onClick = { viewModel.saveToLibrary() }, enabled = !state.savedToLibrary) {
                Text(if (state.savedToLibrary) "Saved to Library" else "Save to Library")
            }
        }
    }

    state.spectrogram?.let { spectrogram ->
        Text("Spectrogram", style = MaterialTheme.typography.titleMedium)
        SpectrogramView(spectrogram)
    }
    if (state.loudnessHistory.isNotEmpty()) {
        Text("Loudness History", style = MaterialTheme.typography.titleMedium)
        LoudnessHistoryView(state.loudnessHistory)
    }
}

@Composable
private fun StudioToggleRow(label: String, checked: Boolean, onCheckedChange: (Boolean) -> Unit) {
    Row(
        Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(label, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
        Switch(checked = checked, onCheckedChange = onCheckedChange)
    }
}

@Composable
private fun StudioScoreRow(label: String, score: Int) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(label, style = MaterialTheme.typography.bodyMedium)
        Text("$score", style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
private fun StudioRecordingRow(recording: RecordingEntity, isSelected: Boolean, onClick: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (isSelected) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceVariant,
        ),
    ) {
        Column(Modifier.padding(12.dp)) {
            Text(recording.title, style = MaterialTheme.typography.titleMedium)
            Text(
                "${recording.recordingMode} · ${recording.sampleRate} Hz · ${recording.bitDepth}-bit",
                style = MaterialTheme.typography.bodyMedium,
            )
        }
    }
}
