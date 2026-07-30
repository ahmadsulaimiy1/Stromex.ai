package com.sajjil.app.ui.screens.enhance

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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.core.dsp.NoiseReductionStrength

@Composable
fun EnhanceScreen(viewModel: EnhanceViewModel, modifier: Modifier = Modifier) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    Column(modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text("SAJJIL Enhance", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.SemiBold)
        Text(
            "AI restoration laboratory: remove noise, echo and hiss while preserving natural voice.",
            style = MaterialTheme.typography.bodyMedium,
        )

        Text("Select a recording", style = MaterialTheme.typography.titleMedium)
        LazyColumn(modifier = Modifier.fillMaxWidth().height(180.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            items(state.recordings, key = { it.id }) { recording ->
                RecordingRow(recording, isSelected = recording.id == state.selected?.id) { viewModel.select(recording) }
            }
        }

        if (state.selected != null) {
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
    }
}

@Composable
private fun RecordingRow(recording: RecordingEntity, isSelected: Boolean, onClick: () -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
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
