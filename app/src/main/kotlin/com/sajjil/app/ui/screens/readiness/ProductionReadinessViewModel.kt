package com.sajjil.app.ui.screens.readiness

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sajjil.app.data.db.RecordingEntity
import com.sajjil.app.di.asSajjilApplication
import com.sajjil.core.analysis.AnalyticsCalculator
import com.sajjil.core.analysis.AudioQualityScorer
import com.sajjil.core.analysis.LoudnessAnalyzer
import com.sajjil.core.analysis.RecordingSummary
import com.sajjil.core.audio.WavIO
import com.sajjil.core.assistant.ProjectAssistant
import com.sajjil.core.assistant.ProjectInsight
import com.sajjil.core.quran.AyahRange
import com.sajjil.core.quran.JuzProgressCalculator
import com.sajjil.core.quran.QuranMetadata
import com.sajjil.core.quran.RecordedTake
import com.sajjil.core.quran.SurahProgressCalculator
import com.sajjil.core.readiness.ProductionReadinessCalculator
import com.sajjil.core.readiness.ProductionReadinessReport
import com.sajjil.core.readiness.ReadinessTake
import java.io.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

data class ProductionReadinessUiState(
    val library: List<RecordingEntity> = emptyList(),
    val report: ProductionReadinessReport? = null,
    val insights: List<ProjectInsight> = emptyList(),
    val isChecking: Boolean = false,
    val checkedCount: Int = 0,
)

/**
 * SAJJIL Production Readiness Center: a single score plus a concrete
 * checklist before a Qur'an project ships. The clipping/noise checks read
 * each recording's actual audio (peak level, noise floor) rather than
 * reusing a cached readiness score — those already-persisted scores are
 * a *composite* number, not the raw measurement Readiness needs to tell
 * "this take clips" from "this take is just quiet." Because that means
 * reading every WAV file in the library, the check is explicit and
 * user-initiated ([runCheck]), the same tradeoff Batch Production makes,
 * not run automatically every time this screen opens.
 */
class ProductionReadinessViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application.asSajjilApplication()

    private val _uiState = MutableStateFlow(ProductionReadinessUiState())
    val uiState: StateFlow<ProductionReadinessUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            app.recordingRepository.observeQuranLibrary().collect { library ->
                _uiState.value = _uiState.value.copy(library = library)
            }
        }
    }

    fun runCheck() {
        val state = _uiState.value
        if (state.isChecking) return
        val primaryTakes = state.library.filter { it.isPrimaryVersion && it.ayahStart != null && it.ayahEnd != null }
        if (primaryTakes.isEmpty()) {
            _uiState.value = state.copy(report = ProductionReadinessCalculator.evaluate(QuranMetadata.surahs, emptyList()))
            return
        }

        _uiState.value = state.copy(isChecking = true, checkedCount = 0)
        viewModelScope.launch {
            val readinessTakes = withContext(Dispatchers.Default) {
                primaryTakes.map { recording ->
                    val take = measureTake(recording)
                    _uiState.value = _uiState.value.copy(checkedCount = _uiState.value.checkedCount + 1)
                    take
                }
            }

            val report = ProductionReadinessCalculator.evaluate(QuranMetadata.surahs, readinessTakes)
            val insights = computeInsights(state.library)
            _uiState.value = _uiState.value.copy(report = report, insights = insights, isChecking = false)
        }
    }

    private fun measureTake(recording: RecordingEntity): ReadinessTake {
        val fallback = ReadinessTake(
            recordingId = recording.id,
            title = recording.title,
            surahNumber = recording.surahNumber,
            ayahRange = AyahRange(recording.ayahStart!!, recording.ayahEnd!!),
            hasClipping = false,
        )
        return try {
            val audio = WavIO.read(File(recording.filePath).readBytes())
            val metrics = LoudnessAnalyzer.analyze(audio.samples, audio.sampleRate)
            val report = AudioQualityScorer.score(metrics)
            fallback.copy(
                hasClipping = metrics.peakDb > -0.1,
                noiseScore = report.noiseScore,
                integratedLoudnessLufs = metrics.integratedLoudnessLufs,
            )
        } catch (e: java.io.IOException) {
            fallback
        }
    }

    private fun computeInsights(library: List<RecordingEntity>): List<ProjectInsight> {
        val tagged = library.filter { it.isPrimaryVersion && it.surahNumber != null && it.ayahStart != null && it.ayahEnd != null }
        val takesBySurah = tagged.groupBy { it.surahNumber!! }
            .mapValues { (_, recs) -> recs.map { RecordedTake(AyahRange(it.ayahStart!!, it.ayahEnd!!), it.studioReadinessScore) } }

        val surahProgresses = QuranMetadata.surahs.map { SurahProgressCalculator.compute(it, takesBySurah[it.number].orEmpty()) }
        val juzProgresses = (1..30).map { JuzProgressCalculator.compute(it, takesBySurah) }

        val summaries = library.map {
            RecordingSummary(it.durationMs, it.createdAtEpochMs, it.surahNumber, it.ayahStart, it.ayahEnd, it.studioReadinessScore, it.fileSizeBytes)
        }
        val analytics = AnalyticsCalculator.compute(summaries)

        return ProjectAssistant.analyze(surahProgresses, juzProgresses, analytics).insights
    }
}
