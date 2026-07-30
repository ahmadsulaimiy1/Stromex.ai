package com.sajjil.app.ui.screens.master

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
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
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
import com.sajjil.core.modes.VoiceProfile

@Composable
fun MasterScreen(viewModel: MasterViewModel, modifier: Modifier = Modifier) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    Column(
        modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text("SAJJIL Master", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.SemiBold)
        Text("Broadcast mastering suite: one-click mastering toward a premium voice profile.", style = MaterialTheme.typography.bodyMedium)

        Text("Select a recording", style = MaterialTheme.typography.titleMedium)
        LazyColumn(Modifier.fillMaxWidth().height(150.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            items(state.recordings, key = { it.id }) { recording ->
                MasterRecordingRow(recording, isSelected = recording.id == state.selected?.id) { viewModel.select(recording) }
            }
        }

        if (state.selected != null) {
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

            Text("Audio Restoration Laboratory", style = MaterialTheme.typography.titleMedium)
            ToggleRow(
                label = "Repair damage (declip, denoise, rescue level)",
                checked = state.repairDamage,
                onCheckedChange = viewModel::setRepairDamage,
            )
            ToggleRow(
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
                        ScoreRow("Studio Readiness", report.studioReadinessScore)
                        ScoreRow("Broadcast Readiness", report.broadcastReadinessScore)
                        ScoreRow("Archive Readiness", report.archiveReadinessScore)
                        ScoreRow("Clarity", report.clarityScore)
                        ScoreRow("Noise", report.noiseScore)
                        ScoreRow("Loudness", report.loudnessScore)
                        report.echoScore?.let { ScoreRow("Echo", it) }
                    }
                }
                OutlinedButton(onClick = { viewModel.playMastered() }) { Text("Preview Mastered") }
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
    }
}

@Composable
private fun ToggleRow(label: String, checked: Boolean, onCheckedChange: (Boolean) -> Unit) {
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
private fun ScoreRow(label: String, score: Int) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(label, style = MaterialTheme.typography.bodyMedium)
        Text("$score", style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
private fun MasterRecordingRow(recording: RecordingEntity, isSelected: Boolean, onClick: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (isSelected) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceVariant,
        ),
    ) {
        Column(Modifier.padding(12.dp)) {
            Text(recording.title, style = MaterialTheme.typography.titleMedium)
            Text("${recording.recordingMode} · ${recording.sampleRate} Hz", style = MaterialTheme.typography.bodyMedium)
        }
    }
}
