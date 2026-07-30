package com.sajjil.app.ui.screens.editor

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sajjil.app.ui.components.WaveformSelectionView

@Composable
fun EditorScreen(viewModel: EditorViewModel, recordingId: Long, modifier: Modifier = Modifier) {
    LaunchedEffect(recordingId) { viewModel.load(recordingId) }
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    Column(modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text("Edit Recording", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.SemiBold)
        state.recording?.let { recording ->
            Text(recording.title, style = MaterialTheme.typography.bodyMedium)
        }

        if (state.isLoading) {
            CircularProgressIndicator()
            return@Column
        }

        Text("Choose a start and end point below.", style = MaterialTheme.typography.bodyMedium)
        WaveformSelectionView(
            peaks = state.waveformPeaks,
            selectionStart = state.selectionStart,
            selectionEnd = state.selectionEnd,
            modifier = Modifier.fillMaxWidth().height(56.dp),
        )
        Text("Start", style = MaterialTheme.typography.labelMedium)
        Slider(
            value = state.selectionStart,
            onValueChange = { viewModel.setSelection(it, state.selectionEnd) },
            valueRange = 0f..1f,
        )
        Text("End", style = MaterialTheme.typography.labelMedium)
        Slider(
            value = state.selectionEnd,
            onValueChange = { viewModel.setSelection(state.selectionStart, it) },
            valueRange = 0f..1f,
        )

        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Text("Fade in", style = MaterialTheme.typography.bodyMedium)
            Switch(checked = state.fadeInEnabled, onCheckedChange = { viewModel.toggleFadeIn() })
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Text("Fade out", style = MaterialTheme.typography.bodyMedium)
            Switch(checked = state.fadeOutEnabled, onCheckedChange = { viewModel.toggleFadeOut() })
        }

        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Button(onClick = { viewModel.applyTrim() }, enabled = !state.isProcessing) {
                if (state.isProcessing) {
                    CircularProgressIndicator(modifier = Modifier.height(18.dp), strokeWidth = 2.dp)
                } else {
                    Text("Trim to Selection")
                }
            }
            OutlinedButton(onClick = { viewModel.applyCut() }, enabled = !state.isProcessing) {
                Text("Delete Selection")
            }
        }

        if (state.savedToLibrary) {
            Text(
                "Saved to Library as a new take.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.primary,
            )
        }
    }
}
