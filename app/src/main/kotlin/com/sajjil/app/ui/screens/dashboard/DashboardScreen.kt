package com.sajjil.app.ui.screens.dashboard

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sajjil.app.ui.components.GlassCard
import com.sajjil.app.ui.components.SpectrogramView
import com.sajjil.core.analysis.AudioAnalysisReport

@Composable
fun DashboardScreen(viewModel: DashboardViewModel, recordingId: Long, modifier: Modifier = Modifier) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    LaunchedEffect(recordingId) { viewModel.load(recordingId) }

    Column(
        modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text("Executive Dashboard", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.SemiBold)

        if (state.isLoading) {
            CircularProgressIndicator()
            return@Column
        }

        state.recording?.let { recording -> Text(recording.title, style = MaterialTheme.typography.titleLarge) }

        state.report?.let { report -> DashboardScores(report) }

        state.spectrogram?.let { spectrogram ->
            Text("Spectrogram", style = MaterialTheme.typography.titleMedium)
            SpectrogramView(spectrogram)
        }
    }
}

@Composable
private fun DashboardScores(report: AudioAnalysisReport) {
    GlassCard {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            ScoreMeter("Studio Readiness", report.studioReadinessScore)
            ScoreMeter("Broadcast Readiness", report.broadcastReadinessScore)
            ScoreMeter("Archive Readiness", report.archiveReadinessScore)
            ScoreMeter("Clarity Score", report.clarityScore)
            ScoreMeter("Noise Score", report.noiseScore)
            ScoreMeter("Loudness Score", report.loudnessScore)
            ScoreMeter("Dynamics Score", report.dynamicsScore)
            report.echoScore?.let { ScoreMeter("Echo Score", it) }

            Text("Loudness Metrics", style = MaterialTheme.typography.titleMedium)
            Text("Peak: ${"%.1f".format(report.loudness.peakDb)} dBFS")
            Text("RMS: ${"%.1f".format(report.loudness.rmsDb)} dBFS")
            Text("Integrated Loudness: ${"%.1f".format(report.loudness.integratedLoudnessLufs)} LUFS")
            Text("Dynamic Range: ${"%.1f".format(report.loudness.dynamicRangeDb)} dB")
            Text("Noise Floor: ${"%.1f".format(report.loudness.noiseFloorDb)} dBFS")
        }
    }
}

@Composable
private fun ScoreMeter(label: String, score: Int) {
    Column {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Text(label, style = MaterialTheme.typography.bodyMedium)
            Text("$score / 100", style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold)
        }
        LinearProgressIndicator(
            progress = { score / 100f },
            modifier = Modifier.fillMaxWidth(),
        )
    }
}
