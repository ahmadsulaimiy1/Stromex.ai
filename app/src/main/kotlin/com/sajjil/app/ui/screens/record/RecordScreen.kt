package com.sajjil.app.ui.screens.record

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sajjil.core.modes.RecordingMode
import com.sajjil.core.modes.RecordingQuality
import kotlin.math.roundToInt

@Composable
fun RecordScreen(viewModel: RecordViewModel, modifier: Modifier = Modifier) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp),
    ) {
        Text("SAJJIL Record", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.SemiBold)
        Text(
            state.mode.config.description,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
        )

        RecordingModeSelector(
            selected = state.mode,
            enabled = !state.isRecording,
            onSelect = viewModel::selectMode,
        )

        QualitySelector(
            selected = state.quality,
            enabled = !state.isRecording,
            onSelect = viewModel::selectQuality,
        )

        LevelMeterCard(peakDb = state.level.peakDb, rmsDb = state.level.rmsDb)

        Spacer(Modifier.height(4.dp))

        Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
            RecordButton(
                isRecording = state.isRecording,
                onClick = { if (state.isRecording) viewModel.stopRecording() else viewModel.startRecording() },
            )
        }

        if (state.isRecording) {
            Text(
                formatElapsed(state.elapsedMs),
                style = MaterialTheme.typography.titleLarge,
                modifier = Modifier.fillMaxWidth(),
                textAlign = androidx.compose.ui.text.style.TextAlign.Center,
            )
        }
    }
}

@Composable
private fun RecordingModeSelector(selected: RecordingMode, enabled: Boolean, onSelect: (RecordingMode) -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Recording Mode", style = MaterialTheme.typography.titleMedium)
        LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            items(RecordingMode.entries) { mode ->
                FilterChip(
                    selected = mode == selected,
                    enabled = enabled,
                    onClick = { onSelect(mode) },
                    label = { Text(mode.displayName) },
                )
            }
        }
    }
}

@Composable
private fun QualitySelector(selected: RecordingQuality, enabled: Boolean, onSelect: (RecordingQuality) -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Quality", style = MaterialTheme.typography.titleMedium)
        LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            items(RecordingQuality.entries) { quality ->
                FilterChip(
                    selected = quality == selected,
                    enabled = enabled,
                    onClick = { onSelect(quality) },
                    label = { Text(quality.displayName) },
                )
            }
        }
    }
}

@Composable
private fun LevelMeterCard(peakDb: Float, rmsDb: Float) {
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Live Level", style = MaterialTheme.typography.titleMedium)
            LevelBar(label = "Peak", db = peakDb)
            LevelBar(label = "RMS", db = rmsDb)
        }
    }
}

@Composable
private fun LevelBar(label: String, db: Float) {
    val fraction = ((db + 60f) / 60f).coerceIn(0f, 1f)
    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(label, modifier = Modifier.padding(end = 4.dp))
        LinearProgressIndicator(
            progress = { fraction },
            modifier = Modifier
                .fillMaxWidth()
                .height(8.dp),
            color = if (db > -3f) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary,
        )
    }
    Text("${db.roundToInt()} dB", style = MaterialTheme.typography.labelMedium)
}

@Composable
private fun RecordButton(isRecording: Boolean, onClick: () -> Unit) {
    Surface(
        shape = CircleShape,
        color = if (isRecording) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary,
        modifier = Modifier
            .aspectRatio(1f)
            .height(88.dp)
            .clickable(onClick = onClick),
    ) {
        Box(contentAlignment = Alignment.Center) {
            Icon(
                imageVector = if (isRecording) Icons.Filled.Stop else Icons.Filled.Mic,
                contentDescription = if (isRecording) "Stop recording" else "Start recording",
                tint = if (isRecording) MaterialTheme.colorScheme.onError else MaterialTheme.colorScheme.onPrimary,
                modifier = Modifier.height(36.dp),
            )
        }
    }
}

private fun formatElapsed(ms: Long): String {
    val totalSeconds = ms / 1000
    val minutes = totalSeconds / 60
    val seconds = totalSeconds % 60
    return "%02d:%02d".format(minutes, seconds)
}
