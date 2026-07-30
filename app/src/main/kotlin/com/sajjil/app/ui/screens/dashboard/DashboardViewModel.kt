package com.sajjil.app.ui.screens.dashboard

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.app.di.asSajjilApplication
import com.sajjil.core.analysis.AcousticAnalyzer
import com.sajjil.core.analysis.AudioAnalysisReport
import com.sajjil.core.analysis.AudioQualityScorer
import com.sajjil.core.analysis.LoudnessAnalyzer
import com.sajjil.core.analysis.Spectrogram
import com.sajjil.core.analysis.SpectrogramAnalyzer
import com.sajjil.core.audio.WavIO
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

data class DashboardUiState(
    val recording: RecordingEntity? = null,
    val report: AudioAnalysisReport? = null,
    val spectrogram: Spectrogram? = null,
    val isLoading: Boolean = true,
)

class DashboardViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application.asSajjilApplication()

    private val _uiState = MutableStateFlow(DashboardUiState())
    val uiState: StateFlow<DashboardUiState> = _uiState.asStateFlow()

    fun load(recordingId: Long) {
        viewModelScope.launch {
            val recording = app.recordingRepository.getById(recordingId) ?: return@launch
            val (report, spectrogram) = withContext(Dispatchers.Default) {
                val audio = WavIO.read(File(recording.filePath).readBytes())
                val rt60 = AcousticAnalyzer.estimateRt60(audio.samples, audio.sampleRate)
                val metrics = LoudnessAnalyzer.analyze(audio.samples, audio.sampleRate)
                AudioQualityScorer.score(metrics, rt60) to SpectrogramAnalyzer.compute(audio.samples, audio.sampleRate)
            }
            _uiState.value = DashboardUiState(recording = recording, report = report, spectrogram = spectrogram, isLoading = false)

            // Persist the freshly computed scores so Executive Analytics (average quality,
            // improvement trend, Juz completion) has real numbers to work with instead of
            // every recording sitting at a permanent null score.
            if (recording.studioReadinessScore != report.studioReadinessScore ||
                recording.broadcastReadinessScore != report.broadcastReadinessScore ||
                recording.archiveReadinessScore != report.archiveReadinessScore
            ) {
                app.recordingRepository.update(
                    recording.copy(
                        studioReadinessScore = report.studioReadinessScore,
                        broadcastReadinessScore = report.broadcastReadinessScore,
                        archiveReadinessScore = report.archiveReadinessScore,
                    ),
                )
            }
        }
    }
}
