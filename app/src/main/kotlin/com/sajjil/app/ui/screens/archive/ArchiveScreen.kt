package com.sajjil.app.ui.screens.archive

import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ContentCut
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.SaveAlt
import androidx.compose.material.icons.filled.Share
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.outlined.StarOutline
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.app.export.ShareExporter
import com.sajjil.app.ui.components.PlaybackWaveformView
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun ArchiveScreen(
    viewModel: ArchiveViewModel,
    onOpenDashboard: (Long) -> Unit,
    onOpenEditor: (Long) -> Unit,
    modifier: Modifier = Modifier,
) {
    val recordings by viewModel.recordings.collectAsStateWithLifecycle()
    val query by viewModel.searchQuery.collectAsStateWithLifecycle()
    val isPlaying by viewModel.isPlaying.collectAsStateWithLifecycle()
    val positionMs by viewModel.positionMs.collectAsStateWithLifecycle()
    val durationMs by viewModel.durationMs.collectAsStateWithLifecycle()
    val playingFile by viewModel.playingFile.collectAsStateWithLifecycle()
    val waveformPeaks by viewModel.waveformPeaks.collectAsStateWithLifecycle()
    val exportMessage by viewModel.exportMessage.collectAsStateWithLifecycle()

    val context = LocalContext.current
    var saveTarget by remember { mutableStateOf<RecordingEntity?>(null) }
    val saveLauncher = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("audio/*")) { uri ->
        val target = saveTarget
        if (uri != null && target != null) viewModel.exportTo(uri, target)
        saveTarget = null
    }

    LaunchedEffect(exportMessage) {
        exportMessage?.let {
            Toast.makeText(context, it, Toast.LENGTH_SHORT).show()
            viewModel.clearExportMessage()
        }
    }

    Column(modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text("SAJJIL Library", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.SemiBold)
        Text("Every recording, one tap from playing.", style = MaterialTheme.typography.bodyMedium)

        OutlinedTextField(
            value = query,
            onValueChange = viewModel::onQueryChange,
            label = { Text("Search recordings") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )

        if (recordings.isEmpty()) {
            Text("No recordings yet — capture something in SAJJIL Record.", style = MaterialTheme.typography.bodyMedium)
        } else {
            LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(recordings, key = { it.id }) { recording ->
                    val isActive = playingFile?.absolutePath == recording.filePath
                    ArchiveRow(
                        recording = recording,
                        isActive = isActive,
                        isPlaying = isActive && isPlaying,
                        positionMs = if (isActive) positionMs else 0L,
                        durationMs = if (isActive && durationMs > 0L) durationMs else recording.durationMs,
                        waveformPeaks = if (isActive) waveformPeaks else null,
                        onTogglePlay = { viewModel.togglePlay(recording) },
                        onSeek = { viewModel.seekTo(it) },
                        onToggleFavorite = { viewModel.toggleFavorite(recording) },
                        onDelete = { viewModel.delete(recording) },
                        onShare = { context.startActivity(ShareExporter.shareIntent(context, File(recording.filePath))) },
                        onSaveToDevice = {
                            saveTarget = recording
                            saveLauncher.launch(File(recording.filePath).name)
                        },
                        onEdit = { onOpenEditor(recording.id) },
                        onOpenDashboard = { onOpenDashboard(recording.id) },
                    )
                }
            }
        }
    }
}

@Composable
private fun ArchiveRow(
    recording: RecordingEntity,
    isActive: Boolean,
    isPlaying: Boolean,
    positionMs: Long,
    durationMs: Long,
    waveformPeaks: FloatArray?,
    onTogglePlay: () -> Unit,
    onSeek: (Long) -> Unit,
    onToggleFavorite: () -> Unit,
    onDelete: () -> Unit,
    onShare: () -> Unit,
    onSaveToDevice: () -> Unit,
    onEdit: () -> Unit,
    onOpenDashboard: () -> Unit,
) {
    var menuExpanded by remember { mutableStateOf(false) }

    Card(
        colors = CardDefaults.cardColors(
            containerColor = if (isActive) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceVariant,
        ),
        modifier = Modifier.fillMaxWidth().clickable(onClick = onOpenDashboard),
    ) {
        Column(Modifier.padding(12.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                    IconButton(onClick = onTogglePlay) {
                        Icon(
                            imageVector = if (isPlaying) Icons.Filled.Pause else Icons.Filled.PlayArrow,
                            contentDescription = if (isPlaying) "Pause" else "Play",
                            tint = MaterialTheme.colorScheme.primary,
                        )
                    }
                    Column {
                        Text(recording.title, style = MaterialTheme.typography.titleMedium)
                        Text(
                            "${recording.recordingMode} · ${formatDate(recording.createdAtEpochMs)} · ${formatDuration(recording.durationMs)}",
                            style = MaterialTheme.typography.bodyMedium,
                        )
                        if (recording.surahNumber != null) {
                            Text(
                                "Surah ${recording.surahNumber} · Ayah ${recording.ayahStart}-${recording.ayahEnd} · Juz ${recording.juz}",
                                style = MaterialTheme.typography.labelMedium,
                                color = MaterialTheme.colorScheme.primary,
                            )
                        }
                    }
                }

                // A single overflow menu instead of a growing row of icons -- Favorite, Share,
                // Save to device, and Delete all live here rather than each claiming their own
                // permanently-visible IconButton, per the "reduce icons" review feedback.
                Column {
                    IconButton(onClick = { menuExpanded = true }) {
                        Icon(Icons.Filled.MoreVert, contentDescription = "More actions")
                    }
                    DropdownMenu(expanded = menuExpanded, onDismissRequest = { menuExpanded = false }) {
                        DropdownMenuItem(
                            text = { Text(if (recording.isFavorite) "Unfavorite" else "Favorite") },
                            leadingIcon = {
                                Icon(if (recording.isFavorite) Icons.Filled.Star else Icons.Outlined.StarOutline, contentDescription = null)
                            },
                            onClick = { menuExpanded = false; onToggleFavorite() },
                        )
                        DropdownMenuItem(
                            text = { Text("Share") },
                            leadingIcon = { Icon(Icons.Filled.Share, contentDescription = null) },
                            onClick = { menuExpanded = false; onShare() },
                        )
                        DropdownMenuItem(
                            text = { Text("Save to device") },
                            leadingIcon = { Icon(Icons.Filled.SaveAlt, contentDescription = null) },
                            onClick = { menuExpanded = false; onSaveToDevice() },
                        )
                        DropdownMenuItem(
                            text = { Text("Edit (trim / cut)") },
                            leadingIcon = { Icon(Icons.Filled.ContentCut, contentDescription = null) },
                            onClick = { menuExpanded = false; onEdit() },
                        )
                        DropdownMenuItem(
                            text = { Text("Delete") },
                            leadingIcon = { Icon(Icons.Filled.Delete, contentDescription = null) },
                            onClick = { menuExpanded = false; onDelete() },
                        )
                    }
                }
            }

            if (isActive) {
                PlaybackWaveformView(
                    peaks = waveformPeaks,
                    progress = if (durationMs > 0L) positionMs.toFloat() / durationMs.toFloat() else 0f,
                    modifier = Modifier.fillMaxWidth().height(40.dp).padding(top = 8.dp),
                )
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Text(formatDuration(positionMs), style = MaterialTheme.typography.labelSmall)
                    Slider(
                        value = positionMs.toFloat().coerceIn(0f, durationMs.toFloat().coerceAtLeast(1f)),
                        onValueChange = { onSeek(it.toLong()) },
                        valueRange = 0f..durationMs.toFloat().coerceAtLeast(1f),
                        modifier = Modifier.weight(1f).padding(horizontal = 8.dp),
                    )
                    Text(formatDuration(durationMs), style = MaterialTheme.typography.labelSmall)
                }
            }
        }
    }
}

private fun formatDate(epochMs: Long): String =
    SimpleDateFormat("d MMM yyyy", Locale.getDefault()).format(Date(epochMs))

private fun formatDuration(ms: Long): String {
    val totalSeconds = ms / 1000
    return "%d:%02d".format(totalSeconds / 60, totalSeconds % 60)
}
