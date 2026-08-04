package ai.sajjil.app.ui.quran

import ai.sajjil.app.Services
import ai.sajjil.app.data.QuranProjectEntity
import ai.sajjil.app.ui.components.EmptyState
import ai.sajjil.app.ui.theme.Radius
import ai.sajjil.app.ui.theme.Space
import ai.sajjil.app.ui.theme.sajjilColors
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
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
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
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
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel

/**
 * Qur'an Studio.
 *
 * A project is a surah, a juz, or the whole Qur'an, and its unit of work is an ayah range with
 * several takes to choose between. Progress is the share of ayat that have a chosen take — which
 * is the only number a reciter actually wants, and it is shown as a ring rather than a table.
 */
@Composable
fun QuranScreen(
    services: Services,
    onOpenRecording: (Long) -> Unit,
    onStartRecording: () -> Unit,
) {
    val viewModel: QuranViewModel = viewModel(factory = QuranViewModel.Factory(services))
    val state by viewModel.state.collectAsStateWithLifecycle()
    var showNewProject by remember { mutableStateOf(false) }

    Column(modifier = Modifier.fillMaxSize()) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = Space.pageHorizontal, vertical = Space.md),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text("Qur'an", style = MaterialTheme.typography.headlineLarge)
                if (state.projects.isNotEmpty()) {
                    Text(
                        text = "${state.projects.size} projects",
                        style = MaterialTheme.typography.bodySmall,
                        color = sajjilColors.onSurfaceMuted,
                    )
                }
            }
            Button(onClick = { showNewProject = true }) {
                Icon(Icons.Filled.Add, contentDescription = null)
                Spacer(Modifier.width(Space.xs))
                Text("New project")
            }
        }

        if (state.projects.isEmpty()) {
            EmptyState(
                icon = Icons.Filled.MenuBook,
                title = "No Qur'an projects yet",
                body = "A project tracks a surah, a juz or the whole Qur'an — every ayah, every take, " +
                    "and how far through you are.",
                actionLabel = "Create a project",
                onAction = { showNewProject = true },
            )
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(
                    start = Space.pageHorizontal,
                    end = Space.pageHorizontal,
                    bottom = Space.xxl,
                ),
                verticalArrangement = Arrangement.spacedBy(Space.sm),
            ) {
                items(state.projects, key = { it.id }) { project ->
                    ProjectCard(
                        project = project,
                        completedAyah = state.completedByProject[project.id] ?: 0,
                        onClick = { viewModel.selectProject(project.id) },
                    )
                }
            }
        }
    }

    if (showNewProject) {
        NewProjectDialog(
            onDismiss = { showNewProject = false },
            onCreate = { name, kind, number, totalAyah ->
                viewModel.createProject(name, kind, number, totalAyah)
                showNewProject = false
            },
        )
    }
}

@Composable
private fun ProjectCard(
    project: QuranProjectEntity,
    completedAyah: Int,
    onClick: () -> Unit,
) {
    val fraction = if (project.totalAyah <= 0) 0f else completedAyah.toFloat() / project.totalAyah

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(sajjilColors.surfaceElevated, RoundedCornerShape(Radius.medium))
            .clickable(onClick = onClick)
            .padding(Space.md),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        ProgressRing(fraction = fraction, label = "$completedAyah/${project.totalAyah}")
        Spacer(Modifier.width(Space.md))
        Column(Modifier.weight(1f)) {
            Text(
                text = project.name,
                style = MaterialTheme.typography.titleMedium,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Text(
                text = when (project.kind) {
                    QuranProjectKind.SURAH.name -> "Surah ${project.surahNumber ?: ""}".trim()
                    QuranProjectKind.JUZ.name -> "Juz ${project.juzNumber ?: ""}".trim()
                    else -> "Complete Qur'an"
                },
                style = MaterialTheme.typography.bodySmall,
                color = sajjilColors.onSurfaceMuted,
            )
        }
    }
}

/** Progress as a ring, which reads at a glance where a percentage does not. */
@Composable
private fun ProgressRing(fraction: Float, label: String) {
    val colors = sajjilColors
    // Read outside the Canvas: a DrawScope is not a composable scope.
    val progressColor = if (fraction >= 1f) colors.good else MaterialTheme.colorScheme.primary
    Box(
        modifier = Modifier.size(64.dp),
        contentAlignment = Alignment.Center,
    ) {
        Canvas(Modifier.fillMaxSize()) {
            val stroke = size.minDimension * 0.09f
            drawArc(
                color = colors.onSurfaceFaint.copy(alpha = 0.2f),
                startAngle = -90f,
                sweepAngle = 360f,
                useCenter = false,
                style = Stroke(width = stroke, cap = StrokeCap.Round),
                topLeft = androidx.compose.ui.geometry.Offset(stroke / 2, stroke / 2),
                size = androidx.compose.ui.geometry.Size(size.width - stroke, size.height - stroke),
            )
            drawArc(
                color = progressColor,
                startAngle = -90f,
                sweepAngle = 360f * fraction.coerceIn(0f, 1f),
                useCenter = false,
                style = Stroke(width = stroke, cap = StrokeCap.Round),
                topLeft = androidx.compose.ui.geometry.Offset(stroke / 2, stroke / 2),
                size = androidx.compose.ui.geometry.Size(size.width - stroke, size.height - stroke),
            )
        }
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = sajjilColors.onSurfaceMuted,
        )
    }
}

enum class QuranProjectKind(val label: String, val defaultTotalAyah: Int) {
    SURAH("A surah", 7),
    JUZ("A juz", 200),
    FULL("The whole Qur'an", 6236),
}

@Composable
private fun NewProjectDialog(
    onDismiss: () -> Unit,
    onCreate: (String, QuranProjectKind, Int?, Int) -> Unit,
) {
    var name by remember { mutableStateOf("") }
    var kind by remember { mutableStateOf(QuranProjectKind.SURAH) }
    var number by remember { mutableStateOf("") }
    var totalAyah by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("New project") },
        text = {
            Column {
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("Name") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                Spacer(Modifier.height(Space.md))
                Row(horizontalArrangement = Arrangement.spacedBy(Space.sm)) {
                    for (option in QuranProjectKind.entries) {
                        val selected = option == kind
                        Text(
                            text = option.label,
                            style = MaterialTheme.typography.labelMedium,
                            color = if (selected) {
                                MaterialTheme.colorScheme.primary
                            } else {
                                sajjilColors.onSurfaceMuted
                            },
                            modifier = Modifier
                                .clickable { kind = option }
                                .padding(Space.sm),
                        )
                    }
                }
                if (kind != QuranProjectKind.FULL) {
                    Spacer(Modifier.height(Space.sm))
                    OutlinedTextField(
                        value = number,
                        onValueChange = { number = it.filter(Char::isDigit) },
                        label = { Text(if (kind == QuranProjectKind.SURAH) "Surah number" else "Juz number") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
                Spacer(Modifier.height(Space.sm))
                OutlinedTextField(
                    value = totalAyah,
                    onValueChange = { totalAyah = it.filter(Char::isDigit) },
                    label = { Text("Number of ayat") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        },
        confirmButton = {
            TextButton(
                enabled = name.isNotBlank(),
                onClick = {
                    onCreate(
                        name.trim(),
                        kind,
                        number.toIntOrNull(),
                        totalAyah.toIntOrNull() ?: kind.defaultTotalAyah,
                    )
                },
            ) {
                Text("Create")
            }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } },
    )
}
