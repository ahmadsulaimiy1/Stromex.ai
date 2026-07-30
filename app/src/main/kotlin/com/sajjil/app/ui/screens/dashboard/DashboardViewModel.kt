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
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
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
            // RT60 estimation, loudness/quality metrics, and the spectrogram are three
            // independent read-only passes over the same decoded audio — run them
            // concurrently instead of one after another, per the "unified pipeline must
            // operate concurrently, not sequentially" direction.
            val (report, spectrogram) = withContext(Dispatchers.Default) {
                val audio = WavIO.read(File(recording.filePath).readBytes())
                coroutineScope {
                    val rt60Deferred = async { AcousticAnalyzer.estimateRt60(audio.samples, audio.sampleRate) }
                    val metricsDeferred = async { LoudnessAnalyzer.analyze(audio.samples, audio.sampleRate) }
                    val spectrogramDeferred = async { SpectrogramAnalyzer.compute(audio.samples, audio.sampleRate) }
                    val metrics = metricsDeferred.await()
                    val rt60 = rt60Deferred.await()
                    AudioQualityScorer.score(metrics, rt60) to spectrogramDeferred.await()
                }
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
