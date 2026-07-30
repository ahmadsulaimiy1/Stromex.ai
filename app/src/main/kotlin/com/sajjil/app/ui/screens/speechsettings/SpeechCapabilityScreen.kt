package com.sajjil.app.ui.screens.speechsettings

import android.content.ActivityNotFoundException
import android.content.Intent
import android.provider.Settings
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Error
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sajjil.app.speech.CapabilityDetail
import com.sajjil.app.speech.SpeechCapabilityStatus
import com.sajjil.app.ui.components.GlassCard

@Composable
fun SpeechCapabilityScreen(viewModel: SpeechCapabilityViewModel, modifier: Modifier = Modifier) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val context = LocalContext.current

    LazyColumn(modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        item {
            Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Speech & Language Packs", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.SemiBold)
                IconButton(onClick = viewModel::refresh) { Icon(Icons.Filled.Refresh, contentDescription = "Refresh") }
            }
            Text(
                "What this device can actually do offline, checked just now — not assumed.",
                style = MaterialTheme.typography.bodyMedium,
            )
        }

        state.report?.let { report ->
            items(report.languages) { language ->
                GlassCard {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text(language.language.displayName, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                        CapabilityRow("Offline Recognition", language.recognition)
                        CapabilityRow("Offline Voice (TTS)", language.textToSpeech)
                    }
                }
            }
        }

        item {
            GlassCard {
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("How SAJJIL chooses a speech engine", fontWeight = FontWeight.SemiBold)
                    Text("1. Installed Android offline speech services — active.", style = MaterialTheme.typography.bodySmall)
                    Text(
                        "2. SAJJIL Offline Speech Pack (downloadable) — not yet available in this build. " +
                            "No model has been sourced or verified to ship here; see docs/SPEECH_INTELLIGENCE.md.",
                        style = MaterialTheme.typography.bodySmall,
                    )
                    Text(
                        "3. Optional cloud processing — never used. SAJJIL does not send audio to a network " +
                            "service, and never will without you explicitly turning it on.",
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            }
        }

        item {
            GlassCard {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Install a language pack", fontWeight = FontWeight.SemiBold)
                    Text(
                        "SAJJIL cannot install offline speech packs itself — Android manages them. " +
                            "These buttons open the system screens where you install or manage them.",
                        style = MaterialTheme.typography.bodySmall,
                    )
                    OutlinedButton(onClick = { openSettings(context, Settings.ACTION_VOICE_INPUT_SETTINGS) }) {
                        Text("Open Voice Input Settings")
                    }
                    OutlinedButton(onClick = { openTtsSettings(context) }) {
                        Text("Open Text-to-Speech Settings")
                    }
                }
            }
        }

        if (state.voices.isNotEmpty()) {
            item { Text("Installed voices", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold) }
            items(state.voices) { voice ->
                GlassCard {
                    Text(voice.localeTag, fontWeight = FontWeight.Medium)
                    Text(
                        "${voice.qualityLabel} quality · ${if (voice.isOffline) "Offline" else "Requires network"}",
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            }
        }
    }
}

@Composable
private fun CapabilityRow(label: String, detail: CapabilityDetail) {
    Row(verticalAlignment = androidx.compose.ui.Alignment.Top, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        val (icon, tint) = when (detail.status) {
            SpeechCapabilityStatus.AVAILABLE -> Icons.Filled.CheckCircle to Color(0xFF2E7D32)
            SpeechCapabilityStatus.LANGUAGE_PACK_MISSING -> Icons.Filled.Warning to Color(0xFFF9A825)
            SpeechCapabilityStatus.UNSUPPORTED -> Icons.Filled.Error to Color(0xFFC62828)
        }
        Icon(icon, contentDescription = null, tint = tint)
        Column {
            Text(label, fontWeight = FontWeight.Medium)
            Text(detail.message, style = MaterialTheme.typography.bodySmall)
        }
    }
}

private fun openSettings(context: android.content.Context, action: String) {
    try {
        context.startActivity(Intent(action).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
    } catch (e: ActivityNotFoundException) {
        try {
            context.startActivity(Intent(Settings.ACTION_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        } catch (inner: ActivityNotFoundException) {
            // Nothing more we can do — degrade silently rather than crash on a device with no Settings app.
        }
    }
}

private fun openTtsSettings(context: android.content.Context) {
    try {
        context.startActivity(Intent("com.android.settings.TTS_SETTINGS").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
    } catch (e: ActivityNotFoundException) {
        openSettings(context, Settings.ACTION_SETTINGS)
    }
}
