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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import android.media.AudioDeviceInfo
import com.sajjil.app.audio.AudioInputDevices
import com.sajjil.app.ui.components.LiveWaveformView
import com.sajjil.core.analysis.AcousticProfile
import com.sajjil.core.analysis.DirectorGuidance
import com.sajjil.core.analysis.GuidanceSeverity
import com.sajjil.core.modes.MicrophoneProfile
import com.sajjil.core.modes.RecordingMode
import com.sajjil.core.modes.RecordingQuality
import com.sajjil.core.quran.QuranMetadata
import com.sajjil.core.quran.SurahInfo
import kotlin.math.roundToInt

@Composable
fun RecordScreen(viewModel: RecordViewModel, modifier: Modifier = Modifier) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
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

        if (state.availableInputDevices.size > 1) {
            InputDeviceSelector(
                devices = state.availableInputDevices,
                selected = state.selectedInputDevice,
                enabled = !state.isRecording,
                onSelect = viewModel::selectInputDevice,
            )
        }

        MicrophoneProfileSelector(
            selected = state.microphoneProfile,
            enabled = !state.isRecording,
            onSelect = viewModel::selectMicrophoneProfile,
        )

        QuranTargetSelector(
            selectedSurah = state.targetSurah,
            ayahStart = state.targetAyahStart,
            ayahEnd = state.targetAyahEnd,
            enabled = !state.isRecording,
            onSelectSurah = viewModel::selectTargetSurah,
            onSetAyahRange = viewModel::setTargetAyahRange,
        )

        RoomCheckSection(
            isChecking = state.isCheckingRoom,
            profile = state.roomProfile,
            enabled = !state.isRecording,
            onCheckRoom = viewModel::runRoomCheck,
            onApplyRecommendedMode = viewModel::applyRecommendedMode,
            onDismiss = viewModel::dismissRoomCheck,
        )

        if (state.isRecording) {
            LiveWaveformView(state.waveformHistory, modifier = Modifier.fillMaxWidth().height(60.dp))
            if (state.clippingDetected) {
                Text(
                    "Clipping detected in this take — consider lowering input gain and re-recording.",
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodySmall,
                )
            }
            LevelMeterCard(peakDb = state.level.peakDb, rmsDb = state.level.rmsDb)
        } else {
            LiveDirectorCard(state.liveGuidance)
        }

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
private fun InputDeviceSelector(
    devices: List<AudioDeviceInfo>,
    selected: AudioDeviceInfo?,
    enabled: Boolean,
    onSelect: (AudioDeviceInfo?) -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Input Device", style = MaterialTheme.typography.titleMedium)
        LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            item {
                FilterChip(
                    selected = selected == null,
                    enabled = enabled,
                    onClick = { onSelect(null) },
                    label = { Text("Default") },
                )
            }
            items(devices) { device ->
                FilterChip(
                    selected = device.id == selected?.id,
                    enabled = enabled,
                    onClick = { onSelect(device) },
                    label = { Text(AudioInputDevices.friendlyName(device)) },
                )
            }
        }
    }
}

@Composable
private fun MicrophoneProfileSelector(selected: MicrophoneProfile, enabled: Boolean, onSelect: (MicrophoneProfile) -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Microphone", style = MaterialTheme.typography.titleMedium)
        LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            items(MicrophoneProfile.entries) { profile ->
                FilterChip(
                    selected = profile == selected,
                    enabled = enabled,
                    onClick = { onSelect(profile) },
                    label = { Text(profile.displayName) },
                )
            }
        }
    }
}

@Composable
private fun RoomCheckSection(
    isChecking: Boolean,
    profile: AcousticProfile?,
    enabled: Boolean,
    onCheckRoom: () -> Unit,
    onApplyRecommendedMode: () -> Unit,
    onDismiss: () -> Unit,
) {
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                Text("AI Acoustic Intelligence", style = MaterialTheme.typography.titleMedium)
                if (isChecking) {
                    CircularProgressIndicator(modifier = Modifier.height(18.dp), strokeWidth = 2.dp)
                } else {
                    OutlinedButton(onClick = onCheckRoom, enabled = enabled) { Text("Check Room (3s)") }
                }
            }
            if (profile != null) {
                Text("Echo: ${profile.echoSeverity.name.lowercase().replaceFirstChar(Char::uppercase)}", style = MaterialTheme.typography.bodyMedium)
                profile.estimatedRt60Seconds?.let {
                    Text("Estimated decay time: ${"%.1f".format(it)}s", style = MaterialTheme.typography.bodyMedium)
                }
                profile.recommendations.forEach { note ->
                    Text("• $note", style = MaterialTheme.typography.bodyMedium)
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (profile.recommendedModeName != null) {
                        Button(onClick = onApplyRecommendedMode) { Text("Use Suggested Profile") }
                    }
                    OutlinedButton(onClick = onDismiss) { Text("Dismiss") }
                }
            } else if (!isChecking) {
                Text(
                    "Run a 3-second room check before recording to catch noise, echo and clipping risk early.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
                )
            }
        }
    }
}

@Composable
private fun QuranTargetSelector(
    selectedSurah: SurahInfo?,
    ayahStart: Int,
    ayahEnd: Int,
    enabled: Boolean,
    onSelectSurah: (SurahInfo?) -> Unit,
    onSetAyahRange: (Int, Int) -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }

    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                Text("Qur'an Target", style = MaterialTheme.typography.titleMedium)
                if (selectedSurah != null) {
                    OutlinedButton(onClick = { onSelectSurah(null) }, enabled = enabled) { Text("Clear") }
                }
            }
            Text(
                "Set the Surah and Ayah range before recording — SAJJIL tags the take automatically when you stop.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
            )
            Box {
                OutlinedTextField(
                    value = selectedSurah?.let { "${it.number}. ${it.transliteratedName}" } ?: "None selected",
                    onValueChange = {},
                    readOnly = true,
                    enabled = enabled,
                    label = { Text("Surah") },
                    modifier = Modifier.fillMaxWidth().clickable(enabled = enabled) { expanded = true },
                )
                DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                    QuranMetadata.surahs.forEach { surah ->
                        DropdownMenuItem(
                            text = { Text("${surah.number}. ${surah.transliteratedName} (${surah.ayahCount} ayat)") },
                            onClick = { onSelectSurah(surah); expanded = false },
                        )
                    }
                }
            }
            if (selectedSurah != null) {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = ayahStart.toString(),
                        onValueChange = { it.toIntOrNull()?.let { v -> onSetAyahRange(v, ayahEnd) } },
                        label = { Text("Ayah start") },
                        enabled = enabled,
                        keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(keyboardType = KeyboardType.Number),
                        modifier = Modifier.weight(1f),
                    )
                    OutlinedTextField(
                        value = ayahEnd.toString(),
                        onValueChange = { it.toIntOrNull()?.let { v -> onSetAyahRange(ayahStart, v) } },
                        label = { Text("Ayah end") },
                        enabled = enabled,
                        keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(keyboardType = KeyboardType.Number),
                        modifier = Modifier.weight(1f),
                    )
                }
            }
        }
    }
}

@Composable
private fun LiveDirectorCard(guidance: DirectorGuidance?) {
    val color = when (guidance?.severity) {
        GuidanceSeverity.GOOD -> Color(0xFF2FB380)
        GuidanceSeverity.WARNING -> MaterialTheme.colorScheme.error
        else -> MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
    }
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text("Recording Director", style = MaterialTheme.typography.titleMedium)
            Text(
                guidance?.message ?: "Listening…",
                style = MaterialTheme.typography.bodyMedium,
                color = color,
            )
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
