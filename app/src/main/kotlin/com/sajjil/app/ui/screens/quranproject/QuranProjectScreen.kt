package com.sajjil.app.ui.screens.quranproject

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.outlined.StarOutline
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.app.ui.components.GlassCard
import com.sajjil.core.quran.AyahRange

@Composable
fun QuranProjectScreen(viewModel: QuranProjectViewModel, surahNumber: Int, modifier: Modifier = Modifier) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    LaunchedEffect(surahNumber) { viewModel.load(surahNumber) }

    Column(
        modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        val surah = state.surah
        Text(
            surah?.let { "${it.number}. ${it.transliteratedName}" } ?: "Surah Project",
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.SemiBold,
        )

        state.progress?.let { progress ->
            GlassCard {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Progress", style = MaterialTheme.typography.titleMedium)
                        Text("${progress.percentComplete.toInt()}%", fontWeight = FontWeight.SemiBold)
                    }
                    LinearProgressIndicator(progress = { (progress.percentComplete / 100.0).toFloat() }, modifier = Modifier.fillMaxWidth())
                    Text("${progress.coveredAyahs} / ${progress.totalAyahs} ayahs recorded", style = MaterialTheme.typography.bodyMedium)
                    progress.averageQualityScore?.let {
                        Text("Average quality: ${it.toInt()} / 100", style = MaterialTheme.typography.bodyMedium)
                    }
                    if (progress.isComplete) {
                        Text("Surah complete", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.primary)
                    } else if (progress.missingRanges.isNotEmpty()) {
                        Text("Still needed:", style = MaterialTheme.typography.titleMedium)
                        progress.missingRanges.forEach { range ->
                            Text("• Ayah ${range.start}–${range.end}", style = MaterialTheme.typography.bodyMedium)
                        }
                    }
                }
            }
        }

        Text("Recorded Takes", style = MaterialTheme.typography.titleMedium)
        if (state.versionGroups.isEmpty()) {
            Text(
                "No takes recorded yet — use SAJJIL Record with this Surah set as your Qur'an Target.",
                style = MaterialTheme.typography.bodyMedium,
            )
        } else {
            state.versionGroups.forEach { (range, recordings) ->
                VersionGroupCard(
                    range = range,
                    recordings = recordings,
                    onSetPrimary = { chosen -> viewModel.setPrimaryVersion(range, chosen) },
                    onSaveNotes = { recording, notes -> viewModel.updateNotes(recording, notes) },
                )
            }
        }
    }
}

@Composable
private fun VersionGroupCard(
    range: AyahRange,
    recordings: List<RecordingEntity>,
    onSetPrimary: (RecordingEntity) -> Unit,
    onSaveNotes: (RecordingEntity, String) -> Unit,
) {
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text("Ayah ${range.start}–${range.end}", style = MaterialTheme.typography.titleMedium)
            recordings.forEach { recording ->
                VersionRow(recording, isOnlyVersion = recordings.size == 1, onSetPrimary = { onSetPrimary(recording) }, onSaveNotes = { onSaveNotes(recording, it) })
            }
        }
    }
}

@Composable
private fun VersionRow(
    recording: RecordingEntity,
    isOnlyVersion: Boolean,
    onSetPrimary: () -> Unit,
    onSaveNotes: (String) -> Unit,
) {
    var notesExpanded by remember { mutableStateOf(false) }
    var notesText by remember(recording.id) { mutableStateOf(recording.notes.orEmpty()) }

    Column(Modifier.fillMaxWidth().clickable { notesExpanded = !notesExpanded }) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Column {
                Text(recording.title, style = MaterialTheme.typography.bodyMedium)
                Text(
                    "${recording.recordingMode} · ${recording.studioReadinessScore?.let { "$it/100" } ?: "not scored"}",
                    style = MaterialTheme.typography.labelMedium,
                )
            }
            if (!isOnlyVersion) {
                IconButton(onClick = onSetPrimary) {
                    Icon(
                        imageVector = if (recording.isPrimaryVersion) Icons.Filled.Star else Icons.Outlined.StarOutline,
                        contentDescription = "Set as primary version",
                    )
                }
            }
        }
        if (notesExpanded) {
            OutlinedTextField(
                value = notesText,
                onValueChange = { notesText = it },
                label = { Text("Notes") },
                modifier = Modifier.fillMaxWidth().padding(top = 4.dp),
            )
            Row(horizontalArrangement = Arrangement.End, modifier = Modifier.fillMaxWidth()) {
                TextButton(onClick = { onSaveNotes(notesText); notesExpanded = false }) { Text("Save Notes") }
            }
        }
    }
}
