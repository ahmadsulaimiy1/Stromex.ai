package com.sajjil.app.ui.screens.analytics

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sajjil.app.ui.components.GlassCard
import com.sajjil.core.analysis.ExecutiveAnalytics
import kotlin.math.roundToInt

@Composable
fun AnalyticsScreen(viewModel: AnalyticsViewModel, modifier: Modifier = Modifier) {
    val analytics by viewModel.analytics.collectAsStateWithLifecycle()

    Column(modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text("Executive Analytics", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.SemiBold)
        Text("Your production output at a glance.", style = MaterialTheme.typography.bodyMedium)

        analytics?.let { data ->
            val tiles = buildTiles(data)
            LazyVerticalGrid(
                columns = GridCells.Fixed(2),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
                modifier = Modifier.fillMaxWidth(),
            ) {
                items(tiles) { tile -> StatTile(tile) }
            }
        }
    }
}

private data class StatTileData(val label: String, val value: String, val emphasis: Boolean = false)

private fun buildTiles(data: ExecutiveAnalytics): List<StatTileData> {
    val trendText = data.improvementTrend?.let {
        val sign = if (it >= 0) "+" else ""
        "$sign${it.roundToInt()} pts"
    } ?: "Not enough history yet"

    return listOf(
        StatTileData("Recording Hours", "%.1f".format(data.totalRecordingHours)),
        StatTileData("Surahs Recorded", "${data.surahsRecorded} / 114"),
        StatTileData("Juz Completed", "${data.juzCompleted} / 30"),
        StatTileData("Average Quality", data.averageQualityScore?.let { "${it.roundToInt()} / 100" } ?: "Not scored yet"),
        StatTileData("Improvement Trend", trendText, emphasis = true),
        StatTileData("Library Size", "${data.librarySize} recordings"),
        StatTileData("Storage Used", formatBytes(data.totalStorageBytes)),
    )
}

private fun formatBytes(bytes: Long): String = when {
    bytes >= 1_073_741_824L -> "%.2f GB".format(bytes / 1_073_741_824.0)
    bytes >= 1_048_576L -> "%.1f MB".format(bytes / 1_048_576.0)
    bytes >= 1024L -> "%.0f KB".format(bytes / 1024.0)
    else -> "$bytes B"
}

@Composable
private fun StatTile(tile: StatTileData) {
    GlassCard {
        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(tile.label, style = MaterialTheme.typography.labelMedium)
            Text(
                tile.value,
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.SemiBold,
                color = if (tile.emphasis) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface,
            )
        }
    }
}
