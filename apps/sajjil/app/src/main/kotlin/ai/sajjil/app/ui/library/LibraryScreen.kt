package ai.sajjil.app.ui.library

import ai.sajjil.app.Services
import ai.sajjil.app.data.LibrarySort
import ai.sajjil.app.data.RecordingEntity
import ai.sajjil.app.ui.Format
import ai.sajjil.app.ui.components.CircularIconButton
import ai.sajjil.app.ui.components.EmptyState
import ai.sajjil.app.ui.theme.Radius
import ai.sajjil.app.ui.theme.Space
import ai.sajjil.app.ui.theme.sajjilColors
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.LibraryMusic
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Sort
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.filled.StarBorder
import androidx.compose.material.icons.filled.TextSnippet
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel

/**
 * The Library.
 *
 * Premium cards, each carrying only what helps someone recognise a recording and act on it:
 * title, when, how long, how good it sounds, whether it has a transcript, play, share. Sample
 * rates and file paths are not on the card because nobody scanning a list is looking for them.
 */
@Composable
fun LibraryScreen(
    services: Services,
    onOpen: (Long) -> Unit,
    onStartRecording: () -> Unit,
) {
    val viewModel: LibraryViewModel = viewModel(factory = LibraryViewModel.Factory(services))
    val state by viewModel.state.collectAsStateWithLifecycle()
    val playback by services.playback.state.collectAsStateWithLifecycle()

    var showSearch by remember { mutableStateOf(false) }
    var sortMenuOpen by remember { mutableStateOf(false) }
    var pendingDeletion by remember { mutableStateOf<RecordingEntity?>(null) }

    Column(modifier = Modifier.fillMaxSize()) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = Space.pageHorizontal, vertical = Space.md),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text("Library", style = MaterialTheme.typography.headlineLarge)
                if (state.totalCount > 0) {
                    Text(
                        text = "${state.totalCount} recordings · " +
                            "${Format.duration(state.totalDurationMs)} · " +
                            Format.fileSize(state.totalBytes),
                        style = MaterialTheme.typography.bodySmall,
                        color = sajjilColors.onSurfaceMuted,
                    )
                }
            }
            CircularIconButton(
                icon = Icons.Filled.Search,
                description = "Search recordings",
                onClick = { showSearch = !showSearch },
                tint = sajjilColors.onSurfaceMuted,
            )
            Box {
                CircularIconButton(
                    icon = Icons.Filled.Sort,
                    description = "Change the order",
                    onClick = { sortMenuOpen = true },
                    tint = sajjilColors.onSurfaceMuted,
                )
                DropdownMenu(expanded = sortMenuOpen, onDismissRequest = { sortMenuOpen = false }) {
                    for (sort in LibrarySort.entries) {
                        DropdownMenuItem(
                            text = { Text(sort.label()) },
                            onClick = {
                                viewModel.setSort(sort)
                                sortMenuOpen = false
                            },
                        )
                    }
                }
            }
        }

        if (showSearch) {
            OutlinedTextField(
                value = state.query,
                onValueChange = viewModel::setQuery,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = Space.pageHorizontal),
                placeholder = { Text("Search titles, tags and transcripts") },
                singleLine = true,
            )
            Spacer(Modifier.height(Space.sm))
        }

        when {
            state.isLoading -> Box(Modifier.fillMaxSize())
            state.recordings.isEmpty() && state.query.isNotEmpty() -> EmptyState(
                icon = Icons.Filled.Search,
                title = "Nothing matched",
                body = "No recording has \"${state.query}\" in its title, tags, notes or transcript.",
            )
            state.recordings.isEmpty() -> EmptyState(
                icon = Icons.Filled.LibraryMusic,
                title = "No recordings yet",
                body = "Everything you record appears here, with its waveform, length and quality score.",
                actionLabel = "Start recording",
                onAction = onStartRecording,
            )
            else -> LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = androidx.compose.foundation.layout.PaddingValues(
                    start = Space.pageHorizontal,
                    end = Space.pageHorizontal,
                    bottom = Space.xxl,
                ),
                verticalArrangement = Arrangement.spacedBy(Space.sm),
            ) {
                items(state.recordings, key = { it.id }) { recording ->
                    RecordingCard(
                        recording = recording,
                        hasTranscript = recording.id in state.transcribedIds,
                        isPlaying = playback.isPlaying && playback.recordingId == recording.id,
                        onOpen = { onOpen(recording.id) },
                        onPlayPause = { viewModel.togglePlayback(recording) },
                        onToggleFavourite = { viewModel.toggleFavourite(recording) },
                        onDelete = { pendingDeletion = recording },
                    )
                }
            }
        }
    }

    // Deleting audio is not undoable once the file is gone, so it asks. Nothing else in the app
    // does — every other action is reversible and a confirmation would just be friction.
    pendingDeletion?.let { recording ->
        AlertDialog(
            onDismissRequest = { pendingDeletion = null },
            title = { Text("Delete this recording?") },
            text = {
                Text(
                    "\"${recording.title}\" and its audio will be removed from this device. " +
                        "This cannot be undone."
                )
            },
            confirmButton = {
                TextButton(onClick = {
                    viewModel.delete(recording)
                    pendingDeletion = null
                }) {
                    Text("Delete", color = sajjilColors.problem)
                }
            },
            dismissButton = {
                TextButton(onClick = { pendingDeletion = null }) { Text("Keep") }
            },
        )
    }
}

@Composable
private fun RecordingCard(
    recording: RecordingEntity,
    hasTranscript: Boolean,
    isPlaying: Boolean,
    onOpen: () -> Unit,
    onPlayPause: () -> Unit,
    onToggleFavourite: () -> Unit,
    onDelete: () -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(sajjilColors.surfaceElevated, RoundedCornerShape(Radius.medium))
            .clickable(onClick = onOpen)
            .padding(Space.md),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        // Play sits on the card itself: opening a recording just to hear it would be two taps
        // where one will do.
        Box(
            modifier = Modifier
                .size(48.dp)
                .background(MaterialTheme.colorScheme.primary.copy(alpha = 0.15f), RoundedCornerShape(24.dp))
                .clickable(onClick = onPlayPause),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                imageVector = if (isPlaying) Icons.Filled.Pause else Icons.Filled.PlayArrow,
                contentDescription = if (isPlaying) "Pause" else "Play ${recording.title}",
                tint = MaterialTheme.colorScheme.primary,
            )
        }

        Spacer(Modifier.width(Space.md))

        Column(Modifier.weight(1f)) {
            Text(
                text = recording.title,
                style = MaterialTheme.typography.titleMedium,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Spacer(Modifier.height(2.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = Format.duration(recording.durationMs),
                    style = MaterialTheme.typography.bodySmall,
                    color = sajjilColors.onSurfaceMuted,
                )
                Text(
                    text = " · ${Format.relativeDate(recording.createdAt)}",
                    style = MaterialTheme.typography.bodySmall,
                    color = sajjilColors.onSurfaceMuted,
                )
                recording.qualityScore?.let { score ->
                    Text(
                        text = " · ",
                        style = MaterialTheme.typography.bodySmall,
                        color = sajjilColors.onSurfaceMuted,
                    )
                    Text(
                        text = "$score",
                        style = MaterialTheme.typography.bodySmall,
                        color = when {
                            score >= 85 -> sajjilColors.good
                            score >= 55 -> sajjilColors.caution
                            else -> sajjilColors.problem
                        },
                    )
                }
                if (hasTranscript) {
                    Spacer(Modifier.width(Space.xs))
                    Icon(
                        imageVector = Icons.Filled.TextSnippet,
                        contentDescription = "Has a transcript",
                        tint = sajjilColors.onSurfaceFaint,
                        modifier = Modifier.size(14.dp),
                    )
                }
            }
        }

        CircularIconButton(
            icon = if (recording.isFavourite) Icons.Filled.Star else Icons.Filled.StarBorder,
            description = if (recording.isFavourite) "Remove from favourites" else "Add to favourites",
            onClick = onToggleFavourite,
            tint = if (recording.isFavourite) MaterialTheme.colorScheme.primary else sajjilColors.onSurfaceFaint,
        )
        CircularIconButton(
            icon = Icons.Filled.Delete,
            description = "Delete ${recording.title}",
            onClick = onDelete,
            tint = sajjilColors.onSurfaceFaint,
        )
    }
}

private fun LibrarySort.label(): String = when (this) {
    LibrarySort.NEWEST -> "Newest first"
    LibrarySort.OLDEST -> "Oldest first"
    LibrarySort.LONGEST -> "Longest first"
    LibrarySort.SHORTEST -> "Shortest first"
    LibrarySort.TITLE -> "By title"
    LibrarySort.QUALITY -> "Best sounding first"
}
