package com.sajjil.app.ui.screens.voicestudio

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material.icons.filled.VolumeUp
import androidx.compose.material3.Button
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sajjil.app.speech.SpeechCapabilityStatus
import com.sajjil.app.ui.components.GlassCard
import com.sajjil.core.speech.TranscriptLanguage

@Composable
fun VoiceStudioScreen(viewModel: VoiceStudioViewModel, modifier: Modifier = Modifier) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    var title by remember { mutableStateOf("") }

    LazyColumn(modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        item {
            Text("Voice Studio", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.SemiBold)
            Text(
                "Record, transcribe offline, search, and read back — one workflow.",
                style = MaterialTheme.typography.bodyMedium,
            )
        }

        item { LanguageSelector(state.selectedLanguage, state.isListening, viewModel::selectLanguage) }

        item {
            val capability = state.capability?.forLanguage(state.selectedLanguage)
            if (capability != null && capability.recognition.status != SpeechCapabilityStatus.AVAILABLE) {
                GlassCard {
                    Text("Recognition unavailable", fontWeight = FontWeight.SemiBold)
                    Text(capability.recognition.message, style = MaterialTheme.typography.bodySmall)
                }
            }
        }

        item {
            GlassCard {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        Button(onClick = { if (state.isListening) viewModel.stopListening() else viewModel.startListening() }) {
                            Icon(if (state.isListening) Icons.Filled.Stop else Icons.Filled.Mic, contentDescription = null)
                            Text(if (state.isListening) "  Stop" else "  Start Listening")
                        }
                        state.statusMessage?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
                    }
                    if (state.partialText.isNotBlank()) {
                        Text(state.partialText, style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.Light)
                    }
                }
            }
        }

        items(state.segments) { segment ->
            GlassCard {
                Text(formatTimestamp(segment.startMs), style = MaterialTheme.typography.labelSmall)
                Text(segment.text, style = MaterialTheme.typography.bodyMedium)
                segment.confidence?.let {
                    Text("Confidence: ${(it * 100).toInt()}%", style = MaterialTheme.typography.labelSmall)
                }
            }
        }

        if (state.segments.isNotEmpty() && !state.isListening) {
            item {
                GlassCard {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("Save this session", fontWeight = FontWeight.SemiBold)
                        OutlinedTextField(
                            value = title,
                            onValueChange = { title = it },
                            label = { Text("Title") },
                            modifier = Modifier.fillMaxWidth(),
                        )
                        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            Button(onClick = { viewModel.saveSession(title) }) { Text("Save") }
                            IconButton(onClick = { viewModel.speak(state.fullTranscriptText) }) {
                                Icon(Icons.Filled.VolumeUp, contentDescription = "Read transcript aloud")
                            }
                        }
                    }
                }
            }
        }

        state.lastSavedTitle?.let { saved ->
            item { Text("Saved \"$saved\" to your library.", style = MaterialTheme.typography.bodySmall) }
        }

        item {
            GlassCard {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Search transcripts", fontWeight = FontWeight.SemiBold)
                    OutlinedTextField(
                        value = state.searchQuery,
                        onValueChange = viewModel::search,
                        leadingIcon = { Icon(Icons.Filled.Search, contentDescription = null) },
                        label = { Text("Search across saved transcripts") },
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
            }
        }

        items(state.searchResults) { result ->
            GlassCard {
                Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text("Recording #${result.recordingId} · ${formatTimestamp(result.segment.startMs)}", style = MaterialTheme.typography.labelSmall)
                        Text(result.segment.text, style = MaterialTheme.typography.bodyMedium)
                    }
                    IconButton(onClick = { viewModel.speak(result.segment.text) }) {
                        Icon(Icons.Filled.PlayArrow, contentDescription = "Read aloud")
                    }
                }
            }
        }
    }
}

@Composable
private fun LanguageSelector(selected: TranscriptLanguage, disabled: Boolean, onSelect: (TranscriptLanguage) -> Unit) {
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        TranscriptLanguage.entries.forEach { language ->
            FilterChip(
                selected = language == selected,
                onClick = { if (!disabled) onSelect(language) },
                label = { Text(language.displayName) },
            )
        }
    }
}

private fun formatTimestamp(ms: Long): String {
    val totalSeconds = ms / 1000
    val minutes = totalSeconds / 60
    val seconds = totalSeconds % 60
    return "%d:%02d".format(minutes, seconds)
}
