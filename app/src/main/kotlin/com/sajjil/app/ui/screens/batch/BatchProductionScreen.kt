package com.sajjil.app.ui.screens.batch

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
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Error
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.core.modes.VoiceProfile

@Composable
fun BatchProductionScreen(viewModel: BatchProductionViewModel, modifier: Modifier = Modifier) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    Column(modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text("Batch Qur'an Production", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.SemiBold)
        Text(
            "Master an entire Surah, Juz, or your whole tagged recitation library in one pass.",
            style = MaterialTheme.typography.bodyMedium,
        )

        if (state.library.isEmpty()) {
            Text(
                "No recitations tagged yet — tag recordings with a Surah/Ayah in Qur'an Studio first.",
                style = MaterialTheme.typography.bodyMedium,
            )
            return@Column
        }

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton(onClick = viewModel::selectAll) { Text("Select All") }
            OutlinedButton(onClick = viewModel::clearSelection) { Text("Clear") }
        }

        LazyColumn(Modifier.fillMaxWidth().height(220.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            items(state.library, key = { it.id }) { recording ->
                LibrarySelectRow(
                    recording = recording,
                    checked = recording.id in state.selectedIds,
                    onToggle = { viewModel.toggleSelected(recording.id) },
                )
            }
        }

        Text("Mastering Profile", style = MaterialTheme.typography.titleMedium)
        LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            items(VoiceProfile.entries) { profile ->
                FilterChip(
                    selected = profile == state.profile,
                    onClick = { viewModel.selectProfile(profile) },
                    label = { Text(profile.displayName) },
                )
            }
        }

        Button(onClick = viewModel::runBatch, enabled = !state.isRunning && state.selectedIds.isNotEmpty()) {
            Text("Master ${state.selectedIds.size} Recording(s)")
        }

        if (state.total > 0) {
            LinearProgressIndicator(
                progress = { if (state.total == 0) 0f else state.completed.toFloat() / state.total },
                modifier = Modifier.fillMaxWidth(),
            )
            Text("${state.completed} / ${state.total} complete", style = MaterialTheme.typography.bodyMedium)
        }

        if (state.results.isNotEmpty()) {
            LazyColumn(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                items(state.results, key = { it.item.label + it.item.outputFile.path }) { result ->
                    Row(
                        Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(result.item.label, style = MaterialTheme.typography.bodyMedium)
                        Icon(
                            imageVector = if (result.success) Icons.Filled.Check else Icons.Filled.Error,
                            contentDescription = if (result.success) "Succeeded" else "Failed",
                            tint = if (result.success) Color(0xFF2FB380) else MaterialTheme.colorScheme.error,
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun LibrarySelectRow(recording: RecordingEntity, checked: Boolean, onToggle: () -> Unit) {
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Checkbox(checked = checked, onCheckedChange = { onToggle() })
        Column {
            Text(recording.title, style = MaterialTheme.typography.bodyMedium)
            Text(
                "Surah ${recording.surahNumber} · Ayah ${recording.ayahStart}-${recording.ayahEnd}",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.primary,
            )
        }
    }
}
