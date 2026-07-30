package com.sajjil.app.ui.screens.quranstudio

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.core.quran.SurahInfo

@Composable
fun QuranStudioScreen(
    viewModel: QuranStudioViewModel,
    onOpenBatchProduction: () -> Unit = {},
    onOpenSurahProject: (Int) -> Unit = {},
    modifier: Modifier = Modifier,
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    Column(modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text("SAJJIL Qur'an Studio", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.SemiBold)
        Text("Organise recitations by Surah, Ayah and Juz.", style = MaterialTheme.typography.bodyMedium)

        Button(onClick = onOpenBatchProduction) { Text("Batch Qur'an Production") }

        if (state.untaggedRecordings.isNotEmpty()) {
            Text("Tag a recording", style = MaterialTheme.typography.titleMedium)
            LazyColumn(Modifier.fillMaxWidth().height(120.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                items(state.untaggedRecordings, key = { it.id }) { recording ->
                    UntaggedRow(recording, isSelected = recording.id == state.selectedRecording?.id) {
                        viewModel.selectRecording(recording)
                    }
                }
            }

            if (state.selectedRecording != null) {
                SurahPicker(selected = state.selectedSurah, onSelect = viewModel::selectSurah)

                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = state.ayahStart.toString(),
                        onValueChange = { it.toIntOrNull()?.let { v -> viewModel.setAyahRange(v, state.ayahEnd) } },
                        label = { Text("Ayah start") },
                        keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(keyboardType = KeyboardType.Number),
                        modifier = Modifier.weight(1f),
                    )
                    OutlinedTextField(
                        value = state.ayahEnd.toString(),
                        onValueChange = { it.toIntOrNull()?.let { v -> viewModel.setAyahRange(state.ayahStart, v) } },
                        label = { Text("Ayah end") },
                        keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(keyboardType = KeyboardType.Number),
                        modifier = Modifier.weight(1f),
                    )
                }

                Button(onClick = { viewModel.tagSelected() }) { Text("Save to Qur'an Library") }
            }
        }

        Text("Qur'an Library", style = MaterialTheme.typography.titleMedium)
        if (state.library.isEmpty()) {
            Text("No recitations catalogued yet.", style = MaterialTheme.typography.bodyMedium)
        } else {
            LazyColumn(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                items(state.library, key = { it.id }) { recording ->
                    LibraryRow(recording, onClick = { recording.surahNumber?.let(onOpenSurahProject) })
                }
            }
        }
    }
}

@Composable
private fun SurahPicker(selected: SurahInfo, onSelect: (SurahInfo) -> Unit) {
    var expanded by androidx.compose.runtime.remember { androidx.compose.runtime.mutableStateOf(false) }
    Column {
        OutlinedTextField(
            value = "${selected.number}. ${selected.transliteratedName} (${selected.ayahCount} ayat)",
            onValueChange = {},
            readOnly = true,
            label = { Text("Surah") },
            modifier = Modifier.fillMaxWidth().clickable { expanded = true },
            enabled = false,
        )
        androidx.compose.material3.DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            com.sajjil.core.quran.QuranMetadata.surahs.forEach { surah ->
                androidx.compose.material3.DropdownMenuItem(
                    text = { Text("${surah.number}. ${surah.transliteratedName}") },
                    onClick = { onSelect(surah); expanded = false },
                )
            }
        }
    }
}

@Composable
private fun UntaggedRow(recording: RecordingEntity, isSelected: Boolean, onClick: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (isSelected) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceVariant,
        ),
    ) {
        Text(recording.title, Modifier.padding(12.dp), style = MaterialTheme.typography.bodyMedium)
    }
}

@Composable
private fun LibraryRow(recording: RecordingEntity, onClick: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
    ) {
        Column(Modifier.padding(12.dp)) {
            Text(recording.title, style = MaterialTheme.typography.titleMedium)
            Text(
                "Surah ${recording.surahNumber} · Ayah ${recording.ayahStart}-${recording.ayahEnd} · Juz ${recording.juz}",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.primary,
            )
        }
    }
}
