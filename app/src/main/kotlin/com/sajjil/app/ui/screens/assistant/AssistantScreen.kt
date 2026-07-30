package com.sajjil.app.ui.screens.assistant

import androidx.compose.foundation.clickable
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
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sajjil.app.ui.components.GlassCard
import com.sajjil.core.speech.TranscriptLanguage

@Composable
fun AssistantScreen(viewModel: AssistantViewModel, modifier: Modifier = Modifier) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    LazyColumn(modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        item {
            Text("SAJJIL Assistant", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.SemiBold)
            Text(
                "Pattern-based request handling over your real library — not a conversational AI. " +
                    "It understands a fixed set of phrasings and says so plainly when a request doesn't match one.",
                style = MaterialTheme.typography.bodySmall,
                fontStyle = FontStyle.Italic,
            )
        }

        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                TranscriptLanguage.entries.forEach { language ->
                    FilterChip(
                        selected = language == state.language,
                        onClick = { viewModel.selectLanguage(language) },
                        label = { Text(language.displayName) },
                    )
                }
            }
        }

        item {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = state.inputText,
                    onValueChange = viewModel::updateInput,
                    label = { Text("Ask SAJJIL") },
                    placeholder = { Text("Show me Surah Al-Kahf recordings") },
                    modifier = Modifier.weight(1f),
                )
                IconButton(onClick = { if (state.isListening) viewModel.stopListening() else viewModel.listenForCommand() }) {
                    Icon(if (state.isListening) Icons.Filled.Stop else Icons.Filled.Mic, contentDescription = "Speak your request")
                }
                IconButton(onClick = viewModel::submit) {
                    Icon(Icons.Filled.Send, contentDescription = "Submit")
                }
            }
        }

        state.responseMessage?.let { message ->
            item {
                GlassCard {
                    Text(message, style = MaterialTheme.typography.bodyMedium)
                }
            }
        }

        if (state.results.isEmpty() && state.responseMessage == null) {
            item {
                GlassCard {
                    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text("Try asking:", fontWeight = FontWeight.SemiBold)
                        Text("\"Show me Surah Al-Kahf recordings\"", style = MaterialTheme.typography.bodySmall)
                        Text("\"Find where I discussed zakat\"", style = MaterialTheme.typography.bodySmall)
                        Text("\"Read this transcript\"", style = MaterialTheme.typography.bodySmall)
                        Text("\"Which recordings have poor quality?\"", style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }

        items(state.results) { result ->
            GlassCard(modifier = Modifier.fillMaxWidth().clickable { viewModel.selectResult(result) }) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    Column {
                        Text(result.title, fontWeight = FontWeight.Medium)
                        Text(result.subtitle, style = MaterialTheme.typography.bodySmall)
                    }
                    if (result.recordingId == state.selectedRecordingId) {
                        Text("Selected", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
                    }
                }
            }
        }
    }
}
