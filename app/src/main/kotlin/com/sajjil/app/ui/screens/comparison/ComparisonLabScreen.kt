package com.sajjil.app.ui.screens.comparison

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
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
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

@Composable
fun ComparisonLabScreen(viewModel: ComparisonLabViewModel, modifier: Modifier = Modifier) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val activeSlot by viewModel.player.activeSlot.collectAsStateWithLifecycle()
    val isPlaying by viewModel.player.isPlaying.collectAsStateWithLifecycle()
    val positionMs by viewModel.player.positionMs.collectAsStateWithLifecycle()

    var pickerForSlot by remember { mutableStateOf<String?>(null) }

    Column(modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text("Audio Comparison Laboratory", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.SemiBold)
        Text(
            "Load up to three takes and switch between them at the same point in the recording.",
            style = MaterialTheme.typography.bodyMedium,
        )

        state.slots.forEach { (slot, recording) ->
            SlotCard(
                slot = slot,
                recording = recording,
                isActive = activeSlot == slot,
                isPlaying = isPlaying && activeSlot == slot,
                onPick = { pickerForSlot = slot },
                onPlay = { viewModel.play(slot) },
            )
        }

        if (activeSlot != null) {
            val durationMs = viewModel.player.currentDurationMs.coerceAtLeast(1)
            LinearProgressIndicator(progress = { (positionMs.toFloat() / durationMs).coerceIn(0f, 1f) }, modifier = Modifier.fillMaxWidth())
            OutlinedButton(onClick = { viewModel.stop() }) { Text("Stop") }
        }

        pickerForSlot?.let { slot ->
            Text("Choose a recording for slot $slot", style = MaterialTheme.typography.titleMedium)
            LazyColumn(Modifier.fillMaxWidth().height(220.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                items(state.library, key = { it.id }) { recording ->
                    Card(
                        modifier = Modifier.fillMaxWidth().clickable {
                            viewModel.assignSlot(slot, recording)
                            pickerForSlot = null
                        },
                        shape = RoundedCornerShape(12.dp),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                    ) {
                        Text(recording.title, Modifier.padding(12.dp), style = MaterialTheme.typography.bodyMedium)
                    }
                }
            }
        }
    }
}

@Composable
private fun SlotCard(
    slot: String,
    recording: RecordingEntity?,
    isActive: Boolean,
    isPlaying: Boolean,
    onPick: () -> Unit,
    onPlay: () -> Unit,
) {
    Card(
        colors = CardDefaults.cardColors(
            containerColor = if (isActive) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceVariant,
        ),
    ) {
        Row(
            Modifier.fillMaxWidth().padding(12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f).clickable(onClick = onPick)) {
                Text("Slot $slot", style = MaterialTheme.typography.labelLarge)
                Text(recording?.title ?: "Tap to choose a recording", style = MaterialTheme.typography.bodyMedium)
            }
            if (recording != null) {
                Button(onClick = onPlay) { Text(if (isPlaying) "Playing" else "Play") }
            }
        }
    }
}
