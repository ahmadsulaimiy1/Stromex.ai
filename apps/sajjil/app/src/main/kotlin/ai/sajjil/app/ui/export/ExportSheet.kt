package ai.sajjil.app.ui.export

import ai.sajjil.app.Services
import ai.sajjil.app.audio.ExportFormat
import ai.sajjil.app.audio.ExportQuality
import ai.sajjil.app.audio.ExportResult
import ai.sajjil.app.ui.Format
import ai.sajjil.app.ui.theme.Radius
import ai.sajjil.app.ui.theme.Space
import ai.sajjil.app.ui.theme.sajjilColors
import android.content.Intent
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider

/**
 * Export.
 *
 * Three decisions and a button: format, quality, go. Where the file ends up is Android's
 * business, not this app's — the share sheet already knows about every destination the user has,
 * including their SD card, their cloud drives and their messaging apps, and reimplementing a file
 * browser here would be both worse and less capable.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ExportSheet(
    services: Services,
    onDismiss: () -> Unit,
    onExport: (ExportFormat, ExportQuality) -> Unit,
    lastExport: ExportResult? = null,
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val context = LocalContext.current

    // Only formats this device can genuinely produce. A format that would fail is never offered.
    val formats = remember { ExportFormat.availableOn() }
    var selectedFormat by remember { mutableStateOf(ExportFormat.M4A) }
    var selectedQuality by remember { mutableStateOf(ExportQuality.DEFAULT) }

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = sheetState,
        containerColor = sajjilColors.surfaceElevated,
        shape = RoundedCornerShape(topStart = Radius.sheet, topEnd = Radius.sheet),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = Space.pageHorizontal)
                .padding(bottom = Space.xxl),
        ) {
            Text("Export", style = MaterialTheme.typography.headlineMedium)
            Spacer(Modifier.height(Space.lg))

            Text(
                "Format",
                style = MaterialTheme.typography.labelMedium,
                color = sajjilColors.onSurfaceMuted,
            )
            Spacer(Modifier.height(Space.sm))
            for (format in formats) {
                OptionRow(
                    title = format.displayName,
                    summary = format.summary,
                    trailing = if (format.isLossless) "Lossless" else null,
                    selected = format == selectedFormat,
                    onClick = { selectedFormat = format },
                )
                Spacer(Modifier.height(Space.sm))
            }

            if (formats.none { it == ExportFormat.MP3 }) {
                // Said once, plainly, rather than leaving someone hunting for a missing option.
                Text(
                    text = "This device has no MP3 encoder, so MP3 is not offered. M4A is the same " +
                        "size and plays everywhere MP3 does.",
                    style = MaterialTheme.typography.bodySmall,
                    color = sajjilColors.onSurfaceFaint,
                )
                Spacer(Modifier.height(Space.sm))
            }

            if (!selectedFormat.isLossless) {
                Spacer(Modifier.height(Space.md))
                Text(
                    "Quality",
                    style = MaterialTheme.typography.labelMedium,
                    color = sajjilColors.onSurfaceMuted,
                )
                Spacer(Modifier.height(Space.sm))
                Row(horizontalArrangement = Arrangement.spacedBy(Space.sm)) {
                    for (quality in ExportQuality.entries) {
                        QualityChip(
                            quality = quality,
                            selected = quality == selectedQuality,
                            onClick = { selectedQuality = quality },
                            modifier = Modifier.weight(1f),
                        )
                    }
                }
            }

            Spacer(Modifier.height(Space.lg))

            Button(
                onClick = { onExport(selectedFormat, selectedQuality) },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                shape = RoundedCornerShape(Radius.medium),
            ) {
                Text("Export as ${selectedFormat.displayName}")
            }

            lastExport?.let { result ->
                Spacer(Modifier.height(Space.md))
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(sajjilColors.good.copy(alpha = 0.12f), RoundedCornerShape(Radius.small))
                        .padding(Space.md),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(Modifier.weight(1f)) {
                        Text(
                            text = "${result.format.displayName} ready",
                            style = MaterialTheme.typography.titleMedium,
                            color = sajjilColors.good,
                        )
                        Text(
                            text = Format.fileSize(result.sizeBytes),
                            style = MaterialTheme.typography.bodySmall,
                            color = sajjilColors.onSurfaceMuted,
                        )
                    }
                    TextButton(onClick = {
                        val uri = FileProvider.getUriForFile(
                            context,
                            "${context.packageName}.fileprovider",
                            result.file,
                        )
                        context.startActivity(
                            Intent.createChooser(
                                Intent(Intent.ACTION_SEND).apply {
                                    type = result.format.mimeType
                                    putExtra(Intent.EXTRA_STREAM, uri)
                                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                                },
                                "Share recording",
                            )
                        )
                    }) {
                        Text("Share")
                    }
                }
            }
        }
    }
}

@Composable
private fun OptionRow(
    title: String,
    summary: String,
    trailing: String?,
    selected: Boolean,
    onClick: () -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(
                if (selected) MaterialTheme.colorScheme.primary.copy(alpha = 0.10f) else Color.Transparent,
                RoundedCornerShape(Radius.medium),
            )
            .border(
                if (selected) 2.dp else 1.dp,
                if (selected) {
                    MaterialTheme.colorScheme.primary
                } else {
                    MaterialTheme.colorScheme.outline.copy(alpha = 0.5f)
                },
                RoundedCornerShape(Radius.medium),
            )
            .clickable(onClick = onClick)
            .padding(Space.md),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f)) {
            Text(text = title, style = MaterialTheme.typography.titleMedium)
            Text(
                text = summary,
                style = MaterialTheme.typography.bodySmall,
                color = sajjilColors.onSurfaceMuted,
            )
        }
        if (trailing != null) {
            Spacer(Modifier.width(Space.sm))
            Text(
                text = trailing,
                style = MaterialTheme.typography.labelSmall,
                color = sajjilColors.good,
            )
        }
    }
}

@Composable
private fun QualityChip(
    quality: ExportQuality,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .background(
                if (selected) MaterialTheme.colorScheme.primary.copy(alpha = 0.12f) else Color.Transparent,
                RoundedCornerShape(Radius.small),
            )
            .border(
                if (selected) 2.dp else 1.dp,
                if (selected) {
                    MaterialTheme.colorScheme.primary
                } else {
                    MaterialTheme.colorScheme.outline.copy(alpha = 0.5f)
                },
                RoundedCornerShape(Radius.small),
            )
            .clickable(onClick = onClick)
            .padding(vertical = Space.sm, horizontal = Space.xs),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            text = quality.displayName,
            style = MaterialTheme.typography.labelMedium,
            color = if (selected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface,
        )
        Text(
            text = "${quality.bitrate / 1000}k",
            style = MaterialTheme.typography.labelSmall,
            color = sajjilColors.onSurfaceFaint,
        )
    }
}
