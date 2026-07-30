package com.sajjil.app.ui.screens.readiness

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Error
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sajjil.app.ui.components.GlassCard
import com.sajjil.core.assistant.InsightCategory
import com.sajjil.core.assistant.ProjectInsight
import com.sajjil.core.readiness.ReadinessIssue
import com.sajjil.core.readiness.ReadinessSeverity

@Composable
fun ProductionReadinessScreen(viewModel: ProductionReadinessViewModel, modifier: Modifier = Modifier) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    LazyColumn(modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        item {
            Text("Production Readiness Center", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.SemiBold)
            Text(
                "One score, and exactly what's stopping it from being higher.",
                style = MaterialTheme.typography.bodyMedium,
            )
        }

        item {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Button(onClick = viewModel::runCheck, enabled = !state.isChecking) {
                    Text(if (state.isChecking) "Checking…" else "Run Readiness Check")
                }
                if (state.isChecking) {
                    CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp)
                    Text("${state.checkedCount} / ${state.library.count { it.isPrimaryVersion }}", style = MaterialTheme.typography.bodySmall)
                }
            }
        }

        state.report?.let { report ->
            item {
                GlassCard {
                    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text(report.label, style = MaterialTheme.typography.headlineLarge, fontWeight = FontWeight.Bold)
                        Text(
                            "${report.coveredAyahs} / ${report.totalAyahs} ayahs recorded (${"%.1f".format(report.percentComplete)}%)",
                            style = MaterialTheme.typography.bodyMedium,
                        )
                        if (report.issues.isEmpty()) {
                            Text("No issues found.", style = MaterialTheme.typography.bodyMedium)
                        }
                    }
                }
            }

            items(report.issues.sortedByDescending { it.severity.ordinal }) { issue -> IssueRow(issue) }
        }

        if (state.insights.isNotEmpty()) {
            item { Text("Project Assistant", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold) }
            items(state.insights) { insight -> InsightRow(insight) }
        }
    }
}

@Composable
private fun IssueRow(issue: ReadinessIssue) {
    GlassCard {
        Row(verticalAlignment = Alignment.Top, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            val (icon, tint) = when (issue.severity) {
                ReadinessSeverity.CRITICAL -> Icons.Filled.Error to Color(0xFFC62828)
                ReadinessSeverity.WARNING -> Icons.Filled.Warning to Color(0xFFF9A825)
                ReadinessSeverity.INFO -> Icons.Filled.Info to Color(0xFF1565C0)
            }
            Icon(icon, contentDescription = null, tint = tint)
            Column {
                Text(issue.category, fontWeight = FontWeight.SemiBold)
                Text(issue.message, style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}

@Composable
private fun InsightRow(insight: ProjectInsight) {
    GlassCard {
        Text(categoryLabel(insight.category), style = MaterialTheme.typography.labelMedium)
        Text(insight.message, style = MaterialTheme.typography.bodyMedium)
    }
}

private fun categoryLabel(category: InsightCategory): String = when (category) {
    InsightCategory.PROGRESS -> "Progress"
    InsightCategory.QUALITY -> "Quality"
    InsightCategory.RECOMMENDATION -> "Recommendation"
}
