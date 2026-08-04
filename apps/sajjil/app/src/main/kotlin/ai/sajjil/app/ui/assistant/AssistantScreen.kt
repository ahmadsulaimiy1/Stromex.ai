package ai.sajjil.app.ui.assistant

import ai.sajjil.app.Services
import ai.sajjil.app.ui.Format
import ai.sajjil.app.ui.components.QualityRing
import ai.sajjil.app.ui.theme.Radius
import ai.sajjil.app.ui.theme.Space
import ai.sajjil.app.ui.theme.sajjilColors
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel

/**
 * The Assistant.
 *
 * A read-out of what SAJJIL has measured across the library, and what would improve the next
 * recording. Everything here is computed on this device from measurements the app already has —
 * there is no model and no network call, and the screen says so rather than implying otherwise.
 */
@Composable
fun AssistantScreen(services: Services) {
    val viewModel: AssistantViewModel = viewModel(factory = AssistantViewModel.Factory(services))
    val state by viewModel.state.collectAsStateWithLifecycle()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = Space.pageHorizontal),
    ) {
        Spacer(Modifier.height(Space.md))
        Text("Assistant", style = MaterialTheme.typography.headlineLarge)
        Text(
            text = "Measured on this device. Nothing is uploaded.",
            style = MaterialTheme.typography.bodySmall,
            color = sajjilColors.onSurfaceMuted,
        )

        Spacer(Modifier.height(Space.lg))

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(sajjilColors.surfaceElevated, RoundedCornerShape(Radius.medium))
                .padding(Space.md),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            QualityRing(
                score = state.averageQuality,
                grade = state.averageGrade,
                label = "Average quality",
            )
            Spacer(Modifier.height(Space.md))
            Column(Modifier.padding(start = Space.md)) {
                Statistic("Recordings", state.recordingCount.toString())
                Statistic("Total length", Format.duration(state.totalDurationMs))
                Statistic("On this device", Format.fileSize(state.totalBytes))
            }
        }

        Spacer(Modifier.height(Space.lg))

        Text("What would help next time", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(Space.sm))

        if (state.suggestions.isEmpty()) {
            Text(
                text = if (state.recordingCount == 0) {
                    "Record something and SAJJIL will start measuring how it sounds."
                } else {
                    "Nothing to flag — your recordings are measuring well."
                },
                style = MaterialTheme.typography.bodyMedium,
                color = sajjilColors.onSurfaceMuted,
            )
        } else {
            Column(verticalArrangement = Arrangement.spacedBy(Space.sm)) {
                for (suggestion in state.suggestions) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(sajjilColors.surfaceElevated, RoundedCornerShape(Radius.medium))
                            .padding(Space.md),
                    ) {
                        Text(suggestion.title, style = MaterialTheme.typography.titleMedium)
                        Spacer(Modifier.height(Space.xs))
                        Text(
                            text = suggestion.body,
                            style = MaterialTheme.typography.bodySmall,
                            color = sajjilColors.onSurfaceMuted,
                        )
                    }
                }
            }
        }

        Spacer(Modifier.height(Space.lg))

        Text("Transcription", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(Space.sm))
        Text(
            text = "SAJJIL uses Android's own speech recognition, which works offline on devices " +
                "that have a language pack installed and needs a connection on those that do not. " +
                "Arabic and English are both supported where the device provides them.",
            style = MaterialTheme.typography.bodySmall,
            color = sajjilColors.onSurfaceMuted,
        )

        Spacer(Modifier.height(Space.xxl))
    }
}

@Composable
private fun Statistic(label: String, value: String) {
    Row(
        modifier = Modifier.padding(vertical = 2.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = value,
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurface,
        )
        Spacer(Modifier.padding(horizontal = Space.xs))
        Text(
            text = label,
            style = MaterialTheme.typography.bodySmall,
            color = sajjilColors.onSurfaceMuted,
        )
    }
}
